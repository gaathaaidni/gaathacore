from flask import Flask

def register_blueprints(app: Flask):
    try:
        from .auth.routes import auth_bp
        app.register_blueprint(auth_bp)
    except ImportError:
        pass
        
    try:
        from .crm.routes import crm_bp
        app.register_blueprint(crm_bp)
    except ImportError:
        pass