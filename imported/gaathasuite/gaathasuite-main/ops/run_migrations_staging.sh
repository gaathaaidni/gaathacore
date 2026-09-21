#!/usr/bin/env bash
# Run DB migrations on the staging server. Edit variables before use.
set -e
# Example usage: ./ops/run_migrations_staging.sh

STAGING_SSH_USER="${STAGING_SSH_USER:-}"
STAGING_HOST="${STAGING_HOST:-}"
APP_DIR="${APP_DIR:-/srv/gaatha}"

if [ -z "$STAGING_SSH_USER" ] || [ -z "$STAGING_HOST" ]; then
  echo "STAGING_SSH_USER or STAGING_HOST not set. Edit this script or export the env vars and re-run."
  echo "Example: export STAGING_SSH_USER=deploy && export STAGING_HOST=staging.example.com && ./ops/run_migrations_staging.sh"
  exit 1
fi

echo "About to run migrations on staging: ${STAGING_HOST} (user ${STAGING_SSH_USER})"
echo "Make sure you have SSH access and the staging environment variables set."

ssh -oBatchMode=yes ${STAGING_SSH_USER}@${STAGING_HOST} <<SSH
  set -e
  cd ${APP_DIR}
  # Activate virtualenv if necessary, e.g. source venv/bin/activate
  flask db upgrade
SSH

echo "Migrations requested on staging. Check staging logs for results."
