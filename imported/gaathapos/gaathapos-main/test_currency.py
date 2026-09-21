import unittest
from app import create_app
from extensions import db, convert_currency
from models import User, MenuItem, Invoice, Collection, Payment, Transaction
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

class TestCurrencyConversion(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        # Disable CSRF in tests to simplify form submissions
        self.app.config['WTF_CSRF_ENABLED'] = False
        # Use an in-memory database for isolation
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        # Use deterministic exchange rates for tests
        self.app.config['EXCHANGE_RATES'] = {
            'USD': 1.0,
            'EUR': 0.92,
            'GBP': 0.79,
            'INR': 83.12,
            'RON': 4.5,
            'CAD': 1.35,
            'AUD': 1.45,
            'JPY': 110.0,
            'CNY': 7.0,
            'AED': 3.67
        }
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # ensure no leftover test users exist (avoid unique constraint failures)
            for uname in ('user_usd', 'user_eur'):
                existing = User.query.filter_by(username=uname).first()
                if existing:
                    db.session.delete(existing)
            db.session.commit()
            # create some default users used by the tests
            user_usd = User(username='user_usd', password_hash=generate_password_hash('pass'), role='admin', currency='USD')
            user_eur = User(username='user_eur', password_hash=generate_password_hash('pass'), role='admin', currency='EUR')
            db.session.add_all([user_usd, user_eur])
            db.session.commit()

        self.rates = self.app.config.get('EXCHANGE_RATES', {})

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            # Clear rows instead of dropping schema to avoid breaking other tests
            try:
                for table in reversed(db.metadata.sorted_tables):
                    try:
                        db.session.execute(table.delete())
                    except Exception:
                        pass
                db.session.commit()
            except Exception:
                db.session.rollback()
    
    def test_convert_currency_usd_to_eur(self):
        """Test converting USD to EUR"""
        amount = 100.0
        converted = convert_currency(amount, 'USD', 'EUR', self.rates)
        # 100 USD * 0.92 = 92 EUR
        self.assertAlmostEqual(converted, 92.0, places=2)
    
    def test_convert_currency_usd_to_gbp(self):
        """Test converting USD to GBP"""
        amount = 100.0
        converted = convert_currency(amount, 'USD', 'GBP', self.rates)
        # 100 USD * 0.79 = 79 GBP
        self.assertAlmostEqual(converted, 79.0, places=2)
    
    def test_convert_currency_usd_to_inr(self):
        """Test converting USD to INR"""
        amount = 1.0
        converted = convert_currency(amount, 'USD', 'INR', self.rates)
        # 1 USD * 83.12 = 83.12 INR
        self.assertAlmostEqual(converted, 83.12, places=2)
    
    def test_convert_currency_same_currency(self):
        """Test converting to same currency (should return unchanged)"""
        rates = self.app.config.get('EXCHANGE_RATES', {})
        amount = 100.0
        converted = convert_currency(amount, 'USD', 'USD', rates)
        self.assertEqual(converted, 100.0)
    
    def test_convert_currency_cross_currency(self):
        """Test converting between two non-USD currencies (EUR to GBP)"""
        rates = self.app.config.get('EXCHANGE_RATES', {})
        amount = 100.0
        # 100 EUR = 100 / 0.92 USD ≈ 108.7 USD
        # 108.7 USD * 0.79 GBP ≈ 85.86 GBP
        converted = convert_currency(amount, 'EUR', 'GBP', rates)
        expected = (100.0 / 0.92) * 0.79
        self.assertAlmostEqual(converted, expected, places=1)
    
    def test_convert_currency_rounds_to_2_decimals(self):
        """Test that conversion rounds to 2 decimal places"""
        rates = self.app.config.get('EXCHANGE_RATES', {})
        amount = 33.33
        converted = convert_currency(amount, 'USD', 'EUR', rates)
        # Should have exactly 2 decimal places
        self.assertEqual(len(str(converted).split('.')[-1]), 2)
    
    def test_user_currency_preference_in_menu_endpoint(self):
        """Test that menu endpoint returns prices in user's selected currency"""
        with self.app.app_context():
            # Create a menu item with USD price
            item = MenuItem(name='Test Item', description='Test', price=100.0, available=True)
            db.session.add(item)
            db.session.commit()
            
            # Login as EUR user and check menu price
            with self.client:
                self.client.post('/auth/login', data={'username': 'user_eur', 'password': 'pass'}, follow_redirects=True)
                response = self.client.get('/admin/api/menu')
                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertGreater(len(data), 0)
                # Price should be converted to EUR (100 * 0.92 = 92)
                self.assertAlmostEqual(data[0]['price'], 92.0, places=2)
    
    def test_user_currency_endpoint_update(self):
        """Test updating user's currency preference"""
        with self.app.app_context():
            with self.client:
                # Login and update currency
                self.client.post('/auth/login', data={'username': 'user_usd', 'password': 'pass'}, follow_redirects=True)
                response = self.client.put('/admin/api/users/1/currency', 
                                          json={'currency': 'eur'},
                                          content_type='application/json')
                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertEqual(data['currency'], 'EUR')
                
                # Verify currency was updated in database
                user = db.session.get(User, 1)
                self.assertEqual(user.currency, 'EUR')
    
    def test_invalid_currency_rejected(self):
        """Test that invalid currency codes are rejected"""
        with self.app.app_context():
            with self.client:
                self.client.post('/auth/login', data={'username': 'user_usd', 'password': 'pass'}, follow_redirects=True)
                response = self.client.put('/admin/api/users/1/currency',
                                          json={'currency': 'XXX'},
                                          content_type='application/json')
                self.assertEqual(response.status_code, 400)
                data = response.get_json()
                self.assertIn('error', data)

class TestCurrencyInvoices(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        # Disable CSRF for test client
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        # Use deterministic exchange rates for tests
        self.app.config['EXCHANGE_RATES'] = {
            'USD': 1.0,
            'EUR': 0.92,
            'GBP': 0.79,
            'INR': 83.12,
            'RON': 4.5,
            'CAD': 1.35,
            'AUD': 1.45,
            'JPY': 110.0,
            'CNY': 7.0,
            'AED': 3.67
        }
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test users
            # Avoid duplicate users from previous runs
            for uname in ('user_usd','user_eur'):
                ex = User.query.filter_by(username=uname).first()
                if ex:
                    db.session.delete(ex)
            self.user_usd = User(username='user_usd', password_hash=generate_password_hash('pass'), role='admin', currency='USD')
            self.user_eur = User(username='user_eur', password_hash=generate_password_hash('pass'), role='admin', currency='EUR')
            
            # Create test invoices
            # remove any existing invoices with the same numbers
            for num in ('INV-001','INV-002'):
                exi = Invoice.query.filter_by(invoice_number=num).first()
                if exi:
                    db.session.delete(exi)
            inv1 = Invoice(invoice_number='INV-001', customer_name='Customer 1', total=100.0, status='issued', issued_at=datetime.now(timezone.utc))
            inv2 = Invoice(invoice_number='INV-002', customer_name='Customer 2', total=500.0, status='issued', issued_at=datetime.now(timezone.utc))
            
            db.session.add_all([self.user_usd, self.user_eur, inv1, inv2])
            db.session.commit()
            # ensure deterministic rates are set on the active app context
            self.app.config['EXCHANGE_RATES'] = self.app.config.get('EXCHANGE_RATES')
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            # Clear rows instead of dropping schema to avoid breaking other tests
            try:
                for table in reversed(db.metadata.sorted_tables):
                    try:
                        db.session.execute(table.delete())
                    except Exception:
                        pass
                db.session.commit()
            except Exception:
                db.session.rollback()
    
    def test_invoices_converted_in_user_currency(self):
        """Test that invoices API returns amounts in user's currency"""
        with self.app.app_context():
            with self.client:
                # Login as EUR user
                self.client.post('/auth/login', data={'username': 'user_eur', 'password': 'pass'}, follow_redirects=True)
                response = self.client.get('/admin/api/invoices')
                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertGreater(len(data), 0)
                # Find the invoice INV-001 in the returned list and verify conversion
                inv = next((i for i in data if i.get('invoice_number') == 'INV-001'), None)
                self.assertIsNotNone(inv)
                # INV-001: 100 USD * 0.92 = 92 EUR
                self.assertAlmostEqual(inv['total'], 92.0, places=2)

class TestCurrencyCollections(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        # Disable CSRF for test client
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        # Use deterministic exchange rates for tests
        self.app.config['EXCHANGE_RATES'] = {
            'USD': 1.0,
            'EUR': 0.92,
            'GBP': 0.79,
            'INR': 83.12,
            'RON': 4.5,
            'CAD': 1.35,
            'AUD': 1.45,
            'JPY': 110.0,
            'CNY': 7.0,
            'AED': 3.67
        }
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test users
            for uname in ('user_usd','user_gbp'):
                ex = User.query.filter_by(username=uname).first()
                if ex:
                    db.session.delete(ex)
            self.user_usd = User(username='user_usd', password_hash=generate_password_hash('pass'), role='admin', currency='USD')
            self.user_gbp = User(username='user_gbp', password_hash=generate_password_hash('pass'), role='admin', currency='GBP')
            
            # Create test collections with payments
            col1 = Collection(customer_name='Customer A', total_amount=200.0, paid_amount=100.0, balance=100.0, status='pending')
            pay1 = Payment(collection_id=1, amount=100.0, payment_method='cash', reference_id='REF-001', received_by='User', payment_date=datetime.now(timezone.utc))
            
            db.session.add_all([self.user_usd, self.user_gbp, col1])
            db.session.commit()
            
            pay1.collection_id = col1.id
            db.session.add(pay1)
            db.session.commit()
            # ensure deterministic rates are set on the active app context
            self.app.config['EXCHANGE_RATES'] = self.app.config.get('EXCHANGE_RATES')
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            # Clear rows instead of dropping schema to avoid breaking other tests
            try:
                for table in reversed(db.metadata.sorted_tables):
                    try:
                        db.session.execute(table.delete())
                    except Exception:
                        pass
                db.session.commit()
            except Exception:
                db.session.rollback()
    
    def test_collections_converted_in_user_currency(self):
        """Test that collections API returns amounts in user's currency"""
        with self.app.app_context():
            with self.client:
                # Login as GBP user
                self.client.post('/auth/login', data={'username': 'user_gbp', 'password': 'pass'}, follow_redirects=True)
                response = self.client.get('/admin/api/collections')
                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertGreater(len(data), 0)
                # Collection: 200 USD * 0.79 = 158 GBP
                self.assertAlmostEqual(data[0]['total'], 158.0, places=2)
                # Paid: 100 USD * 0.79 = 79 GBP
                self.assertAlmostEqual(data[0]['paid'], 79.0, places=2)

if __name__ == '__main__':
    unittest.main()
