#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.core.yml}"
CORE_POSTGRES_DB="${CORE_POSTGRES_DB:-gaathacore_core}"
CORE_POSTGRES_USER="${CORE_POSTGRES_USER:-core_local}"
CORE_BACKUP_FILE="${CORE_BACKUP_FILE:-/tmp/gaathacore_core_staging.dump}"

usage() {
    cat <<'EOF'
Usage: scripts/core_staging.sh <command>

Commands:
  up              Start the isolated Core PostgreSQL service and wait for health
  down            Stop the isolated Core PostgreSQL service (keeps its volume)
  status          Show Compose service status
  logs            Show recent Core PostgreSQL logs
  identity        Verify the connected database identity without printing a URL
  migrate-status  Show Core migration head and pending migrations
  migrate-up     Apply pending Core migrations
  health          Require Core readiness
  backup          Create a custom-format Core PostgreSQL backup
  restore         Destructive restore; requires explicit disposable confirmation
EOF
}

compose() {
    docker compose -f "$COMPOSE_FILE" "$@"
}

require_tools() {
    command -v docker >/dev/null || { echo "docker is required" >&2; exit 2; }
    command -v python >/dev/null || { echo "python is required" >&2; exit 2; }
}

require_disposable_restore() {
    [[ "${CORE_STAGING_DISPOSABLE:-}" == "1" ]] || {
        echo "restore requires CORE_STAGING_DISPOSABLE=1" >&2
        exit 2
    }
    [[ "${CORE_RESTORE_CONFIRM:-}" == "RESTORE_CORE_DISPOSABLE" ]] || {
        echo "restore requires CORE_RESTORE_CONFIRM=RESTORE_CORE_DISPOSABLE" >&2
        exit 2
    }
}

case "${1:-}" in
    up)
        require_tools
        compose up -d --wait
        ;;
    down)
        require_tools
        compose down
        ;;
    status)
        require_tools
        compose ps
        ;;
    logs)
        require_tools
        compose logs --tail="${CORE_LOG_TAIL:-100}" core-postgres
        ;;
    identity)
        python -m core.operations_cli identity
        ;;
    migrate-status)
        python -m core.operations_cli status
        ;;
    migrate-up)
        python -m core.operations_cli upgrade
        ;;
    health)
        python -m core.operations_cli health
        ;;
    backup)
        require_tools
        mkdir -p "$(dirname "$CORE_BACKUP_FILE")"
        compose exec -T core-postgres pg_dump -U "$CORE_POSTGRES_USER" -d "$CORE_POSTGRES_DB" --format=custom --no-owner > "$CORE_BACKUP_FILE"
        [[ -s "$CORE_BACKUP_FILE" ]] || { echo "backup file is missing or empty: $CORE_BACKUP_FILE" >&2; exit 2; }
        compose exec -T core-postgres pg_restore --list < "$CORE_BACKUP_FILE" >/dev/null
        echo "Core backup written to $CORE_BACKUP_FILE"
        ;;
    restore)
        require_tools
        require_disposable_restore
        [[ -s "$CORE_BACKUP_FILE" ]] || { echo "backup file is missing or empty: $CORE_BACKUP_FILE" >&2; exit 2; }
        compose exec -T core-postgres psql -U "$CORE_POSTGRES_USER" -d "$CORE_POSTGRES_DB" -v ON_ERROR_STOP=1 -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
        compose exec -T core-postgres pg_restore -U "$CORE_POSTGRES_USER" -d "$CORE_POSTGRES_DB" --exit-on-error --no-owner < "$CORE_BACKUP_FILE"
        echo "Disposable Core restore completed from $CORE_BACKUP_FILE"
        ;;
    *)
        usage
        exit 2
        ;;
esac
