import json

from app import create_app
from extensions import db
from werkzeug.security import generate_password_hash
from models import (
    AuditLog,
    Customer,
    DelayedOrder,
    Discount,
    MenuItem,
    Order,
    OrderItem,
    PaymentMethod,
    Product,
    Receipt,
    Restaurant,
    RestaurantFloorPlan,
    Table,
    TableSection,
    User,
    CashRegister,
)


def build_app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    return app


def login_as(client, user_id):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True


def make_restaurant(app, name, username):
    with app.app_context():
        restaurant = Restaurant(name=name, email=f"{username}@example.com", owner_id=1)
        db.session.add(restaurant)
        db.session.flush()

        user = User(
            username=username,
            password_hash=generate_password_hash("pass"),
            role="manager",
            restaurant_id=restaurant.id,
            is_super_admin=False,
        )
        db.session.add(user)
        db.session.flush()

        restaurant.owner_id = user.id

        product = Product(
            restaurant_id=restaurant.id,
            name=f"{name} Product",
            base_price=10.0,
            available=True,
            active=True,
        )
        db.session.add(product)
        db.session.flush()

        payment_method = PaymentMethod(
            restaurant_id=restaurant.id,
            name=f"{name} Cash",
            payment_type="cash",
            active=True,
        )
        db.session.add(payment_method)
        db.session.flush()

        db.session.add(CashRegister(
            restaurant_id=restaurant.id,
            register_name=f"{name} Register",
            status="opened",
            opening_balance=0,
            current_balance=0,
        ))

        floor_plan = RestaurantFloorPlan(restaurant_id=restaurant.id, name=f"{name} Plan")
        db.session.add(floor_plan)
        db.session.flush()

        section = TableSection(floor_plan_id=floor_plan.id, name="Main")
        db.session.add(section)
        db.session.flush()

        table = Table(section_id=section.id, table_number="1", seats=4, status="available")
        db.session.add(table)
        db.session.flush()

        db.session.commit()
        return {
            "restaurant_id": restaurant.id,
            "user_id": user.id,
            "product_id": product.id,
            "payment_method_id": payment_method.id,
            "table_id": table.id,
        }


def create_order_for_restaurant(client, user, product_id):
    payload = {"items": [{"product_id": product_id, "quantity": 2}]}
    resp = client.post("/pos/orders", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 201, resp.get_data(as_text=True)
    order_id = resp.get_json()["id"]
    with client.application.app_context():
        return db.session.get(Order, order_id)


def test_cross_restaurant_data_isolation():
    app = build_app()
    with app.app_context():
        restaurant_a = make_restaurant(app, "A", "tenant_a")
        restaurant_b = make_restaurant(app, "B", "tenant_b")

    client = app.test_client()
    login_as(client, restaurant_a["user_id"])

    with app.app_context():
        b_order = Order(
            restaurant_id=restaurant_b["restaurant_id"],
            status="pending",
        )
        db.session.add(b_order)
        db.session.flush()
        db.session.add(OrderItem(order_id=b_order.id, menu_item_id=restaurant_b["product_id"], quantity=1))

        receipt = Receipt(
            order_id=b_order.id,
            receipt_number="B-REC-1",
            content="Forbidden",
            header_text="A",
            footer_text="B",
        )
        db.session.add(receipt)
        db.session.commit()
        bad_order_id = b_order.id

    b_payment_id = restaurant_b["payment_method_id"]
    b_table_id = restaurant_b["table_id"]

    routes = [
        ("GET", f"/pos/orders/{bad_order_id}"),
        ("PUT", f"/pos/orders/{bad_order_id}/status", {"status": "cooking"}),
        ("POST", f"/pos/orders/{bad_order_id}/checkout", {"payment_method_id": b_payment_id, "amount": 20.0}),
        ("POST", f"/pos/orders/{bad_order_id}/split-bill", {"splits": [{"payment_method_id": b_payment_id, "amount": 20.0}]}),
        ("POST", f"/pos/orders/{bad_order_id}/discount", {"type": "percentage", "value": 10, "applies_to": "order"}),
        ("PUT", f"/pos/orders/{bad_order_id}/parallel", {}),
        ("POST", "/pos/delayed-orders", {"order_id": bad_order_id, "course_number": 2, "delay_minutes": 15}),
        ("GET", f"/pos/orders/{bad_order_id}/receipt"),
        ("POST", f"/pos/orders/{bad_order_id}/receipt/print", {}),
    ]

    for method, path, *rest in routes:
        payload = rest[0] if rest else None
        if method == "GET":
            resp = client.get(path)
        elif method == "PUT":
            resp = client.put(path, data=json.dumps(payload), content_type="application/json")
        else:
            resp = client.post(path, data=json.dumps(payload), content_type="application/json")
        assert resp.status_code == 404, (path, resp.status_code, resp.get_data(as_text=True))

    resp = client.post(
        "/pos/tables/1/assign",
        data=json.dumps({"order_id": bad_order_id, "customer_name": "Bad Tenant"}),
        content_type="application/json",
    )
    assert resp.status_code == 404

    resp = client.post(
        "/pos/tables/1/transfer",
        data=json.dumps({"destination_table_id": b_table_id}),
        content_type="application/json",
    )
    assert resp.status_code == 404

    resp = client.post(
        "/pos/orders/1/checkout",
        data=json.dumps({"payment_method_id": b_payment_id, "amount": 20.0}),
        content_type="application/json",
    )
    assert resp.status_code == 404


def test_order_rejects_product_from_another_restaurant_without_creating_order():
    app = build_app()
    with app.app_context():
        restaurant_a = make_restaurant(app, "Product A", "product_a")
        restaurant_b = make_restaurant(app, "Product B", "product_b")

    client = app.test_client()
    login_as(client, restaurant_a["user_id"])
    with app.app_context():
        before = Order.query.filter_by(restaurant_id=restaurant_a["restaurant_id"]).count()

    response = client.post(
        "/pos/orders",
        json={"items": [{"product_id": restaurant_b["product_id"], "quantity": 1}]},
    )

    assert response.status_code == 404
    with app.app_context():
        assert Order.query.filter_by(restaurant_id=restaurant_a["restaurant_id"]).count() == before
        assert OrderItem.query.filter_by(menu_item_id=restaurant_b["product_id"]).count() == 0


def test_admin_menu_and_logs_are_restaurant_scoped():
    app = build_app()
    with app.app_context():
        restaurant_a = make_restaurant(app, "Admin A", "admin_a")
        restaurant_b = make_restaurant(app, "Admin B", "admin_b")

        b_menu = MenuItem(
            restaurant_id=restaurant_b["restaurant_id"],
            name="Tenant B Only",
            price=29.99,
            available=True,
            description="Hidden",
        )
        db.session.add(b_menu)
        db.session.flush()
        b_menu_id = b_menu.id

        db.session.add(AuditLog(
            user_id=restaurant_b["user_id"],
            username="admin_b",
            action="login",
            object_type="session",
            object_id=restaurant_b["user_id"],
            details="foreign tenant audit record",
        ))
        db.session.commit()

    client = app.test_client()
    login_as(client, restaurant_a["user_id"])

    assert client.get(f"/admin/api/menu/{b_menu_id}").status_code == 404
    assert client.put(f"/admin/api/menu/{b_menu_id}", json={"price": 99.0}).status_code == 404
    assert client.delete(f"/admin/api/menu/{b_menu_id}").status_code == 404

    logs = client.get("/admin/api/logs").get_json()
    usernames = {entry["username"] for entry in logs}
    assert "admin_b" not in usernames


def test_same_restaurant_pos_workflow_still_works():
    app = build_app()
    with app.app_context():
        restaurant_a = make_restaurant(app, "SameA", "same_a")

    client = app.test_client()
    login_as(client, restaurant_a["user_id"])

    order = create_order_for_restaurant(client, restaurant_a["user_id"], restaurant_a["product_id"])
    assert order.restaurant_id == restaurant_a["restaurant_id"]

    resp = client.get(f"/pos/orders/{order.id}")
    assert resp.status_code == 200

    resp = client.put(
        f"/pos/orders/{order.id}/status",
        data=json.dumps({"status": "cooking"}),
        content_type="application/json",
    )
    assert resp.status_code == 200

    resp = client.post(
        f"/pos/orders/{order.id}/discount",
        data=json.dumps({"type": "percentage", "value": 10, "applies_to": "order"}),
        content_type="application/json",
    )
    assert resp.status_code == 200

    resp = client.put(
        f"/pos/orders/{order.id}/parallel",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 200

    resp = client.post(
        "/pos/delayed-orders",
        data=json.dumps({"order_id": order.id, "course_number": 2, "delay_minutes": 15}),
        content_type="application/json",
    )
    assert resp.status_code == 201

    receipt = Receipt(
        order_id=order.id,
        receipt_number="A-REC-1",
        content="OK",
        header_text="Store",
        footer_text="Thanks",
    )
    with app.app_context():
        db.session.add(receipt)
        db.session.commit()

    resp = client.get(f"/pos/orders/{order.id}/receipt")
    assert resp.status_code == 404

    resp = client.post(f"/pos/orders/{order.id}/receipt/print", data=json.dumps({}), content_type="application/json")
    assert resp.status_code == 404

    checkout_payload = {"payment_method_id": restaurant_a["payment_method_id"], "amount": 20.0}
    resp = client.post(f"/pos/orders/{order.id}/checkout", data=json.dumps(checkout_payload), content_type="application/json")
    assert resp.status_code == 200, resp.get_data(as_text=True)

    assert client.get(f"/pos/orders/{order.id}/receipt").status_code == 200
    assert client.post(
        f"/pos/orders/{order.id}/receipt/print", json={}
    ).status_code == 200

    split_payload = {"splits": [{"payment_method_id": restaurant_a["payment_method_id"], "amount": 20.0}]}
    resp = client.post(f"/pos/orders/{order.id}/split-bill", data=json.dumps(split_payload), content_type="application/json")
    assert resp.status_code == 201, resp.get_data(as_text=True)

    assign_resp = client.post(
        f"/pos/tables/{restaurant_a['table_id']}/assign",
        data=json.dumps({"order_id": order.id, "customer_name": "Same Tenant"}),
        content_type="application/json",
    )
    assert assign_resp.status_code == 200, assign_resp.get_data(as_text=True)
