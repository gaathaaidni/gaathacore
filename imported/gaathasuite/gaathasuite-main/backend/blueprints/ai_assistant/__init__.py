"""AI assistant blueprint package.

This package is used by the FastAPI app through ``blueprints.ai_assistant.routes``.
Avoid importing optional Flask compatibility modules at package import time so the
FastAPI application can start even when those legacy modules are absent/empty.
"""
try:
    from fastapi import APIRouter
    router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    router = None

__all__ = [
    "FASTAPI_AVAILABLE",
    "router",
]
