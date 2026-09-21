# Architecture

**Status:** IMPLEMENTED BUT NOT FULLY VERIFIED.

## Runtime path

The active ASGI application is `backend/app/main.py`; `backend/main.py` exports it for server commands. The app registers FastAPI routers, middleware, health endpoints, and static frontend serving. The frontend is a React 18/Vite application under `frontend/` and is built into the backend static directory by `Dockerfile`.

## Data and services

PostgreSQL is accessed through SQLAlchemy 2 async sessions. Alembic migrations are under `backend/migrations`. Redis configuration exists for Pub/Sub, task, and rate-limiting concerns, but a deployed worker and complete shared Redis integration are not verified. Uploads use the application static uploads path and a Compose volume in production configuration.

## Compatibility boundary

`backend/blueprints/` and legacy Flask dependencies remain in the repository. They are a transition surface, not evidence that every route is active in the FastAPI runtime. When debugging, first confirm whether the request is registered by `app.main`.

## Request lifecycle

1. Nginx or the local server receives the request.
2. FastAPI middleware applies CORS/security headers and exception handling.
3. A registered router resolves authentication and authorization dependencies.
4. SQLAlchemy obtains an async database session.
5. The route validates input, applies organization ownership checks where implemented, and commits or returns a response.
6. Unhandled errors are logged server-side and returned as a generic structured error.

For practical diagnosis see [USER_REPORT_DIAGNOSTICS.md](USER_REPORT_DIAGNOSTICS.md).
