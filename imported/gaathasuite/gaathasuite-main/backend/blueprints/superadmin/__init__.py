from flask import Blueprint

bp = Blueprint('superadmin', __name__, template_folder='templates', url_prefix='/superadmin')

# Expose additional templates path for superadmin
__all__ = ['bp']

from . import routes
