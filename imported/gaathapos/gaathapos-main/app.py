import logging
import uuid
from flask import Flask, render_template, jsonify, request, redirect, url_for, g
from extensions import db, migrate, login_manager, csrf, limiter
from datetime import datetime
from sqlalchemy import text
from config import Config
from blueprints import register_blueprints
import models  # noqa: F401


def generic_error_response(message="An unexpected error occurred. Please try again later.", status=500):
    return jsonify({"error": message}), status


def initialize_database(app):
    """Create the database schema on startup and repair known schema mismatches."""
    with app.app_context():
        try:
            db.create_all()
        except Exception as exc:
            app.logger.warning("Database initialization skipped: %s", exc)

        try:
            engine_url = str(db.engine.url).lower()
            if engine_url.startswith("postgresql"):
                from sqlalchemy import text
                db.session.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(512)'))
                db.session.commit()
        except Exception as exc:
            db.session.rollback()
            app.logger.warning("Password hash column repair skipped: %s", exc)


def create_app():
    app = Flask(__name__)
    # 🔧 Ensure the Flask 'instance' directory exists early during startup.
    # This prevents SQLite from failing to create the DB file when the
    # default DB path is `instance/app.db` and the `instance/` folder is missing.
    import os
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        app.logger.debug(f"Ensured instance dir exists: {app.instance_path}")
    except Exception:
        # Ignore any error here (permissions/race conditions should not block app start)
        pass
    app.config.from_object(Config)
    if app.config.get("USE_PROXY_FIX"):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

    app.logger.setLevel(getattr(logging, str(app.config.get("LOG_LEVEL", "INFO")).upper(), logging.INFO))

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    # Ensure templates can call `csrf_token()` even if Flask-WTF doesn't auto-register it
    try:
        from flask_wtf.csrf import generate_csrf
        app.jinja_env.globals['csrf_token'] = lambda: generate_csrf()
    except Exception:
        pass
    from extensions import babel
    babel.init_app(app)
    # Register locale selector if available
    try:
        from extensions import get_locale
        # Some Flask-Babel versions expose a 'localeselector' decorator on the Babel instance,
        # others expect registration via function call. Try both defensively.
        try:
            babel.localeselector(get_locale)
        except Exception:
            try:
                # fallback to attribute-based registration
                babel.get_locale = get_locale
            except Exception:
                pass
    except Exception:
        pass

    # Initialise the database schema before serving requests or running tasks.
    initialize_database(app)

    # Register blueprints
    register_blueprints(app)

    # Register the new dashboard API blueprint
    from routes import dashboard_api_bp
    app.register_blueprint(dashboard_api_bp)

    # Inject current year into all templates
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.utcnow().year}

    # Start exchange rate updater if enabled
    try:
        if app.config.get('ENABLE_EXCHANGE_UPDATER', True):
            from extensions import schedule_exchange_rate_updater, update_exchange_rates
            # perform a first-time immediate update
            with app.app_context():
                update_exchange_rates(app)
            # schedule background updates
            schedule_exchange_rate_updater(app, interval_seconds=app.config.get('EXCHANGE_UPDATE_INTERVAL', 60*60*6))
    except Exception:
        pass

    @login_manager.unauthorized_handler
    def handle_unauthorized():
        if request.accept_mimetypes.accept_json:
            return generic_error_response("Authentication required", 401)
        return redirect(url_for("auth.login"))

    @app.errorhandler(400)
    def handle_bad_request(error):
        return generic_error_response("The request could not be processed.", 400)

    @app.errorhandler(401)
    def handle_unauthorized_error(error):
        return generic_error_response("Authentication required", 401)

    @app.errorhandler(403)
    def handle_forbidden(error):
        return generic_error_response("Access denied", 403)

    @app.errorhandler(404)
    def handle_not_found(error):
        return generic_error_response("Resource not found", 404)

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return generic_error_response("Method not allowed", 405)

    @app.errorhandler(500)
    def handle_server_error(error):
        app.logger.exception("Unhandled server error", exc_info=error)
        return generic_error_response("An unexpected error occurred. Please try again later.", 500)

    @app.before_request
    def attach_request_context():
        request_id = request.headers.get("X-Request-ID") or f"pos-{uuid.uuid4()}"
        g.request_id = request_id
        g.current_module = "pos"

    @app.after_request
    def apply_security_headers(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Request-ID"] = getattr(g, "request_id", request.headers.get("X-Request-ID") or "pos-request")
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # Root route
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/about")
    def about():
        return render_template("public_info.html", page="about")

    @app.route("/contact")
    def contact():
        return render_template("public_info.html", page="contact")

    @app.route("/terms")
    def terms():
        return render_template("public_info.html", page="terms")

    @app.route("/privacy")
    def privacy():
        return render_template("public_info.html", page="privacy")

    @app.route("/user-policy")
    def user_policy():
        return render_template("public_info.html", page="user-policy")

    @app.route("/health")
    def health_check():
        try:
            db.session.execute(text('SELECT 1'))
            return {"status": "healthy", "database": "connected"}, 200
        except Exception:
            app.logger.exception("Health check failed")
            return {"status": "unhealthy", "database": "disconnected"}, 503

    @app.route("/api/v1/health")
    def api_health_check():
        try:
            db.session.execute(text('SELECT 1'))
            return {
                "service": "gaatha-pos",
                "status": "healthy",
                "dependencies": {"database": "available"},
            }, 200
        except Exception:
            app.logger.exception("API health check failed")
            return {
                "service": "gaatha-pos",
                "status": "unhealthy",
                "dependencies": {"database": "unavailable"},
            }, 503

    @app.route("/ready")
    @app.route("/readyz")
    def readiness_check():
        checks = {"database": False, "redis": "disabled"}
        try:
            db.session.execute(text('SELECT 1'))
            checks["database"] = True
        except Exception:
            app.logger.exception("Readiness check failed at database")

        redis_url = app.config.get("RATELIMIT_STORAGE_URI")
        if redis_url:
            try:
                import redis
                client = redis.Redis.from_url(redis_url, decode_responses=True)
                client.ping()
                checks["redis"] = "ready"
            except Exception as exc:
                app.logger.warning("Redis readiness check failed: %s", exc)
                checks["redis"] = "unavailable"

        ready = checks["database"] and checks["redis"] in {"ready", "disabled"}
        payload = {
            "status": "ready" if ready else "degraded",
            "database": "connected" if checks["database"] else "disconnected",
            "redis": checks["redis"],
        }
        return payload, 200 if ready else 503

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3006, debug=True)
