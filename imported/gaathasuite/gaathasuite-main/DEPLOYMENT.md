# Gaatha Suite Production Deployment Guide

For a normal Linux VPS, use [DEPLOYMENT_VPS.md](DEPLOYMENT_VPS.md) and
`docker-compose.prod.yml`. This legacy guide describes the general Compose
workflow; the default `docker-compose.yml` is for local development and uses
development-specific database networking.

This guide reflects the current repository layout: a FastAPI backend started from `backend/main.py`, a Docker entrypoint in `backend/entrypoint.sh`, and a Docker Compose stack defined in `docker-compose.yml` and `docker-compose.prod.yml`.

## 1. Prepare the environment

Create or update the backend environment file before deploying:

```bash
cp backend/.env.example backend/.env
```

Use real production values for:
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (for Compose production)
- optional payment and AI keys (`CASHFREE_*`, `GROQ_*`)

## 2. Deploy with Docker Compose

```bash
cd /path/to/gaathasuite

docker compose down --remove-orphans
docker compose up -d --build
```

If your environment still uses the legacy `docker-compose` binary, replace `docker compose` with `docker-compose`.

Verify the stack:

```bash
docker compose ps
 docker compose logs -f web
```

## 3. What happens during startup

The container starts with `backend/entrypoint.sh`, which:
1. waits for PostgreSQL to become ready,
2. runs `python init_db.py`, and
3. starts the FastAPI app with `uvicorn main:app --host 0.0.0.0 --port 5000 --workers 4`.

The application exposes:
- API and UI on `http://<host>:5000`
- health checks at `http://<host>:5000/_health`

## 4. Production notes

- Keep the Compose defaults in `docker-compose.yml` for local development only; replace them with real secrets for any public deployment.
- The production Compose file expects `DATABASE_URL`, `SECRET_KEY`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` to be available in the environment.
- Health checks and startup sequencing are handled by Docker Compose and `backend/entrypoint.sh`.

## 5. Useful operational commands

Initialize the database manually if needed:

```bash
docker compose exec web python init_db.py
```

Inspect the database:

```bash
docker compose exec db psql -U gaatha -d gaatha
```

Back up the database:

```bash
docker compose exec db pg_dump -U gaatha gaatha > backup.sql
```

Restore the database:

```bash
docker compose exec -T db psql -U gaatha gaatha < backup.sql
```

## 6. Troubleshooting

Check logs:

```bash
docker compose logs web --tail 100
docker compose logs db --tail 100
```

If the backend is not listening on port 5000 yet, confirm the container is healthy and that the entrypoint finished successfully.

## 7. Security checklist

1. Rotate `SECRET_KEY` and database credentials before production deployment.
2. Use real environment variables instead of sample values.
3. Enable HTTPS through a reverse proxy or managed platform.
4. Restrict CORS origins in production instead of leaving them open.
5. Keep regular PostgreSQL backups and monitor container health.
