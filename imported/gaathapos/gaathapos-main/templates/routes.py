from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import Order, OrderItem, MenuItem, InventoryItem, RecipeItem
from decorators import admin_required
from sqlalchemy import func, case
from datetime import datetime, time

dashboard_api_bp = Blueprint('dashboard_api', __name__, url_prefix='/admin/api/dashboard')

def get_today_range():
    """Returns the start and end datetime for the current day."""
    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    today_end = datetime.combine(datetime.utcnow().date(), time.max)
    return today_start, today_end

@dashboard_api_bp.route('/stats')
@login_required
@admin_required
def dashboard_stats():
    """Provides key statistics for the restaurant owner's dashboard."""
    today_start, today_end = get_today_range()
    restaurant_id = current_user.restaurant_id

    # Base query for today's completed orders
    base_query = Order.query.filter(
        Order.restaurant_id == restaurant_id,
        Order.created_at.between(today_start, today_end),
        Order.status.in_(['ready', 'served', 'completed'])
    )

    # --- Calculate Revenue and Cost ---
    revenue_and_cost_query = db.session.query(
        func.sum(OrderItem.quantity * MenuItem.price).label('total_revenue'),
        func.sum(OrderItem.quantity * func.coalesce(MenuItem.cost, 0)).label('total_cost')
    ).join(MenuItem, OrderItem.menu_item_id == MenuItem.id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(
        Order.restaurant_id == restaurant_id,
        Order.created_at.between(today_start, today_end),
        Order.status.in_(['ready', 'served', 'completed'])
    ).first()

    total_revenue = float(revenue_and_cost_query.total_revenue or 0)
    total_cost = float(revenue_and_cost_query.total_cost or 0)

    # --- Other Stats ---
    total_orders = base_query.count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    food_cost_percent = (total_cost / total_revenue) * 100 if total_revenue > 0 else 0

    return jsonify({
        "revenue": total_revenue,
        "orders": total_orders,
        "avg_order_value": avg_order_value,
        "food_cost_percent": food_cost_percent,
    })

@dashboard_api_bp.route('/top-items')
@login_required
@admin_required
def top_items():
    """Returns the top-selling menu items for the day."""
    today_start, today_end = get_today_range()
    restaurant_id = current_user.restaurant_id

    top_items = db.session.query(
        MenuItem.name,
        func.sum(OrderItem.quantity).label('quantity_sold')
    ).join(OrderItem, MenuItem.id == OrderItem.menu_item_id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(
        Order.restaurant_id == restaurant_id,
        Order.created_at.between(today_start, today_end)
    ).group_by(MenuItem.name).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()

    return jsonify([{'name': name, 'quantity_sold': qty} for name, qty in top_items])


@dashboard_api_bp.route('/menu/<int:item_id>/recipe', methods=['GET'])
@login_required
@admin_required
def get_recipe(item_id):
    """Gets the recipe for a given menu item."""
    menu_item = MenuItem.query.filter_by(id=item_id, restaurant_id=current_user.restaurant_id).first()
    if not menu_item:
        return jsonify({'error': 'Menu item not found'}), 404
    recipe_items = RecipeItem.query.filter_by(menu_item_id=item_id, restaurant_id=current_user.restaurant_id).all()
    result = [{
        'recipe_item_id': item.id,
        'inventory_item_id': item.inventory_item_id,
        'name': item.inventory_item.name,
        'quantity': item.quantity,
        'unit': item.inventory_item.unit
    } for item in recipe_items]
    return jsonify(result)

@dashboard_api_bp.route('/menu/<int:item_id>/recipe', methods=['POST'])
@login_required
@admin_required
def add_recipe_item(item_id):
    """Adds an ingredient to a menu item's recipe."""
    data = request.get_json()
    if not data or 'inventory_item_id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Missing data'}), 400

    # Ensure menu item and inventory item belong to the user's restaurant
    menu_item = MenuItem.query.filter_by(id=item_id, restaurant_id=current_user.restaurant_id).first_or_404()
    inv_item = InventoryItem.query.filter_by(id=data['inventory_item_id'], restaurant_id=current_user.restaurant_id).first_or_404()

    new_recipe_item = RecipeItem(
        restaurant_id=current_user.restaurant_id,
        menu_item_id=menu_item.id,
        inventory_item_id=inv_item.id,
        quantity=float(data['quantity'])
    )
    db.session.add(new_recipe_item)
    db.session.commit()

    return jsonify({
        'recipe_item_id': new_recipe_item.id,
        'name': inv_item.name,
        'quantity': new_recipe_item.quantity
    }), 201

@dashboard_api_bp.route('/recipe-items/<int:recipe_item_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_recipe_item(recipe_item_id):
    """Removes an ingredient from a recipe."""
    recipe_item = RecipeItem.query.join(MenuItem, RecipeItem.menu_item_id == MenuItem.id).filter(
        RecipeItem.id == recipe_item_id,
        RecipeItem.restaurant_id == current_user.restaurant_id,
        MenuItem.restaurant_id == current_user.restaurant_id,
    ).first_or_404()

    # Security check: ensure the recipe item belongs to a menu item in the user's restaurant
    menu_item = MenuItem.query.filter_by(id=recipe_item.menu_item_id, restaurant_id=current_user.restaurant_id).first()
    if not menu_item or menu_item.restaurant_id != current_user.restaurant_id:
        return jsonify({'error': 'Forbidden'}), 403

    db.session.delete(recipe_item)
    db.session.commit()
    return '', 204