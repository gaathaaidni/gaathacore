#!/usr/bin/env bash
set -euo pipefail
: "${POSTGRES_URL:?Set POSTGRES_URL}"; mkdir -p backups; pg_dump --format=custom --no-owner "$POSTGRES_URL" > "backups/sentira-$(date -u +%Y%m%dT%H%M%SZ).dump"
