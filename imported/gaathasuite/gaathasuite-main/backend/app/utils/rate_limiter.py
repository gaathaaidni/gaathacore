"""
Rate limiting configuration using Flask-Limiter.
Prevents abuse by limiting API requests per IP address.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask
from typing import Callable
from functools import wraps


# Initialize limiter (to be bound to app in factory)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # Use Redis in production: "redis://localhost:6379"
)


def init_rate_limiter(app: Flask) -> None:
    """Initialize rate limiter with Flask app."""
    limiter.init_app(app)


# Decorator presets for common rate limits
def rate_limit_strict(f: Callable) -> Callable:
    """Strict rate limit: 10 requests per minute."""
    return limiter.limit("10/minute")(f)


def rate_limit_moderate(f: Callable) -> Callable:
    """Moderate rate limit: 100 requests per hour."""
    return limiter.limit("100/hour")(f)


def rate_limit_api(f: Callable) -> Callable:
    """Standard API rate limit: 100 requests per hour per IP."""
    return limiter.limit("100/hour")(f)


def rate_limit_high(f: Callable) -> Callable:
    """High rate limit: 1000 requests per hour."""
    return limiter.limit("1000/hour")(f)


def get_limiter() -> Limiter:
    """Get the limiter instance."""
    return limiter
