import os

from app import create_app


def test_instance_dir_created():
    app = create_app()
    # Use the Flask-provided instance_path for the check
    assert os.path.isdir(app.instance_path), f"instance dir should exist at {app.instance_path}"
