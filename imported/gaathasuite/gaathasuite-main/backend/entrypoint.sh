#!/bin/sh
set -eu

export PYTHONPATH="${PYTHONPATH:-/app/backend}:/app/backend"

echo "=== GaathaSuite FastAPI startup ==="

database_host="${DATABASE_HOST:-db}"
database_port="${DATABASE_PORT:-5432}"

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

echo "Waiting for PostgreSQL at ${database_host}:${database_port}..."
until timeout 5 nc -z -w 2 "$database_host" "$database_port"; do
  sleep 1
done

echo "Applying Alembic migrations..."
PYTHONPATH="$PYTHONPATH" alembic -c migrations/alembic.ini upgrade head

echo "Starting FastAPI application..."
exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-5000}" --workers "${WEB_CONCURRENCY:-2}"
