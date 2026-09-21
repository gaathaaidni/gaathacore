"""
Role-Based Access Control (RBAC) middleware and decorators.
Provides role checking and permission enforcement for protected routes.
"""
from flask import request, abort, jsonify, current_app
from functools import wraps
from typing import Callable, List, Optional
from flask_login import current_user


class RBACError(Exception):
    """Raised when RBAC check fails."""
    pass


def require_role(*roles: str) -> Callable:
    """
    Decorator to enforce role-based access control.
    
    Usage:
        @bp.route('/admin')
        @require_role('admin', 'superadmin')
        def admin_only():
            return "Admin only content"
    
    Args:
        roles: Required roles (user must have at least one)
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required'}), 401
                abort(401)
            
            # Check if user has required role
            user_role = getattr(current_user, 'role', None)
            if user_role not in roles:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': f'Required role(s): {", ".join(roles)}'}), 403
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_permission(permission: str) -> Callable:
    """
    Decorator to enforce permission-based access control.
    
    Usage:
        @bp.route('/customers/delete')
        @require_permission('crm.delete_customer')
        def delete_customer():
            return "Customer deleted"
    
    Args:
        permission: Required permission string (e.g., 'crm.delete_customer')
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required'}), 401
                abort(401)
            
            # Check if user has permission
            user_permissions = getattr(current_user, 'permissions', [])
            if permission not in user_permissions:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': f'Permission denied: {permission}'}), 403
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_role(*roles: str) -> bool:
    """
    Check if current user has one of the specified roles.
    
    Args:
        roles: Roles to check
        
    Returns:
        True if user has at least one role, False otherwise
    """
    if not current_user.is_authenticated:
        return False
    
    user_role = getattr(current_user, 'role', None)
    return user_role in roles


def check_permission(permission: str) -> bool:
    """
    Check if current user has a specific permission.
    
    Args:
        permission: Permission to check
        
    Returns:
        True if user has permission, False otherwise
    """
    if not current_user.is_authenticated:
        return False
    
    user_permissions = getattr(current_user, 'permissions', [])
    return permission in user_permissions


def get_user_permissions() -> List[str]:
    """
    Get list of permissions for current user.
    
    Returns:
        List of permission strings
    """
    if not current_user.is_authenticated:
        return []
    
    return getattr(current_user, 'permissions', [])


# Sample role and permission definitions
ROLE_DEFINITIONS = {
    'superadmin': ['*'],  # All permissions
    'admin': [
        'crm.create',
        'crm.read',
        'crm.update',
        'crm.delete',
        'books.read',
        'books.write',
        'inventory.read',
        'inventory.write',
        'users.manage',
    ],
    'manager': [
        'crm.create',
        'crm.read',
        'crm.update',
        'books.read',
        'inventory.read',
        'inventory.write',
    ],
    'user': [
        'crm.read',
        'books.read',
        'inventory.read',
    ],
}
