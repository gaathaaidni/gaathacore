import os

from config import Config


def test_secret_key_is_not_hardcoded_in_default_config():
    assert Config.SECRET_KEY not in (None, "", "dev_secret")


def test_session_cookie_security_is_enabled_for_production_defaults():
    assert Config.SESSION_COOKIE_HTTPONLY is True
    assert Config.SESSION_COOKIE_SAMESITE in {"Lax", "Strict", "None"}
