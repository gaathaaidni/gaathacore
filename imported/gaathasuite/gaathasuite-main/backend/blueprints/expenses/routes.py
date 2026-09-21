from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Expense, Vendor, Organization
from blueprints.expenses.forms import ExpenseForm
from utils.auth import require_permission, get_current_organization
from services.activity_service import log_activity
from datetime import datetime

expenses_bp = Blueprint('expenses', __name__, url_prefix='/expenses')

@expenses_bp.route('/')
@login_required
@require_permission('expenses.view')
def list_expenses():
    org = get_current_organization()
    page = request.args.get('page', 1, type=int)
    per_page = 25

    query = Expense.query.filter_by(organization_id=org.id)

    # Filters
    vendor_id = request.args.get('vendor_id', type=int)
    category = request.args.get('category')
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    if vendor_id:
        query = query.filter_by(vendor_id=vendor_id)
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    if date_from:
        query = query.filter(Expense.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(Expense.date <= datetime.strptime(date_to, '%Y-%m-%d').date())

    expenses = query.order_by(Expense.date.desc()).paginate(page=page, per_page=per_page)
    vendors = Vendor.query.filter_by(organization_id=org.id).all()

    return render_template('expenses/list.html',
                         expenses=expenses,
                         vendors=vendors,
                         filters=request.args)

@expenses_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('expenses.create')
def create_expense():
    org = get_current_organization()
    form = ExpenseForm()

    if form.validate_on_submit():
        expense = Expense(
            organization_id=org.id,
            vendor_id=form.vendor_id.data if form.vendor_id.data != 0 else None,
            description=form.description.data,
            amount=form.amount.data,
            category=form.category.data,
            date=form.date.data,
            status='pending',
            created_by=current_user.id
        )

        db.session.add(expense)
        db.session.commit()

        log_activity(org.id, 'expense_created', f'Expense created: {expense.description}', current_user.id, expense.id, 'expense')

        flash('Expense created successfully!', 'success')
        return redirect(url_for('expenses.list_expenses'))

    vendors = Vendor.query.filter_by(organization_id=org.id).all()
    return render_template('expenses/form.html', form=form, vendors=vendors, action='Create')

@expenses_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('expenses.edit')
def edit_expense(id):
    org = get_current_organization()
    expense = Expense.query.filter_by(id=id, organization_id=org.id).first_or_404()

    form = ExpenseForm()

    if form.validate_on_submit():
        expense.vendor_id = form.vendor_id.data if form.vendor_id.data != 0 else None
        expense.description = form.description.data
        expense.amount = form.amount.data
        expense.category = form.category.data
        expense.date = form.date.data

        db.session.commit()

        log_activity(org.id, 'expense_updated', f'Expense updated: {expense.description}', current_user.id, expense.id, 'expense')

        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expenses.list_expenses'))

    # Pre-populate form
    form.vendor_id.data = expense.vendor_id or 0
    form.description.data = expense.description
    form.amount.data = expense.amount
    form.category.data = expense.category
    form.date.data = expense.date

    vendors = Vendor.query.filter_by(organization_id=org.id).all()
    return render_template('expenses/form.html', form=form, vendors=vendors, expense=expense, action='Edit')

@expenses_bp.route('/<int:id>/approve', methods=['POST'])
@login_required
@require_permission('expenses.approve')
def approve_expense(id):
    org = get_current_organization()
    expense = Expense.query.filter_by(id=id, organization_id=org.id).first_or_404()

    expense.status = 'approved'
    expense.approved_by = current_user.id
    expense.approved_at = datetime.utcnow()

    db.session.commit()

    log_activity(org.id, 'expense_approved', f'Expense approved: {expense.description}', current_user.id, expense.id, 'expense')

    flash('Expense approved successfully!', 'success')
    return redirect(url_for('expenses.list_expenses'))

@expenses_bp.route('/<int:id>/reject', methods=['POST'])
@login_required
@require_permission('expenses.approve')
def reject_expense(id):
    org = get_current_organization()
    expense = Expense.query.filter_by(id=id, organization_id=org.id).first_or_404()

    expense.status = 'rejected'
    expense.rejected_by = current_user.id
    expense.rejected_at = datetime.utcnow()

    db.session.commit()

    log_activity(org.id, 'expense_rejected', f'Expense rejected: {expense.description}', current_user.id, expense.id, 'expense')

    flash('Expense rejected!', 'warning')
    return redirect(url_for('expenses.list_expenses'))

@expenses_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@require_permission('expenses.delete')
def delete_expense(id):
    org = get_current_organization()
    expense = Expense.query.filter_by(id=id, organization_id=org.id).first_or_404()

    db.session.delete(expense)
    db.session.commit()

    log_activity(org.id, 'expense_deleted', f'Expense deleted: {expense.description}', current_user.id, expense.id, 'expense')

    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expenses.list_expenses'))

# API endpoints for AJAX
@expenses_bp.route('/api/categories')
@login_required
def get_categories():
    org = get_current_organization()
    categories = db.session.query(Expense.category).filter_by(organization_id=org.id).distinct().all()
    return jsonify([cat[0] for cat in categories])

@expenses_bp.route('/api/stats')
@login_required
@require_permission('expenses.view')
def get_expense_stats():
    org = get_current_organization()
    stats = db.session.query(
        Expense.status,
        db.func.count(Expense.id).label('count'),
        db.func.sum(Expense.amount).label('total')
    ).filter_by(organization_id=org.id).group_by(Expense.status).all()

    return jsonify({
        'stats': [
            {'status': s.status, 'count': s.count, 'total': float(s.total or 0)}
            for s in stats
        ]
    })