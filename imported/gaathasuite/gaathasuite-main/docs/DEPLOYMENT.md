# Deployment

## Container

The image builds the React frontend, installs backend dependencies, waits for PostgreSQL, runs:

```sh
alembic -c migrations/alembic.ini upgrade head
```

and starts:

```sh
uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 2
```

The container requires `DATABASE_URL` and `SECRET_KEY`. PostgreSQL credentials and other secrets are supplied through the environment. Readiness is `GET /ready`; liveness is `GET /health`.

## Render

Render uses an explicit Alembic migration command followed by Gunicorn with `uvicorn.workers.UvicornWorker` and `app.main:app`. The health path is `/ready`.

## Compose

Development Compose requires `SECRET_KEY` and `POSTGRES_PASSWORD`; it no longer sets Flask startup variables or uses a development secret. The backend waits for the PostgreSQL health check.

## Current blocker

Do not deploy until the Alembic graph is reconciled and a clean PostgreSQL migration plus authenticated smoke test succeeds. No production readiness claim is made by this document.
