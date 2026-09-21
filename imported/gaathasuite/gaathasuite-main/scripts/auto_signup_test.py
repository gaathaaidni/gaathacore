"""Automated test: register a test user and confirm via token without sending external email.
This script uses the Flask test client and the app context.
"""
import sys
from pathlib import Path
# ensure project root is on sys.path when running this script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os
from app import create_app
from extensions import db
from models import User
import time

# This test requires a PostgreSQL DATABASE_URL to be set in the environment.
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print('ERROR: DATABASE_URL must be set to run this test (PostgreSQL).')
    print('Example: export DATABASE_URL=postgresql+psycopg2://gaatha:changeme@localhost:5432/gaatha')
    raise SystemExit(1)

app = create_app()

with app.app_context():
    # ensure migrations have been applied (prefer using alembic). Create tables if missing.
    db.create_all()

    # use in-process client but avoid form validations (email_validator) by creating user directly
    app.config['RESEND_API_KEY'] = None
    client = app.test_client()

    ts = int(time.time())
    username = f"testuser_{ts}"
    email = f"test+{ts}@gaatha.local"
    password = "password123"

    # Ensure schema has new columns (email_confirmed) — prefer alembic migrations.
    inspector = None
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        cols = [c['name'] for c in inspector.get_columns('user')]
        if 'email_confirmed' not in cols or 'email_confirmed_at' not in cols:
            print('WARNING: `user.email_confirmed` columns missing. Run: flask db upgrade')
            raise SystemExit(1)
    except Exception:
        print('Could not inspect database schema; ensure migrations have been applied.')
        raise

    # create user directly to avoid external package requirements for form validation
    user = User(username=username, email=email)
    user.set_password(password)
    user.email_confirmed = False
    db.session.add(user)
    db.session.commit()
    print('User created:', user.username, user.email)

    # generate token and confirm via client
    token = user.get_email_confirmation_token()
    confirm_resp = client.get(f'/auth/confirm/{token}', follow_redirects=True)
    user = User.query.get(user.id)
    print('Confirmed:', bool(user.email_confirmed))

print('Done')
