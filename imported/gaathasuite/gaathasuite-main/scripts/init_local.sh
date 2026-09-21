#!/usr/bin/env bash
set -euo pipefail

# Quick local setup script — uses SQLite by default (no DATABASE_URL required)
# Usage: ./scripts/init_local.sh

echo "Setting up virtualenv and installing requirements..."
python -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# force use of local SQLite even if DATABASE_URL exists in the environment
unset DATABASE_URL
export FLASK_APP=run.py

echo "Running database migrations (fallback to create_all if migrations fail)..."
if ! python -m flask db upgrade; then
  echo "flask db upgrade failed; running SQLAlchemy create_all() as fallback..."
  python - <<'PY'
from app import create_app
from extensions import db
app = create_app()
with app.app_context():
    db.create_all()
print('Tables created via db.create_all()')
PY
fi

echo "Seeding database..."
python seed.py

echo "Running smoke checks..."
python - <<'PY'
from app import create_app
app = create_app()
with app.test_client() as c:
    r = c.get('/_health')
    print('HEALTH', r.status_code, r.get_json())
with app.app_context():
    from models import User, Customer
    print('Users:', User.query.count(), 'Customers:', Customer.query.count())
PY

echo "Local initialization complete. Start the app with: flask run --host=0.0.0.0 or gunicorn -w 4 -b 0.0.0.0:5000 run:app"