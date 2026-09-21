import os
import sys
sys.path.insert(0, os.path.abspath('.'))
os.environ['ENABLE_EXCHANGE_UPDATER'] = 'False'
from app import create_app
from extensions import db
from werkzeug.security import generate_password_hash
from models import User

app = create_app()
with app.app_context():
    db.create_all()
    u = User.query.filter_by(username='admin').first()
    if not u:
        u = User(username='admin', password_hash=generate_password_hash('admin'), role='admin')
        db.session.add(u)
        db.session.commit()
        print('Seeded admin/admin')

    client = app.test_client()
    # Get login page first to obtain CSRF token
    resp_get = client.get('/auth/login')
    html = resp_get.get_data(as_text=True)
    # Rudimentary extraction of csrf token
    import re
    m = re.search(r"name=\"csrf_token\" value=\"([^\"]+)\"", html)
    csrf = m.group(1) if m else None
    print('Found csrf:', bool(csrf))

    data = {'username': 'admin', 'password': 'admin'}
    if csrf:
        data['csrf_token'] = csrf
    resp = client.post('/auth/login', data=data, follow_redirects=True)
    print('POST status:', resp.status_code)
    print('Final URL:', resp.request.path)
    print('Response snippet:')
    print(resp.get_data(as_text=True)[:2000])
