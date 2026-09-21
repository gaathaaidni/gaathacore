"""Legacy helper: add missing email confirmation columns to a SQLite DB.
This script targets legacy `instance/app.db` SQLite databases and will add
`email_confirmed` and `email_confirmed_at` if they're missing. Keep for
migration/repair use only; the application now requires PostgreSQL.
"""
"""Legacy helper: (SQLite) email confirmation columns fixer.

This repository now targets PostgreSQL. This helper is retained only for
legacy local SQLite databases (instance/app.db). For PostgreSQL you should
use Alembic migrations: `flask db upgrade`.

Usage (legacy SQLite only):
    python scripts/add_email_confirm_columns.py
"""
import os
from pathlib import Path

db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres'):
    print('DATABASE_URL points to PostgreSQL; use `flask db upgrade` instead of this helper.')
    raise SystemExit(1)

import sqlite3

db_path = Path(__file__).resolve().parents[1] / 'instance' / 'app.db'
if not db_path.exists():
    print('Legacy SQLite DB not found at', db_path)
    raise SystemExit(1)

with sqlite3.connect(str(db_path)) as conn:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info('user')")
    cols = [r[1] for r in cur.fetchall()]
    if 'email_confirmed' not in cols:
        try:
            cur.execute("ALTER TABLE user ADD COLUMN email_confirmed BOOLEAN DEFAULT 0")
            print('Added column email_confirmed')
        except Exception as e:
            print('Failed to add email_confirmed:', e)
    else:
        print('email_confirmed already present')
    if 'email_confirmed_at' not in cols:
        try:
            cur.execute("ALTER TABLE user ADD COLUMN email_confirmed_at DATETIME")
            print('Added column email_confirmed_at')
        except Exception as e:
            print('Failed to add email_confirmed_at:', e)
    else:
        print('email_confirmed_at already present')
    conn.commit()
print('Done')
