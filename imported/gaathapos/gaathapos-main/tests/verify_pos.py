# Smoke/verification script for key POS features
# Run with: python -m tests.verify_pos or python tests/verify_pos.py

from app import app
from extensions import db
from werkzeug.security import generate_password_hash
from models import (
    Restaurant, User, ProductCategory, Product, BarcodeMapping,
    PaymentMethod, RestaurantFloorPlan, TableSection, Table,
    Customer, LoyaltyCard, eWallet
)
import json


def setup_data():
    with app.app_context():
        # Enable testing mode and disable CSRF for the smoke script
        app.config['TESTING'] = True
        # If the app uses Flask-WTF CSRF, disable it for tests
        app.config['WTF_CSRF_ENABLED'] = False
        # Clear data instead of dropping schema to avoid breaking other tests
        try:
            for table in reversed(db.metadata.sorted_tables):
                try:
                    db.session.execute(table.delete())
                except Exception:
                    pass
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Create restaurant
        restaurant = Restaurant(name='Test Resto', email='resto@example.com', phone='123', address='Addr', owner_id=1)
        db.session.add(restaurant)
        db.session.flush()

        # Create owner user
        owner = User(username='owner', password_hash=generate_password_hash('ownerpass'), role='restaurant_admin', restaurant_id=restaurant.id, is_super_admin=False)
        db.session.add(owner)
        db.session.flush()
        restaurant.owner_id = owner.id

        # Manager user
        manager = User(username='manager', password_hash=generate_password_hash('managerpass'), role='manager', restaurant_id=restaurant.id)
        db.session.add(manager)
        db.session.flush()

        # Chef / kitchen user
        chef = User(username='chef', password_hash=generate_password_hash('chefpass'), role='kitchen', restaurant_id=restaurant.id)
        db.session.add(chef)
        db.session.flush()
        
        # Admin user (platform admin) for privileged actions
        admin = User(username='admin', password_hash=generate_password_hash('adminpass'), role='admin', restaurant_id=restaurant.id, is_super_admin=True)
        db.session.add(admin)
        db.session.flush()

        # Create waiter user for POS
        waiter = User(username='waiter', password_hash=generate_password_hash('waiterpass'), role='waiter', restaurant_id=restaurant.id)
        db.session.add(waiter)
        db.session.flush()

        # Product category and product
        cat = ProductCategory(restaurant_id=restaurant.id, name='Beverages')
        db.session.add(cat)
        db.session.flush()

        prod = Product(restaurant_id=restaurant.id, category_id=cat.id, name='Coffee', base_price=2.5, available=True)
        db.session.add(prod)
        db.session.flush()

        # Barcode mapping
        bm = BarcodeMapping(product_id=prod.id, barcode='TEST123', embedded_price=2.5)
        db.session.add(bm)

        # Payment method
        pm = PaymentMethod(restaurant_id=restaurant.id, name='Cash', payment_type='cash', requires_external_terminal=False)
        db.session.add(pm)

        # Cash register
        from models import CashRegister, Kiosk
        register = CashRegister(restaurant_id=restaurant.id, register_name='Main Register', hardware_id='REG-1')
        db.session.add(register)

        # Kiosk
        kiosk = Kiosk(restaurant_id=restaurant.id, name='Lobby Kiosk', kiosk_code='KIOSK1')
        db.session.add(kiosk)

        # Floor plan and table
        fp = RestaurantFloorPlan(restaurant_id=restaurant.id, name='Main')
        db.session.add(fp)
        db.session.flush()

        section = TableSection(floor_plan_id=fp.id, name='Indoor', capacity=20)
        db.session.add(section)
        db.session.flush()

        table = Table(section_id=section.id, table_number='T1', seats=4)
        db.session.add(table)

        # Customer + loyalty + ewallet
        customer = Customer(restaurant_id=restaurant.id, name='John Doe', email='john@example.com', phone='555')
        db.session.add(customer)
        db.session.flush()

        loyalty = LoyaltyCard(customer_id=customer.id, card_number='LC1001', points_balance=100)
        db.session.add(loyalty)

        wallet = eWallet(customer_id=customer.id, balance=10.0, currency='USD')
        db.session.add(wallet)

        db.session.commit()

        return {
            'restaurant_id': restaurant.id,
            'owner_id': owner.id,
            'manager_id': manager.id,
            'chef_id': chef.id,
            'admin_id': admin.id,
            'waiter_id': waiter.id,
            'waiter_username': 'waiter',
            'waiter_password': 'waiterpass',
            'product_barcode': 'TEST123',
            'product_name': prod.name,
            'payment_method_id': pm.id,
            'customer_id': customer.id,
            'table_id': table.id
        }


def run_smoke_checks(data):
    with app.test_client() as client:
        # Ensure testing and CSRF disabled on client side too
        client.application.config['TESTING'] = True
        client.application.config['WTF_CSRF_ENABLED'] = False
        def show(r, label=None):
            try:
                payload = r.get_json()
            except Exception:
                payload = None
            if payload is None:
                text = (r.data.decode('utf-8') or '').strip()
                print(label or '', r.status_code, text[:400])
            else:
                print(label or '', r.status_code, payload)
        # Simulate logged-in waiter by setting Flask-Login session keys
        with client.session_transaction() as sess:
            sess['_user_id'] = str(data['waiter_id'])
            sess['_fresh'] = True

        # Products
        r = client.get('/pos/products')
        print('/pos/products', r.status_code, r.get_json()[:1] if r.is_json else r.data[:200])

        # Barcode lookup
        r = client.get(f"/pos/products/by-barcode/{data['product_barcode']}")
        print('/pos/products/by-barcode', r.status_code, r.get_json())

        # Payment methods
        r = client.get('/pos/payment-methods')
        print('/pos/payment-methods', r.status_code, r.get_json())

        # Tables
        r = client.get('/pos/tables')
        print('/pos/tables', r.status_code, r.get_json())

        # Customer search
        r = client.get('/pos/customers/search?q=John')
        print('/pos/customers/search?q=John', r.status_code, r.get_json())

        # Customer loyalty info
        r = client.get(f"/pos/customers/{data['customer_id']}/loyalty")
        print(f"/pos/customers/{data['customer_id']}/loyalty", r.status_code, r.get_json())

        # Create an order (as waiter)
        with client.session_transaction() as sess:
            sess['_user_id'] = str(data['waiter_id'])
            sess['_fresh'] = True
        order_payload = {"items": [{"product_id": 1, "quantity": 2}]}
        r = client.post('/pos/orders', json=order_payload)
        show(r, '/pos/orders (create)')
        order_resp = None
        try:
            order_resp = r.get_json() or {}
        except Exception:
            order_resp = {}
        order_id = order_resp.get('id')

        # Try a split-bill (2 splits) — use admin/privileged user
        if order_id:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(data['admin_id'])
                sess['_fresh'] = True
            split_payload = {"splits": [{"payment_method_id": data['payment_method_id'], "amount": 2.5}, {"payment_method_id": data['payment_method_id'], "amount": 2.5}]}
            r = client.post(f'/pos/orders/{order_id}/split-bill', json=split_payload)
            show(r, f'/pos/orders/{order_id}/split-bill')

            # Checkout / payment (admin)
            checkout_payload = {"payment_method_id": data['payment_method_id'], "amount": 5.0}
            r = client.post(f'/pos/orders/{order_id}/checkout', json=checkout_payload)
            show(r, f'/pos/orders/{order_id}/checkout')

        # Redeem loyalty points (use admin for privileged actions)
        with client.session_transaction() as sess:
            sess['_user_id'] = str(data['admin_id'])
            sess['_fresh'] = True
        r = client.post(f"/pos/customers/{data['customer_id']}/loyalty/redeem", json={'reward_id': None, 'points': 10})
        show(r, '/pos/customers/<id>/loyalty/redeem')

        # E-wallet topup
        r = client.post(f"/pos/customers/{data['customer_id']}/ewallet/topup", json={'amount': 20.0, 'payment_method_id': data['payment_method_id']})
        show(r, '/pos/customers/<id>/ewallet/topup')

        # Create a delayed order entry
        if order_id:
            r = client.post('/pos/delayed-orders', json={'order_id': order_id, 'course_number': 2, 'delay_minutes': 15})
            print('/pos/delayed-orders', r.status_code, r.get_json())

        # Kiosk menu
        r = client.get('/pos/kiosk/KIOSK1/menu')
        print('/pos/kiosk/KIOSK1/menu', r.status_code, r.get_json())

        # Open cash register (use admin)
        with client.session_transaction() as sess:
            sess['_user_id'] = str(data['admin_id'])
            sess['_fresh'] = True
        open_payload = {'register_id': 1, 'opening_balance': 100.0}
        r = client.post('/pos/cash-registers/open', json=open_payload)
        show(r, '/pos/cash-registers/open')

        # Close cash register
        r = client.post('/pos/cash-registers/1/close', json={'actual_balance': 105.0})
        show(r, '/pos/cash-registers/1/close')

        # Offline sync: simulate syncing (no offline payments inserted here, just call)
        r = client.post('/pos/orders/sync', json={'orders': []})
        print('/pos/orders/sync', r.status_code, r.get_json())

        # Check owner (restaurant_admin) access to admin dashboard
        with client.session_transaction() as sess:
            sess['_user_id'] = str(data['owner_id'])
            sess['_fresh'] = True
        r = client.get('/admin/')
        print('/admin/ (owner)', r.status_code)

        # Check manager access to admin dashboard
        with client.session_transaction() as sess:
            sess['_user_id'] = str(data['manager_id'])
            sess['_fresh'] = True
        r = client.get('/admin/')
        print('/admin/ (manager)', r.status_code)

        # Check chef access to KDS pending orders
        with client.session_transaction() as sess:
            sess['_user_id'] = str(data['chef_id'])
            sess['_fresh'] = True
        r = client.get('/kds/orders')
        print('/kds/orders (chef)', r.status_code, r.get_json() if r.is_json else r.data[:200])


if __name__ == '__main__':
    print('Setting up test data...')
    data = setup_data()
    print('Running smoke checks...')
    run_smoke_checks(data)
    print('Done')
