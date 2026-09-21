# Gaatha Suite Setup Guide

This repository contains a React frontend and a Python backend. The current backend runtime is based on FastAPI in `backend/app/`, with supporting legacy and integration modules under `backend/blueprints/`.

## Repository overview

- `backend/`
  - `backend/app/`: the current FastAPI application package
  - `backend/requirements.txt`: Python dependencies for the backend
  - `backend/entrypoint.sh`: Docker entrypoint that waits for Postgres, initializes the DB, and starts Uvicorn
  - `backend/init_db.py`: database initialization script
  - `backend/blueprints/`: legacy Flask-style and integration modules used by the backend
- `frontend/`
  - React + Vite UI application
  - `frontend/package.json`: frontend dependencies and build scripts
- `docker-compose.yml`: developer compose file with local Postgres and Redis
- `docker-compose.prod.yml`: production compose file that uses environment variables
- `Dockerfile`: multi-stage Docker build for frontend and backend
- `render.yaml`, `render.prod.yaml`: Render deployment configuration templates

## Status of README and env docs

The existing `README.md` is currently outdated in several places:
- it references an old Flask-style root app layout (`app.py`, `run.py`, `seed.py`) that does not match the current `backend/app/` FastAPI architecture
- it mentions SQLite local defaults, while the current backend code defaults to PostgreSQL
- it does not expose a `.env.example` template for developers

This guide is the accurate reference for cloning, configuring, and deploying Gaatha Suite.

## Clone the repository

```bash
git clone https://github.com/gaathatech/gaathasuite.git
cd gaathasuite
```

## Environment configuration

The backend loads environment variables from `backend/.env` and `backend/instance/.env` if present. In containerized or production setups, use real environment variables instead of a `.env` file.

1. Copy the template:

```bash
cp backend/.env.example backend/.env
```

2. Edit `backend/.env` and replace placeholders with real values.

### Required variables

- `SECRET_KEY` — strong application secret for session signing and JWTs
- `DATABASE_URL` — PostgreSQL URI, e.g. `postgresql+asyncpg://gaatha:StrongPassword@db:5432/gaatha`

### Recommended variables

- `REDIS_URL` — Redis URL for caching and background tasks
- `RESEND_API_KEY` — preferred email provider API key
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_USE_TLS` — SMTP fallback
- `SUPPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD` — one-time admin credentials during first deployment
- `CASHFREE_CLIENT_ID`, `CASHFREE_CLIENT_SECRET`, `CASHFREE_ENV` — Cashfree payment gateway credentials
- `GROQ_API_KEY`, `GROQ_MODEL` — AI assistant support

## Local development with Docker

The easiest local development path is using Docker Compose.

```bash
docker compose up --build
```

If your Docker Compose binary is `docker-compose`, use:

```bash
docker-compose up --build
```

### What this starts

- `web`: the backend application
- `db`: Postgres database
- `redis`: Redis instance

### Dev environment notes

- `docker-compose.yml` currently includes dev defaults for `DATABASE_URL` and `SECRET_KEY`. These are fine for local testing but must be replaced before any public demo.
- The backend service starts with `backend/entrypoint.sh`, which waits for the database, runs `python init_db.py`, and starts the FastAPI app using Uvicorn.

## Production deployment with Docker Compose

Use `docker-compose.prod.yml` for production-style deployment.

1. Create a `.env` file inside `backend/` or set environment variables in your host environment.
2. Run:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

3. Confirm:

```bash
docker-compose -f docker-compose.prod.yml ps
```

### Required production environment variables

- `DATABASE_URL`
- `SECRET_KEY`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

## Render deployment

Render support is provided via `render.yaml` and `render.prod.yaml`.

### Key points

- Build command: `cd backend && pip install -r requirements.txt`
- Start command: `cd backend && gunicorn -w 4 -b 0.0.0.0:$PORT main:app`
- Health check path: `/_health`
- Required environment variables: `DATABASE_URL`, `SECRET_KEY`

If you deploy on Render, set those variables as secrets in the dashboard.

## Non-Docker local development

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

If you prefer to run the app from the repository root, use `cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 5000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Build frontend for production

```bash
cd frontend
npm install
npm run build
```

The Dockerfile automatically builds the frontend and copies the compiled assets into `backend/static/dist/`.

## Recommended presentation checklist

- Confirm `backend/.env` is configured with real secrets and not the repository sample values.
- Verify `docker-compose.yml` defaults are not used in any public deployment.
- Confirm the root `README.md` is not being used as the only setup source; use `SETUP.md` instead.
- Verify the `backend/app/main.py` FastAPI entry point and `backend/entrypoint.sh` startup path.
- Ensure `frontend` build completes successfully before demo.

## Notes on architecture

- The current backend runtime is FastAPI in `backend/app/main.py`.
- The React frontend lives in `frontend/` and is built into `backend/static/dist/`.
- `backend/blueprints/` contains legacy integration modules and support code, but the main app is still FastAPI.
- The Docker container uses `uvicorn main:app` from inside the `backend` working directory.
