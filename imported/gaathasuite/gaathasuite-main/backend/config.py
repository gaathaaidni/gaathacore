import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent

# Load .env from project root and instance/ if present (do not commit .env)
load_dotenv(dotenv_path=str(basedir / '.env'))
load_dotenv(dotenv_path=str(basedir / 'instance' / '.env'))

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is required. Do not generate a default production secret. "
        "Set SECRET_KEY in the environment or in a local .env file before startup."
    )

if not os.environ.get('DATABASE_URL'):
    raise RuntimeError("DATABASE_URL is required for production startup.")


class Config:
    ENVIRONMENT = os.environ.get('APP_ENV', 'development').lower()
    SECRET_KEY = SECRET_KEY
    BASE_URL = os.environ.get("BASE_URL") or (
        "http://localhost:5000" if ENVIRONMENT != "production" else ""
    )

    # Storage for uploads
    UPLOAD_FOLDER = os.path.join(basedir, "static", "uploads")

    # Database Configuration (PostgreSQL Required)
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required for production startup.")

    # Redis Configuration (For Celery & Rate Limiting)
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # JWT Security
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", 60 * 24)) # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30
    COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'

    # Super Admin (God Mode) Credentials from .env
    # In production, these must be complex and rotated
    SUPERADMIN_EMAIL = os.environ.get('SUPERADMIN_EMAIL')
    SUPERADMIN_PASSWORD = os.environ.get('SUPERADMIN_PASSWORD')
    if not SUPERADMIN_PASSWORD and os.environ.get('FLASK_ENV') == 'production':
        print("WARNING: Super Admin credentials not configured for production!")

    # OAuth credentials (set in instance .env)
    OAUTH_PROVIDERS = {
        'google': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
            'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET')
        },
        'microsoft': {
            'client_id': os.environ.get('MICROSOFT_CLIENT_ID'),
            'client_secret': os.environ.get('MICROSOFT_CLIENT_SECRET')
        }
    }
    # SMTP config: support both legacy and Gmail .env
    SMTP_SERVER = os.environ.get('SMTP_SERVER') or os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT') or os.environ.get('MAIL_PORT', 587))

    SMTP_USER = os.environ.get('SMTP_USER') or os.environ.get('MAIL_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD') or os.environ.get('MAIL_PASSWORD')
    SMTP_USE_TLS = (
        os.environ.get('SMTP_USE_TLS') or os.environ.get('MAIL_USE_TLS', 'True')
    ) in ('True', 'true', '1')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME')
    # Resend.com API key (preferred over SMTP if present)
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
    # Company/legal details (set via environment or instance .env)
    COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Aidni Global LLP')
    COMPANY_EMAIL = os.environ.get('COMPANY_EMAIL', 'support@aidniglobal.in')
    COMPANY_WEBSITE = os.environ.get('COMPANY_WEBSITE', 'https://www.aidniglobal.in')
    COMPANY_JURISDICTION = os.environ.get('COMPANY_JURISDICTION', 'India')
    # Security settings
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'False') in ('True', 'true', '1')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True') in ('True', 'true', '1')
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True') in ('True', 'true', '1')
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    REMEMBER_COOKIE_DURATION_DAYS = int(os.environ.get('REMEMBER_COOKIE_DURATION_DAYS', '14'))

    # CORS / allowed origins (comma-separated)
    CORS_ORIGINS = [o.strip() for o in os.environ.get('CORS_ORIGINS', '').split(',') if o.strip()]

    # HSTS (when using HTTPS)
    HSTS_SECONDS = int(os.environ.get('HSTS_SECONDS', '31536000'))
    HSTS_INCLUDE_SUBDOMAINS = os.environ.get('HSTS_INCLUDE_SUBDOMAINS', 'True') in ('True', 'true', '1')
    CSP_ENABLED = os.environ.get('CSP_ENABLED', 'False') in ('True', 'true', '1')

    @staticmethod
    def public_url(path: str = "") -> str:
        base = (Config.BASE_URL or "").rstrip("/")
        if not base:
            return path
        path = path.lstrip("/")
        return f"{base}/{path}" if path else base
    # Toggle whether we require users to confirm email before certain actions
    REQUIRE_EMAIL_VERIFICATION = os.environ.get('REQUIRE_EMAIL_VERIFICATION', 'False') in ('True', 'true', '1')
