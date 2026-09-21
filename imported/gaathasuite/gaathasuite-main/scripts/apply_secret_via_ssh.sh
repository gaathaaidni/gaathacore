#!/usr/bin/env bash
# Helper: deploy local .env to a list of servers and restart the app.
# Edit `TARGETS` and `REMOTE_PATH` before use.

set -euo pipefail

TARGETS=("server1.example.com" "server2.example.com")
DEPLOY_USER=deployuser
REMOTE_PATH=/opt/gaatha/shared/.env
RESTART_CMD='sudo systemctl restart gaatha.service'

if [ ! -f .env ]; then
  echo ".env not found in current directory" >&2
  exit 2
fi

for host in "${TARGETS[@]}"; do
  echo "Deploying to $host"
  scp .env ${DEPLOY_USER}@${host}:/tmp/gaatha.env.new
  ssh ${DEPLOY_USER}@${host} "sudo mv /tmp/gaatha.env.new ${REMOTE_PATH} && sudo chown gaatha:gaatha ${REMOTE_PATH} && sudo chmod 600 ${REMOTE_PATH}"
  echo "Restarting app on $host"
  ssh ${DEPLOY_USER}@${host} "${RESTART_CMD}"
done

echo "Deployment complete. Run smoke tests and monitor logs." 
