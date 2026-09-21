# Blueprint Registration Manager

def register_blueprints(app):
    # Import blueprints
    from .admin.routes import admin_bp
    from .analytics.routes import analytics_bp
    from .api.routes import api_bp
    from .auth.routes import auth_bp
    from .inventory.routes import inventory_bp
    from .kds.routes import kds_bp
    from .menu.routes import menu_bp
    from .pos.routes import pos_bp
    from .payments.routes import payments_bp

    # Register with correct URL prefixes
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(kds_bp, url_prefix="/kds")
    app.register_blueprint(menu_bp, url_prefix="/menu")
    app.register_blueprint(pos_bp, url_prefix="/pos")
    app.register_blueprint(payments_bp, url_prefix="/payments")