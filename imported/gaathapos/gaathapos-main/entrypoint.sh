#!/bin/sh

set -eu

export PATH="/opt/venv/bin:${PATH:-}"
export APP_ENV="${APP_ENV:-production}"
export PORT="${PORT:-3006}"
export DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"
export REDIS_WAIT_TIMEOUT="${REDIS_WAIT_TIMEOUT:-60}"

if [ -z "${SECRET_KEY:-}" ]; then
  export SECRET_KEY="$(python - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
)"
fi

wait_for_url() {
  label="$1"
  url="$2"
  timeout_seconds="$3"

  if [ -z "$url" ]; then
    return 0
  fi

  i=0
  while [ "$i" -lt "$timeout_seconds" ]; do
    if python - "$url" <<'PY'
import socket
import sys
from urllib.parse import urlparse

url = sys.argv[1]
parsed = urlparse(url)
scheme = (parsed.scheme or "").lower()
if scheme in {"redis", "rediss"}:
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
elif scheme in {"postgres", "postgresql", "postgresql+psycopg2"}:
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
else:
    host = parsed.hostname or "localhost"
    port = parsed.port or 80

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
try:
    sock.connect((host, port))
    print("ready")
    sys.exit(0)
except Exception:
    sys.exit(1)
finally:
    sock.close()
PY
    then
      echo "$label is ready."
      return 0
    fi
    i=$((i + 1))
    echo "$label not ready yet (attempt $i/$timeout_seconds); retrying in 2s..."
    sleep 2
  done

  echo "ERROR: $label did not become ready within ${timeout_seconds}s." >&2
  return 1
}

if [ -n "${DATABASE_URL:-}" ] && printf '%s' "$DATABASE_URL" | grep -qi '^sqlite'; then
  echo "SQLite database detected; skipping Alembic migration bootstrap in this container."
else
  wait_for_url "PostgreSQL" "${DATABASE_URL:-postgresql://gaatha:change_me_now@db:5432/gaathapos}" "$DB_WAIT_TIMEOUT"
  echo "Applying database migrations..."
  python -m flask db upgrade
fi

if [ -n "${REDIS_URL:-}" ]; then
  wait_for_url "Redis" "$REDIS_URL" "$REDIS_WAIT_TIMEOUT"
fi

echo "Starting Gunicorn..."
exec gunicorn --workers "${GUNICORN_WORKERS:-4}" --bind "0.0.0.0:${PORT}" wsgi:app