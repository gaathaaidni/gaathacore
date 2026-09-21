#!/usr/bin/env bash
set -euo pipefail

# Usage: in a deploy hook or Render postdeploy
# Example: ./scripts/postdeploy_migrate.sh

echo "Running database migrations..."
python -m flask db upgrade
if [ $? -ne 0 ]; then
  echo "Migrations failed" >&2
  exit 1
fi

echo "Seeding database (if necessary)..."
python seed.py || true

echo "Post-deploy tasks finished."