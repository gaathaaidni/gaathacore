from flask import render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from utils.auth import require_superadmin
from extensions import db
from models import User, Organization, ActivityLog, Coupon, OrganizationPayment
from utils.audit import log_activity
from utils.background_jobs import run_background, get_job

from . import bp


@bp.route('/')
@login_required
@require_superadmin()
def dashboard():
    # Filters & pagination for activity logs
    from flask import request
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get('per_page', 20))
    except (TypeError, ValueError):
        per_page = 20
    action_filter = request.args.get('action')
    module_filter = request.args.get('module')

    users = User.query.all()
    orgs = Organization.query.all()

    q = ActivityLog.query
    if action_filter:
        q = q.filter(ActivityLog.action.ilike(f"%{action_filter}%"))
    if module_filter:
        q = q.filter(ActivityLog.module.ilike(f"%{module_filter}%"))

    total = q.count()
    recent_logs = q.order_by(ActivityLog.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()
    return render_template('superadmin/dashboard.html', users=users, orgs=orgs, recent_logs=recent_logs, page=page, per_page=per_page, total=total)


@bp.route('/rotate-secret', methods=['POST'])
@login_required
@require_superadmin()
def rotate_secret():
    # Kick off a background job to rotate the secret using utils.secret_manager
    try:
        from utils.secret_manager import rotate_secret as rotate_fn
        job_id = run_background(rotate_fn, '.env', False)
        org_id = getattr(current_user, 'organization_id', None)
        log_activity(current_user.id, org_id, 'rotate_secret_started', 'secrets', record_id=0, record_type='secret_rotation', new_values={'job_id': job_id})
        flash('Secret rotation started (job id: ' + job_id + ').', 'info')
        return redirect(url_for('superadmin.dashboard'))
    except Exception as e:
        org_id = getattr(current_user, 'organization_id', None)
        log_activity(current_user.id, org_id, 'rotate_secret_failed', 'secrets', record_id=0, record_type='secret_rotation', new_values={'error': str(e)})
        flash('Secret rotation failed to start: ' + str(e), 'danger')
        return redirect(url_for('superadmin.dashboard'))


@bp.route('/rotate-status/<job_id>')
@login_required
@require_superadmin()
def rotate_status(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({'error': 'not_found'}), 404
    return jsonify(job)


@bp.route('/coupons')
@login_required
@require_superadmin()
def coupons():
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    orgs = Organization.query.all()
    # analytics
    total_uses = sum([c.used_count or 0 for c in coupons])
    active_count = Coupon.query.filter_by(active=True).count()
    from datetime import date, timedelta
    soon = date.today() + timedelta(days=30)
    expiring_soon = Coupon.query.filter(Coupon.end_date != None, Coupon.end_date <= soon).count()
    return render_template('superadmin/coupons.html', coupons=coupons, orgs=orgs, total_uses=total_uses, active_count=active_count, expiring_soon=expiring_soon)


@bp.route('/coupons/new', methods=['GET', 'POST'])
@login_required
@require_superadmin()
def coupon_new():
    if request.method == 'POST':
        data = request.form
        code = data.get('code')
        if not code:
            flash('Coupon code is required', 'danger')
            return redirect(url_for('superadmin.coupon_new'))
        # simple uniqueness check
        if Coupon.query.filter_by(code=code).first():
            flash('Coupon code already exists', 'danger')
            return redirect(url_for('superadmin.coupon_new'))
        c = Coupon(
            code=code.strip().upper(),
            description=data.get('description'),
            discount_type=data.get('discount_type', 'percentage'),
            value=float(data.get('value') or 0),
            organization_id=int(data.get('organization_id')) if data.get('organization_id') else None,
            usage_limit=int(data.get('usage_limit')) if data.get('usage_limit') else None,
            active=True,
            created_by=current_user.id
        )
        db.session.add(c)
        db.session.commit()
        log_activity(current_user.id, None, 'create_coupon', 'coupons', record_id=c.id, record_type='coupon', new_values={'code': c.code})
        flash('Coupon created', 'success')
        return redirect(url_for('superadmin.coupons'))
    orgs = Organization.query.all()
    return render_template('superadmin/coupon_form.html', orgs=orgs)


@bp.route('/coupons/<int:coupon_id>/edit', methods=['GET', 'POST'])
@login_required
@require_superadmin()
def coupon_edit(coupon_id):
    c = Coupon.query.get_or_404(coupon_id)
    if request.method == 'POST':
        data = request.form
        old = { 'code': c.code, 'value': c.value }
        c.description = data.get('description')
        c.discount_type = data.get('discount_type', c.discount_type)
        c.value = float(data.get('value') or 0)
        c.organization_id = int(data.get('organization_id')) if data.get('organization_id') else None
        c.usage_limit = int(data.get('usage_limit')) if data.get('usage_limit') else None
        c.active = True if data.get('active') == '1' else False
        db.session.commit()
        log_activity(current_user.id, None, 'edit_coupon', 'coupons', record_id=c.id, record_type='coupon', old_values=old, new_values={'value': c.value})
        flash('Coupon updated', 'success')
        return redirect(url_for('superadmin.coupons'))
    orgs = Organization.query.all()
    return render_template('superadmin/coupon_form.html', coupon=c, orgs=orgs)


@bp.route('/coupons/<int:coupon_id>/toggle', methods=['POST'])
@login_required
@require_superadmin()
def coupon_toggle(coupon_id):
    c = Coupon.query.get_or_404(coupon_id)
    c.active = not c.active
    db.session.commit()
    log_activity(current_user.id, None, 'toggle_coupon', 'coupons', record_id=c.id, record_type='coupon', new_values={'active': c.active})
    flash('Coupon updated', 'success')
    return redirect(url_for('superadmin.coupons'))


@bp.route('/coupons/<int:coupon_id>/delete', methods=['POST'])
@login_required
@require_superadmin()
def coupon_delete(coupon_id):
    c = Coupon.query.get_or_404(coupon_id)
    db.session.delete(c)
    db.session.commit()
    log_activity(current_user.id, None, 'delete_coupon', 'coupons', record_id=coupon_id, record_type='coupon')
    flash('Coupon deleted', 'success')
    return redirect(url_for('superadmin.coupons'))


@bp.route('/coupons/export')
@login_required
@require_superadmin()
def coupons_export():
    import csv
    from io import StringIO
    q = Coupon.query.order_by(Coupon.created_at.desc()).all()
    si = StringIO()
    w = csv.writer(si)
    w.writerow(['id','code','description','discount_type','value','start_date','end_date','usage_limit','used_count','active','organization_id'])
    for c in q:
        w.writerow([c.id,c.code,c.description,c.discount_type,c.value,c.start_date,c.end_date,c.usage_limit,c.used_count,c.active,c.organization_id])
    # Audit export
    try:
        log_activity(current_user.id, None, 'export_coupons', 'coupons', record_id=0, record_type='coupon_export', new_values={'count': len(q)})
    except Exception:
        pass
    return (si.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename="coupons.csv"'})


@bp.route('/coupons/import', methods=['POST'])
@login_required
@require_superadmin()
def coupons_import():
    # simple CSV import expecting header
    f = request.files.get('file')
    if not f:
        flash('No file uploaded', 'danger')
        return redirect(url_for('superadmin.coupons'))
    import csv
    from io import TextIOWrapper
    reader = csv.DictReader(TextIOWrapper(f.stream))
    imported = 0
    for row in reader:
        code = row.get('code')
        if not code:
            continue
        if Coupon.query.filter(Coupon.code.ilike(code)).first():
            continue
        c = Coupon(code=code.strip().upper(), description=row.get('description'), discount_type=row.get('discount_type') or 'percentage', value=float(row.get('value') or 0), active=(row.get('active','True') in ('True','true','1')))
        db.session.add(c)
        imported += 1
    db.session.commit()
    try:
        log_activity(current_user.id, None, 'import_coupons', 'coupons', record_id=0, record_type='coupon_import', new_values={'count': imported})
    except Exception:
        pass
    flash(f'Imported {imported} coupons', 'success')
    return redirect(url_for('superadmin.coupons'))


@bp.route('/org-payments')
@login_required
@require_superadmin()
def org_payments():
    org_id = request.args.get('org_id')
    q = OrganizationPayment.query
    if org_id:
        q = q.filter_by(organization_id=org_id)
    payments = q.order_by(OrganizationPayment.created_at.desc()).limit(200).all()
    orgs = Organization.query.all()
    return render_template('superadmin/org_payments.html', payments=payments, orgs=orgs)


@bp.route('/org-payments/<int:payment_id>/update-status', methods=['POST'])
@login_required
@require_superadmin()
def org_payment_update_status(payment_id):
    p = OrganizationPayment.query.get_or_404(payment_id)
    new_status = request.form.get('status')
    old = {'status': p.status}
    p.status = new_status
    db.session.commit()
    log_activity(current_user.id, p.organization_id, 'update_org_payment', 'payments', record_id=p.id, record_type='org_payment', old_values=old, new_values={'status': new_status})
    flash('Payment status updated', 'success')
    return redirect(url_for('superadmin.org_payments'))


@bp.route('/org-payments/<int:payment_id>/refund', methods=['POST'])
@login_required
@require_superadmin()
def org_payment_refund(payment_id):
    p = OrganizationPayment.query.get_or_404(payment_id)
    old = {'status': p.status}
    p.status = 'refunded'
    db.session.commit()
    log_activity(current_user.id, p.organization_id, 'refund_org_payment', 'payments', record_id=p.id, record_type='org_payment', old_values=old, new_values={'status': 'refunded'})
    flash('Payment marked as refunded', 'info')
    return redirect(url_for('superadmin.org_payments'))
