import pytest
from sqlalchemy.exc import IntegrityError, NoResultFound
from werkzeug.security import generate_password_hash

from conftest import app
from extensions import db
from models import (
    CashRegister,
    InventoryItem,
    InventoryMovement,
    PaymentMethod,
    PaymentTransaction,
    Product,
    ProductRecipe,
    Restaurant,
    User,
)
from blueprints.inventory.services import (
    InsufficientStockError,
    create_product_recipe,
    deduct_stock,
    deduct_stock_and_record_movement,
    record_movement,
)


app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def make_tenant(name, username):
    user = User(
        username=username,
        password_hash=generate_password_hash("pass"),
        role="manager",
    )
    db.session.add(user)
    db.session.flush()
    restaurant = Restaurant(name=name, email=f"{username}@example.com", owner_id=user.id)
    db.session.add(restaurant)
    db.session.flush()
    user.restaurant_id = restaurant.id
    product = Product(
        restaurant_id=restaurant.id,
        name=f"{name} product",
        base_price=10,
        active=True,
    )
    ingredient = InventoryItem(
        restaurant_id=restaurant.id,
        name=f"{name} ingredient",
        quantity=10,
    )
    db.session.add_all([product, ingredient])
    db.session.commit()
    return {
        "user_id": user.id,
        "restaurant_id": restaurant.id,
        "product_id": product.id,
        "ingredient_id": ingredient.id,
    }


def test_inventory_crud_is_tenant_scoped_and_creation_uses_current_restaurant():
    with app.app_context():
        tenant_a = make_tenant("A", "inventory_a")
        tenant_b = make_tenant("B", "inventory_b")

    client = app.test_client()
    login_as(client, tenant_a["user_id"])
    created = client.post("/admin/api/inventory", json={"name": "A stock", "quantity": 4})
    assert created.status_code == 201, created.get_data(as_text=True)
    created_id = created.get_json()["id"]

    assert client.get(f"/admin/api/inventory/{tenant_b['ingredient_id']}").status_code == 404
    assert client.put(
        f"/admin/api/inventory/{tenant_b['ingredient_id']}",
        json={"quantity": 3},
    ).status_code == 404
    assert client.delete(f"/admin/api/inventory/{tenant_b['ingredient_id']}").status_code == 404

    with app.app_context():
        created_item = db.session.get(InventoryItem, created_id)
        foreign_item = db.session.get(InventoryItem, tenant_b["ingredient_id"])
        assert created_item.restaurant_id == tenant_a["restaurant_id"]
        assert foreign_item.quantity == 10


def test_negative_inventory_quantity_is_rejected_by_api():
    with app.app_context():
        tenant = make_tenant("Negative", "inventory_negative")

    client = app.test_client()
    login_as(client, tenant["user_id"])
    assert client.post(
        "/admin/api/inventory", json={"name": "invalid", "quantity": -1}
    ).status_code == 400
    assert client.put(
        f"/admin/api/inventory/{tenant['ingredient_id']}", json={"quantity": -1}
    ).status_code == 400


def test_product_recipe_requires_same_tenant_and_rejects_duplicates():
    with app.app_context():
        tenant_a = make_tenant("Recipe A", "recipe_a")
        tenant_b = make_tenant("Recipe B", "recipe_b")

        with pytest.raises(NoResultFound):
            create_product_recipe(
                tenant_a["product_id"],
                tenant_b["ingredient_id"],
                tenant_a["restaurant_id"],
                1,
            )
        with pytest.raises(NoResultFound):
            create_product_recipe(
                tenant_b["product_id"],
                tenant_a["ingredient_id"],
                tenant_b["restaurant_id"],
                1,
            )

        create_product_recipe(
            tenant_a["product_id"],
            tenant_a["ingredient_id"],
            tenant_a["restaurant_id"],
            2,
        )
        db.session.commit()
        create_product_recipe(
            tenant_a["product_id"],
            tenant_a["ingredient_id"],
            tenant_a["restaurant_id"],
            1,
        )
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_movement_is_tenant_owned_and_sale_reference_is_unique():
    with app.app_context():
        tenant_a = make_tenant("Movement A", "movement_a")
        tenant_b = make_tenant("Movement B", "movement_b")

        with pytest.raises(NoResultFound):
            record_movement(
                tenant_b["ingredient_id"],
                tenant_a["restaurant_id"],
                1,
                "sale",
                "order",
                "100",
            )

        record_movement(
            tenant_a["ingredient_id"], tenant_a["restaurant_id"], -2,
            "sale", "order", "100",
        )
        db.session.commit()
        movement = InventoryMovement.query.one()
        assert movement.restaurant_id == tenant_a["restaurant_id"]

        record_movement(
            tenant_a["ingredient_id"], tenant_a["restaurant_id"], -2,
            "sale", "order", "100",
        )
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_conditional_stock_service_rejects_oversell_without_checkout_integration():
    with app.app_context():
        tenant = make_tenant("Stock", "stock_service")
        deduct_stock(tenant["ingredient_id"], tenant["restaurant_id"], 4)
        db.session.commit()
        assert db.session.get(InventoryItem, tenant["ingredient_id"]).quantity == 6

        with pytest.raises(InsufficientStockError):
            deduct_stock(tenant["ingredient_id"], tenant["restaurant_id"], 7)
        db.session.rollback()
        assert db.session.get(InventoryItem, tenant["ingredient_id"]).quantity == 6


def test_new_inventory_model_requires_restaurant():
    with app.app_context():
        item = InventoryItem(name="unowned", quantity=1)
        db.session.add(item)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_product_stock_mode_requires_explicit_inventory_or_recipe():
    with app.app_context():
        tenant = make_tenant("StockMode", "stock_mode")
        product = db.session.get(Product, tenant["product_id"])
        product.stock_mode = "direct"
        product.inventory_item_id = tenant["ingredient_id"]
        db.session.commit()
        assert product.stock_mode == "direct"

        recipe_product = Product(
            restaurant_id=tenant["restaurant_id"],
            name="Recipe product",
            base_price=12,
            stock_mode="recipe",
        )
        db.session.add(recipe_product)
        db.session.flush()
        with pytest.raises(ValueError):
            recipe_product.validate_stock_mode()

        recipe_product.inventory_item_id = None
        db.session.add(ProductRecipe(
            restaurant_id=tenant["restaurant_id"],
            product_id=recipe_product.id,
            inventory_item_id=tenant["ingredient_id"],
            quantity=1.0,
        ))
        db.session.flush()
        recipe_product.validate_stock_mode()


def test_atomic_stock_and_movement_is_one_transaction():
    with app.app_context():
        tenant = make_tenant("Atomic", "atomic")
        product = db.session.get(Product, tenant["product_id"])
        product.stock_mode = "direct"
        product.inventory_item_id = tenant["ingredient_id"]
        db.session.commit()

        movement = deduct_stock_and_record_movement(
            restaurant_id=tenant["restaurant_id"],
            inventory_item_id=tenant["ingredient_id"],
            quantity=3,
            movement_type="sale",
            reference_type="order",
            reference_id="order-400",
        )
        assert movement.inventory_item_id == tenant["ingredient_id"]
        assert movement.quantity_delta == -3
        assert db.session.get(InventoryItem, tenant["ingredient_id"]).quantity == 7

        duplicate = deduct_stock_and_record_movement(
            restaurant_id=tenant["restaurant_id"],
            inventory_item_id=tenant["ingredient_id"],
            quantity=3,
            movement_type="sale",
            reference_type="order",
            reference_id="order-400",
        )
        assert duplicate.id == movement.id
        assert InventoryMovement.query.filter_by(reference_id="order-400").count() == 1
        assert db.session.get(InventoryItem, tenant["ingredient_id"]).quantity == 7


def test_settled_checkout_deducts_configured_direct_stock_once():
    with app.app_context():
        tenant = make_tenant("Checkout stock", "checkout_stock")
        product = db.session.get(Product, tenant["product_id"])
        product.stock_mode = "direct"
        product.inventory_item_id = tenant["ingredient_id"]
        method = PaymentMethod(
            restaurant_id=tenant["restaurant_id"],
            name="Cash",
            payment_type="cash",
            active=True,
        )
        register = CashRegister(
            restaurant_id=tenant["restaurant_id"],
            register_name="Main",
            status="opened",
            current_balance=0,
        )
        db.session.add_all([method, register])
        db.session.commit()
        method_id = method.id
        register_id = register.id

    client = app.test_client()
    login_as(client, tenant["user_id"])
    order_response = client.post(
        "/pos/orders", json={"items": [{"product_id": tenant["product_id"], "quantity": 2}]}
    )
    assert order_response.status_code == 201
    order_id = order_response.get_json()["id"]

    payment_response = client.post(
        f"/pos/orders/{order_id}/checkout",
        json={"payment_method_id": method_id, "amount": 20, "register_id": register_id},
    )
    assert payment_response.status_code == 200

    with app.app_context():
        assert db.session.get(InventoryItem, tenant["ingredient_id"]).quantity == 8
        assert InventoryMovement.query.filter_by(reference_id=str(order_id)).count() == 1


def test_insufficient_configured_stock_rolls_back_payment_and_stock():
    with app.app_context():
        tenant = make_tenant("Checkout rollback", "checkout_rollback")
        product = db.session.get(Product, tenant["product_id"])
        product.stock_mode = "direct"
        product.inventory_item_id = tenant["ingredient_id"]
        db.session.get(InventoryItem, tenant["ingredient_id"]).quantity = 1
        method = PaymentMethod(
            restaurant_id=tenant["restaurant_id"], name="Card", payment_type="card", active=True
        )
        db.session.add(method)
        db.session.commit()
        method_id = method.id

    client = app.test_client()
    login_as(client, tenant["user_id"])
    order_response = client.post(
        "/pos/orders", json={"items": [{"product_id": tenant["product_id"], "quantity": 2}]}
    )
    order_id = order_response.get_json()["id"]
    with app.app_context():
        payment_count_before = PaymentTransaction.query.filter_by(order_id=order_id).count()
    payment_response = client.post(
        f"/pos/orders/{order_id}/checkout",
        json={"payment_method_id": method_id, "amount": 20},
    )
    assert payment_response.status_code == 400

    with app.app_context():
        assert db.session.get(InventoryItem, tenant["ingredient_id"]).quantity == 1
        assert PaymentTransaction.query.filter_by(order_id=order_id).count() == payment_count_before