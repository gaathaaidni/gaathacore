from flask import render_template, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from . import admin_bp
from decorators import admin_required, permission_required
from extensions import db, convert_currency
from models import MenuItem, InventoryItem, PriceHistory, AuditLog, RolePermission, Transaction, Collection, Payment
from models import Invoice, Restaurant, StoreSettings
from blueprints.inventory.services import get_inventory_item, validate_quantity
import csv, io
from datetime import datetime, timezone
from models import User
from werkzeug.security import generate_password_hash
from flask import current_app


def _user_in_current_restaurant(user_id):
    query = User.query.filter_by(id=user_id)
    if not getattr(current_user, "is_super_admin", False):
        query = query.filter_by(restaurant_id=current_user.restaurant_id)
    return query.first()


def _users_in_current_restaurant():
    query = User.query
    if not getattr(current_user, "is_super_admin", False):
        query = query.filter_by(restaurant_id=current_user.restaurant_id)
    return query


def _menu_item_for_current_restaurant(item_id):
    query = MenuItem.query.filter_by(id=item_id)
    if not getattr(current_user, "is_super_admin", False):
        if current_user.restaurant_id is None:
            query = query.filter(MenuItem.restaurant_id.is_(None))
        else:
            query = query.filter_by(restaurant_id=current_user.restaurant_id)
    return query.first()


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    return render_template("admin_dashboard.html")


### Menu management API
@admin_bp.route("/api/menu", methods=["GET"])
@login_required
@permission_required('manage_menu')
def api_get_menu():
    try:
        query = MenuItem.query
        if not getattr(current_user, "is_super_admin", False):
            if current_user.restaurant_id is None:
                query = query.filter(MenuItem.restaurant_id.is_(None))
            else:
                query = query.filter_by(restaurant_id=current_user.restaurant_id)
        items = query.order_by(MenuItem.id.desc()).all()
        user_currency = current_user.currency
        rates = current_app.config.get('EXCHANGE_RATES', {})
        return jsonify([{
            "id": i.id,
            "name": i.name,
            "description": i.description,
            "price": convert_currency(i.price, 'USD', user_currency, rates),
            "available": i.available
        } for i in items])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


### User management
@admin_bp.route('/api/users', methods=['GET'])
@login_required
@permission_required('manage_users')
def api_get_users():
    try:
        users = _users_in_current_restaurant().order_by(User.id.desc()).all()
        return jsonify([{"id": u.id, "username": u.username, "role": u.role} for u in users])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/api/users', methods=['POST'])
@login_required
@permission_required('manage_users')
def api_create_user():
    data = request.get_json() or {}
    try:
        username = data.get('username')
        password = data.get('password')
        role = data.get('role') or 'waiter'
        if not username or not password:
            return jsonify({'error':'username and password required'}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({'error':'username exists'}), 400
        if role not in {"waiter", "kitchen", "manager", "cashier"}:
            return jsonify({'error': 'invalid role'}), 400
        if current_user.restaurant_id is None and not current_user.is_super_admin:
            return jsonify({'error': 'restaurant context is required'}), 400
        u = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            restaurant_id=current_user.restaurant_id,
        )
        db.session.add(u)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='create', object_type='user', object_id=u.id, details=f'created user {username} role={role}')
        db.session.add(log)
        db.session.commit()
        return jsonify({'id': u.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@permission_required('manage_users')
def api_update_user(user_id):
    data = request.get_json() or {}
    try:
        u = _user_in_current_restaurant(user_id)
        if u is None:
            return jsonify({'error': 'User not found'}), 404
        changed = []
        if 'username' in data and data.get('username') != u.username:
            changed.append(f'username: {u.username} -> {data.get("username")}')
            u.username = data.get('username')
        if 'role' in data and data.get('role') != u.role:
            changed.append(f'role: {u.role} -> {data.get("role")}')
            u.role = data.get('role')
        db.session.commit()
        if changed:
            log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='update', object_type='user', object_id=u.id, details='; '.join(changed))
            db.session.add(log)
            db.session.commit()
        return jsonify({'status':'ok'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


### Accounting & Collections
@admin_bp.route('/api/transactions', methods=['GET'])
@login_required
@permission_required('view_accounting')
def api_get_transactions():
    try:
        rows = Transaction.query.order_by(Transaction.id.desc()).limit(200).all()
        return jsonify([{'id': r.id, 'transaction_type': r.transaction_type, 'amount': r.amount, 'category': r.category, 'description': r.description, 'recorded_by': r.recorded_by, 'created_at': (r.created_at.isoformat() if getattr(r,'created_at',None) else None)} for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/transactions', methods=['POST'])
@login_required
@permission_required('manage_accounting')
def api_create_transaction():
    data = request.get_json() or {}
    try:
        ttype = data.get('transaction_type') or 'income'
        amount = float(data.get('amount', 0))
        category = data.get('category') or 'other'
        desc = data.get('description')
        t = Transaction(transaction_type=ttype, amount=amount, category=category, description=desc, recorded_by=getattr(current_user,'username',None))
        db.session.add(t)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='create', object_type='transaction', object_id=t.id, details=f'{ttype} {amount} {category or ""}')
        db.session.add(log)
        db.session.commit()
        return jsonify({'id': t.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/transactions/<int:txn_id>', methods=['DELETE'])
@login_required
@permission_required('manage_accounting')
def api_delete_transaction(txn_id):
    try:
        t = Transaction.query.get_or_404(txn_id)
        db.session.delete(t)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='delete', object_type='transaction', object_id=txn_id, details=f'deleted txn')
        db.session.add(log)
        db.session.commit()
        return jsonify({'status':'deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/accounting/summary', methods=['GET'])
@login_required
@permission_required('view_accounting')
def api_accounting_summary():
    try:
        income = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter(Transaction.transaction_type=='income').scalar() or 0
        expenses = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter(Transaction.transaction_type=='expense').scalar() or 0
        user_currency = current_user.currency
        rates = current_app.config.get('EXCHANGE_RATES', {})
        return jsonify({'income': convert_currency(float(income), 'USD', user_currency, rates), 'expenses': convert_currency(float(expenses), 'USD', user_currency, rates)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/collections', methods=['GET'])
@login_required
@permission_required('view_collections')
def api_get_collections():
    try:
        cols = Collection.query.order_by(Collection.id.desc()).all()
        user_currency = current_user.currency
        rates = current_app.config.get('EXCHANGE_RATES', {})
        out = []
        for c in cols:
            out.append({'id': c.id, 'customer': c.customer_name, 'phone': c.customer_phone, 'total': convert_currency(c.total_amount, 'USD', user_currency, rates), 'paid': convert_currency(c.paid_amount, 'USD', user_currency, rates), 'balance': convert_currency(c.balance, 'USD', user_currency, rates), 'status': c.status, 'due_date': c.due_date.isoformat() if c.due_date else None, 'payments': [{'id': p.id, 'amount': convert_currency(p.amount, 'USD', user_currency, rates), 'method': p.payment_method, 'reference': p.reference_id, 'received_by': p.received_by, 'created_at': p.payment_date.isoformat() if p.payment_date else None} for p in c.payments]})
        return jsonify(out)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/collections', methods=['POST'])
@login_required
@permission_required('manage_collections')
def api_create_collection():
    data = request.get_json() or {}
    try:
        customer = data.get('customer') or data.get('customer_name') or 'Customer'
        phone = data.get('phone') or data.get('customer_phone')
        total = float(data.get('total', data.get('total_amount', 0)))
        c = Collection(customer_name=customer, customer_phone=phone, total_amount=total, paid_amount=0.0, balance=total, status='pending')
        db.session.add(c)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='create', object_type='collection', object_id=c.id, details=f'created collection for {customer} total={total}')
        db.session.add(log)
        db.session.commit()
        return jsonify({'id': c.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/collections/<int:col_id>', methods=['GET'])
@login_required
@permission_required('view_collections')
def api_get_collection(col_id):
    try:
        c = Collection.query.get_or_404(col_id)
        user_currency = current_user.currency
        rates = current_app.config.get('EXCHANGE_RATES', {})
        return jsonify({'id': c.id, 'customer': c.customer_name, 'phone': c.customer_phone, 'total': convert_currency(c.total_amount, 'USD', user_currency, rates), 'paid': convert_currency(c.paid_amount, 'USD', user_currency, rates), 'balance': convert_currency(c.balance, 'USD', user_currency, rates), 'status': c.status, 'payments': [{'id': p.id, 'amount': convert_currency(p.amount, 'USD', user_currency, rates), 'method': p.payment_method, 'reference': p.reference_id, 'received_by': p.received_by, 'created_at': p.payment_date.isoformat() if p.payment_date else None} for p in c.payments]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/collections/<int:col_id>', methods=['PUT'])
@login_required
@permission_required('manage_collections')
def api_update_collection(col_id):
    data = request.get_json() or {}
    try:
        c = Collection.query.get_or_404(col_id)
        changed = []
        if 'customer' in data and data.get('customer') != c.customer:
            changed.append(f'customer: {c.customer_name} -> {data.get("customer")}')
            c.customer_name = data.get('customer')
        if 'total' in data:
            new_total = float(data.get('total'))
            if new_total != c.total:
                changed.append(f'total: {c.total_amount} -> {new_total}')
                c.total_amount = new_total
                c.balance = max(0, c.total_amount - c.paid_amount)
        db.session.commit()
        if changed:
            log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='update', object_type='collection', object_id=c.id, details='; '.join(changed))
            db.session.add(log)
            db.session.commit()
        return jsonify({'status':'ok'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/collections/<int:col_id>', methods=['DELETE'])
@login_required
@permission_required('manage_collections')
def api_delete_collection(col_id):
    try:
        c = Collection.query.get_or_404(col_id)
        db.session.delete(c)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='delete', object_type='collection', object_id=col_id, details=f'deleted collection')
        db.session.add(log)
        db.session.commit()
        return jsonify({'status':'deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/collections/<int:col_id>/payment', methods=['POST'])
@login_required
@permission_required('manage_collections')
def api_add_payment(col_id):
    data = request.get_json() or {}
    try:
        c = Collection.query.get_or_404(col_id)
        amount = float(data.get('amount', 0))
        method = data.get('method') or 'cash'
        reference = data.get('reference')
        p = Payment(collection_id=c.id, amount=amount, payment_method=method, reference_id=reference, received_by=getattr(current_user,'username',None))
        db.session.add(p)
        # update collection totals
        c.paid_amount = (c.paid_amount or 0) + amount
        c.balance = max(0, c.total_amount - c.paid_amount)
        if c.balance <= 0:
            c.status = 'paid'
        else:
            c.status = 'partial'
        # create corresponding transaction for accounting
        t = Transaction(transaction_type='income', amount=amount, category='collection', description=f'payment for collection {c.id}', recorded_by=getattr(current_user,'username',None))
        db.session.add(t)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='create', object_type='payment', object_id=p.id, details=f'payment {amount} for collection {c.id}')
        db.session.add(log)
        db.session.commit()
        return jsonify({'id': p.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/collection/summary', methods=['GET'])
@login_required
@permission_required('view_collections')
def api_collection_summary():
    try:
        collected = db.session.query(db.func.coalesce(db.func.sum(Collection.paid_amount), 0)).scalar() or 0
        outstanding = db.session.query(db.func.coalesce(db.func.sum(Collection.balance), 0)).scalar() or 0
        return jsonify({'collected': float(collected), 'outstanding': float(outstanding)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


### Invoicing
@admin_bp.route('/api/invoices', methods=['GET'])
@login_required
@permission_required('view_accounting')
def api_get_invoices():
    try:
        invs = Invoice.query.order_by(Invoice.id.desc()).all()
        user_currency = current_user.currency
        rates = current_app.config.get('EXCHANGE_RATES', {})
        out = []
        for i in invs:
            out.append({'id': i.id, 'invoice_number': i.invoice_number, 'customer': i.customer_name, 'total': convert_currency(i.total, 'USD', user_currency, rates), 'status': i.status, 'issued_at': i.issued_at.isoformat() if i.issued_at else None})
        return jsonify(out)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/invoices', methods=['POST'])
@login_required
@permission_required('manage_accounting')
def api_create_invoice():
    data = request.get_json() or {}
    try:
        # Allow creating from collection or order
        collection_id = data.get('collection_id')
        order_id = data.get('order_id')
        customer = data.get('customer')
        phone = data.get('phone')
        items = data.get('items') or ''
        total = float(data.get('total', 0))
        # generate invoice number - more unique (include milliseconds)
        import time
        ms = int((time.time() % 1) * 10000)
        num = f"INV-{int(datetime.now(timezone.utc).timestamp())}-{ms}"
        inv = Invoice(invoice_number=num, order_id=order_id, collection_id=collection_id, customer_name=customer, customer_phone=phone, items=items, total=total, status='issued', issued_at=datetime.now(timezone.utc))
        db.session.add(inv)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='create', object_type='invoice', object_id=inv.id, details=f'created invoice {inv.invoice_number}')
        db.session.add(log)
        db.session.commit()
        return jsonify({'id': inv.id, 'invoice_number': inv.invoice_number}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/invoices/<int:inv_id>', methods=['GET'])
@login_required
@permission_required('view_accounting')
def api_get_invoice(inv_id):
    try:
        i = Invoice.query.get_or_404(inv_id)
        return jsonify({'id': i.id, 'invoice_number': i.invoice_number, 'customer': i.customer_name, 'phone': i.customer_phone, 'items': i.items, 'total': i.total, 'status': i.status, 'issued_at': i.issued_at.isoformat() if i.issued_at else None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/invoices/<int:inv_id>/mark-paid', methods=['PUT'])
@login_required
@permission_required('manage_accounting')
def api_mark_invoice_paid(inv_id):
    try:
        i = Invoice.query.get_or_404(inv_id)
        i.status = 'paid'
        i.paid_at = datetime.now(timezone.utc)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='update', object_type='invoice', object_id=i.id, details=f'marked invoice {i.invoice_number} as paid')
        db.session.add(log)
        db.session.commit()
        return jsonify({'status':'paid'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/invoices/<int:inv_id>', methods=['DELETE'])
@login_required
@permission_required('manage_accounting')
def api_delete_invoice(inv_id):
    try:
        i = Invoice.query.get_or_404(inv_id)
        num = i.invoice_number
        db.session.delete(i)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='delete', object_type='invoice', object_id=inv_id, details=f'deleted invoice {num}')
        db.session.add(log)
        db.session.commit()
        return jsonify({'status':'deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/invoices/<int:inv_id>/print', methods=['GET'])
@login_required
@permission_required('view_accounting')
def print_invoice(inv_id):
    try:
        i = Invoice.query.get_or_404(inv_id)
        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Invoice {i.invoice_number}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    .header {{ text-align: center; margin-bottom: 30px; }}
    .logo {{ font-size: 24px; font-weight: bold; color: #d32f2f; }}
    .invoice-number {{ font-size: 14px; margin-top: 10px; }}
    .details {{ margin: 20px 0; }}
    .details-row {{ display: flex; justify-content: space-between; margin: 8px 0; }}
    .label {{ font-weight: bold; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
    th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
    th {{ background-color: #f5f5f5; font-weight: bold; }}
    .total-row {{ font-weight: bold; font-size: 16px; background-color: #f5f5f5; }}
    .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #666; }}
    .status {{ display: inline-block; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
    .status-paid {{ background-color: #4caf50; color: white; }}
    .status-issued {{ background-color: #ff9800; color: white; }}
    .status-draft {{ background-color: #ccc; color: #333; }}
  </style>
</head>
<body>
  <div class="header">
    <div class="logo">Gaatha POS</div>
    <div class="invoice-number">Invoice: {i.invoice_number}</div>
    <div class="status status-{i.status}">{i.status.upper()}</div>
  </div>

  <div class="details">
    <div class="details-row">
      <div><span class="label">Customer:</span> {i.customer_name or 'N/A'}</div>
      <div><span class="label">Phone:</span> {i.customer_phone or 'N/A'}</div>
    </div>
    <div class="details-row">
      <div><span class="label">Issued:</span> {i.issued_at.strftime('%Y-%m-%d %H:%M') if i.issued_at else 'N/A'}</div>
      <div><span class="label">Paid:</span> {i.paid_at.strftime('%Y-%m-%d %H:%M') if i.paid_at else 'Pending'}</div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Description</th>
        <th>Amount</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>{i.items or 'Services'}</td>
        <td>{i.total:.2f}</td>
      </tr>
      <tr class="total-row">
        <td>TOTAL</td>
        <td>{i.total:.2f}</td>
      </tr>
    </tbody>
  </table>

  <div class="footer">
    <p>Thank you for your business!</p>
    <p>Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}</p>
  </div>
</body>
</html>"""
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@admin_bp.route('/api/users/<int:user_id>/password', methods=['PUT'])
@login_required
@permission_required('manage_users')
def api_reset_password(user_id):
    data = request.get_json() or {}
    try:
        newpw = data.get('password')
        if not newpw:
            return jsonify({'error':'password required'}), 400
        u = _user_in_current_restaurant(user_id)
        if u is None:
            return jsonify({'error': 'User not found'}), 404
        u.password_hash = generate_password_hash(newpw)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='reset_password', object_type='user', object_id=u.id, details='password reset')
        db.session.add(log)
        db.session.commit()
        return jsonify({'status':'ok'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@permission_required('manage_users')
def api_delete_user(user_id):
    try:
        u = _user_in_current_restaurant(user_id)
        if u is None:
            return jsonify({'error': 'User not found'}), 404
        if u.id == current_user.id:
            return jsonify({'error': 'Cannot delete the current user'}), 400
        username = u.username
        db.session.delete(u)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='delete', object_type='user', object_id=user_id, details=f'deleted {username}')
        db.session.add(log)
        db.session.commit()
        return jsonify({'status':'deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/menu/<int:item_id>', methods=['GET'])
@login_required
@permission_required('manage_menu')
def api_get_menu_item(item_id):
    try:
        i = _menu_item_for_current_restaurant(item_id)
        if i is None:
            return jsonify({'error': 'Menu item not found'}), 404
        return jsonify({
            'id': i.id,
            'name': i.name,
            'description': i.description,
            'price': i.price,
            'available': i.available
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route("/api/menu", methods=["POST"])
@login_required
@permission_required('manage_menu')
def api_create_menu():
    data = request.get_json() or {}
    try:
        name = data.get("name")
        price = float(data.get("price", 0))
        description = data.get("description")
        available = bool(data.get("available", True))
        if not name:
            return jsonify({"error": "name is required"}), 400
        restaurant_id = None if getattr(current_user, "is_super_admin", False) else current_user.restaurant_id
        item = MenuItem(
            name=name,
            description=description,
            price=price,
            available=available,
            restaurant_id=restaurant_id,
        )
        db.session.add(item)
        db.session.commit()
        # audit
        log = AuditLog(user_id=getattr(current_user, 'id', None), username=getattr(current_user, 'username', None), action='create', object_type='menu_item', object_id=item.id, details=f'created {item.name}')
        db.session.add(log)
        db.session.commit()
        return jsonify({"id": item.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/api/menu/<int:item_id>", methods=["PUT"])
@login_required
@permission_required('manage_menu')
def api_update_menu(item_id):
    data = request.get_json() or {}
    try:
        item = _menu_item_for_current_restaurant(item_id)
        if item is None:
            return jsonify({'error': 'Menu item not found'}), 404
        changed = []
        if "name" in data and data.get("name")!=item.name:
            changed.append(f'name: {item.name} -> {data.get("name")}')
            item.name = data.get("name")
        if "description" in data and data.get("description")!=item.description:
            changed.append('description updated')
            item.description = data.get("description")
        if "price" in data:
            new_price = float(data.get("price"))
            if new_price != item.price:
                # record price history
                ph = PriceHistory(menu_item_id=item.id, old_price=item.price, new_price=new_price, changed_by=getattr(current_user,'username',None))
                db.session.add(ph)
                changed.append(f'price: {item.price} -> {new_price}')
                item.price = new_price
        if "available" in data and bool(data.get("available")) != item.available:
            changed.append(f'available: {item.available} -> {data.get("available")}')
            item.available = bool(data.get("available"))
        db.session.commit()
        # audit
        if changed:
            log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='update', object_type='menu_item', object_id=item.id, details='; '.join(changed))
            db.session.add(log)
            db.session.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/api/menu/<int:item_id>", methods=["DELETE"])
@login_required
@permission_required('manage_menu')
def api_delete_menu(item_id):
    try:
        item = _menu_item_for_current_restaurant(item_id)
        if item is None:
            return jsonify({'error': 'Menu item not found'}), 404
        name = item.name
        db.session.delete(item)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='delete', object_type='menu_item', object_id=item_id, details=f'deleted {name}')
        db.session.add(log)
        db.session.commit()
        return jsonify({"status": "deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/api/menu/<int:item_id>/history', methods=['GET'])
@login_required
@permission_required('manage_menu')
def api_menu_history(item_id):
    try:
        rows = PriceHistory.query.filter_by(menu_item_id=item_id).order_by(PriceHistory.changed_at.desc()).limit(50).all()
        return jsonify([{"old_price": r.old_price, "new_price": r.new_price, "changed_by": r.changed_by, "changed_at": r.changed_at.isoformat()} for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/api/inventory/<int:item_id>', methods=['GET'])
@login_required
@permission_required('manage_inventory')
def api_get_inventory_item(item_id):
    try:
        i = get_inventory_item(item_id, current_user.restaurant_id)
        if i is None:
            return jsonify({'error': 'Inventory item not found'}), 404
        return jsonify({
            'id': i.id,
            'name': i.name,
            'quantity': i.quantity,
            'unit': i.unit,
            'updated_at': i.updated_at.isoformat() if i.updated_at else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/menu/import', methods=['POST'])
@login_required
@permission_required('manage_menu')
def api_menu_import():
    try:
        restaurant_id = None if getattr(current_user, "is_super_admin", False) else current_user.restaurant_id
        f = request.files.get('file')
        if not f:
            return jsonify({'error':'file required'}), 400
        stream = io.StringIO(f.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        created = []
        results = []
        row_no = 0
        for row in reader:
            row_no += 1
            name = row.get('name') or row.get('Name')
            if not name:
                results.append({'row': row_no, 'status': 'skipped', 'reason': 'missing name'})
                continue
            try:
                price = float(row.get('price') or row.get('Price') or 0)
            except Exception:
                results.append({'row': row_no, 'status': 'error', 'reason': 'invalid price'})
                continue
            description = row.get('description') or row.get('Description')
            available = True
            try:
                item = MenuItem(
                    name=name,
                    price=price,
                    description=description,
                    available=available,
                    restaurant_id=restaurant_id,
                )
                db.session.add(item)
                db.session.flush()
                created.append(item.id)
                results.append({'row': row_no, 'status': 'created', 'id': item.id})
            except Exception as e:
                db.session.rollback()
                results.append({'row': row_no, 'status': 'error', 'reason': str(e)})
        db.session.commit()
        # audit
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='import', object_type='menu_item', object_id=None, details=f'imported {len(created)} items')
        db.session.add(log)
        db.session.commit()
        return jsonify({'created': created, 'results': results}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/menu/export', methods=['GET'])
@login_required
@permission_required('manage_menu')
def api_menu_export():
    try:
        query = MenuItem.query
        if not getattr(current_user, "is_super_admin", False):
            if current_user.restaurant_id is None:
                query = query.filter(MenuItem.restaurant_id.is_(None))
            else:
                query = query.filter_by(restaurant_id=current_user.restaurant_id)
        items = query.all()
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['id','name','description','price','available'])
        for i in items:
            writer.writerow([i.id,i.name,i.description or '',i.price,i.available])
        si.seek(0)
        return send_file(io.BytesIO(si.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='menu_export.csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/menu/template', methods=['GET'])
@login_required
@permission_required('manage_menu')
def api_menu_template():
    try:
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['name','price','description'])
        si.seek(0)
        return send_file(io.BytesIO(si.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='menu_template.csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


### Inventory management API
@admin_bp.route("/api/inventory", methods=["GET"])
@login_required
@permission_required('manage_inventory')
def api_get_inventory():
    """
    Get paginated, sorted, and searchable inventory items.
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 15, type=int)
        search = request.args.get('search', '', type=str)
        sort_by = request.args.get('sort_by', 'name', type=str)
        sort_dir = request.args.get('sort_dir', 'asc', type=str)

        query = InventoryItem.query.filter_by(restaurant_id=current_user.restaurant_id)

        if search:
            query = query.filter(InventoryItem.name.ilike(f'%{search}%'))

        sort_column = getattr(InventoryItem, sort_by, InventoryItem.name)
        if sort_dir == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        paginated_items = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "items": [{
                "id": i.id, "name": i.name, "quantity": i.quantity, "unit": i.unit,
                "low_stock_threshold": i.low_stock_threshold,
                "updated_at": i.updated_at.isoformat() if i.updated_at else None
            } for i in paginated_items.items],
            "pagination": {
                "page": paginated_items.page, "per_page": paginated_items.per_page,
                "total_pages": paginated_items.pages, "total_items": paginated_items.total,
                "has_next": paginated_items.has_next, "has_prev": paginated_items.has_prev
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/api/inventory", methods=["POST"])
@login_required
@permission_required('manage_inventory')
def api_create_inventory():
    data = request.get_json() or {}
    try:
        name = data.get("name")
        quantity = validate_quantity(data.get("quantity", 0))
        unit = data.get("unit", "unit")
        if not name:
            return jsonify({"error": "name is required"}), 400
        if current_user.restaurant_id is None:
            return jsonify({"error": "restaurant context is required"}), 400
        item = InventoryItem(
            name=name,
            quantity=quantity,
            unit=unit,
            restaurant_id=current_user.restaurant_id,
        )
        db.session.add(item)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='create', object_type='inventory_item', object_id=item.id, details=f'created {item.name}')
        db.session.add(log)
        db.session.commit()
        return jsonify({"id": item.id}), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/api/inventory/<int:item_id>", methods=["PUT"])
@login_required
@permission_required('manage_inventory')
def api_update_inventory(item_id):
    data = request.get_json() or {}
    try:
        item = get_inventory_item(item_id, current_user.restaurant_id)
        if item is None:
            return jsonify({"error": "Inventory item not found"}), 404
        changes = []
        if "name" in data and data.get("name")!=item.name:
            changes.append(f'name: {item.name} -> {data.get("name")}')
            item.name = data.get("name")
        if "quantity" in data and int(data.get("quantity"))!=item.quantity:
            quantity = validate_quantity(data.get("quantity"))
            changes.append(f'quantity: {item.quantity} -> {quantity}')
            item.quantity = quantity
        if "unit" in data and data.get("unit")!=item.unit:
            changes.append(f'unit: {item.unit} -> {data.get("unit")}')
            item.unit = data.get("unit")
        db.session.commit()
        if changes:
            log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='update', object_type='inventory_item', object_id=item.id, details='; '.join(changes))
            db.session.add(log)
            db.session.commit()
        return jsonify({"status": "ok"})
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/api/inventory/<int:item_id>", methods=["DELETE"])
@login_required
@permission_required('manage_inventory')
def api_delete_inventory(item_id):
    try:
        item = get_inventory_item(item_id, current_user.restaurant_id)
        if item is None:
            return jsonify({"error": "Inventory item not found"}), 404
        name = item.name
        db.session.delete(item)
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='delete', object_type='inventory_item', object_id=item_id, details=f'deleted {name}')
        db.session.add(log)
        db.session.commit()
        return jsonify({"status": "deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/api/inventory/import', methods=['POST'])
@login_required
@permission_required('manage_inventory')
def api_inventory_import():
    try:
        if current_user.restaurant_id is None:
            return jsonify({'error': 'restaurant context is required'}), 400
        f = request.files.get('file')
        if not f:
            return jsonify({'error':'file required'}), 400
        stream = io.StringIO(f.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        created = []
        results = []
        row_no = 0
        for row in reader:
            row_no += 1
            name = row.get('name') or row.get('Name')
            if not name:
                results.append({'row': row_no, 'status': 'skipped', 'reason': 'missing name'})
                continue
            try:
                quantity = int(float(row.get('quantity') or row.get('Quantity') or 0))
            except Exception:
                results.append({'row': row_no, 'status': 'error', 'reason': 'invalid quantity'})
                continue
            unit = row.get('unit') or row.get('Unit') or 'unit'
            try:
                if quantity < 0:
                    raise ValueError('quantity cannot be negative')
                item = InventoryItem(
                    name=name,
                    quantity=quantity,
                    unit=unit,
                    restaurant_id=current_user.restaurant_id,
                )
                db.session.add(item)
                db.session.flush()
                created.append(item.id)
                results.append({'row': row_no, 'status': 'created', 'id': item.id})
            except Exception as e:
                db.session.rollback()
                results.append({'row': row_no, 'status': 'error', 'reason': str(e)})
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='import', object_type='inventory_item', object_id=None, details=f'imported {len(created)} items')
        db.session.add(log)
        db.session.commit()
        return jsonify({'created': created, 'results': results}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/inventory/export', methods=['GET'])
@login_required
@permission_required('manage_inventory')
def api_inventory_export():
    try:
        items = InventoryItem.query.filter_by(
            restaurant_id=current_user.restaurant_id
        ).all()
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['id','name','quantity','unit','updated_at'])
        for i in items:
            writer.writerow([i.id,i.name,i.quantity,i.unit,i.updated_at.isoformat() if i.updated_at else ''])
        si.seek(0)
        return send_file(io.BytesIO(si.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='inventory_export.csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/inventory/template', methods=['GET'])
@login_required
@permission_required('manage_inventory')
def api_inventory_template():
    try:
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['name','quantity','unit'])
        si.seek(0)
        return send_file(io.BytesIO(si.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='inventory_template.csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/logs', methods=['GET'])
@login_required
@admin_required
def api_get_logs():
    try:
        # allow optional filtering: user, action, object_type
        q = AuditLog.query
        if not getattr(current_user, "is_super_admin", False):
            if current_user.restaurant_id is None:
                q = q.filter(AuditLog.user_id == current_user.id)
            else:
                restaurant_user_ids = [u.id for u in _users_in_current_restaurant().all()]
                if not restaurant_user_ids:
                    return jsonify([])
                q = q.filter(AuditLog.user_id.in_(restaurant_user_ids))
        user = request.args.get('user')
        action = request.args.get('action')
        object_type = request.args.get('object_type')
        if user:
            q = q.filter(AuditLog.username == user)
        if action:
            q = q.filter(AuditLog.action == action)
        if object_type:
            q = q.filter(AuditLog.object_type == object_type)
        rows = q.order_by(AuditLog.created_at.desc()).limit(200).all()
        return jsonify([{"id": r.id, "user_id": r.user_id, "username": r.username, "action": r.action, "object_type": r.object_type, "object_id": r.object_id, "details": r.details, "created_at": r.created_at.isoformat()} for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


### Role permissions
@admin_bp.route('/api/roles', methods=['GET'])
@login_required
@admin_required
def api_get_roles():
    try:
        # define canonical roles and permissions
        roles = ['admin', 'manager', 'waiter', 'kitchen']
        permissions = ['manage_menu', 'manage_inventory', 'manage_users', 'view_logs', 'manage_orders', 'view_analytics', 'view_accounting', 'manage_accounting', 'view_collections', 'manage_collections']
        # defaults when creating missing rows
        defaults = {
            'admin': {p: True for p in permissions},
            'manager': { 'manage_menu': True, 'manage_inventory': True, 'manage_users': False, 'view_logs': True, 'manage_orders': True, 'view_analytics': True, 'view_accounting': True, 'manage_accounting': True, 'view_collections': True, 'manage_collections': True },
            'waiter': { 'manage_menu': False, 'manage_inventory': False, 'manage_users': False, 'view_logs': False, 'manage_orders': True, 'view_analytics': False, 'view_accounting': False, 'manage_accounting': False, 'view_collections': False, 'manage_collections': False },
            'kitchen': { 'manage_menu': False, 'manage_inventory': False, 'manage_users': False, 'view_logs': False, 'manage_orders': True, 'view_analytics': False, 'view_accounting': False, 'manage_accounting': False, 'view_collections': False, 'manage_collections': False }
        }

        out = {}
        for role in roles:
            out[role] = {}
            for perm in permissions:
                rp = RolePermission.query.filter_by(role=role, permission=perm).first()
                if not rp:
                    # create default if missing
                    allowed = defaults.get(role, {}).get(perm, False)
                    rp = RolePermission(role=role, permission=perm, allowed=allowed)
                    db.session.add(rp)
                    db.session.flush()
                out[role][perm] = bool(rp.allowed)
        db.session.commit()
        return jsonify({'roles': out, 'permissions': permissions})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/roles', methods=['PUT'])
@login_required
@admin_required
def api_update_role():
    data = request.get_json() or {}
    try:
        role = data.get('role')
        perms = data.get('permissions') or {}
        if not role:
            return jsonify({'error':'role required'}), 400
        changed = []
        for perm, allowed in perms.items():
            rp = RolePermission.query.filter_by(role=role, permission=perm).first()
            if not rp:
                rp = RolePermission(role=role, permission=perm, allowed=bool(allowed))
                db.session.add(rp)
                changed.append(f'created {perm}={allowed}')
            else:
                if bool(rp.allowed) != bool(allowed):
                    changed.append(f'{perm}: {rp.allowed} -> {allowed}')
                    rp.allowed = bool(allowed)
        db.session.commit()
        if changed:
            log = AuditLog(user_id=getattr(current_user,'id',None), username=getattr(current_user,'username',None), action='update', object_type='role_permissions', object_id=None, details=f'{role}: ' + '; '.join(changed))
            db.session.add(log)
            db.session.commit()
        return jsonify({'status':'ok'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>/currency', methods=['PUT'])
@login_required
@permission_required('manage_users')
def set_user_currency(user_id):
    """Update user's currency preference"""
    try:
        user = _user_in_current_restaurant(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        new_currency = data.get('currency', '').upper()
        
        if not new_currency or len(new_currency) != 3:
            return jsonify({'error': 'Invalid currency code'}), 400
        
        supported_currencies = ['USD', 'EUR', 'GBP', 'INR', 'RON', 'CAD', 'AUD', 'JPY', 'CNY', 'AED']
        if new_currency not in supported_currencies:
            return jsonify({'error': f'Unsupported currency. Supported: {", ".join(supported_currencies)}'}), 400
        
        old_currency = user.currency
        user.currency = new_currency
        db.session.commit()
        
        log = AuditLog(
            user_id=getattr(current_user, 'id', None),
            username=getattr(current_user, 'username', None),
            action='update',
            object_type='user_currency',
            object_id=user_id,
            details=f'Currency changed from {old_currency} to {new_currency}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'status': 'ok', 'message': f'Currency updated to {new_currency}', 'currency': new_currency})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/users/<int:user_id>/locale', methods=['PUT'])
@login_required
@permission_required('manage_users')
def set_user_locale(user_id):
    """Update user's locale/language preference"""
    try:
        user = _user_in_current_restaurant(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        data = request.get_json() or {}
        new_locale = (data.get('locale') or '').strip()
        if not new_locale:
            return jsonify({'error': 'Invalid locale'}), 400
        supported = current_app.config.get('LANGUAGES', ['en'])
        if new_locale not in supported:
            return jsonify({'error': f'Unsupported locale. Supported: {", ".join(supported)}'}), 400
        old = user.locale
        user.locale = new_locale
        db.session.commit()
        log = AuditLog(user_id=getattr(current_user, 'id', None), username=getattr(current_user, 'username', None), action='update', object_type='user_locale', object_id=user_id, details=f'Locale changed from {old} to {new_locale}')
        db.session.add(log)
        db.session.commit()
        return jsonify({'status': 'ok', 'locale': new_locale})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/exchange-rates', methods=['GET'])
@login_required
@permission_required('view_accounting')
def api_get_exchange_rates():
    try:
        rates = current_app.config.get('EXCHANGE_RATES', {})
        last = current_app.config.get('EXCHANGE_RATES_LAST_UPDATED')
        return jsonify({'rates': rates, 'last_updated': last})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/exchange-rates/update', methods=['POST'])
@login_required
@permission_required('manage_accounting')
def api_update_exchange_rates():
    try:
        # Trigger immediate update
        from extensions import update_exchange_rates
        rates = update_exchange_rates(current_app)
        return jsonify({'rates': rates}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ======================== Restaurant Management ========================

@admin_bp.route('/api/restaurants', methods=['GET'])
@login_required
def api_list_restaurants():
    """List restaurants. Super admin sees all; restaurant admin sees their own."""
    try:
        if current_user.is_super_admin:
            restaurants = Restaurant.query.all()
        elif current_user.role == 'restaurant_admin':
            restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()
        else:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({
            'restaurants': [{
                'id': r.id,
                'name': r.name,
                'email': r.email,
                'phone': r.phone,
                'address': r.address,
                'city': r.city,
                'country': r.country,
                'postal_code': r.postal_code,
                'owner_id': r.owner_id,
                'active': r.active,
                'created_at': r.created_at.isoformat(),
                'updated_at': r.updated_at.isoformat()
            } for r in restaurants]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/restaurants', methods=['POST'])
@login_required
def api_create_restaurant():
    """Create a new restaurant. Only super admin."""
    try:
        if not current_user.is_super_admin:
            return jsonify({'error': 'Only super admin can create restaurants'}), 403
        
        data = request.get_json()
        required = ['name', 'email', 'owner_id']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        owner = db.session.get(User, data['owner_id'])
        if not owner:
            return jsonify({'error': 'Owner user not found'}), 404
        
        restaurant = Restaurant(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            country=data.get('country'),
            postal_code=data.get('postal_code'),
            owner_id=data['owner_id'],
            active=data.get('active', True)
        )
        db.session.add(restaurant)
        
        # Create default StoreSettings for the restaurant
        store_settings = StoreSettings(
            restaurant_id=restaurant.id,
            timezone=data.get('timezone', 'UTC'),
            locale=data.get('locale', 'en'),
            currency=data.get('currency', 'USD'),
            tax_region=data.get('tax_region', 'EU')
        )
        db.session.add(store_settings)
        
        db.session.commit()
        
        log = AuditLog(
            user_id=current_user.id,
            username=current_user.username,
            action='create',
            object_type='restaurant',
            object_id=restaurant.id,
            details=f'Created restaurant: {restaurant.name}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'id': restaurant.id,
            'name': restaurant.name,
            'email': restaurant.email,
            'created_at': restaurant.created_at.isoformat()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/restaurants/<int:restaurant_id>', methods=['GET'])
@login_required
def api_get_restaurant(restaurant_id):
    """Get restaurant details. Super admin sees all; restaurant admin sees only their own."""
    try:
        restaurant = db.session.get(Restaurant, restaurant_id)
        if not restaurant:
            return jsonify({'error': 'Restaurant not found'}), 404
        
        if not current_user.is_super_admin and current_user.id != restaurant.owner_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({
            'id': restaurant.id,
            'name': restaurant.name,
            'email': restaurant.email,
            'phone': restaurant.phone,
            'address': restaurant.address,
            'city': restaurant.city,
            'country': restaurant.country,
            'postal_code': restaurant.postal_code,
            'owner_id': restaurant.owner_id,
            'active': restaurant.active,
            'created_at': restaurant.created_at.isoformat(),
            'updated_at': restaurant.updated_at.isoformat(),
            'store_settings': {
                'id': restaurant.store_settings.id,
                'timezone': restaurant.store_settings.timezone,
                'locale': restaurant.store_settings.locale,
                'currency': restaurant.store_settings.currency,
                'tax_region': restaurant.store_settings.tax_region,
                'address_format': restaurant.store_settings.address_format,
                'business_registration': restaurant.store_settings.business_registration,
                'vat_number': restaurant.store_settings.vat_number,
                'payment_terms': restaurant.store_settings.payment_terms,
                'invoice_prefix': restaurant.store_settings.invoice_prefix
            } if restaurant.store_settings else None
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/restaurants/<int:restaurant_id>', methods=['PUT'])
@login_required
def api_update_restaurant(restaurant_id):
    """Update restaurant details. Restaurant admin updates own; super admin updates any."""
    try:
        restaurant = db.session.get(Restaurant, restaurant_id)
        if not restaurant:
            return jsonify({'error': 'Restaurant not found'}), 404
        
        if not current_user.is_super_admin and current_user.id != restaurant.owner_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if 'name' in data:
            restaurant.name = data['name']
        if 'email' in data:
            restaurant.email = data['email']
        if 'phone' in data:
            restaurant.phone = data['phone']
        if 'address' in data:
            restaurant.address = data['address']
        if 'city' in data:
            restaurant.city = data['city']
        if 'country' in data:
            restaurant.country = data['country']
        if 'postal_code' in data:
            restaurant.postal_code = data['postal_code']
        if 'active' in data and current_user.is_super_admin:
            restaurant.active = data['active']
        
        restaurant.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        log = AuditLog(
            user_id=current_user.id,
            username=current_user.username,
            action='update',
            object_type='restaurant',
            object_id=restaurant.id,
            details=f'Updated restaurant: {restaurant.name}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'status': 'ok', 'id': restaurant.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/restaurants/<int:restaurant_id>/store-settings', methods=['GET'])
@login_required
def api_get_store_settings(restaurant_id):
    """Get store settings for a restaurant."""
    try:
        restaurant = db.session.get(Restaurant, restaurant_id)
        if not restaurant:
            return jsonify({'error': 'Restaurant not found'}), 404
        
        if not current_user.is_super_admin and current_user.id != restaurant.owner_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if not restaurant.store_settings:
            return jsonify({'error': 'Store settings not found'}), 404
        
        settings = restaurant.store_settings
        return jsonify({
            'id': settings.id,
            'restaurant_id': settings.restaurant_id,
            'timezone': settings.timezone,
            'locale': settings.locale,
            'currency': settings.currency,
            'tax_region': settings.tax_region,
            'address_format': settings.address_format,
            'business_registration': settings.business_registration,
            'vat_number': settings.vat_number,
            'payment_terms': settings.payment_terms,
            'invoice_prefix': settings.invoice_prefix,
            'created_at': settings.created_at.isoformat(),
            'updated_at': settings.updated_at.isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/restaurants/<int:restaurant_id>/store-settings', methods=['PUT'])
@login_required
def api_update_store_settings(restaurant_id):
    """Update store settings for a restaurant."""
    try:
        restaurant = db.session.get(Restaurant, restaurant_id)
        if not restaurant:
            return jsonify({'error': 'Restaurant not found'}), 404
        
        if not current_user.is_super_admin and current_user.id != restaurant.owner_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        settings = restaurant.store_settings
        if not settings:
            return jsonify({'error': 'Store settings not found'}), 404
        
        data = request.get_json()
        
        if 'timezone' in data:
            settings.timezone = data['timezone']
        if 'locale' in data:
            settings.locale = data['locale']
        if 'currency' in data:
            settings.currency = data['currency']
        if 'tax_region' in data:
            settings.tax_region = data['tax_region']
        if 'address_format' in data:
            settings.address_format = data['address_format']
        if 'business_registration' in data:
            settings.business_registration = data['business_registration']
        if 'vat_number' in data:
            settings.vat_number = data['vat_number']
        if 'payment_terms' in data:
            settings.payment_terms = data['payment_terms']
        if 'invoice_prefix' in data:
            settings.invoice_prefix = data['invoice_prefix']
        
        settings.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        log = AuditLog(
            user_id=current_user.id,
            username=current_user.username,
            action='update',
            object_type='store_settings',
            object_id=settings.id,
            details=f'Updated store settings for restaurant {restaurant.name}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'status': 'ok', 'id': settings.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
