# GAATHA SUITE — Production Readiness Baseline

## Executive summary

Status: YELLOW — LIVE STACK GREEN; VPS GATES REMAIN OPEN

The repository is functionally beyond the Phase 1 gate and contains a real FastAPI-based production stack, but it is not yet proven to be production-ready. The current evidence confirms:

### PROVEN LOCALLY

- PostgreSQL and Redis services exist in Docker Compose.
- The active backend runtime is FastAPI through `app.main:app`.
- Local health and readiness endpoints return HTTP 200.
- The database-backed backend test suite passes under the required isolated PostgreSQL test database.
- The frontend production build passes.

### PROVEN ON VPS

- No production or public VPS validation was performed in this session.

### NOT YET VERIFIED

- HTTPS and reverse-proxy behavior at `gaathasuite.gaatha.tech`
- private DB/Redis networking on the VPS
- rollback rehearsal in the live environment
- final tenant-isolation smoke through the public endpoint

- PostgreSQL and Redis services exist in Docker Compose.
- The active backend runtime is FastAPI through `app.main:app`.
- Alembic migration checks pass against the isolated PostgreSQL test database.
- The frontend build passes.
- The database-backed backend test suite passes under the required isolated database environment.

The local live stack is now validated: `db` is healthy, `redis` is running, `web` is healthy, and `/health` plus `/ready` return HTTP 200. The remaining blockers are target-environment HTTPS/reverse-proxy validation, production-safe service exposure, and a controlled VPS rehearsal.

## Runtime and deployment baseline

### Backend

- Active framework: FastAPI
- Main entry point: `backend/app/main.py`
- Startup path: `backend/entrypoint.sh`
- Production-process pattern: Gunicorn + Uvicorn worker
- Primary database: PostgreSQL 15 in Compose
- Supporting service: Redis 7 in Compose

### Frontend

- Framework: React + Vite
- Build command: `npm run build`
- Build result: success in this environment

### Infra

- Docker Compose services:
  - `db`
  - `redis`
  - `web`
- Current database service is healthy.
- Web container readiness was confirmed after correcting the Compose startup route and bounding the PostgreSQL probe.

## Repository findings

### Verified strong points

- The stale legacy Flask runtime path was corrected in the service definition.
- The active runtime is not the legacy `run:app` path.
- Alembic migrations are current and clean.
- The repository-level backend tests pass when pointed to the isolated PostgreSQL test database.
- The frontend production build passes.

### Open readiness gaps

- HTTPS and reverse-proxy behavior were not executed in the target environment.
- The local Compose profile publishes PostgreSQL for host-side verification; the VPS deployment must keep PostgreSQL and Redis private.
- The ERP integration suite proves the core transaction paths, while search/filtering and frontend completeness remain partial.

## Evidence summary

### Commands run

- `git status --short`
- `git rev-parse HEAD`
- `git log -5 --oneline`
- `docker compose config --services`
- `docker compose ps`
- `cd frontend && npm run build`
- `cd backend && python -m compileall -q .`
- `python -m alembic -c migrations/alembic.ini upgrade head`
- `python -m alembic -c migrations/alembic.ini check`
- `pytest -q -rs`

### Results

- Frontend build: PASS
- Alembic migration check: PASS
- Backend DB-backed tests: PASS under isolated PostgreSQL test DB
- Live web health check: PASS — `web` healthy; `/health` and `/ready` return HTTP 200
- Restart recovery: PASS — `docker compose restart web`, followed by healthy container and HTTP 200 checks
- Backend tests: PASS — 29 passed

## Remaining production blockers

1. HTTPS/reverse-proxy behavior remains unexecuted in the target environment.
2. The VPS must use private DB/Redis networking; the local host-gateway route is a development-container compatibility path.
3. VPS deployment itself is not executed and is intentionally excluded from automatic deployment.

## Decision

The repository is a validated release candidate for controlled VPS rehearsal, but it remains YELLOW until the target VPS proves private service networking, HTTPS, login, and representative ERP smoke tests.
