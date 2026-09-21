#!/usr/bin/env bash
# Restore .env backup created by rotate_secret.py and restart service on targets.

set -euo pipefail

TARGETS=("server1.example.com" "server2.example.com")
DEPLOY_USER=deployuser
REMOTE_PATH=/opt/gaatha/shared/.env
BACKUP_PATH="${REMOTE_PATH}.bak"
RESTART_CMD='sudo systemctl restart gaatha.service'

for host in "${TARGETS[@]}"; do
  echo "Restoring backup on $host"
  ssh ${DEPLOY_USER}@${host} "if [ -f ${BACKUP_PATH} ]; then sudo mv ${BACKUP_PATH} ${REMOTE_PATH}; sudo chown gaatha:gaatha ${REMOTE_PATH}; sudo chmod 600 ${REMOTE_PATH}; ${RESTART_CMD}; else echo 'No backup found on ${host}'; fi"
done

echo "Rollback attempted on targets. Check logs for success." 
