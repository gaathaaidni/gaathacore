from app import create_app
from extensions import db
from models import User, MenuItem, Restaurant, StoreSettings
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()

    # Create platform super admin
    if not User.query.filter_by(username='superadmin').first():
        superadmin = User(
            username="superadmin",
            password_hash=generate_password_hash("superadmin@123"),
            role="super_admin",
            is_super_admin=True,
            restaurant_id=None
        )
        db.session.add(superadmin)
        db.session.commit()
        print("✓ Super admin created: superadmin/superadmin@123")

    # Create legacy users if they don't exist
    if not User.query.filter_by(username='admin').first():
        admin = User(username="admin", password_hash=generate_password_hash("admin"), role="admin")
        waiter = User(username="waiter", password_hash=generate_password_hash("waiter"), role="waiter")
        kitchen = User(username="kitchen", password_hash=generate_password_hash("kitchen"), role="kitchen")
        manager = User(username="manager", password_hash=generate_password_hash("manager"), role="manager")
        db.session.add_all([admin, waiter, kitchen, manager])
        db.session.commit()
        print("✓ Legacy users created: admin/admin, waiter/waiter, kitchen/kitchen, manager/manager")

    # Create sample restaurant with restaurant_admin
    if not Restaurant.query.first():
        # First create a restaurant_admin user
        restaurant_admin_user = User(
            username="rest_admin",
            password_hash=generate_password_hash("rest_admin123"),
            role="restaurant_admin",
            is_super_admin=False,
            currency="USD"
        )
        db.session.add(restaurant_admin_user)
        db.session.flush()  # Flush to get the ID without committing
        
        # Create a sample restaurant
        restaurant = Restaurant(
            name="Demo Restaurant",
            email="demo@restaurant.local",
            phone="+353-1-234-5678",
            address="123 Main Street",
            city="Dublin",
            country="Ireland",
            postal_code="D01",
            owner_id=restaurant_admin_user.id,
            active=True
        )
        db.session.add(restaurant)
        db.session.flush()
        
        # Create default store settings
        store_settings = StoreSettings(
            restaurant_id=restaurant.id,
            timezone="Europe/Dublin",
            locale="en",
            currency="EUR",
            tax_region="EU",
            address_format="standard",
            business_registration="IE1234567890",
            vat_number="IE1234567890T",
            payment_terms=30,
            invoice_prefix="INV"
        )
        db.session.add(store_settings)
        db.session.commit()
        print("✓ Sample restaurant created: Demo Restaurant (demo@restaurant.local)")
        print("✓ Restaurant admin user created: rest_admin/rest_admin123")

    if not MenuItem.query.first():
        db.session.add(MenuItem(name="Chicken Sizzler", description="Hot sizzling platter", price=45.0))
        db.session.add(MenuItem(name="Paneer Tikka Sizzler", description="Vegetarian delight", price=40.0))
        db.session.add(MenuItem(name="Pasta Alfredo", description="Continental creamy pasta", price=35.0))
        db.session.commit()
        print("✓ Sample menu items added")

    print("\n📋 Seed data loaded successfully!")
    print("Platform accounts:")
    print("  - superadmin/superadmin@123 (super admin - owns platform)")
    print("  - rest_admin/rest_admin123 (restaurant admin - manages Demo Restaurant)")
    print("  - admin/admin (legacy admin account)")
