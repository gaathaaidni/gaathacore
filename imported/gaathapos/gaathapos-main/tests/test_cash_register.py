import json

from app import app
from extensions import db
from models import (
    CashierAccount,
    CashFlow,
    CashRegister,
    Order,
    PaymentMethod,
    PaymentTransaction,
    Product,
    RolePermission,
    Restaurant,
    User,
)

app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def make_tenant(name, username, register_status="closed"):
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
            base_price=10.0,
            active=True,
            available=True,
        )
        cash = PaymentMethod(
            restaurant_id=restaurant.id,
            name=f"{name} cash",
            payment_type="cash",
            active=True,
        )
        card = PaymentMethod(
            restaurant_id=restaurant.id,
            name=f"{name} card",
            payment_type="card",
            active=True,
        )
        register = CashRegister(
            restaurant_id=restaurant.id,
            register_name=f"{name} register",
            status=register_status,
            opening_balance=0,
            current_balance=0,
        )
        db.session.add_all([product, cash, card, register])
        db.session.commit()
        return {
            "user_id": user.id,
            "restaurant_id": restaurant.id,
            "product_id": product.id,
            "cash_id": cash.id,
            "card_id": card.id,
            "register_id": register.id,
        }


def open_register(client, register_id, opening_balance=100):
    return client.post(
        "/pos/cash-registers/open",
        data=json.dumps({"register_id": register_id, "opening_balance": opening_balance}),
        content_type="application/json",
    )


def make_order(client, product_id):
    response = client.post(
        "/pos/orders",
        data=json.dumps({"items": [{"product_id": product_id, "quantity": 1}]}),
        content_type="application/json",
    )
    assert response.status_code == 201
    return response.get_json()["id"]


def test_register_opening_and_duplicate_active_opening_are_rejected():
    tenant = make_tenant("Opening", "opening_user")
    client = app.test_client()
    login_as(client, tenant["user_id"])

    opened = open_register(client, tenant["register_id"])
    duplicate = open_register(client, tenant["register_id"])

    assert opened.status_code == 201
    assert duplicate.status_code == 400


def test_cash_in_out_and_closed_register_rules():
    tenant = make_tenant("Operations", "operations_user")
    client = app.test_client()
    login_as(client, tenant["user_id"])
    assert open_register(client, tenant["register_id"], 100).status_code == 201

    cash_in = client.post(f"/pos/cash-registers/{tenant['register_id']}/cash-in", json={"amount": 20})
    cash_out = client.post(f"/pos/cash-registers/{tenant['register_id']}/cash-out", json={"amount": 30})
    assert cash_in.status_code == 200
    assert cash_out.status_code == 200

    closed = client.post(f"/pos/cash-registers/{tenant['register_id']}/close", json={"actual_balance": 90})
    after_close = client.post(f"/pos/cash-registers/{tenant['register_id']}/cash-in", json={"amount": 1})
    assert closed.status_code == 200
    assert after_close.status_code == 400

    with app.app_context():
        register = db.session.get(CashRegister, tenant["register_id"])
        assert register.current_balance == 90
        assert {flow.adjustment_type for flow in register.cash_flows} >= {
            "opening_balance", "deposit", "withdrawal", "closing_balance"
        }


def test_cash_amounts_and_invalid_register_are_rejected():
    tenant = make_tenant("Validation", "cash_validation_user")
    client = app.test_client()
    login_as(client, tenant["user_id"])
    assert open_register(client, tenant["register_id"]).status_code == 201

    for amount in (0, -1):
        assert client.post(
            f"/pos/cash-registers/{tenant['register_id']}/cash-in", json={"amount": amount}
        ).status_code == 400
        assert client.post(
            f"/pos/cash-registers/{tenant['register_id']}/cash-out", json={"amount": amount}
        ).status_code == 400
    assert client.post("/pos/cash-registers/99999/cash-in", json={"amount": 1}).status_code == 404


def test_register_and_cash_operations_are_tenant_scoped():
    tenant_a = make_tenant("Tenant A", "cash_tenant_a")
    tenant_b = make_tenant("Tenant B", "cash_tenant_b")
    client = app.test_client()
    login_as(client, tenant_a["user_id"])

    assert open_register(client, tenant_b["register_id"]).status_code == 404
    assert client.post(
        f"/pos/cash-registers/{tenant_b['register_id']}/cash-in", json={"amount": 1}
    ).status_code == 404
    assert client.post(
        f"/pos/cash-registers/{tenant_b['register_id']}/cash-out", json={"amount": 1}
    ).status_code == 404
    assert client.post(
        f"/pos/cash-registers/{tenant_b['register_id']}/close", json={"actual_balance": 0}
    ).status_code == 404


def test_cash_payment_is_associated_and_requires_active_register():
    tenant = make_tenant("Payment", "cash_payment_user")
    client = app.test_client()
    login_as(client, tenant["user_id"])
    order_id = make_order(client, tenant["product_id"])

    missing_context = client.post(
        f"/pos/orders/{order_id}/checkout",
        json={"payment_method_id": tenant["cash_id"], "amount": 10},
    )
    assert missing_context.status_code == 400

    assert open_register(client, tenant["register_id"]).status_code == 201
    paid = client.post(
        f"/pos/orders/{order_id}/checkout",
        json={
            "payment_method_id": tenant["cash_id"],
            "amount": 10,
            "register_id": tenant["register_id"],
        },
    )
    assert paid.status_code == 200

    with app.app_context():
        payment = PaymentTransaction.query.filter_by(order_id=order_id).one()
        assert payment.cash_register_id == tenant["register_id"]
        assert payment.cashier_id is None
        assert CashFlow.query.filter_by(
            cash_register_id=tenant["register_id"], adjustment_type="payment"
        ).one().amount == 10


def test_non_cash_payment_does_not_change_register_balance():
    tenant = make_tenant("Card", "card_payment_user")
    client = app.test_client()
    login_as(client, tenant["user_id"])
    order_id = make_order(client, tenant["product_id"])

    paid = client.post(
        f"/pos/orders/{order_id}/checkout",
        json={"payment_method_id": tenant["card_id"], "amount": 10},
    )
    assert paid.status_code == 200

    with app.app_context():
        payment = PaymentTransaction.query.filter_by(order_id=order_id).one()
        register = db.session.get(CashRegister, tenant["register_id"])
        assert payment.cash_register_id is None
        assert register.current_balance == 0
        assert CashFlow.query.filter_by(
            cash_register_id=register.id, adjustment_type="payment"
        ).count() == 0


def test_cashier_ownership_and_active_status_are_enforced():
    tenant = make_tenant("Cashiers", "cashier_manager")
    with app.app_context():
        cashier_user = User(
            username="cashier_one", password_hash="x", role="cashier",
            restaurant_id=tenant["restaurant_id"],
        )
        other_user = User(
            username="cashier_two", password_hash="x", role="cashier",
            restaurant_id=tenant["restaurant_id"],
        )
        inactive_user = User(
            username="cashier_inactive", password_hash="x", role="cashier",
            restaurant_id=tenant["restaurant_id"],
        )
        db.session.add_all([cashier_user, other_user, inactive_user])
        db.session.flush()
        cashier = CashierAccount(user_id=cashier_user.id, active=True)
        other_cashier = CashierAccount(user_id=other_user.id, active=True)
        inactive_cashier = CashierAccount(user_id=inactive_user.id, active=False)
        db.session.add_all([
            cashier,
            other_cashier,
            inactive_cashier,
            RolePermission(role="cashier", permission="manage_cash", allowed=True),
        ])
        db.session.commit()
        cashier_id = cashier_user.id
        other_id = other_user.id
        inactive_id = inactive_user.id

    cashier_client = app.test_client()
    login_as(cashier_client, cashier_id)
    assert open_register(cashier_client, tenant["register_id"], 100).status_code == 201
    assert cashier_client.post(
        f"/pos/cash-registers/{tenant['register_id']}/cash-in", json={"amount": 10}
    ).status_code == 200

    other_client = app.test_client()
    login_as(other_client, other_id)
    assert other_client.post(
        f"/pos/cash-registers/{tenant['register_id']}/cash-in", json={"amount": 10}
    ).status_code == 403

    inactive_client = app.test_client()
    login_as(inactive_client, inactive_id)
    assert inactive_client.post(
        f"/pos/cash-registers/{tenant['register_id']}/cash-in", json={"amount": 10}
    ).status_code == 403

    assert cashier_client.post(
        f"/pos/cash-registers/{tenant['register_id']}/close", json={"actual_balance": 110}
    ).status_code == 200
