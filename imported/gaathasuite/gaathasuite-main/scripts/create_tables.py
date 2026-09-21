#!/usr/bin/env python3
"""Create missing database tables (useful for quick beta setup).

This script calls SQLAlchemy `create_all()` to ensure new models' tables exist.
Use in development/staging only; for production, prefer Alembic migrations.
"""
from app import create_app
from extensions import db

app = create_app()

with app.app_context():
    print('Creating missing tables (db.create_all())...')
    db.create_all()
    print('Done.')
