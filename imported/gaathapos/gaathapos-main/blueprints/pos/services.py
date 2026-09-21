# POS helper functions and business logic
from extensions import db
from models import (
    Order, OrderItem, Discount, BillSplit, PaymentTransaction,
    Receipt, LoyaltyPoints, eWalletTransaction, Product,
    PaymentMethod, Table, TableSection, RestaurantFloorPlan
    , CashRegister, CashFlow
)
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json


CASH_MANAGER_ROLES = {"admin", "manager", "restaurant_admin", "super_admin"}


def get_current_cashier(current_user):
    cashier = getattr(current_user, "cashier_account", None)
    if isinstance(cashier, list):
        return cashier[0] if cashier else None
    return cashier


def get_order_for_current_restaurant(order_id, restaurant_id):
    """Return an order only if it belongs to the caller's restaurant."""
    if restaurant_id is None:
        return None
    return Order.query.filter_by(id=order_id, restaurant_id=restaurant_id).first()


def get_payment_method_for_current_restaurant(payment_method_id, restaurant_id):
    """Return a payment method only if it belongs to the caller's restaurant."""
    if restaurant_id is None:
        return None
    return PaymentMethod.query.filter_by(id=payment_method_id, restaurant_id=restaurant_id).first()


def get_table_for_current_restaurant(table_id, restaurant_id):
    """Return a table only if it belongs to the caller's restaurant."""
    if restaurant_id is None:
        return None
    return (
        Table.query.join(TableSection)
        .join(RestaurantFloorPlan, TableSection.floor_plan_id == RestaurantFloorPlan.id)
        .filter(Table.id == table_id, RestaurantFloorPlan.restaurant_id == restaurant_id)
        .first()
    )


def get_product_for_current_restaurant(product_id, restaurant_id):
    """Return a product only if it belongs to the caller's restaurant."""
    if restaurant_id is None:
        return None
    return Product.query.filter_by(id=product_id, restaurant_id=restaurant_id).first()


def get_cash_register_for_operator(
    register_id, restaurant_id, current_user, require_open=True,
    allow_unassigned_cashier=False
):
    """Validate tenant, cashier, and manager access to a cash register."""
    register = CashRegister.query.filter_by(
        id=register_id, restaurant_id=restaurant_id, active=True
    ).first()
    if not register:
        return None, "Cash register not found", 404

    cashier = get_current_cashier(current_user)
    if cashier is not None and not cashier.active:
        return None, "Cashier account is inactive", 403

    is_manager = current_user.role in CASH_MANAGER_ROLES or getattr(
        current_user, "is_super_admin", False
    )
    if not cashier and not is_manager:
        return None, "Active cashier account is required", 403
    if require_open and register.status != "opened":
        return None, "Cash register is closed", 400
    if register.current_cashier_id and (
        not cashier or register.current_cashier_id != cashier.id
    ) and not is_manager:
        return None, "Cash register is assigned to another cashier", 403
    if cashier and register.current_cashier_id is None and not is_manager and not allow_unassigned_cashier:
        return None, "Cash register is not assigned to this cashier", 403
    return register, None, None


def order_completed_total(order):
    return sum(
        (Decimal(str(payment.amount)) for payment in order.payments
         if payment.status == "completed" and not payment.is_offline
         and payment.synchronization_status != "pending_sync"),
        Decimal("0.00")
    )


def order_is_settled(order):
    """Check financial settlement without relying on order status or receipts."""
    try:
        order_total = calculate_order_total_from_items(order.items)
    except (TypeError, ValueError, InvalidOperation):
        return False
    return order_completed_total(order) >= order_total


def calculate_order_total(items_list):
    """Calculate total from items list"""
    return sum(
        item.get("price", 0) * item.get("quantity", 0)
        for item in items_list
    )


def calculate_order_total_from_items(order_items):
    """Calculate total from OrderItem objects"""
    total = Decimal("0.00")
    for item in order_items:
        restaurant_id = getattr(item.order, "restaurant_id", None)
        menu = Product.query.filter_by(
            id=item.menu_item_id, restaurant_id=restaurant_id
        ).first()
        menu = menu or item.menu_item
        price = getattr(menu, "price", getattr(menu, "base_price", None))
        if price is None or item.quantity is None or item.quantity < 1:
            raise ValueError("Order contains an invalid item")
        total += Decimal(str(price)) * item.quantity
    return total.quantize(Decimal("0.01"))


def apply_discount(order, discount_data):
    """
    Apply discount to order or specific items
    discount_data: {
        "type": "percentage" | "fixed_amount",
        "value": float,
        "applies_to": "product" | "order",
        "product_id": int (optional)
    }
    """
    try:
        discount_type = discount_data.get("type")  # percentage or fixed_amount
        value = discount_data.get("value")
        applies_to = discount_data.get("applies_to", "order")
        product_id = discount_data.get("product_id")
        
        discount_amount = 0
        
        if applies_to == "product" and product_id:
            # Apply to specific product
            for item in order.items:
                if item.menu_item_id == product_id:
                    if discount_type == "percentage":
                        discount_amount += (item.menu_item.price * item.quantity * value / 100)
                    else:
                        discount_amount += value * item.quantity
        else:
            # Apply to entire order
            total = calculate_order_total_from_items(order.items)
            if discount_type == "percentage":
                discount_amount = total * value / 100
            else:
                discount_amount = value
        
        # Store discount info in order metadata if available
        # For now, just return the discount amount
        return {
            "discount_type": discount_type,
            "discount_value": value,
            "discount_amount": discount_amount
        }
    except Exception as e:
        raise Exception(f"Error applying discount: {str(e)}")


def process_payment(order, payment_data, current_user):
    """
    Process payment for an order
    payment_data: {
        "payment_method_id": int,
        "amount": float,
        "is_offline": bool,
        "tip_amount": float (optional),
        "tip_type": "amount" | "percentage" (optional)
    }
    """
    try:
        payment_method_id = payment_data.get("payment_method_id")
        reference_id = payment_data.get("reference_id")
        is_offline = payment_data.get("is_offline", False)
        tip_amount = payment_data.get("tip_amount", 0)
        tip_type = payment_data.get("tip_type", "amount")

        if not payment_method_id or payment_data.get("amount") is None:
            return {"success": False, "error": "Missing payment method or amount"}
        if order.status == "cancelled":
            return {"success": False, "error": "Cannot pay a cancelled order"}

        payment_method = PaymentMethod.query.filter_by(
            id=payment_method_id, restaurant_id=order.restaurant_id, active=True
        ).first()
        if not payment_method:
            return {"success": False, "error": "Payment method not found"}

        if reference_id:
            existing = PaymentTransaction.query.filter_by(
                restaurant_id=order.restaurant_id,
                reference_id=str(reference_id),
            ).first()
            if existing and existing.order_id != order.id:
                return {"success": False, "error": "Payment reference already used"}
            if existing:
                return {
                    "success": True,
                    "payment_id": existing.id,
                    "receipt_id": existing.order.receipts[0].id if existing.order.receipts else None,
                    "amount": existing.amount,
                    "tip": existing.tip_amount or 0,
                    "total": (existing.amount or 0) + (existing.tip_amount or 0),
                    "status": "pending_sync" if existing.is_offline else existing.status,
                    "idempotent": True,
                }

        cash_register = None
        cashier = get_current_cashier(current_user)
        if payment_method.payment_type == "cash":
            register_id = payment_data.get("register_id")
            register_query = CashRegister.query.filter_by(
                restaurant_id=order.restaurant_id, status="opened", active=True
            )
            if register_id is not None:
                cash_register = register_query.filter_by(id=register_id).first()
            elif cashier:
                cash_register = register_query.filter_by(current_cashier_id=cashier.id).first()
            else:
                cash_register = register_query.filter_by(current_cashier_id=None).first()

            if not cash_register:
                return {"success": False, "error": "An active cash register is required"}
            cash_register, error, _ = get_cash_register_for_operator(
                cash_register.id, order.restaurant_id, current_user
            )
            if error:
                return {"success": False, "error": error}

        try:
            amount = Decimal(str(payment_data.get("amount")))
            tip = Decimal(str(tip_amount or 0))
            order_total = calculate_order_total_from_items(order.items)
        except (InvalidOperation, TypeError, ValueError):
            return {"success": False, "error": "Invalid monetary amount or order"}

        if amount <= 0:
            return {"success": False, "error": "Payment amount must be greater than zero"}
        if tip < 0:
            return {"success": False, "error": "Tip amount cannot be negative"}

        completed_total = order_completed_total(order)
        remaining = (order_total - completed_total).quantize(Decimal("0.01"))
        if remaining <= 0:
            return {"success": False, "error": "Order is already fully paid"}
        if amount > remaining:
            return {"success": False, "error": "Payment exceeds the remaining balance"}

        settled = (completed_total + (Decimal("0.00") if is_offline else amount)) >= order_total
        if settled and not is_offline:
            from blueprints.inventory.services import InventoryError, deduct_order_stock

            try:
                with db.session.begin_nested():
                    deduct_order_stock(order, order.restaurant_id, current_user.id)
            except InventoryError as exc:
                return {"success": False, "error": str(exc)}

        payment = PaymentTransaction(
            order_id=order.id,
            payment_method_id=payment_method_id,
            restaurant_id=order.restaurant_id,
            cash_register_id=cash_register.id if cash_register else None,
            cashier_id=cashier.id if cashier else None,
            amount=float(amount),
            currency="USD",  # Should come from restaurant settings
            status="completed" if not is_offline else "pending",
            reference_id=str(reference_id) if reference_id else None,
            is_offline=is_offline,
            synchronization_status="pending_sync" if is_offline else "synced",
            tip_amount=float(tip),
            tip_type=tip_type
        )
        try:
            with db.session.begin_nested():
                db.session.add(payment)
                db.session.flush()
        except Exception as exc:
            from sqlalchemy.exc import IntegrityError
            if not reference_id or not isinstance(exc, IntegrityError):
                raise
            existing = PaymentTransaction.query.filter_by(
                restaurant_id=order.restaurant_id,
                reference_id=str(reference_id),
            ).first()
            if not existing:
                raise
            if existing.order_id != order.id:
                return {"success": False, "error": "Payment reference already used"}
            return {
                "success": True,
                "payment_id": existing.id,
                "receipt_id": existing.order.receipts[0].id if existing.order.receipts else None,
                "amount": existing.amount,
                "tip": existing.tip_amount or 0,
                "total": (existing.amount or 0) + (existing.tip_amount or 0),
                "status": "pending_sync" if existing.is_offline else existing.status,
                "idempotent": True,
            }

        if cash_register and not is_offline:
            cash_amount = float(amount + tip)
            cash_register.current_balance += cash_amount
            db.session.add(CashFlow(
                cash_register_id=cash_register.id,
                adjustment_type="payment",
                amount=cash_amount,
                reason=f"Payment for order #{order.id}",
                recorded_by=current_user.username,
                expected_balance=cash_register.current_balance,
            ))

        receipt = None
        if settled and not is_offline:
            receipt = Receipt(
                order_id=order.id,
                receipt_number=f"REC-{order.id}-{datetime.now(timezone.utc).timestamp()}",
                content=generate_receipt_content(order, payment),
                header_text="Thank you for your purchase!",
                footer_text="Visit us again!"
            )
            db.session.add(receipt)
            db.session.flush()
        
        return {
            "success": True,
            "payment_id": payment.id,
            "receipt_id": receipt.id if receipt else None,
            "amount": float(amount),
            "tip": float(tip),
            "total": float(amount + tip),
            "status": "completed" if not is_offline else "pending_sync"
        }
    except Exception as e:
        raise Exception(f"Error processing payment: {str(e)}")


def generate_receipt_content(order, payment):
    """Generate receipt content"""
    try:
        lines = []
        lines.append("=" * 40)
        lines.append("RECEIPT")
        lines.append("=" * 40)
        lines.append(f"Order #: {order.id}")
        lines.append(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("-" * 40)
        
        total = 0
        from models import Product
        for item in order.items:
            menu = Product.query.filter_by(
                id=item.menu_item_id, restaurant_id=order.restaurant_id
            ).first()
            menu = menu or item.menu_item
            name = getattr(menu, 'name', 'Item')
            unit_price = getattr(menu, 'price', getattr(menu, 'base_price', 0))
            subtotal = unit_price * item.quantity
            total += subtotal
            lines.append(f"{name}")
            lines.append(f"  {item.quantity} x ${unit_price:.2f} = ${subtotal:.2f}")
        
        lines.append("-" * 40)
        lines.append(f"Subtotal: ${total:.2f}")
        lines.append(f"Payment Method: {payment.payment_method.name if hasattr(payment, 'payment_method') else 'N/A'}")
        if payment.tip_amount > 0:
            lines.append(f"Tip: ${payment.tip_amount:.2f}")
            lines.append(f"Total: ${total + payment.tip_amount:.2f}")
        else:
            lines.append(f"Total: ${total:.2f}")
        lines.append("=" * 40)
        
        return "\n".join(lines)
    except Exception as e:
        return f"Error generating receipt: {str(e)}"


def handle_bill_split(order, split_data):
    """
    Handle bill splitting for multiple parties
    split_data: {
        "splits": [
            {"payment_method_id": int, "amount": float},
            {"payment_method_id": int, "amount": float}
        ]
    }
    """
    try:
        splits = split_data.get("splits", [])
        
        bill_splits = []
        for idx, split in enumerate(splits, 1):
            bill_split = BillSplit(
                order_id=order.id,
                split_index=idx,
                amount=split.get("amount"),
                payment_method_id=split.get("payment_method_id"),
                status="pending"
            )
            db.session.add(bill_split)
            bill_splits.append({
                "split_number": idx,
                "amount": split.get("amount"),
                "status": "pending"
            })
        
        return bill_splits
    except Exception as e:
        raise Exception(f"Error handling bill split: {str(e)}")


def add_loyalty_points(customer, order, points_earned):
    """
    Add loyalty points to customer
    """
    try:
        if not customer.loyalty_card:
            return {"success": False, "error": "Customer does not have a loyalty card"}
        
        loyalty_card = customer.loyalty_card
        loyalty_card.points_balance += points_earned
        loyalty_card.points_earned_total += points_earned
        
        points_record = LoyaltyPoints(
            loyalty_card_id=loyalty_card.id,
            order_id=order.id,
            points=points_earned,
            earn_method="purchase",
            description=f"Points earned from order #{order.id}"
        )
        db.session.add(points_record)
        
        return {
            "success": True,
            "points_earned": points_earned,
            "points_balance": loyalty_card.points_balance
        }
    except Exception as e:
        raise Exception(f"Error adding loyalty points: {str(e)}")


def topup_ewallet(ewallet, amount, payment_method_id):
    """
    Top-up customer e-wallet
    """
    try:
        ewallet.balance += amount
        
        transaction = eWalletTransaction(
            ewallet_id=ewallet.id,
            amount=amount,
            transaction_type="topup",
            reference_id=f"TOPUP-{datetime.now(timezone.utc).timestamp()}"
        )
        db.session.add(transaction)
        
        return {
            "success": True,
            "amount_added": amount,
            "new_balance": ewallet.balance
        }
    except Exception as e:
        raise Exception(f"Error topping up e-wallet: {str(e)}")


def calculate_price_with_pricelist(product, pricelist):
    """
    Get product price from specific pricelist
    """
    try:
        from models import PriceListItem
        price_list_item = PriceListItem.query.filter_by(
            pricelist_id=pricelist.id,
            product_id=product.id
        ).first()
        
        if price_list_item:
            return price_list_item.price
        else:
            return product.base_price
    except Exception as e:
        raise Exception(f"Error calculating price from pricelist: {str(e)}")


def validate_credit_limit(customer, order_total):
    """
    Check if customer has exceeded credit limit
    """
    try:
        if customer.credit_limit <= 0:
            return {"allowed": True, "reason": "No credit limit"}
        
        new_balance = customer.outstanding_balance + order_total
        
        if new_balance > customer.credit_limit:
            return {
                "allowed": False,
                "reason": "Credit limit exceeded",
                "credit_limit": customer.credit_limit,
                "current_balance": customer.outstanding_balance,
                "would_be_balance": new_balance
            }
        
        return {"allowed": True, "reason": "Credit limit OK"}
    except Exception as e:
        raise Exception(f"Error validating credit limit: {str(e)}")
