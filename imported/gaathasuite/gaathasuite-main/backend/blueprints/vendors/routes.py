from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Vendor
from blueprints.vendors.forms import VendorForm
from utils.auth import require_permission, get_current_organization
from services.activity_service import log_activity

vendors_bp = Blueprint('vendors', __name__, url_prefix='/vendors')

@vendors_bp.route('/')
@login_required
@require_permission('expenses.view')  # Vendors are related to expenses
def list_vendors():
    org = get_current_organization()
    page = request.args.get('page', 1, type=int)
    per_page = 25

    query = Vendor.query.filter_by(organization_id=org.id)

    # Filters
    search = request.args.get('search')
    category = request.args.get('category')

    if search:
        query = query.filter(
            db.or_(
                Vendor.name.ilike(f'%{search}%'),
                Vendor.email.ilike(f'%{search}%'),
                Vendor.phone.ilike(f'%{search}%')
            )
        )
    if category:
        query = query.filter_by(category=category)

    vendors = query.order_by(Vendor.name).paginate(page=page, per_page=per_page)

    return render_template('vendors/list.html', vendors=vendors, filters=request.args)

@vendors_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('expenses.create')
def create_vendor():
    org = get_current_organization()
    form = VendorForm()

    if form.validate_on_submit():
        vendor = Vendor(
            organization_id=org.id,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            category=form.category.data,
            created_by=current_user.id
        )

        db.session.add(vendor)
        db.session.commit()

        log_activity(org.id, 'vendor_created', f'Vendor created: {vendor.name}', current_user.id, vendor.id, 'vendor')

        flash('Vendor created successfully!', 'success')
        return redirect(url_for('vendors.list_vendors'))

    return render_template('vendors/form.html', form=form, action='Create')

@vendors_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('expenses.edit')
def edit_vendor(id):
    org = get_current_organization()
    vendor = Vendor.query.filter_by(id=id, organization_id=org.id).first_or_404()

    form = VendorForm()

    if form.validate_on_submit():
        vendor.name = form.name.data
        vendor.email = form.email.data
        vendor.phone = form.phone.data
        vendor.address = form.address.data
        vendor.category = form.category.data

        db.session.commit()

        log_activity(org.id, 'vendor_updated', f'Vendor updated: {vendor.name}', current_user.id, vendor.id, 'vendor')

        flash('Vendor updated successfully!', 'success')
        return redirect(url_for('vendors.list_vendors'))

    # Pre-populate form
    form.name.data = vendor.name
    form.email.data = vendor.email
    form.phone.data = vendor.phone
    form.address.data = vendor.address
    form.category.data = vendor.category

    return render_template('vendors/form.html', form=form, vendor=vendor, action='Edit')

@vendors_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@require_permission('expenses.delete')
def delete_vendor(id):
    org = get_current_organization()
    vendor = Vendor.query.filter_by(id=id, organization_id=org.id).first_or_404()

    # Check if vendor has expenses
    if vendor.expenses:
        flash('Cannot delete vendor with existing expenses!', 'danger')
        return redirect(url_for('vendors.list_vendors'))

    db.session.delete(vendor)
    db.session.commit()

    log_activity(org.id, 'vendor_deleted', f'Vendor deleted: {vendor.name}', current_user.id, vendor.id, 'vendor')

    flash('Vendor deleted successfully!', 'success')
    return redirect(url_for('vendors.list_vendors'))

# API endpoints
@vendors_bp.route('/api/search')
@login_required
def search_vendors():
    org = get_current_organization()
    query = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)

    vendors = Vendor.query.filter_by(organization_id=org.id)\
        .filter(Vendor.name.ilike(f'%{query}%'))\
        .limit(limit).all()

    return jsonify([
        {'id': v.id, 'name': v.name, 'email': v.email}
        for v in vendors
    ])