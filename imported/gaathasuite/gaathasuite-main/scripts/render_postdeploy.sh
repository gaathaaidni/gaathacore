#!/usr/bin/env bash
set -euo pipefail

# Run migrations and seed — intended for use in Render postdeploy only.
# Ensure DATABASE_URL and SECRET_KEY are set in the Render Dashboard env vars.

if [ -z "${DATABASE_URL-}" ]; then
  echo "ERROR: DATABASE_URL is not set. Aborting postdeploy."
  exit 1
fi

export FLASK_APP=run.py
python -m flask db upgrade
python seed.py || true

echo "Postdeploy migration & seed finished."
