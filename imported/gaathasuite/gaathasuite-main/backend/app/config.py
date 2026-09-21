import os
from pathlib import Path
from dotenv import load_dotenv

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for env_path in [
    Path(__file__).resolve().parents[2] / ".env",
    Path(__file__).resolve().parents[1] / ".env",
    Path(basedir) / "instance" / ".env",
]:
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path), override=False)


class Config:
    ENVIRONMENT = os.environ.get('APP_ENV', 'development').lower()
    SECRET_KEY = os.environ.get('SECRET_KEY')
    BASE_URL = os.environ.get("BASE_URL") or (
        "http://localhost:5000" if ENVIRONMENT != "production" else ""
    )

    # Storage for uploads
    UPLOAD_FOLDER = os.path.join(basedir, "static", "uploads")

    # Database Configuration (PostgreSQL Required)
    DATABASE_URL = os.environ.get("DATABASE_URL")

    # Redis Configuration (For Celery & Rate Limiting)
    REDIS_URL = os.environ.get("REDIS_URL")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "")

    # JWT Security
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", 60 * 24)) # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30
    COOKIE_SECURE = ENVIRONMENT == 'production'

    # Super Admin (God Mode) Credentials from .env
    # In production, these must be complex and rotated.
    # Keep a runtime fallback for existing deployments where only ADMIN_* is present.
    SUPERADMIN_EMAIL = os.environ.get('SUPERADMIN_EMAIL') or os.environ.get('ADMIN_EMAIL')
    SUPERADMIN_PASSWORD = os.environ.get('SUPERADMIN_PASSWORD') or os.environ.get('ADMIN_PASSWORD')

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

    @classmethod
    def public_url(cls, path: str = "") -> str:
        base = (cls.BASE_URL or "").rstrip("/")
        if not base:
            return path
        path = path.lstrip("/")
        return f"{base}/{path}" if path else base

    @classmethod
    def validate_required(cls):
        missing = [name for name, value in {
            'DATABASE_URL': cls.DATABASE_URL,
            'SECRET_KEY': cls.SECRET_KEY,
        }.items() if not value]
        if cls.ENVIRONMENT == "production" and not cls.BASE_URL:
            missing.append('BASE_URL')
        if missing:
            raise RuntimeError(
                f"Missing required configuration: {', '.join(missing)}"
            )