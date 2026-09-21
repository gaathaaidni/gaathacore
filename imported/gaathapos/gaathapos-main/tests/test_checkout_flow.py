import json
import os

# Prevent background updater from running during tests
try:
    import extensions
    extensions.schedule_exchange_rate_updater = lambda *a, **k: None
    extensions.update_exchange_rates = lambda *a, **k: None
except Exception:
    pass

# Also ensure config flag is disabled before app is created
try:
    from config import Config
    Config.ENABLE_EXCHANGE_UPDATER = False
except Exception:
    pass

from app import create_app
from extensions import db


def setup_app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


def test_order_checkout_flow():
    app = setup_app()
    with app.app_context():
        # Clear data (but keep schema) instead of dropping entirely
        try:
            for table in reversed(db.metadata.sorted_tables):
                try:
                    db.session.execute(table.delete())
                except Exception:
                    pass
            db.session.commit()
        except Exception:
            db.session.rollback()

        # create fixture data via direct model imports to keep test focused
        from models import CashRegister, Product, PaymentMethod, Restaurant, User

        # create a user and restaurant
        user = User(username='owner', password_hash='x', role='manager')
        db.session.add(user)
        db.session.flush()

        r = Restaurant(name='Test R', email='r@test.com', owner_id=user.id)
        db.session.add(r)
        db.session.flush()

        user.restaurant_id = r.id
        db.session.add(user)
        db.session.commit()

        # product
        p = Product(restaurant_id=r.id, name='Test Coffee', base_price=3.5)
        db.session.add(p)
        db.session.commit()

        # payment method
        pm = PaymentMethod(restaurant_id=r.id, name='Cash', payment_type='cash')
        db.session.add(pm)
        db.session.add(CashRegister(
            restaurant_id=r.id,
            register_name='Main register',
            status='opened',
            opening_balance=0,
            current_balance=0,
        ))
        db.session.commit()

        # capture ids while still in the session to avoid detached instances
        user_id = user.id
        r_id = r.id
        p_id = p.id
        pm_id = pm.id

    client = app.test_client()

    # simulate logged-in user in the test client session
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['role'] = 'manager'

    # create an order
    order_payload = {
        'restaurant_id': r_id,
        'items': [{'product_id': p_id, 'quantity': 2}]
    }
    resp = client.post('/pos/orders', data=json.dumps(order_payload), content_type='application/json')
    assert resp.status_code == 201
    order = resp.get_json()
    order_id = order['id']

    # checkout
    checkout_payload = {
        'payment_method_id': pm_id,
        'amount': 7.0
    }
    resp = client.post(f'/pos/orders/{order_id}/checkout', data=json.dumps(checkout_payload), content_type='application/json')
    assert resp.status_code == 200
    out = resp.get_json()
    assert out.get('success') is True
