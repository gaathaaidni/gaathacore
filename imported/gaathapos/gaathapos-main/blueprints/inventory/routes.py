from flask import jsonify
from flask_login import login_required
from . import inventory_bp

@inventory_bp.route("/")
@login_required
def inventory_home():
    try:
        return jsonify({"message": "Inventory system placeholder"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
