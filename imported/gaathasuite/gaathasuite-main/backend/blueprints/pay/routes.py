from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Invoice, Payment
from blueprints.pay.forms import PaymentForm
from datetime import datetime

pay_bp = Blueprint("pay", __name__, template_folder="templates")


@pay_bp.route("/")
def dashboard():
    invoices = Invoice.query.filter_by(status="sent").all()
    return render_template("pay/invoices.html", invoices=invoices, tab="invoices")


@pay_bp.route("/invoices")
def invoices_list():
    invoices = Invoice.query.all()
    return render_template("pay/invoices.html", invoices=invoices)


@pay_bp.route("/invoice/<int:id>/pay", methods=["GET", "POST"])
def pay_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    form = PaymentForm()
    
    if form.validate_on_submit():
        payment = Payment(
            invoice_id=id,
            amount=form.amount.data,
            date=form.date.data or datetime.utcnow().date(),
            method=form.method.data,
            reference=form.reference.data
        )
        
        total_paid = Payment.query.filter_by(invoice_id=id).with_entities(db.func.sum(Payment.amount)).scalar() or 0
        total_paid += form.amount.data
        
        if total_paid >= invoice.total_amount:
            invoice.status = "paid"
        else:
            invoice.status = "sent"
        
        db.session.add(payment)
        db.session.commit()
        flash("Payment recorded", "success")
        return redirect(url_for("pay.invoices_list"))
    
    form.invoice_id.data = id
    form.amount.data = invoice.total_amount
    return render_template("pay/payment_form.html", form=form, invoice=invoice)


@pay_bp.route("/payments")
def payments_list():
    payments = Payment.query.order_by(Payment.created_at.desc()).all()
    return render_template("pay/payments_list.html", payments=payments)


# API to validate and apply a coupon to an invoice.
@pay_bp.route('/apply-coupon', methods=['POST'])
def apply_coupon():
    invoice_id = request.form.get('invoice_id') or request.json.get('invoice_id') if request.json else None
    code = request.form.get('coupon_code') or request.json.get('coupon_code') if request.json else None
    apply_now = (request.form.get('apply') == '1') or (request.json and request.json.get('apply'))
    if not invoice_id or not code:
        return ({'error': 'missing_parameters'}, 400)
    inv = Invoice.query.get(int(invoice_id))
    if not inv:
        return ({'error': 'invoice_not_found'}, 404)
    c = Coupon.query.filter(Coupon.code.ilike(code.strip())).first()
    if not c or not c.is_valid():
        return ({'valid': False, 'error': 'invalid_coupon'}, 200)

    # compute discount
    if c.discount_type == 'percentage':
        discount = (c.value / 100.0) * float(inv.total_amount)
    else:
        discount = float(c.value)
    discount = round(discount, 2)
    new_total = max(0.0, float(inv.total_amount) - discount)

    if apply_now:
        # create a negative invoice line and adjust invoice total
        line = InvoiceLine(invoice_id=inv.id, description=f"Coupon {c.code}", qty=1, unit_price=-discount, total=-discount)
        inv.total_amount = new_total
        c.used_count = (c.used_count or 0) + 1
        # create a billing record to reflect coupon discount
        try:
            from models import BillingRecord
            br = BillingRecord(subscription_id=None, amount=-discount, description=f"Coupon {c.code}", invoice_id=inv.id)
            db.session.add(br)
        except Exception:
            br = None
        db.session.add(line)
        db.session.add(c)
        db.session.add(inv)
        db.session.commit()
    return ({'valid': True, 'discount': discount, 'new_total': new_total, 'applied': bool(apply_now)})
