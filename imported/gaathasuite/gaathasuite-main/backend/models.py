"""
User authentication and account models.
"""
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets


class User(UserMixin, db.Model):
    """User account model with role-based access control."""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(50), default='user')  # user, admin, superadmin
    avatar_url = db.Column(db.String(500))
    
    # Account metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # OAuth
    oauth_id = db.Column(db.String(255), unique=True)
    oauth_provider = db.Column(db.String(50))  # google, microsoft, etc
    
    # Email verification
    email_verified = db.Column(db.Boolean, default=False)
    email_verified_at = db.Column(db.DateTime)
    
    def set_password(self, password: str):
        """Hash and store password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class Role(db.Model):
    """Role definition for RBAC."""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Role {self.name}>'


class Permission(db.Model):
    """Permission definition for RBAC."""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    resource = db.Column(db.String(100))  # e.g., 'crm', 'inventory'
    action = db.Column(db.String(100))    # e.g., 'read', 'write', 'delete'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Permission {self.name}>'


class RolePermission(db.Model):
    """Mapping between roles and permissions."""
    __tablename__ = 'role_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    role = db.relationship('Role', backref=db.backref('permissions'))
    permission = db.relationship('Permission', backref=db.backref('roles'))
    
    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),)


class UserRole(db.Model):
    """Mapping between users and roles."""
    __tablename__ = 'user_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('user_roles'))
    role = db.relationship('Role')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'role_id', name='unique_user_role'),)


class Organization(db.Model):
    """Organization/Tenant model for multi-tenancy."""
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Organization {self.name}>'


class OrganizationUser(db.Model):
    """Mapping between users and organizations."""
    __tablename__ = 'organization_users'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(50), default='member')  # owner, admin, member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    organization = db.relationship('Organization', backref=db.backref('users'))
    user = db.relationship('User', backref=db.backref('organizations'))
    
    __table_args__ = (db.UniqueConstraint('organization_id', 'user_id', name='unique_org_user'),)


class APIKey(db.Model):
    """API key for user authentication."""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100))
    last_used = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref=db.backref('api_keys'))
    
    @classmethod
    def generate_key(cls):
        """Generate a random API key."""
        return secrets.token_urlsafe(32)


class OTP(db.Model):
    """One-time password for two-factor authentication."""
    __tablename__ = 'otps'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=5))
    
    user = db.relationship('User', backref=db.backref('otps'))


class RefreshToken(db.Model):
    """JWT refresh token for session management."""
    __tablename__ = 'refresh_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(500), unique=True, nullable=False, index=True)
    is_revoked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('refresh_tokens'))


class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    monthly_price = db.Column(db.Float, default=0.0)
    yearly_price = db.Column(db.Float, default=0.0)
    features = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscriptions = db.relationship('Subscription', back_populates='plan', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'monthly_price': self.monthly_price,
            'yearly_price': self.yearly_price,
            'features': self.features,
        }


class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='active')
    renewal_period = db.Column(db.String(50), default='monthly')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('subscriptions', lazy='dynamic'))
    plan = db.relationship('SubscriptionPlan', back_populates='subscriptions')


class BetaAccess(db.Model):
    __tablename__ = 'beta_access'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires_on = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('beta_access', lazy='dynamic'))


class BillingRecord(db.Model):
    __tablename__ = 'billing_records'

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=True)
    amount = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subscription = db.relationship('Subscription', backref=db.backref('billing_records', lazy='dynamic'))
    invoice = db.relationship('Invoice', backref=db.backref('billing_records', lazy='dynamic'))


class Payment(db.Model):
    __tablename__ = 'payment'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'))
    amount = db.Column(db.Float, default=0.0)
    date = db.Column(db.Date)
    method = db.Column(db.String(100))
    reference = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoice = db.relationship('Invoice', backref=db.backref('payments', lazy='dynamic'))


class Coupon(db.Model):
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    discount_type = db.Column(db.String(50), default='fixed')
    value = db.Column(db.Float, default=0.0)
    used_count = db.Column(db.Integer, default=0)
    expires_on = db.Column(db.Date)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        if not self.active:
            return False
        if self.expires_on and self.expires_on < datetime.utcnow().date():
            return False
        return True


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True)
    phone = db.Column(db.String(50))
    address = db.Column(db.String(500))
    currency = db.Column(db.String(10), default='USD')
    company = db.Column(db.String(255))
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Lead(db.Model):
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    contact_email = db.Column(db.String(255), index=True)
    source = db.Column(db.String(100))
    company = db.Column(db.String(255))
    status = db.Column(db.String(50), default='new')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Opportunity(db.Model):
    __tablename__ = 'opportunities'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    value = db.Column(db.Float, default=0.0)
    stage = db.Column(db.String(100), default='prospect')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship('Customer', backref=db.backref('opportunities', lazy='dynamic'))


class Account(db.Model):
    __tablename__ = 'account'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, index=True)
    name = db.Column(db.String(200), index=True)
    type = db.Column(db.String(50))
    code = db.Column(db.String(50), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Invoice(db.Model):
    __tablename__ = 'invoice'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, index=True)
    number = db.Column(db.String(50), unique=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    date = db.Column(db.Date, default=datetime.utcnow)
    due_date = db.Column(db.Date)
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='draft')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship('Customer', backref=db.backref('invoices', lazy='dynamic'))
    lines = db.relationship('InvoiceLine', backref='invoice', cascade='all, delete-orphan', lazy='dynamic')


class InvoiceLine(db.Model):
    __tablename__ = 'invoice_line'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'))
    description = db.Column(db.String(300))
    qty = db.Column(db.Float, default=1.0)
    unit_price = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Item(db.Model):
    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    unit_cost = db.Column(db.Float, default=0.0)
    unit_price = db.Column(db.Float, default=0.0)
    quantity_on_hand = db.Column(db.Float, default=0.0)
    quantity = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Warehouse(db.Model):
    __tablename__ = 'warehouse'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    capacity = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StockTransaction(db.Model):
    __tablename__ = 'stock_transaction'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'))
    quantity = db.Column(db.Float, default=0.0)
    transaction_type = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('Item', backref=db.backref('stock_transactions', lazy='dynamic'))
    warehouse = db.relationship('Warehouse', backref=db.backref('stock_transactions', lazy='dynamic'))


class Department(db.Model):
    __tablename__ = 'department'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    manager = db.relationship('User', backref=db.backref('managed_departments', lazy='dynamic'))


class Employee(db.Model):
    __tablename__ = 'employee'

    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(100), unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    position = db.Column(db.String(255))
    hired_date = db.Column(db.Date)
    salary = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.relationship('Department', backref=db.backref('employees', lazy='dynamic'))


class Payslip(db.Model):
    __tablename__ = 'payslip'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    gross = db.Column(db.Float, default=0.0)
    net = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', backref=db.backref('payslips', lazy='dynamic'))


class Ticket(db.Model):
    __tablename__ = 'ticket'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(50), default='normal')
    status = db.Column(db.String(50), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship('Customer', backref=db.backref('tickets', lazy='dynamic'))


class TicketComment(db.Model):
    __tablename__ = 'ticket_comment'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message = db.Column(db.Text)
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket = db.relationship('Ticket', backref=db.backref('comments', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('ticket_comments', lazy='dynamic'))


class Project(db.Model):
    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    status = db.Column(db.String(50), default='active')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization', backref=db.backref('projects', lazy='dynamic'))
    tasks = db.relationship('Task', backref='project', cascade='all, delete-orphan', lazy='dynamic')


class Task(db.Model):
    __tablename__ = 'task'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='todo')
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assignee = db.relationship('User', backref=db.backref('tasks', lazy='dynamic'))


class Vendor(db.Model):
    __tablename__ = 'vendor'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), index=True)
    phone = db.Column(db.String(50))
    address = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Expense(db.Model):
    __tablename__ = 'expense'

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    amount = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(255))
    status = db.Column(db.String(50), default='draft')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vendor = db.relationship('Vendor', backref=db.backref('expenses', lazy='dynamic'))
    organization = db.relationship('Organization', backref=db.backref('expenses', lazy='dynamic'))


class ApprovalRequest(db.Model):
    __tablename__ = 'approval_request'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    document_type = db.Column(db.String(100))
    document_id = db.Column(db.Integer)
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requester = db.relationship('User', foreign_keys=[requester_id], backref=db.backref('approval_requests', lazy='dynamic'))
    approver = db.relationship('User', foreign_keys=[approved_by_user_id])
    organization = db.relationship('Organization', backref=db.backref('approval_requests', lazy='dynamic'))


class ApprovalWorkflow(db.Model):
    __tablename__ = 'approval_workflow'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    rule = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_record'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), index=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    date = db.Column(db.Date)
    status = db.Column(db.String(50), default='present')
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)
    hours_worked = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization', backref=db.backref('attendance_records', lazy='dynamic'))
    employee = db.relationship('Employee', backref=db.backref('attendance_records', lazy='dynamic'))


class Asset(db.Model):
    __tablename__ = 'asset'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    serial_number = db.Column(db.String(255), unique=True, index=True)
    category = db.Column(db.String(100))
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    purchased_on = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assigned_to = db.relationship('User', backref=db.backref('assets', lazy='dynamic'))


class Invitation(db.Model):
    __tablename__ = 'invitation'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    email = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime)
    accepted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization', backref=db.backref('invitations', lazy='dynamic'))


class OrganizationSettings(db.Model):
    __tablename__ = 'organization_settings'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    settings = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization', backref=db.backref('settings', uselist=False))


class OrganizationPayment(db.Model):
    __tablename__ = 'organization_payment'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    amount = db.Column(db.Float, default=0.0)
    date = db.Column(db.Date)
    reference = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization', backref=db.backref('payments', lazy='dynamic'))


class Workflow(db.Model):
    __tablename__ = 'workflow'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class WorkflowAction(db.Model):
    __tablename__ = 'workflow_action'

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id'))
    action_type = db.Column(db.String(255))
    payload = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    workflow = db.relationship('Workflow', backref=db.backref('actions', lazy='dynamic'))


class WorkflowCondition(db.Model):
    __tablename__ = 'workflow_condition'

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id'))
    condition_type = db.Column(db.String(255))
    parameters = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    workflow = db.relationship('Workflow', backref=db.backref('conditions', lazy='dynamic'))


class WorkflowExecutionLog(db.Model):
    __tablename__ = 'workflow_execution_log'

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id'))
    status = db.Column(db.String(100))
    message = db.Column(db.Text)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)

    workflow = db.relationship('Workflow', backref=db.backref('execution_logs', lazy='dynamic'))


class WorkflowEvent(db.Model):
    __tablename__ = 'workflow_event'

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id'))
    event_name = db.Column(db.String(255))
    payload = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    workflow = db.relationship('Workflow', backref=db.backref('events', lazy='dynamic'))


class Report(db.Model):
    __tablename__ = 'report'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Dashboard(db.Model):
    __tablename__ = 'dashboard'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DashboardWidget(db.Model):
    __tablename__ = 'dashboard_widget'

    id = db.Column(db.Integer, primary_key=True)
    dashboard_id = db.Column(db.Integer, db.ForeignKey('dashboard.id'))
    name = db.Column(db.String(255), nullable=False)
    settings = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    dashboard = db.relationship('Dashboard', backref=db.backref('widgets', lazy='dynamic'))


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(255))
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('activity_logs', lazy='dynamic'))


class Comment(db.Model):
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))


class Notification(db.Model):
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(255))
    body = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))


class Folder(db.Model):
    __tablename__ = 'folder'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    parent = db.relationship('Folder', remote_side=[id], backref=db.backref('children', lazy='dynamic'))


class Document(db.Model):
    __tablename__ = 'document'

    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    folder = db.relationship('Folder', backref=db.backref('documents', lazy='dynamic'))


class DocumentVersion(db.Model):
    __tablename__ = 'document_version'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    version_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    document = db.relationship('Document', backref=db.backref('versions', lazy='dynamic'))


class Webhook(db.Model):
    __tablename__ = 'webhook'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    secret = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class WebhookEvent(db.Model):
    __tablename__ = 'webhook_event'

    id = db.Column(db.Integer, primary_key=True)
    webhook_id = db.Column(db.Integer, db.ForeignKey('webhook.id'))
    payload = db.Column(db.JSON)
    status = db.Column(db.String(100), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    webhook = db.relationship('Webhook', backref=db.backref('events', lazy='dynamic'))


class WebhookDeliveryLog(db.Model):
    __tablename__ = 'webhook_delivery_log'

    id = db.Column(db.Integer, primary_key=True)
    webhook_event_id = db.Column(db.Integer, db.ForeignKey('webhook_event.id'))
    status_code = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    webhook_event = db.relationship('WebhookEvent', backref=db.backref('delivery_logs', lazy='dynamic'))


# Import additional models from app.models
# from app.models.books import InvoiceSequence

class InvoiceSequence(db.Model):
    __tablename__ = 'invoice_sequence'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, index=True)
    year = db.Column(db.Integer, unique=True, index=True)
    last_number = db.Column(db.Integer, default=0)


class WorkflowTrigger(db.Model):
    __tablename__ = 'workflow_triggers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    # Add other fields as needed
