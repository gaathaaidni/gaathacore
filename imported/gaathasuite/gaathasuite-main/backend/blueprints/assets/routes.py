from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Asset
from blueprints.assets.forms import AssetForm  # We'll create this
from utils.auth import require_permission, get_current_organization
from services.activity_service import log_activity
from datetime import datetime

assets_bp = Blueprint('assets', __name__, url_prefix='/assets')

@assets_bp.route('/')
@login_required
@require_permission('assets.view')
def list_assets():
    org = get_current_organization()
    page = request.args.get('page', 1, type=int)
    per_page = 25

    query = Asset.query.filter_by(organization_id=org.id)

    # Filters
    category = request.args.get('category')
    status = request.args.get('status')
    assigned_to = request.args.get('assigned_to', type=int)

    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)

    assets = query.order_by(Asset.name).paginate(page=page, per_page=per_page)

    return render_template('assets/list.html', assets=assets, filters=request.args)

@assets_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('assets.create')
def create_asset():
    org = get_current_organization()
    form = AssetForm()

    if form.validate_on_submit():
        asset = Asset(
            organization_id=org.id,
            name=form.name.data,
            description=form.description.data,
            category=form.category.data,
            asset_tag=form.asset_tag.data,
            serial_number=form.serial_number.data,
            purchase_date=form.purchase_date.data,
            purchase_cost=form.purchase_cost.data,
            current_value=form.current_value.data,
            location=form.location.data,
            status=form.status.data,
            assigned_to=form.assigned_to.data if form.assigned_to.data != 0 else None,
            notes=form.notes.data,
            created_by=current_user.id
        )

        db.session.add(asset)
        db.session.commit()

        log_activity(org.id, 'asset_created', f'Asset created: {asset.name}', current_user.id, asset.id, 'asset')

        flash('Asset created successfully!', 'success')
        return redirect(url_for('assets.list_assets'))

    return render_template('assets/form.html', form=form, action='Create')

@assets_bp.route('/<int:id>')
@login_required
@require_permission('assets.view')
def view_asset(id):
    org = get_current_organization()
    asset = Asset.query.filter_by(id=id, organization_id=org.id).first_or_404()

    return render_template('assets/view.html', asset=asset)

@assets_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('assets.edit')
def edit_asset(id):
    org = get_current_organization()
    asset = Asset.query.filter_by(id=id, organization_id=org.id).first_or_404()

    form = AssetForm()

    if form.validate_on_submit():
        asset.name = form.name.data
        asset.description = form.description.data
        asset.category = form.category.data
        asset.asset_tag = form.asset_tag.data
        asset.serial_number = form.serial_number.data
        asset.purchase_date = form.purchase_date.data
        asset.purchase_cost = form.purchase_cost.data
        asset.current_value = form.current_value.data
        asset.location = form.location.data
        asset.status = form.status.data
        asset.assigned_to = form.assigned_to.data if form.assigned_to.data != 0 else None
        asset.notes = form.notes.data

        db.session.commit()

        log_activity(org.id, 'asset_updated', f'Asset updated: {asset.name}', current_user.id, asset.id, 'asset')

        flash('Asset updated successfully!', 'success')
        return redirect(url_for('assets.list_assets'))

    # Pre-populate form
    form.name.data = asset.name
    form.description.data = asset.description
    form.category.data = asset.category
    form.asset_tag.data = asset.asset_tag
    form.serial_number.data = asset.serial_number
    form.purchase_date.data = asset.purchase_date
    form.purchase_cost.data = asset.purchase_cost
    form.current_value.data = asset.current_value
    form.location.data = asset.location
    form.status.data = asset.status
    form.assigned_to.data = asset.assigned_to or 0
    form.notes.data = asset.notes

    return render_template('assets/form.html', form=form, asset=asset, action='Edit')

@assets_bp.route('/<int:id>/assign', methods=['POST'])
@login_required
@require_permission('assets.edit')
def assign_asset(id):
    org = get_current_organization()
    asset = Asset.query.filter_by(id=id, organization_id=org.id).first_or_404()

    assigned_to = request.form.get('assigned_to', type=int)
    asset.assigned_to = assigned_to if assigned_to != 0 else None
    asset.status = 'assigned' if assigned_to else 'available'

    db.session.commit()

    log_activity(org.id, 'asset_assigned', f'Asset assigned: {asset.name}', current_user.id, asset.id, 'asset')

    flash('Asset assignment updated!', 'success')
    return redirect(url_for('assets.view_asset', id=id))

@assets_bp.route('/<int:id>/maintenance', methods=['POST'])
@login_required
@require_permission('assets.edit')
def add_maintenance(id):
    org = get_current_organization()
    asset = Asset.query.filter_by(id=id, organization_id=org.id).first_or_404()

    maintenance_date = request.form.get('maintenance_date')
    description = request.form.get('description')
    cost = request.form.get('cost', type=float)

    # In a real implementation, you'd have a Maintenance model
    # For now, we'll just update the notes
    maintenance_note = f"\nMaintenance on {maintenance_date}: {description}"
    if cost:
        maintenance_note += f" (Cost: ${cost})"

    asset.notes = (asset.notes or '') + maintenance_note
    asset.last_maintenance = datetime.strptime(maintenance_date, '%Y-%m-%d').date()

    db.session.commit()

    log_activity(org.id, 'asset_maintenance', f'Maintenance added to asset: {asset.name}', current_user.id, asset.id, 'asset')

    flash('Maintenance record added!', 'success')
    return redirect(url_for('assets.view_asset', id=id))

@assets_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@require_permission('assets.delete')
def delete_asset(id):
    org = get_current_organization()
    asset = Asset.query.filter_by(id=id, organization_id=org.id).first_or_404()

    db.session.delete(asset)
    db.session.commit()

    log_activity(org.id, 'asset_deleted', f'Asset deleted: {asset.name}', current_user.id, asset.id, 'asset')

    flash('Asset deleted successfully!', 'success')
    return redirect(url_for('assets.list_assets'))

# API endpoints
@assets_bp.route('/api/categories')
@login_required
def get_categories():
    org = get_current_organization()
    categories = db.session.query(Asset.category).filter_by(organization_id=org.id).distinct().all()
    return jsonify([cat[0] for cat in categories])

@assets_bp.route('/api/stats')
@login_required
@require_permission('assets.view')
def get_asset_stats():
    org = get_current_organization()
    stats = db.session.query(
        Asset.status,
        db.func.count(Asset.id).label('count'),
        db.func.sum(Asset.current_value).label('total_value')
    ).filter_by(organization_id=org.id).group_by(Asset.status).all()

    return jsonify({
        'stats': [
            {'status': s.status, 'count': s.count, 'total_value': float(s.total_value or 0)}
            for s in stats
        ]
    })