from flask import jsonify
from flask_login import login_required, current_user
from models import Order, OrderItem
from decorators import permission_required
from extensions import db
from . import kds_bp
from flask import render_template

@kds_bp.route("/orders")
@login_required
@permission_required('manage_orders')
def pending_orders():
    try:
        orders = Order.query.filter_by(status="pending", restaurant_id=current_user.restaurant_id).all()
        order_data = []
        for o in orders:
            items = []
            for item in o.items:
                # Be defensive: menu_item relationship may be None if OrderItem stores a product id
                menu = item.menu_item
                if not menu:
                    from models import Product
                    menu = Product.query.filter_by(
                        id=item.menu_item_id,
                        restaurant_id=current_user.restaurant_id,
                    ).first()

                items.append({
                    "name": getattr(menu, 'name', None) or 'Unknown',
                    "quantity": item.quantity,
                    "price": float(getattr(menu, 'price', getattr(menu, 'base_price', 0) or 0))
                })
            order_data.append({
                "id": o.id,
                "status": o.status,
                "created_at": o.created_at.isoformat(),
                "items": items
            })
        return jsonify(order_data)
    except Exception:
        return jsonify({"error": "Unable to load kitchen orders"}), 500


@kds_bp.route("/")
@login_required
@permission_required('manage_orders')
def kds_home():
    try:
        return render_template('kds.html')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
