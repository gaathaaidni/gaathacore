# Architecture

## Authoritative runtime

- Frontend: React/Vite, built with `npm --prefix frontend run build`.
- API: FastAPI at `backend/app/main.py`.
- ASGI compatibility export: `backend/main.py` imports `app.main:app`.
- Database: PostgreSQL through SQLAlchemy async sessions.
- Migrations: standalone Alembic configuration under `backend/migrations`.
- Production process: Uvicorn workers through Gunicorn on Render, or Uvicorn directly in the container.

`backend/app/__init__.py` no longer imports the Flask application factory. Legacy Flask modules remain on disk because their feature usage still requires migration or removal work; they are not part of the authoritative boot path.

## Startup

The container entrypoint requires `DATABASE_URL`, waits for PostgreSQL, runs `alembic -c migrations/alembic.ini upgrade head`, and starts `app.main:app`. It does not repair migration state, call `create_all`, or mutate schema directly.

Application startup validates required configuration and disposes the async database engine during shutdown. `/health` reports process availability; `/ready` checks PostgreSQL.

## Known blocker

The existing migration files contain multiple roots and heads. The history must be reconciled and tested against a clean PostgreSQL database before this architecture can be considered production-ready.
