#!/usr/bin/env bash
set -euo pipefail
: "${POSTGRES_URL:?Set POSTGRES_URL}"; : "${1:?Usage: restore-postgres.sh backup.dump}"; pg_restore --clean --if-exists --no-owner --dbname="$POSTGRES_URL" "$1"
