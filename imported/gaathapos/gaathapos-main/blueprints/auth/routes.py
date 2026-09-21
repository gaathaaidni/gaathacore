from flask import render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db, login_manager, limiter
from models import User, Restaurant, StoreSettings
from services.totp import generate_totp_secret, verify_totp_token, use_backup_code
from . import auth_bp
from flask import current_app

@login_manager.user_loader
def load_user(user_id):
    # Use session.get() to avoid SQLAlchemy Query.get() legacy warning
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("100 per minute")  # Brute force protection
def login():
    if request.method == "POST":
        try:
            username = request.form.get("username")
            password = request.form.get("password")
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                # If 2FA is enabled, don't log in yet - store temp session and redirect to 2FA verification
                if user.totp_enabled:
                    session['pending_user_id'] = user.id
                    session['pending_2fa'] = True
                    flash("Please verify your 2FA code", "info")
                    return redirect(url_for("auth.verify_2fa"))

                remember = request.form.get('remember_me') == 'on'
                login_user(user, remember=remember)
                flash("Logged in successfully", "success")
                if user.role in ["admin", "manager", "super_admin", "restaurant_admin"]:
                    return redirect(url_for("admin.dashboard"))
                elif user.role == "waiter":
                    return redirect(url_for("pos.pos_home"))
                elif user.role == "kitchen":
                    return redirect(url_for("kds.pending_orders"))
                else:
                    return redirect(url_for("menu.show_menu"))
            flash("Invalid credentials", "danger")
        except Exception:
            current_app.logger.exception("Error during login POST")
            flash("Unable to process login request. Please try again.", "danger")
            return redirect(url_for("auth.login"))
    return render_template("login.html")

@auth_bp.route("/signup", methods=["GET", "POST"])
@limiter.limit("20 per minute")
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        restaurant_name = request.form.get("restaurant_name", "").strip()
        restaurant_email = request.form.get("restaurant_email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        country = request.form.get("country", "").strip()
        postal_code = request.form.get("postal_code", "").strip()

        if not username or not password or not restaurant_name or not restaurant_email:
            flash("Please fill in all required fields", "danger")
            return render_template("signup.html")

        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose another.", "danger")
            return render_template("signup.html")

        if Restaurant.query.filter_by(email=restaurant_email).first():
            flash("A restaurant with that email already exists.", "danger")
            return render_template("signup.html")

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role="restaurant_admin",
            currency="USD",
            locale="en",
            is_super_admin=False,
        )
        db.session.add(user)
        db.session.flush()

        restaurant = Restaurant(
            name=restaurant_name,
            email=restaurant_email,
            phone=phone,
            address=address,
            city=city,
            country=country,
            postal_code=postal_code,
            owner_id=user.id,
            active=True,
        )
        db.session.add(restaurant)
        db.session.flush()

        user.restaurant_id = restaurant.id
        db.session.add(user)

        if not StoreSettings.query.filter_by(restaurant_id=restaurant.id).first():
            settings = StoreSettings(restaurant_id=restaurant.id)
            db.session.add(settings)

        db.session.commit()

        login_user(user)
        flash("Signup successful. Welcome to Gaatha POS!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("signup.html")

@auth_bp.route("/verify-2fa", methods=["GET", "POST"])
@limiter.limit("10 per minute")  # Strict limit for 2FA attempts
def verify_2fa():
    """Verify TOTP token or backup code after successful password authentication"""
    if 'pending_user_id' not in session or not session.get('pending_2fa'):
        flash("Please log in first", "danger")
        return redirect(url_for("auth.login"))
    
    user = db.session.get(User, session['pending_user_id'])
    if not user:
        flash("User not found", "danger")
        session.pop('pending_user_id', None)
        session.pop('pending_2fa', None)
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        token = request.form.get("token", "").strip()
        
        # Check if it's a backup code (longer, alphanumeric) or a TOTP token (6 digits)
        if len(token) == 8 and token.isalnum():
            # Try backup code
            result = use_backup_code(user.backup_codes, token)
            if result['valid']:
                user.backup_codes = result['remaining_codes_json']
                db.session.commit()
                
                login_user(user)
                session.pop('pending_user_id', None)
                session.pop('pending_2fa', None)
                flash("Logged in successfully (backup code used)", "success")
                if user.role in ["admin", "manager", "super_admin", "restaurant_admin"]:
                    return redirect(url_for("admin.dashboard"))
                else:
                    return redirect(url_for("pos.pos_home"))
        else:
            # Try TOTP token
            if verify_totp_token(user.totp_secret, token):
                login_user(user)
                session.pop('pending_user_id', None)
                session.pop('pending_2fa', None)
                flash("Logged in successfully", "success")
                if user.role in ["admin", "manager", "super_admin", "restaurant_admin"]:
                    return redirect(url_for("admin.dashboard"))
                else:
                    return redirect(url_for("pos.pos_home"))
        
        flash("Invalid 2FA code or backup code", "danger")
    
    return render_template("verify_2fa.html", username=user.username)

@auth_bp.route("/api/2fa-setup", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def api_2fa_setup():
    """Initialize 2FA setup for current user. Returns QR code and backup codes."""
    if current_user.totp_enabled:
        return jsonify({'error': '2FA already enabled. Disable first.'}), 400
    
    result = generate_totp_secret(current_user.username, issuer='Gaatha POS')
    
    # Store secret temporarily in session (not confirmed yet)
    session['pending_totp_secret'] = result['secret']
    session['pending_backup_codes_hashed'] = result['backup_codes_hashed']
    
    return jsonify({
        'qr_code': result['qr_code_data_uri'],
        'secret': result['secret'],
        'backup_codes': result['backup_codes'],
        'message': 'Scan QR code with authenticator app. Save backup codes in a safe place.'
    }), 200

@auth_bp.route("/api/2fa-confirm", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def api_2fa_confirm():
    """Confirm 2FA setup by verifying a TOTP token"""
    if current_user.totp_enabled:
        return jsonify({'error': '2FA already enabled'}), 400
    
    token = request.json.get('token', '').strip()
    
    # Retrieve pending secret from session
    secret = session.get('pending_totp_secret')
    backup_codes_hashed = session.get('pending_backup_codes_hashed')
    
    if not secret:
        return jsonify({'error': 'No pending 2FA setup found. Call /api/2fa-setup first.'}), 400
    
    # Verify the token
    if not verify_totp_token(secret, token):
        return jsonify({'error': 'Invalid TOTP token. Please try again.'}), 400
    
    # All valid - enable 2FA for user
    current_user.totp_secret = secret
    current_user.totp_enabled = True
    current_user.backup_codes = backup_codes_hashed
    db.session.commit()
    
    # Clear pending data from session
    session.pop('pending_totp_secret', None)
    session.pop('pending_backup_codes_hashed', None)
    
    return jsonify({'message': '2FA enabled successfully'}), 200

@auth_bp.route("/api/2fa-disable", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def api_2fa_disable():
    """Disable 2FA for current user (requires password confirmation)"""
    if not current_user.totp_enabled:
        return jsonify({'error': '2FA not enabled'}), 400
    
    password = request.json.get('password', '')
    
    if not check_password_hash(current_user.password_hash, password):
        return jsonify({'error': 'Invalid password'}), 401
    
    current_user.totp_secret = None
    current_user.totp_enabled = False
    current_user.backup_codes = None
    db.session.commit()
    
    return jsonify({'message': '2FA disabled successfully'}), 200

@auth_bp.route("/api/2fa-status", methods=["GET"])
@login_required
def api_2fa_status():
    """Get current user's 2FA status"""
    return jsonify({
        'totp_enabled': current_user.totp_enabled,
        'has_backup_codes': current_user.backup_codes is not None
    }), 200

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route('/debug-status')
def debug_status():
    """Temporary debug endpoint: shows current_user and session keys when running in debug mode."""
    if not current_app.debug:
        return jsonify({'error': 'debug endpoint disabled'}), 404
    return jsonify({
        'is_authenticated': getattr(current_user, 'is_authenticated', False),
        'username': getattr(current_user, 'username', None),
        'role': getattr(current_user, 'role', None),
        'session_keys': list(session.keys())
    }), 200

