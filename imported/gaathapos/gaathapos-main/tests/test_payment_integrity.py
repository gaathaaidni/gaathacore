import json

from app import app
from extensions import db
from models import CashRegister, Order, PaymentTransaction, Receipt, PaymentMethod, Product, Restaurant, User

app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def make_tenant(name, username, price=10.0):
    with app.app_context():
        user = User(username=username, password_hash="x", role="manager")
        db.session.add(user)
        db.session.flush()
        restaurant = Restaurant(name=name, email=f"{username}@example.com", owner_id=user.id)
        db.session.add(restaurant)
        db.session.flush()
        user.restaurant_id = restaurant.id
        product = Product(
            restaurant_id=restaurant.id,
            name=f"{name} item",
            base_price=price,
            active=True,
            available=True,
        )
        method = PaymentMethod(
            restaurant_id=restaurant.id,
            name=f"{name} cash",
            payment_type="cash",
            active=True,
        )
        register = CashRegister(
            restaurant_id=restaurant.id,
            register_name=f"{name} register",
            status="opened",
            opening_balance=0,
            current_balance=0,
        )
        db.session.add_all([product, method, register])
        db.session.commit()
        return {"user_id": user.id, "restaurant_id": restaurant.id, "product_id": product.id, "method_id": method.id}


def make_order(client, product_id, quantity=1):
    response = client.post(
        "/pos/orders",
        data=json.dumps({"items": [{"product_id": product_id, "quantity": quantity}]}),
        content_type="application/json",
    )
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.get_json()["id"]


def pay(client, order_id, method_id, amount, **kwargs):
    payload = {"payment_method_id": method_id, "amount": amount, **kwargs}
    return client.post(
        f"/pos/orders/{order_id}/checkout",
        data=json.dumps(payload),
        content_type="application/json",
    )


def test_full_payment_settles_order_and_creates_paid_receipt():
    tenant = make_tenant("Full", "full_user")
    client = app.test_client()
    login_as(client, tenant["user_id"])
    order_id = make_order(client, tenant["product_id"])

    response = pay(client, order_id, tenant["method_id"], 10.0)

    assert response.status_code == 200
    assert response.get_json()["status"] == "completed"
    with app.app_context():
        order = db.session.get(Order, order_id)
        assert order.status == "completed"
        assert len(order.payments) == 1
        assert len(order.receipts) == 1

    assert client.get(f"/pos/orders/{order_id}/receipt").status_code == 200
    assert client.post(f"/pos/orders/{order_id}/receipt/print", json={}).status_code == 200


def test_zero_negative_and_overpayment_are_rejected_without_payment_rows():
    tenant = make_tenant("Validation", "validation_user")
    client = app.test_client()
    login_as(client, tenant["user_id"])
    order_id = make_order(client, tenant["product_id"])

    for amount in (0, -1, 10.01):
        response = pay(client, order_id, tenant["method_id"], amount)
        assert response.status_code == 400

    with app.app_context():
        assert PaymentTransaction.query.filter_by(order_id=order_id).count() == 0


def test_partial_payments_do_not_settle_until_remaining_balance_is_paid():
    tenant = make_tenant("Partial", "partial_user")
    client = app.test_client()
    login_as(client, tenant["user_id"])
    order_id = make_order(client, tenant["product_id"])

    first = pay(client, order_id, tenant["method_id"], 4.0, reference_id="partial-1")
    assert first.status_code == 200
    assert first.get_json()["receipt_id"] is None
    assert client.get(f"/pos/orders/{order_id}/receipt").status_code == 404
    assert client.post(f"/pos/orders/{order_id}/receipt/print", json={}).status_code == 404
    with app.app_context():
        assert db.session.get(Order, order_id).status == "pending"
        assert Receipt.query.filter_by(order_id=order_id).count() == 0

    second = pay(client, order_id, tenant["method_id"], 6.0, reference_id="partial-2")
    assert second.status_code == 200
    with app.app_context():
        assert db.session.get(Order, order_id).status == "completed"
        assert PaymentTransaction.query.filter_by(order_id=order_id).count() == 2
        assert Receipt.query.filter_by(order_id=order_id).count() == 1


def test_second_payment_after_settlement_is_rejected_and_duplicate_reference_is_idempotent():
    tenant = make_tenant("Duplicate", "duplicate_user")
    client = app.test_client()
    login_as(client, tenant["user_id"])
    order_id = make_order(client, tenant["product_id"])

    first = pay(client, order_id, tenant["method_id"], 10.0, reference_id="same-payment")
    duplicate = pay(client, order_id, tenant["method_id"], 10.0, reference_id="same-payment")
    second = pay(client, order_id, tenant["method_id"], 1.0, reference_id="new-payment")

    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert duplicate.get_json()["idempotent"] is True
    assert second.status_code == 400
    with app.app_context():
        assert PaymentTransaction.query.filter_by(order_id=order_id).count() == 1


def test_offline_payment_remains_pending_and_has_no_paid_receipt():
    tenant = make_tenant("Offline", "offline_user")
    client = app.test_client()
    login_as(client, tenant["user_id"])
    order_id = make_order(client, tenant["product_id"])

    response = pay(client, order_id, tenant["method_id"], 10.0, is_offline=True, reference_id="offline-1")

    assert response.status_code == 200
    assert response.get_json()["status"] == "pending_sync"
    with app.app_context():
        order = db.session.get(Order, order_id)
        payment = PaymentTransaction.query.filter_by(order_id=order_id).one()
        assert order.status == "pending"
        assert payment.status == "pending"
        assert payment.synchronization_status == "pending_sync"
        assert Receipt.query.filter_by(order_id=order_id).count() == 0
    assert client.get(f"/pos/orders/{order_id}/receipt").status_code == 404
    assert client.post(f"/pos/orders/{order_id}/receipt/print", json={}).status_code == 404


def test_wrong_tenant_order_and_payment_method_are_rejected():
    tenant_a = make_tenant("Tenant A", "tenant_a")
    tenant_b = make_tenant("Tenant B", "tenant_b")
    client_a = app.test_client()
    login_as(client_a, tenant_a["user_id"])
    order_a = make_order(client_a, tenant_a["product_id"])
    client_b = app.test_client()
    login_as(client_b, tenant_b["user_id"])
    order_b = make_order(client_b, tenant_b["product_id"])

    assert pay(client_a, order_a, tenant_b["method_id"], 10.0).status_code == 404
    assert pay(client_a, order_b, tenant_a["method_id"], 10.0).status_code == 404

    with app.app_context():
        assert PaymentTransaction.query.count() == 0


def test_offline_sync_is_scoped_to_tenant_and_expected_order():
    tenant_a = make_tenant("Sync A", "sync_a")
    tenant_b = make_tenant("Sync B", "sync_b")
    client_a = app.test_client()
    login_as(client_a, tenant_a["user_id"])
    order_a = make_order(client_a, tenant_a["product_id"])
    offline = pay(
        client_a, order_a, tenant_a["method_id"], 10.0,
        is_offline=True, reference_id="sync-reference",
    )
    assert offline.status_code == 200

    client_b = app.test_client()
    login_as(client_b, tenant_b["user_id"])
    assert client_b.post(
        "/pos/orders/sync",
        json={"orders": [{"order_id": order_a, "reference_id": "sync-reference"}]},
    ).status_code == 404

    order_a_second = make_order(client_a, tenant_a["product_id"])
    wrong_order = client_a.post(
        "/pos/orders/sync",
        json={"orders": [{"order_id": order_a_second, "reference_id": "sync-reference"}]},
    )
    assert wrong_order.status_code == 400

    valid = client_a.post(
        "/pos/orders/sync",
        json={"orders": [{"order_id": order_a, "reference_id": "sync-reference"}]},
    )
    repeated = client_a.post(
        "/pos/orders/sync",
        json={"orders": [{"order_id": order_a, "reference_id": "sync-reference"}]},
    )
    assert valid.status_code == 200
    assert repeated.status_code == 200
    with app.app_context():
        payment = PaymentTransaction.query.filter_by(reference_id="sync-reference").one()
        assert payment.order_id == order_a
        assert payment.is_offline is False
        assert payment.status == "pending"
        assert db.session.get(Order, order_a).status == "pending"
