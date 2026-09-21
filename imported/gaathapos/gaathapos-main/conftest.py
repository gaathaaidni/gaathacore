import pytest
import os

# Use a temporary file-backed SQLite DB for tests (shared across connections)
os.environ.setdefault('DATABASE_URL', 'sqlite:////tmp/nexorapos_test.db')
# Remove any leftover test DB from previous runs to start clean
try:
    if os.path.exists('/tmp/nexorapos_test.db'):
        os.remove('/tmp/nexorapos_test.db')
except Exception:
    pass

from app import create_app
from extensions import db
from werkzeug.security import generate_password_hash

# Create an application for the test session and ensure the DB schema exists
app = create_app()
app.config.setdefault("WTF_CSRF_ENABLED", False)

# Ensure schema exists as soon as conftest is imported (before test collection)
with app.app_context():
    try:
        db.create_all()
    except Exception:
        pass


def safe_reset_db(app=app):
    """Helper function: safely clear all data and reseed without dropping schema.
    Tests can import and call this to reset DB state without breaking the schema.
    """
    with app.app_context():
        # Clear all data (but keep schema)
        try:
            for table in reversed(db.metadata.sorted_tables):
                try:
                    db.session.execute(table.delete())
                except Exception:
                    pass
            db.session.commit()
        except Exception:
            pass

        # Seed basic users and menu items expected by tests
        try:
            from models import User, MenuItem, InventoryItem

            admin = User(username="admin", password_hash=generate_password_hash("admin"), role="admin")
            waiter = User(username="waiter", password_hash=generate_password_hash("waiter"), role="waiter")
            kitchen = User(username="kitchen", password_hash=generate_password_hash("kitchen"), role="kitchen")
            manager = User(username="manager", password_hash=generate_password_hash("manager"), role="manager")
            db.session.add_all([admin, waiter, kitchen, manager])
            
            db.session.add(MenuItem(name="Chicken Sizzler", description="Hot sizzling platter", price=45.0))
            db.session.add(MenuItem(name="Paneer Tikka Sizzler", description="Vegetarian delight", price=40.0))
            db.session.add(MenuItem(name="Pasta Alfredo", description="Continental creamy pasta", price=35.0))
            
            # Add inventory items for tests that expect them
            db.session.add(InventoryItem(name="Chicken", quantity=50, unit="kg"))
            db.session.add(InventoryItem(name="Oil", quantity=20, unit="liters"))
            db.session.commit()
        except Exception:
            pass


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Session fixture: create schema at start, drop at end."""
    with app.app_context():
        try:
            db.create_all()
        except Exception:
            pass
    
    yield

    with app.app_context():
        try:
            db.drop_all()
        except Exception:
            pass


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Function fixture: clear tables before each test and seed basic data."""
    safe_reset_db(app)
    yield
    # Clean up after test
    with app.app_context():
        try:
            db.session.rollback()
        except Exception:
            pass
