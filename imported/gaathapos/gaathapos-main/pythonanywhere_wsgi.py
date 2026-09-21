"""
WSGI entry point for PythonAnywhere deployment.
This file is loaded by PythonAnywhere's web server.

Place this at: /var/www/username_pythonanywhere_com_wsgi.py
(Replace 'username' with your PythonAnywhere username)
"""

import sys
import os
from pathlib import Path

# Add the project directory to the Python path
project_path = os.path.expanduser('~/nexorapos')
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Activate the virtual environment
activate_this = os.path.expanduser('~/.virtualenvs/nexorapos/bin/activate_this.py')
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(project_path, '.env'))

# Import Flask app
from app import create_app

# Create the Flask application
app = create_app()

# Set Flask app for PythonAnywhere
application = app

# Ensure production settings
application.config['ENV'] = 'production'
application.config['DEBUG'] = False

# Optional: Error handling
@application.errorhandler(404)
def not_found(e):
    return {'error': 'Not found'}, 404

@application.errorhandler(500)
def server_error(e):
    return {'error': 'Server error'}, 500
