from flask import jsonify
from models import MenuItem
from . import api_bp

@api_bp.route("/menu")
def menu_json():
    try:
        items = MenuItem.query.all()
        return jsonify([
            {"id": m.id, "name": m.name, "price": m.price, "available": m.available}
            for m in items
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/menu-items")
def get_menu_items():
    """Fetch available menu items for POS"""
    try:
        items = MenuItem.query.filter_by(available=True).all()
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
