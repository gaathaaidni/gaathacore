from flask import jsonify
from flask_login import login_required, current_user
from decorators import permission_required
from extensions import db
from models import Order, OrderItem, MenuItem
from . import analytics_bp

@analytics_bp.route("/sales")
@login_required
@permission_required('view_analytics')
def sales_summary():
    try:
        total_orders = Order.query.filter_by(restaurant_id=current_user.restaurant_id).count()
        total_items = (
            db.session.query(db.func.coalesce(db.func.sum(OrderItem.quantity), 0))
            .join(Order)
            .filter(Order.restaurant_id == current_user.restaurant_id)
            .scalar()
            or 0
        )
        total_revenue = (
            db.session.query(db.func.coalesce(db.func.sum(OrderItem.quantity * MenuItem.price), 0))
            .join(MenuItem)
            .join(Order)
            .filter(
                Order.restaurant_id == current_user.restaurant_id,
                MenuItem.restaurant_id == current_user.restaurant_id,
            )
            .scalar()
            or 0
        )
        return jsonify({
            "total_orders": total_orders,
            "total_items": int(total_items),
            "total_revenue": float(total_revenue),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
