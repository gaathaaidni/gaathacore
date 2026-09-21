# Codebase Guide

**Status:** IMPLEMENTED audit guide.

## Main locations

- `backend/app/main.py`: active FastAPI application, middleware, router registration, health, readiness, and frontend serving.
- `backend/main.py`: compatibility export of the active app.
- `backend/app/routes/`: active FastAPI route modules.
- `backend/app/models/`: SQLAlchemy models.
- `backend/app/tasks/`: notifications, imports/exports, reports, authentication, and Celery-related code.
- `backend/migrations/`: Alembic configuration and revision history.
- `backend/tests/`: current backend foundation/regression tests.
- `backend/blueprints/`: legacy or transition Flask-style modules; not automatically active.
- `frontend/src/`: React/Vite application.
- `Dockerfile`, Compose, Render, Nginx, and Kubernetes files: deployment surfaces.

When tracing a report, start with router registration in `backend/app/main.py`, then follow the route schema, dependency, model query, and migration. Confirm organization scope and role checks at each boundary.
