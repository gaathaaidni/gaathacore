import os
import secrets


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    APP_ENV = os.environ.get("APP_ENV") or (
        "production" if os.environ.get("FLASK_ENV") == "production" else "development"
    )
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.abspath('instance/app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI") or os.environ.get("REDIS_URL")
    if APP_ENV == "production" and not RATELIMIT_STORAGE_URI:
        RATELIMIT_STORAGE_URI = "redis://redis:6379/0"
    LANGUAGES = ["en", "ro"]
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = _as_bool(os.environ.get("SESSION_COOKIE_SECURE"), APP_ENV == "production")
    SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "gaatha_session")
    PERMANENT_SESSION_LIFETIME = int(os.environ.get("SESSION_LIFETIME_SECONDS", str(60 * 60 * 8)))
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "https")
    TRUSTED_HOSTS = [
        h.strip() for h in os.environ.get("TRUSTED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",") if h.strip()
    ]
    WTF_CSRF_ENABLED = os.environ.get("WTF_CSRF_ENABLED", "True").lower() not in {"0", "false", "no", "off"}
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024)))
    SECURE_PROXY_SSL_HEADER = ("X-Forwarded-Proto", "https")
    # Currency support: base currency and exchange rates
    BASE_CURRENCY = "USD"
    EXCHANGE_RATES = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "INR": 83.12,
        "RON": 4.97,
        "CAD": 1.32,
        "AUD": 1.52,
        "JPY": 149.50,
        "CNY": 7.24,
        "AED": 3.67,
    }
    ENABLE_EXCHANGE_UPDATER = os.environ.get("ENABLE_EXCHANGE_UPDATER", "True").lower() not in {"0", "false", "no", "off"}
    EXCHANGE_UPDATE_INTERVAL = int(os.environ.get("EXCHANGE_UPDATE_INTERVAL", str(60 * 60 * 6)))
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    USE_PROXY_FIX = _as_bool(os.environ.get("USE_PROXY_FIX"), True)
