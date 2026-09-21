#!/usr/bin/env python
"""
Initialize the database by creating all tables from SQLAlchemy models.
This script should be run once to set up a fresh database.
"""
import asyncio
import sys
import os
from sqlalchemy import create_engine, event, text, inspect
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import engine, Base, AsyncSessionLocal
from app.config import Config
from app.models.user import User
from app.utils.roles import ROLE_SUPERADMIN
from app.utils.schema_sync import ensure_schema_compatibility

# Import only the essential models to avoid circular imports
# These are ordered by dependency
print("Loading models...")

# Core models (no dependencies)
try:
    from app.models.organization import Organization
    print("✓ Loaded Organization")
except Exception as e:
    print(f"✗ Organization: {e}")

try:
    from app.models.user import User, APIKey, OTP, RefreshToken
    print("✓ Loaded User models")
except Exception as e:
    print(f"✗ User models: {e}")

try:
    from app.models.base import ActivityLog
    print("✓ Loaded ActivityLog")
except Exception as e:
    print(f"✗ ActivityLog: {e}")

# Inventory models BEFORE Purchase Order (due to FK dependency)
try:
    from app.models.inventory import Item, Warehouse, StockTransaction
    print("✓ Loaded Inventory models")
except Exception as e:
    print(f"✗ Inventory models: {e}")

# Models that depend on Organization
try:
    from app.models.notifications import Notification
    print("✓ Loaded Notification")
except Exception as e:
    print(f"✗ Notification: {e}")

try:
    from app.models.expenses import Expense, Vendor
    print("✓ Loaded Expenses and Vendor")
except Exception as e:
    print(f"✗ Expenses/Vendor: {e}")

try:
    from app.models.purchase_order import PurchaseOrder, POLineItem
    print("✓ Loaded PurchaseOrder")
except Exception as e:
    print(f"✗ PurchaseOrder: {e}")

# Other models
try:
    from app.models.books import Account, Invoice, InvoiceLine, InvoiceSequence
    print("✓ Loaded Books models")
except Exception as e:
    print(f"✗ Books models: {e}")

try:
    from app.models.crm import Customer, Lead, Opportunity
    print("✓ Loaded CRM models")
except Exception as e:
    print(f"✗ CRM models: {e}")

# HR models (must come after User due to FK dependency)
try:
    from app.models.hr import Department, Employee, Payslip, AttendanceRecord, PerformanceReview
    print("✓ Loaded HR models")
except Exception as e:
    print(f"✗ HR models: {e}")

# Models with known issues - skip them for now
try:
    from app.models.vendor_management import Vendor as VendorMgmt
    print("✓ Loaded Vendor Management")
except Exception as e:
    print(f"✗ Vendor Management: {e}")


async def init_db():
    """Create all database tables."""
    print("\n" + "="*50)
    print("Creating database tables...")
    print("="*50)
    
    try:
        # Backfill missing Base columns on existing legacy tables before creating anything else.
        sync_db_url = os.environ.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL', '').replace('+asyncpg', '')
        sync_engine = create_engine(sync_db_url)
        ensure_schema_compatibility(sync_engine)

        with sync_engine.begin() as conn:
            insp = inspect(conn)
            if insp.has_table('user') and not insp.has_table('users'):
                conn.execute(text('ALTER TABLE "user" RENAME TO users'))
                print('✓ Renamed legacy user table to users for schema sync')

            Base.metadata.create_all(bind=conn)

            if insp.has_table('users'):
                cols = {c['name'] for c in insp.get_columns('users')}
                changes = []
                if 'first_name' not in cols:
                    changes.append('ADD COLUMN first_name VARCHAR(80)')
                if 'last_name' not in cols:
                    changes.append('ADD COLUMN last_name VARCHAR(80)')
                if 'organization_id' not in cols:
                    changes.append('ADD COLUMN organization_id INTEGER')
                if 'avatar_url' not in cols:
                    changes.append('ADD COLUMN avatar_url VARCHAR(500)')
                if 'last_login' not in cols:
                    changes.append('ADD COLUMN last_login TIMESTAMPTZ')
                if 'oauth_id' not in cols:
                    changes.append('ADD COLUMN oauth_id VARCHAR(255)')
                if 'oauth_provider' not in cols:
                    changes.append('ADD COLUMN oauth_provider VARCHAR(50)')
                if 'email_verified' not in cols:
                    changes.append('ADD COLUMN email_verified BOOLEAN DEFAULT FALSE')
                if 'email_verified_at' not in cols:
                    changes.append('ADD COLUMN email_verified_at TIMESTAMPTZ')

                if changes:
                    conn.execute(text('ALTER TABLE users ' + ', '.join(changes)))
                    print('✓ Backfilled missing users columns for schema sync')

                if 'email_verified' in {c['name'] for c in insp.get_columns('users')} and 'email_confirmed' in cols:
                    conn.execute(text("UPDATE users SET email_verified = COALESCE(email_verified, email_confirmed, FALSE) WHERE email_verified IS NULL OR email_verified = FALSE"))
                if 'email_verified_at' in {c['name'] for c in insp.get_columns('users')} and 'email_confirmed_at' in cols:
                    conn.execute(text("UPDATE users SET email_verified_at = COALESCE(email_verified_at, email_confirmed_at) WHERE email_verified_at IS NULL"))

        print('✓ Database tables created successfully!')

        # Bootstrap superadmin user from environment credentials if configured
        if Config.SUPERADMIN_EMAIL and Config.SUPERADMIN_PASSWORD:
            admin_email = Config.SUPERADMIN_EMAIL.strip()
            admin_username = admin_email.split('@')[0]
            Session = sessionmaker(bind=sync_engine)
            with Session() as session:
                admin_user = session.query(User).filter((User.email == admin_email) | (User.username == admin_username)).first()

                if not admin_user:
                    print(f'Creating superadmin user from .env: {admin_username}')
                    admin_user = User(
                        username=admin_username,
                        email=admin_email,
                        role=ROLE_SUPERADMIN,
                        organization_id=None,
                        email_verified=True,
                    )
                    admin_user.set_password(Config.SUPERADMIN_PASSWORD)
                    session.add(admin_user)
                    session.commit()
                    print(f'✓ Superadmin user created: {admin_username}')
                else:
                    changed = False
                    if getattr(admin_user, 'role', '') != ROLE_SUPERADMIN:
                        print(f'Promoting existing user to superadmin: {admin_username}')
                        admin_user.role = ROLE_SUPERADMIN
                        changed = True
                    if admin_user.email != admin_email:
                        admin_user.email = admin_email
                        changed = True
                    if admin_user.username != admin_username:
                        admin_user.username = admin_username
                        changed = True
                    if getattr(admin_user, 'organization_id', None) is not None:
                        admin_user.organization_id = None
                        changed = True
                    if not getattr(admin_user, 'email_verified', False):
                        admin_user.email_verified = True
                        changed = True

                    # Keep the .env superadmin credentials authoritative so an
                    # existing org-admin account with the same email cannot keep
                    # acting like a normal tenant-scoped admin after deployment.
                    admin_user.set_password(Config.SUPERADMIN_PASSWORD)
                    changed = True

                    if changed:
                        session.add(admin_user)
                        session.commit()
                        print(f'✓ Superadmin user synced: {admin_username}')

        return True
    except Exception as e:
        print(f"✗ Error creating database tables: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(init_db())
    sys.exit(0 if success else 1)
