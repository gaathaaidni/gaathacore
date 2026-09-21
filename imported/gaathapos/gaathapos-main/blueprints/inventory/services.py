from datetime import datetime, timezone

from sqlalchemy.exc import NoResultFound

from extensions import db
from models import InventoryItem, InventoryMovement, Product, ProductRecipe, User


class InventoryError(ValueError):
    """Base error for invalid inventory foundation operations."""


class InsufficientStockError(InventoryError):
    """Raised when a conditional stock decrement cannot be completed."""


def calculate_stock_value(items):
    return sum(item["qty"] * item["price"] for item in items)


def get_inventory_item(item_id, restaurant_id):
    if restaurant_id is None:
        return None
    return InventoryItem.query.filter_by(id=item_id, restaurant_id=restaurant_id).first()


def validate_quantity(quantity):
    try:
        quantity = int(quantity)
    except (TypeError, ValueError) as exc:
        raise InventoryError("quantity must be a non-negative integer") from exc
    if quantity < 0:
        raise InventoryError("quantity cannot be negative")
    return quantity


def create_product_recipe(product_id, inventory_item_id, restaurant_id, quantity):
    """Create a tenant-safe Product recipe line without changing stock."""
    if restaurant_id is None:
        raise InventoryError("restaurant context is required")
    try:
        quantity = float(quantity)
    except (TypeError, ValueError) as exc:
        raise InventoryError("recipe quantity must be positive") from exc
    if quantity <= 0:
        raise InventoryError("recipe quantity must be positive")

    product = Product.query.filter_by(id=product_id, restaurant_id=restaurant_id).first()
    ingredient = get_inventory_item(inventory_item_id, restaurant_id)
    if not product or not ingredient:
        raise NoResultFound("product and ingredient must belong to the current restaurant")

    recipe = ProductRecipe(
        restaurant_id=restaurant_id,
        product_id=product.id,
        inventory_item_id=ingredient.id,
        quantity=quantity,
    )
    db.session.add(recipe)
    return recipe


def deduct_stock(inventory_item_id, restaurant_id, quantity):
    """Prepare an atomic conditional decrement; caller owns the transaction."""
    if restaurant_id is None:
        raise InventoryError("restaurant context is required")
    try:
        quantity = float(quantity)
    except (TypeError, ValueError) as exc:
        raise InventoryError("deduction quantity must be positive") from exc
    if quantity <= 0:
        raise InventoryError("deduction quantity must be positive")

    updated = InventoryItem.query.filter(
        InventoryItem.id == inventory_item_id,
        InventoryItem.restaurant_id == restaurant_id,
        InventoryItem.quantity >= quantity,
    ).update(
        {
            InventoryItem.quantity: InventoryItem.quantity - quantity,
            InventoryItem.updated_at: datetime.now(timezone.utc),
        },
        synchronize_session=False,
    )
    if updated != 1:
        raise InsufficientStockError("inventory item not found or stock is insufficient")


def record_movement(
    inventory_item_id,
    restaurant_id,
    quantity_delta,
    movement_type,
    reference_type=None,
    reference_id=None,
    reason=None,
    created_by=None,
):
    """Add one auditable movement; uniqueness is enforced by the database."""
    if restaurant_id is None or not movement_type:
        raise InventoryError("restaurant and movement type are required")
    if get_inventory_item(inventory_item_id, restaurant_id) is None:
        raise NoResultFound("inventory item does not belong to the current restaurant")
    if quantity_delta == 0:
        raise InventoryError("movement quantity cannot be zero")
    if created_by is not None:
        user = db.session.get(User, created_by)
        if user is None or user.restaurant_id != restaurant_id:
            raise ValueError("created_by must belong to the same restaurant")
    if reference_type is None and reference_id is not None:
        raise InventoryError("reference_type is required when reference_id is provided")
    if movement_type == 'sale' and (reference_type is None or reference_id is None):
        raise InventoryError("sale movements require both reference_type and reference_id")

    movement = InventoryMovement(
        restaurant_id=restaurant_id,
        inventory_item_id=inventory_item_id,
        quantity_delta=quantity_delta,
        movement_type=movement_type,
        reference_type=reference_type,
        reference_id=str(reference_id) if reference_id is not None else None,
        reason=reason,
        created_by=created_by,
    )
    db.session.add(movement)
    return movement


def deduct_stock_and_record_movement(
    inventory_item_id,
    restaurant_id,
    quantity,
    movement_type,
    reference_type,
    reference_id,
    reason=None,
    created_by=None,
):
    """Atomically reduce stock and write the movement in one transaction."""
    if restaurant_id is None or not movement_type:
        raise InventoryError("restaurant and movement type are required")
    if reference_type is None or reference_id is None:
        raise InventoryError("sale reference must include both type and id")
    if created_by is not None:
        user = db.session.get(User, created_by)
        if user is None or user.restaurant_id != restaurant_id:
            raise ValueError("created_by must belong to the same restaurant")

    try:
        quantity = float(quantity)
    except (TypeError, ValueError) as exc:
        raise InventoryError("deduction quantity must be positive") from exc
    if quantity <= 0:
        raise InventoryError("deduction quantity must be positive")

    item = InventoryItem.query.filter_by(id=inventory_item_id, restaurant_id=restaurant_id).with_for_update().first()
    if item is None:
        raise NoResultFound("inventory item does not belong to the current restaurant")
    if item.quantity < quantity:
        raise InsufficientStockError("inventory item not found or stock is insufficient")

    existing = InventoryMovement.query.filter_by(
        restaurant_id=restaurant_id,
        inventory_item_id=inventory_item_id,
        movement_type=movement_type,
        reference_type=reference_type,
        reference_id=str(reference_id),
    ).first()
    if existing is not None:
        return existing

    item.quantity = item.quantity - quantity
    item.updated_at = datetime.now(timezone.utc)
    movement = InventoryMovement(
        restaurant_id=restaurant_id,
        inventory_item_id=inventory_item_id,
        quantity_delta=-quantity,
        movement_type=movement_type,
        reference_type=reference_type,
        reference_id=str(reference_id),
        reason=reason,
        created_by=created_by,
    )
    db.session.add(movement)
    db.session.flush()
    return movement


def deduct_order_stock(order, restaurant_id, created_by=None):
    """Deduct configured product stock once for a settled order."""
    if restaurant_id is None or order.restaurant_id != restaurant_id:
        raise InventoryError("order does not belong to the current restaurant")

    for order_item in order.items:
        product = Product.query.filter_by(
            id=order_item.menu_item_id,
            restaurant_id=restaurant_id,
            active=True,
        ).first()
        if product is None:
            raise NoResultFound("order product does not belong to the current restaurant")

        if product.stock_mode == "direct":
            if product.inventory_item_id is None:
                continue
            deduct_stock_and_record_movement(
                product.inventory_item_id,
                restaurant_id,
                order_item.quantity,
                "sale",
                "order",
                order.id,
                reason=f"Settled order #{order.id}",
                created_by=created_by,
            )
        elif product.stock_mode == "recipe":
            recipes = ProductRecipe.query.filter_by(
                product_id=product.id,
                restaurant_id=restaurant_id,
            ).all()
            if not recipes:
                raise InventoryError("recipe product has no ingredients")
            for recipe in recipes:
                deduct_stock_and_record_movement(
                    recipe.inventory_item_id,
                    restaurant_id,
                    recipe.quantity * order_item.quantity,
                    "sale",
                    "order",
                    order.id,
                    reason=f"Settled order #{order.id}",
                    created_by=created_by,
                )
