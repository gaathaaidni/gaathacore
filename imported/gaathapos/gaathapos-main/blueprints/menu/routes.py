from flask import render_template, jsonify
from flask_login import login_required
from models import MenuItem
from . import menu_bp

@menu_bp.route("/")
@login_required
def show_menu():
    try:
        items = MenuItem.query.filter_by(available=True).all()
        return render_template("menu.html", items=items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@menu_bp.route("/api/items", methods=["GET"])
@login_required
def get_menu_items_api():
    """API endpoint to fetch menu items as JSON"""
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


@menu_bp.route('/api/menu-items', methods=['GET'])
@login_required
def get_menu_items_alias():
    """Backward-compatible alias used by POS front-end (returns {items: [...]})"""
    return get_menu_items_api()
