from flask import abort
from flask_login import current_user
from models import RolePermission, AuditLog
from extensions import db
from datetime import datetime
from functools import wraps


def permission_required(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)

            # Check explicit RolePermission if present, otherwise fall back to sensible defaults
            rp = RolePermission.query.filter_by(role=current_user.role, permission=permission).first()
            if rp is not None:
                if not rp.allowed:
                    try:
                        a = AuditLog(user_id=getattr(current_user, 'id', None), username=getattr(current_user, 'username', None), action='forbidden', object_type=permission, object_id=None, details=f'role={current_user.role} denied')
                        db.session.add(a)
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                    abort(403)
                return func(*args, **kwargs)

            # Fallback defaults when RolePermission rows are not yet created
            defaults = {
                'admin': True,
                'manager': True,
                'waiter': permission == 'manage_orders',
                'kitchen': permission == 'manage_orders'
            }
            allowed = defaults.get(current_user.role, False)
            if not allowed:
                try:
                    a = AuditLog(user_id=getattr(current_user, 'id', None), username=getattr(current_user, 'username', None), action='forbidden', object_type=permission, object_id=None, details=f'role={current_user.role} denied (default)')
                    db.session.add(a)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Allow platform and restaurant admins, plus managers
        if not current_user.is_authenticated or current_user.role not in ["admin", "manager", "restaurant_admin", "super_admin"]:
            try:
                a = AuditLog(user_id=getattr(current_user, 'id', None), username=getattr(current_user, 'username', None), action='forbidden', object_type='admin_access', object_id=None, details=f'role={current_user.role} denied admin access')
                db.session.add(a)
                db.session.commit()
            except Exception:
                db.session.rollback()
            abort(403)
        return func(*args, **kwargs)

    return wrapper
