from pathlib import Path

from flask import Flask

from extensions import db
from app import initialize_database
import models
from models import User


def test_initialize_database_creates_expected_tables(tmp_path):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path / 'test.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        initialize_database(app)
        inspector = db.inspect(db.engine)
        assert inspector.has_table("user")
        assert inspector.has_table("order")
        assert inspector.has_table("menu_item")


def test_password_hash_column_is_long_enough_for_werkzeug_hashes():
    assert getattr(User.password_hash.type, "length", None) is not None
    assert User.password_hash.type.length >= 255
