#!/usr/bin/env python3
"""Attempt to migrate a legacy SQLite `instance/app.db` to the configured
PostgreSQL `DATABASE_URL`.

This script tries to use `pgloader` when available. If `pgloader` is not
installed it will emit step-by-step instructions and create a SQL dump of
the SQLite DB to `./tmp/sqlite_dump.sql` which can be inspected or manually
imported.

Usage:
  export DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
  python scripts/migrate_sqlite_to_postgres.py

Note: This script is a convenience helper. For production migrations prefer
using `pgloader` or a tested data-migration pipeline.
"""
import os
import shutil
import subprocess
from pathlib import Path


def main():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print('ERROR: set DATABASE_URL env var to your target Postgres database')
        raise SystemExit(1)

    sqlite_path = Path(__file__).resolve().parents[1] / 'instance' / 'app.db'
    if not sqlite_path.exists():
        print('No legacy SQLite DB found at', sqlite_path)
        raise SystemExit(1)

    tmp_dir = Path('./tmp')
    tmp_dir.mkdir(exist_ok=True)

    # Prefer pgloader if available
    if shutil.which('pgloader'):
        print('pgloader found — attempting automatic migration...')
        cmd = [
            'pgloader',
            str(sqlite_path),
            db_url,
        ]
        print('Running:', ' '.join(cmd))
        subprocess.run(cmd, check=True)
        print('pgloader completed. Verify data in Postgres and run `flask db upgrade`.')
        return

    # Fallback: create SQL dump
    dump_file = tmp_dir / 'sqlite_dump.sql'
    print('pgloader not found. Creating sqlite3 SQL dump at', dump_file)
    try:
        subprocess.run(['sqlite3', str(sqlite_path), '.dump'], stdout=open(dump_file, 'wb'), check=True)
    except Exception:
        # Try using Python sqlite3 to export
        import sqlite3
        with sqlite3.connect(str(sqlite_path)) as conn, open(dump_file, 'w', encoding='utf-8') as out:
            for line in conn.iterdump():
                out.write('%s\n' % line)

    print('\nDump created. Next steps:')
    print('1) Inspect and clean up', dump_file)
    print('2) Create target DB (if not exists) and ensure user has privileges')
    print('3) Import using psql:')
    print("   psql 'DATABASE_URL' -f ", dump_file)
    print('\nAlternatively install pgloader and run: pgloader <sqlite> <postgres>')


if __name__ == '__main__':
    main()
