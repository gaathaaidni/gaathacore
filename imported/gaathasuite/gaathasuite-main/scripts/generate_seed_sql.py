#!/usr/bin/env python3
"""Generate a seed SQL file that mirrors `seed.py` (non-destructive unless you run it).
Run: python scripts/generate_seed_sql.py > seed.sql
"""
from werkzeug.security import generate_password_hash
from datetime import date
import os

lines = []

# Tables to truncate (same order as seed.py)
truncate_tables = [
    'beta_access', 'organization_user', 'organization', 'user', 'customer', 'lead', 'opportunity',
    'account', 'invoice', 'invoice_line', 'item', 'warehouse', 'stock_transaction',
    'employee', 'department', 'payslip', 'payment', 'ticket', 'ticket_comment'
]
lines.append('BEGIN;')
for t in truncate_tables:
    lines.append(f'TRUNCATE TABLE "{t}" RESTART IDENTITY CASCADE;')
lines.append('\n-- USERS')
# Users: admin (is_admin, is_superadmin), john
admin_email = os.environ.get('SUPERADMIN_EMAIL', 'admin@gaatha.local')
admin_pass = os.environ.get('SUPERADMIN_PASSWORD', os.environ.get('SEED_ADMIN_PASSWORD', 'admin123'))
john_pass = os.environ.get('SEED_USER_PASSWORD', 'john123')
admin_hash = generate_password_hash(admin_pass)
john_hash = generate_password_hash(john_pass)
admin_username = admin_email.split('@')[0]
lines.append(
    "INSERT INTO \"user\" (id, username, email, password_hash, is_admin, is_superadmin, created_at) VALUES\n"
    f"(1, '{admin_username}', '{admin_email}', '{admin_hash}', TRUE, TRUE, now()),\n"
    f"(2, 'john', 'john@gaatha.local', '{john_hash}', FALSE, FALSE, now());"
)

lines.append('\n-- SUBSCRIPTION PLANS')
import json

plans = [
    (1, 'Free (Beta)', 'free', 0.0, 0.0, {"users": 3, "orgs": 1, "modules": "all", "storage_gb": 1}),
    (2, 'Basic', 'basic', 14.0, 140.0, {"users": 5, "orgs": 1, "modules": ["CRM","Inventory","Books","HR","Desk"], "invoices_month": 1000, "storage_gb": 5}),
    (3, 'Business', 'business', 29.0, 290.0, {"users": "unlimited", "modules": "all", "storage_gb": 50, "api_access": True}),
    (4, 'Enterprise', 'enterprise', 59.0, 590.0, {"users": "unlimited", "modules": "all", "storage_gb": 200, "multi_org": True})
]
for p in plans:
    id_, name, slug, m, y, features = p
    features_json = json.dumps(features)
    lines.append(f"INSERT INTO subscription_plan (id, name, slug, monthly_price, yearly_price, features) VALUES ({id_}, '{name}', '{slug}', {m}, {y}, '{features_json}'::json);")

lines.append('\n-- BETA ACCESS')
lines.append("INSERT INTO beta_access (user_id, expires_on) VALUES (1, CURRENT_DATE + interval '1 year'), (2, CURRENT_DATE + interval '1 year');")

lines.append('\n-- PERMISSIONS (partial set)')
perms = [
    ('books.view','Books','books','view'),
    ('books.create','Books','books','create'),
    ('crm.view','CRM','crm','view'),
    ('inventory.view','Inventory','inventory','view'),
    ('payroll.view','Payroll','payroll','view')
]
for name, desc, module, action in perms:
    lines.append(f"INSERT INTO permission (name, description, module, action) VALUES ('{name}', '{desc}', '{module}', '{action}');")

lines.append('\n-- DEFAULT ORGANIZATION')
lines.append("INSERT INTO organization (id, name, slug, domain) VALUES (1, 'Default Organization', 'default-org', 'gaatha.local');")
lines.append("INSERT INTO organization_user (organization_id, user_id, role) VALUES (1, 1, 'owner'), (1, 2, 'member');")

lines.append('\n-- CUSTOMERS')
customers = [
    (1, "Acme Corporation", "contact@acme.com", "+1-555-0101", "123 Main St, NYC", 'USD'),
    (2, "Tech Solutions Ltd", "info@techsol.com", "+1-555-0102", "456 Tech Ave, SF", 'USD')
]
for c in customers:
    id_, name, email, phone, address, currency = c
    lines.append(f"INSERT INTO customer (id, name, email, phone, address, currency) VALUES ({id_}, '{name}', '{email}', '{phone}', '{address}', '{currency}');")

lines.append('\n-- LEADS & OPPORTUNITIES')
lines.append("INSERT INTO lead (name, contact_email, source, status) VALUES ('Sarah Johnson','sarah@example.com','Website','new'), ('Mike Davis','mike@example.com','Referral','contacted'), ('Lisa Chen','lisa@example.com','LinkedIn','qualified');")
lines.append("INSERT INTO opportunity (title, customer_id, value, stage) VALUES ('Enterprise Deal', 1, 50000.00, 'prospect'), ('Mid-Market Expansion', 2, 25000.00, 'negotiation');")

lines.append('\n-- ACCOUNTS & INVOICES')
lines.append("INSERT INTO account (name, type, code) VALUES ('Receivables','asset','1000'), ('Revenue','income','4000'), ('COGS','expense','5000');")
lines.append("INSERT INTO invoice (number, customer_id, date, due_date, status, total_amount) VALUES ('INV-2025001', 1, now()::date, (now()+interval '30 days')::date, 'sent', 2000.00), ('INV-2025002', 2, now()::date, (now()+interval '30 days')::date, 'draft', 1000.00);")
lines.append("INSERT INTO invoice_line (invoice_id, description, qty, unit_price, total) VALUES (1, 'Service #1', 1, 1000.00, 1000.00), (1, 'Service #2', 2, 1000.00, 2000.00);")

lines.append('\n-- WAREHOUSES & ITEMS')
lines.append("INSERT INTO warehouse (name, location) VALUES ('Main Warehouse','New York'), ('West Coast Warehouse','Los Angeles');")
lines.append("INSERT INTO item (sku, name, description, unit_cost, unit_price, quantity_on_hand) VALUES ('ITEM-001','Widget A','Premium Widget',10.00,25.00,100), ('ITEM-002','Widget B','Standard Widget',5.00,15.00,250);")

lines.append('\n-- DEPARTMENTS & EMPLOYEES & PAYSLIPS')
lines.append("INSERT INTO department (id, name) VALUES (1, 'Engineering'), (2, 'Sales'), (3, 'Operations');")
lines.append("INSERT INTO employee (id, employee_code, name, email, department_id, position, hired_date, salary) VALUES (1,'EMP-001','Alice Smith','alice@gaatha.local',1,'Senior Engineer','2022-01-15',120000.00), (2,'EMP-002','Bob Johnson','bob@gaatha.local',2,'Sales Manager','2022-06-01',90000.00);")
lines.append("INSERT INTO payslip (employee_id, period_start, period_end, gross, deductions, net, status) VALUES (1, (now()-interval '30 days')::date, now()::date, 10000.00, 1000.00, 9000.00, 'draft');")

lines.append('\n-- PAYMENTS & TICKETS')
lines.append("INSERT INTO payment (invoice_id, amount, date, method, reference) VALUES (1, 3000.00, now()::date, 'bank', 'REF-001');")
lines.append("INSERT INTO ticket (customer_id, subject, description, priority, status) VALUES (1,'Login issues','Cannot access dashboard','high','open');")

# Update sequences
lines.append('\n-- Reset sequences to max ids')
lines.append("SELECT setval(pg_get_serial_sequence('\"user\"','id'), COALESCE((SELECT MAX(id) FROM \"user\"), 1));")
lines.append("SELECT setval(pg_get_serial_sequence('subscription_plan','id'), COALESCE((SELECT MAX(id) FROM subscription_plan), 1));")
lines.append("SELECT setval(pg_get_serial_sequence('customer','id'), COALESCE((SELECT MAX(id) FROM customer), 1));")

lines.append('\nCOMMIT;')

print('\n'.join(lines))
