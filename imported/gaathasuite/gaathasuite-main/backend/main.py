"""Compatibility export for ASGI servers launched from the backend directory."""

from app.main import app

__all__ = ["app"]
