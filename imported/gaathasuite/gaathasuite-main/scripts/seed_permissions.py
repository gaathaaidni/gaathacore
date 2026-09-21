#!/usr/bin/env python3
"""Seed permission records for coupon and payments management."""
from app import create_app
from extensions import db
from models import Permission

app = create_app()
with app.app_context():
    perms = [
        {'name': 'coupons.manage', 'description': 'Create, edit, delete and import/export coupons', 'module': 'coupons', 'action': 'manage'},
        {'name': 'payments.manage', 'description': 'Manage organization payments', 'module': 'payments', 'action': 'manage'},
    ]
    added = 0
    for p in perms:
        if not Permission.query.filter_by(name=p['name']).first():
            Permission(name=p['name'], description=p['description'], module=p['module'], action=p['action'])
            db.session.add(Permission(name=p['name'], description=p['description'], module=p['module'], action=p['action']))
            added += 1
    if added:
        db.session.commit()
    print(f"Seeded {added} permissions")
