from flask import jsonify
from flask_login import login_required, current_user
from models import MenuItem
from . import api_bp

@api_bp.route("/menu")
@login_required
def menu_json():
    try:
        items = MenuItem.query.filter_by(restaurant_id=current_user.restaurant_id).all()
        return jsonify([
            {"id": m.id, "name": m.name, "price": m.price, "available": m.available}
            for m in items
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/menu-items")
@login_required
def get_menu_items():
    """Fetch available menu items for POS"""
    try:
        items = MenuItem.query.filter_by(restaurant_id=current_user.restaurant_id, available=True).all()
        return jsonify({
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "price": item.price,
                    "available": item.available
                }
                for item in items
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
