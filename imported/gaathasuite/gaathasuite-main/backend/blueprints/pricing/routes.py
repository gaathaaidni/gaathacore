from flask import render_template, request, redirect, url_for, flash, current_app
import os
from flask_login import login_required, current_user
from datetime import date, timedelta
from extensions import db
from . import bp
from models import SubscriptionPlan, Subscription, BetaAccess
from flask import jsonify
from flask_login import login_required
from extensions import db
import json
import csv
import io


def _ensure_default_plans():
    # ensure table exists and create default plans if they don't exist
    from sqlalchemy.exc import OperationalError
    try:
        exists = SubscriptionPlan.query.count()
    except OperationalError:
        # try to create tables and retry
        try:
            db.create_all()
        except Exception:
            pass
        try:
            exists = SubscriptionPlan.query.count()
        except Exception:
            exists = 0

    if exists == 0:
        free = SubscriptionPlan(name='Free (Beta)', slug='free', monthly_price=0.0, yearly_price=0.0,
                                features={'users': 3, 'orgs': 1, 'modules': 'all', 'storage_gb': 1})
        basic = SubscriptionPlan(name='Basic', slug='basic', monthly_price=14.0, yearly_price=140.0,
                                 features={'users': 5, 'orgs': 1, 'modules': ['CRM','Inventory','Books','HR','Desk'], 'invoices_month': 1000, 'storage_gb': 5})
        business = SubscriptionPlan(name='Business', slug='business', monthly_price=29.0, yearly_price=290.0,
                                     features={'users': 'unlimited', 'modules': 'all', 'storage_gb': 50, 'api_access': True})
        enterprise = SubscriptionPlan(name='Enterprise', slug='enterprise', monthly_price=59.0, yearly_price=590.0,
                                      features={'users': 'unlimited', 'modules': 'all', 'storage_gb': 200, 'multi_org': True})
        db.session.add_all([free, basic, business, enterprise])
        db.session.commit()


@bp.route('/')
def pricing():
    _ensure_default_plans()
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.monthly_price).all()
    beta_expires = date(2026, 4, 26)
    return render_template('pricing/pricing.html', plans=plans, beta_expires=beta_expires)


@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    _ensure_default_plans()
    plan_slug = request.values.get('plan')
    period = request.values.get('period', 'monthly')
    plan = SubscriptionPlan.query.filter_by(slug=plan_slug).first()
    if not plan:
        flash('Invalid plan selected', 'danger')
        return redirect(url_for('pricing.pricing'))

    if request.method == 'POST':
        # Mock payment: create subscription
        start = date.today()
        if period == 'yearly':
            end = start + timedelta(days=365)
        else:
            end = start + timedelta(days=30)
        sub = Subscription(user_id=current_user.id, plan_id=plan.id, start_date=start, end_date=end, status='active', renewal_period=period)
        db.session.add(sub)
        db.session.commit()

        # create a billing record (mock invoice link)
        try:
            amount = plan.yearly_price if period == 'yearly' else plan.monthly_price
        except Exception:
            amount = 0.0
        from models import BillingRecord
        br = BillingRecord(subscription_id=sub.id, amount=amount, description=f'Mock charge for {plan.name} ({period})')
        db.session.add(br)
        db.session.commit()
        flash('Subscription activated (mock) and billing recorded.', 'success')
        return redirect(url_for('pricing.success'))

    return render_template('pricing/checkout.html', plan=plan, period=period)


@bp.route('/success')
@login_required
def success():
    return render_template('pricing/success.html')


@bp.route('/cancel')
@login_required
def cancel():
    return render_template('pricing/cancel.html')


@bp.route('/subscription')
@login_required
def subscription_status():
    # show latest subscription for user
    sub = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.end_date.desc()).first()
    beta = BetaAccess.query.filter_by(user_id=current_user.id).first()
    return render_template('pricing/subscription_status.html', subscription=sub, beta=beta)


# CLI command to expire subscriptions
@bp.cli.command('subscriptions:expire')
def expire_subscriptions():
    """Mark subscriptions as expired when end_date < today"""
    today = date.today()
    subs = Subscription.query.filter(Subscription.end_date < today, Subscription.status == 'active').all()
    for s in subs:
        s.status = 'expired'
    # expire beta accesses
    betas = BetaAccess.query.filter(BetaAccess.expires_on < today).all()
    for b in betas:
        # No status field on BetaAccess; application logic should check date
        pass
    db.session.commit()
    print(f"Processed {len(subs)} subscriptions and {len(betas)} beta records")


@bp.route('/api/plans')
def api_plans():
    # Ensure default plans/tables exist
    try:
        _ensure_default_plans()
    except Exception:
        pass
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.monthly_price).all()
    return {
        'plans': [p.to_dict() for p in plans]
    }


@bp.route('/api/subscribe', methods=['POST'])
def api_subscribe():
    from flask import jsonify
    if not getattr(current_user, 'is_authenticated', False):
        return (jsonify({'error': 'authentication_required'}), 401)

    data = request.get_json() or {}
    plan_slug = data.get('plan')
    period = data.get('period', 'monthly')
    plan = SubscriptionPlan.query.filter_by(slug=plan_slug).first()
    if not plan:
        return (jsonify({'error': 'invalid_plan'}), 400)

    start = date.today()
    end = start + (timedelta(days=365) if period == 'yearly' else timedelta(days=30))
    sub = Subscription(user_id=current_user.id, plan_id=plan.id, start_date=start, end_date=end, status='active', renewal_period=period)
    db.session.add(sub)
    db.session.commit()
    return jsonify({'status': 'ok', 'subscription_id': sub.id})


@bp.route('/api/status')
def api_status():
    from flask import jsonify
    if not getattr(current_user, 'is_authenticated', False):
        return (jsonify({'error': 'authentication_required'}), 401)
    sub = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.end_date.desc()).first()
    beta = BetaAccess.query.filter_by(user_id=current_user.id).first()
    return jsonify({'subscription': sub.plan.to_dict() if sub else None, 'beta_expires': beta.expires_on.isoformat() if beta else None})


# ------------------ Admin: Manage Plans ------------------
@bp.route('/admin/plans', methods=['GET', 'POST'])
@login_required
def admin_plans():
    # simple admin UI to list and create plans
    if not getattr(current_user, 'is_admin', False):
        return ("Forbidden", 403)

    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        try:
            monthly = float(request.form.get('monthly_price') or 0)
            yearly = float(request.form.get('yearly_price') or 0)
        except ValueError:
            monthly = 0.0; yearly = 0.0
        features_raw = request.form.get('features') or '{}'
        try:
            features = json.loads(features_raw)
        except Exception:
            features = {'raw': features_raw}

        p = SubscriptionPlan(name=name, slug=slug, monthly_price=monthly, yearly_price=yearly, features=features)
        db.session.add(p)
        db.session.commit()
        flash('Plan created', 'success')
        return redirect(url_for('pricing.admin_plans'))

    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.monthly_price).all()
    return render_template('pricing/admin_plans.html', plans=plans)


@bp.route('/admin/plan/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_plan_edit(plan_id):
    if not getattr(current_user, 'is_admin', False):
        return ("Forbidden", 403)
    p = SubscriptionPlan.query.get_or_404(plan_id)
    if request.method == 'POST':
        p.name = request.form.get('name') or p.name
        p.slug = request.form.get('slug') or p.slug
        try:
            p.monthly_price = float(request.form.get('monthly_price') or p.monthly_price)
            p.yearly_price = float(request.form.get('yearly_price') or p.yearly_price)
        except Exception:
            pass
        features_raw = request.form.get('features')
        if features_raw:
            try:
                p.features = json.loads(features_raw)
            except Exception:
                p.features = {'raw': features_raw}
        db.session.commit()
        flash('Plan updated', 'success')
        return redirect(url_for('pricing.admin_plans'))
    return render_template('pricing/admin_plan_edit.html', plan=p)


@bp.route('/admin/plan/<int:plan_id>/delete', methods=['POST'])
@login_required
def admin_plan_delete(plan_id):
    if not getattr(current_user, 'is_admin', False):
        return ("Forbidden", 403)
    p = SubscriptionPlan.query.get_or_404(plan_id)
    db.session.delete(p)
    db.session.commit()
    flash('Plan deleted', 'info')
    return redirect(url_for('pricing.admin_plans'))


@bp.route('/admin/billing')
@login_required
def admin_billing():
    if not getattr(current_user, 'is_admin', False):
        return ("Forbidden", 403)
    from models import BillingRecord
    records = BillingRecord.query.order_by(BillingRecord.created_at.desc()).all()
    return render_template('pricing/billing_history.html', records=records)


@bp.route('/admin/invoices/csv')
@login_required
def admin_invoices_csv():
    if not getattr(current_user, 'is_admin', False):
        return ("Forbidden", 403)
    if not getattr(current_user, 'is_admin', False):
        return ("Forbidden", 403)
    from models import Invoice, Customer
    
    # Get query parameters for filtering
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    
    query = Invoice.query.join(Customer)
    
    if start_date:
        query = query.filter(Invoice.date >= start_date)
    if end_date:
        query = query.filter(Invoice.date <= end_date)
    if status:
        query = query.filter(Invoice.status == status)
    
    invoices = query.order_by(Invoice.date.desc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Invoice Number', 'Customer Name', 'Email', 'Date', 'Due Date', 'Total Amount', 'Status'])
    
    # Write data
    for inv in invoices:
        writer.writerow([
            inv.number,
            inv.customer.name if inv.customer else '',
            inv.customer.email if inv.customer else '',
            inv.date.isoformat() if inv.date else '',
            inv.due_date.isoformat() if inv.due_date else '',
            f"{inv.total_amount:.2f}",
            inv.status
        ])
    
    # Prepare response
    output.seek(0)
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=invoices.csv'}
    )


@bp.route('/admin/billing/<int:billing_id>/invoice')
@login_required
def admin_billing_generate_invoice(billing_id):
    if not getattr(current_user, 'is_admin', False):
        return ("Forbidden", 403)
    from utils.invoicing import create_invoice_from_billing
    inv, pdf_path = create_invoice_from_billing(current_app, billing_id)
    # return the file for download if exists
    if pdf_path and os.path.exists(pdf_path):
        from flask import send_file
        return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))
    flash('Invoice created but PDF not found.', 'warning')
    return redirect(url_for('pricing.admin_billing'))


# ------------------ Mock Payment Scaffold ------------------
@bp.route('/create_payment', methods=['POST'])
@login_required
def create_payment():
    # Mock create payment session (placeholder for Stripe/Razorpay)
    data = request.get_json() or {}
    plan = data.get('plan')
    period = data.get('period', 'monthly')
    # create mock session id
    session = {'id': f'mock_sess_{plan}_{period}', 'url': url_for('pricing.checkout', plan=plan, period=period)}
    return jsonify({'status': 'ok', 'session': session})


@bp.route('/webhook', methods=['POST'])
def webhook():
    # placeholder -- validate signature and process payment events here
    payload = request.get_json(silent=True)
    # for now just acknowledge
    return jsonify({'received': True, 'payload': payload}), 200
