import sys, os
sys.path.insert(0, os.path.abspath('.'))
# Use an in-memory SQLite database for tests to avoid filesystem permissions / missing instance dir issues
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
from app import create_app
from extensions import db
from werkzeug.security import generate_password_hash
from models import User

app = create_app()

with app.app_context():
    db.create_all()
    # Ensure test users
    for uname, pw, role in [('waiter','waiter','waiter'), ('admin','admin','admin'), ('manager','manager','manager'), ('kitchen','kitchen','kitchen')]:
        u = User.query.filter_by(username=uname).first()
        if not u:
            u = User(username=uname, password_hash=generate_password_hash(pw), role=role)
            db.session.add(u)
    db.session.commit()

    client = app.test_client()

    def login(username, password):
        # fetch csrf
        r = client.get('/auth/login')
        import re
        m = re.search(r'name="csrf_token" value="([^"]+)"', r.get_data(as_text=True))
        csrf = m.group(1) if m else None
        data = {'username': username, 'password': password}
        if csrf: data['csrf_token'] = csrf
        return client.post('/auth/login', data=data, follow_redirects=True)

    print('\n-- Testing waiter POS page --')
    r = login('waiter','waiter')
    print('Login status:', r.status_code)
    r2 = client.get('/pos/')
    print('/pos/ ->', r2.status_code)
    print(r2.get_data(as_text=True)[:400])

    print('\n-- Testing manager/admin dashboard --')
    client.get('/auth/logout')
    r = login('manager','manager')
    print('Login manager status:', r.status_code)
    r2 = client.get('/admin/')
    print('/admin/ ->', r2.status_code)
    print(r2.get_data(as_text=True)[:400])

    print('\n-- Testing chef KDS orders API --')
    client.get('/auth/logout')
    r = login('kitchen','kitchen')
    print('Login kitchen status:', r.status_code)
    r2 = client.get('/kds/orders')
    print('/kds/orders ->', r2.status_code)
    print('Response JSON:', r2.get_data(as_text=True)[:400])
