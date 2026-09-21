from flask import Blueprint
kds_bp = Blueprint("kds", __name__, url_prefix="/kds")
from . import routes
