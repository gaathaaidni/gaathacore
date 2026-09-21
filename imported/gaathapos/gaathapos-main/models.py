from extensions import db
from flask_login import UserMixin
from datetime import datetime, timezone

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), default="waiter")  # super_admin/restaurant_admin/manager/waiter/kitchen
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id', use_alter=True), nullable=True)  # Null for super_admin
    # NOTE: use_alter=True marks this FK as part of a known cycle (Restaurant->User) so SQLAlchemy can handle create/drop ordering without errors
    currency = db.Column(db.String(3), default="USD")  # e.g., USD, EUR, GBP, INR, etc.
    locale = db.Column(db.String(10), nullable=True)  # e.g., en, es, pt, hi
    is_super_admin = db.Column(db.Boolean, default=False)  # True only for platform super admin
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # 2FA fields
    totp_secret = db.Column(db.String(32), nullable=True)  # Base32-encoded TOTP secret
    totp_enabled = db.Column(db.Boolean, default=False)  # Is 2FA enabled?
    backup_codes = db.Column(db.Text, nullable=True)  # JSON array of backup codes (hashed)
    restaurant = db.relationship('Restaurant', foreign_keys=[restaurant_id], backref='staff')

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=True, index=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True)
    recipe_items = db.relationship('RecipeItem', backref='menu_item', lazy='dynamic', cascade="all, delete-orphan")
    restaurant = db.relationship('Restaurant', backref='menu_items')

    @property
    def cost(self):
        """Calculates the cost of a menu item based on its recipe."""
        if not self.recipe_items:
            return 0.0
        total_cost = sum(item.inventory_item.cost * item.quantity for item in self.recipe_items if item.inventory_item and item.inventory_item.cost is not None)
        return round(total_cost, 2)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default="pending")  # pending, cooking, ready, served
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    items = db.relationship("OrderItem", backref="order", lazy=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"))
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_item.id"))
    quantity = db.Column(db.Integer, default=1)
    menu_item = db.relationship("MenuItem")


class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    cost = db.Column(db.Float, nullable=True) # Cost per unit
    low_stock_threshold = db.Column(db.Integer, default=10) # Alert when quantity falls below this
    unit = db.Column(db.String(32), default="unit")
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)

    __table_args__ = (
        db.CheckConstraint('quantity IS NULL OR quantity >= 0', name='ck_inventory_item_non_negative_quantity'),
        db.UniqueConstraint('id', 'restaurant_id', name='uq_inventory_item_id_restaurant'),
    )


class RecipeItem(db.Model):
    """Association table for MenuItem and InventoryItem to form a recipe."""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=True, index=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False) # e.g., 0.150 for 150g

    inventory_item = db.relationship('InventoryItem', backref='recipe_usages')
    restaurant = db.relationship('Restaurant', backref='recipe_items')


class InventoryMovement(db.Model):
    """Auditable inventory change, reserved for future stock integrations."""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    inventory_item_id = db.Column(db.Integer, nullable=False)
    quantity_delta = db.Column(db.Float, nullable=False)
    movement_type = db.Column(db.String(32), nullable=False)
    reference_type = db.Column(db.String(32), nullable=True)
    reference_id = db.Column(db.String(128), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['inventory_item_id', 'restaurant_id'],
            ['inventory_item.id', 'inventory_item.restaurant_id'],
            name='fk_inventory_movement_item_restaurant',
        ),
        db.CheckConstraint(
            "(movement_type <> 'sale') OR (reference_type IS NOT NULL AND reference_id IS NOT NULL)",
            name='ck_inventory_movement_sale_reference_required',
        ),
        db.UniqueConstraint(
            'restaurant_id', 'inventory_item_id', 'movement_type',
            'reference_type', 'reference_id',
            name='uq_inventory_movement_reference',
        ),
    )

    inventory_item = db.relationship('InventoryItem', backref='movements', overlaps='product_recipes')
    user = db.relationship('User')


class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    old_price = db.Column(db.Float, nullable=False)
    new_price = db.Column(db.Float, nullable=False)
    changed_by = db.Column(db.String(64))
    changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    username = db.Column(db.String(64))
    action = db.Column(db.String(64))
    object_type = db.Column(db.String(64))
    object_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class RolePermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(64), nullable=False, index=True)
    permission = db.Column(db.String(64), nullable=False, index=True)
    allowed = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('role', 'permission', name='uix_role_permission'),
        {'extend_existing': True}
    )


class Transaction(db.Model):
    """Accounting transactions: income, expense, or refund"""
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # income, expense, refund
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(64), nullable=False)  # food, supplies, utilities, etc
    description = db.Column(db.Text)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    recorded_by = db.Column(db.String(64))
    recorded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Collection(db.Model):
    """Customer payment collection and outstanding balance tracking"""
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(128), nullable=False)
    customer_phone = db.Column(db.String(20))
    total_amount = db.Column(db.Float, nullable=False)  # Total outstanding or order total
    paid_amount = db.Column(db.Float, default=0)  # Amount already paid
    balance = db.Column(db.Float, nullable=False)  # Remaining balance
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, partial, paid, overdue
    notes = db.Column(db.Text)
    last_payment_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Payment(db.Model):
    """Individual payment records for collections"""
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), default='cash')  # cash, card, check, online
    reference_id = db.Column(db.String(128))  # transaction ID, check number, etc
    received_by = db.Column(db.String(64))
    notes = db.Column(db.Text)
    payment_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    collection = db.relationship('Collection', backref='payments')


class Invoice(db.Model):
    """Simple invoice model linking to orders or collections"""
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(64), unique=True, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=True)
    customer_name = db.Column(db.String(128))
    customer_phone = db.Column(db.String(20))
    items = db.Column(db.Text)  # JSON-serialized items or plain text
    total = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), default='draft')  # draft, issued, paid
    issued_at = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ExchangeRate(db.Model):
    """Store exchange rates per currency with last updated timestamp"""
    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(3), nullable=False, index=True)
    rate = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Restaurant(db.Model):
    """Restaurant/merchant account managed by restaurant_admin"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(64))
    country = db.Column(db.String(64))
    postal_code = db.Column(db.String(20))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # restaurant_admin user
    owner = db.relationship('User', foreign_keys=[owner_id], backref='restaurants_owned')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class StoreSettings(db.Model):
    """Store-level settings: timezone, locale, currency, tax region, address formats"""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False, unique=True)
    timezone = db.Column(db.String(64), default='UTC')  # e.g., 'Europe/Dublin', 'America/New_York', 'Asia/Kolkata'
    locale = db.Column(db.String(10), default='en')  # e.g., 'en', 'es', 'pt', 'hi'
    currency = db.Column(db.String(3), default='USD')  # e.g., 'USD', 'EUR', 'INR', 'BRL'
    tax_region = db.Column(db.String(64), default='EU')  # Region code for tax rules (e.g., 'EU', 'US-CA', 'IN')
    address_format = db.Column(db.String(20), default='standard')  # address format: standard, european, asian
    business_registration = db.Column(db.String(128))  # Business/tax registration number
    vat_number = db.Column(db.String(64))  # VAT/GST number
    payment_terms = db.Column(db.Integer, default=0)  # Days for payment terms (0=due on receipt)
    invoice_prefix = db.Column(db.String(10), default='INV')  # Invoice number prefix
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    restaurant = db.relationship('Restaurant', backref='store_settings', uselist=False)


# ============================================================================
# PRODUCTS & CATEGORIES
# ============================================================================
class ProductCategory(db.Model):
    """Product categories - hierarchical structure"""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=True)  # For hierarchy
    display_order = db.Column(db.Integer, default=0)  # Order by popularity
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    parent = db.relationship('ProductCategory', remote_side=[id], backref='subcategories')
    products = db.relationship('Product', backref='category')


class Product(db.Model):
    """POS Products with multiple barcodes and variants."""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    stock_mode = db.Column(db.String(16), nullable=False, default='direct', server_default='direct')
    inventory_item_id = db.Column(db.Integer, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(64), unique=True, nullable=True)
    base_price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=True)
    available = db.Column(db.Boolean, default=True)
    requires_weight = db.Column(db.Boolean, default=False)  # Requires electronic scale
    unit_of_measure = db.Column(db.String(32), default='unit')  # unit, kg, L, etc.
    weight = db.Column(db.Float, nullable=True)  # For fixed weight products
    ship_later = db.Column(db.Boolean, default=False)  # Can be shipped later
    is_gift_card = db.Column(db.Boolean, default=False)
    gift_card_validity_days = db.Column(db.Integer, nullable=True)  # 0 = no expiry
    image_url = db.Column(db.String(255), nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    restaurant = db.relationship('Restaurant', backref='products')
    barcodes = db.relationship('BarcodeMapping', backref='product', cascade='all, delete-orphan')
    variants = db.relationship('ProductVariant', backref='product', cascade='all, delete-orphan')
    recipes = db.relationship(
        'ProductRecipe', back_populates='product', cascade='all, delete-orphan',
        overlaps='product,product_recipes',
    )
    stock_inventory = db.relationship(
        'InventoryItem',
        foreign_keys=[inventory_item_id, restaurant_id],
        overlaps='product_recipes,inventory_item,products,restaurant',
    )

    __table_args__ = (
        db.CheckConstraint("stock_mode IN ('direct', 'recipe')", name='ck_product_stock_mode'),
        db.UniqueConstraint('id', 'restaurant_id', name='uq_product_id_restaurant'),
        db.ForeignKeyConstraint(
            ['inventory_item_id', 'restaurant_id'],
            ['inventory_item.id', 'inventory_item.restaurant_id'],
            name='fk_product_stock_inventory_restaurant',
        ),
    )

    def __init__(self, *args, **kwargs):
        if 'stock_mode' not in kwargs or kwargs['stock_mode'] is None:
            kwargs['stock_mode'] = 'direct'
        super().__init__(*args, **kwargs)
        if self.stock_mode not in {'direct', 'recipe'}:
            raise ValueError(f'unsupported stock mode: {self.stock_mode}')

    @property
    def uses_direct_stock(self):
        return self.stock_mode == 'direct'

    @property
    def uses_recipe_stock(self):
        return self.stock_mode == 'recipe'

    def validate_stock_mode(self):
        """Enforce the product stock invariant without connecting to checkout."""
        if self.stock_mode == 'direct':
            if self.inventory_item_id is None:
                raise ValueError('direct stock products must define inventory_item_id')
            if self.stock_inventory is None:
                raise ValueError('direct stock products must own a valid inventory item')
            return True
        if self.stock_mode == 'recipe':
            needs_recipe = db.session.query(ProductRecipe.id).filter_by(
                product_id=self.id,
                restaurant_id=self.restaurant_id,
            ).first()
            if not needs_recipe:
                raise ValueError('recipe stock products must have at least one ingredient')
            return True
        raise ValueError(f'unsupported stock mode: {self.stock_mode}')


class ProductRecipe(db.Model):
    """Tenant-safe recipe line for an active POS Product."""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    inventory_item_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['product_id', 'restaurant_id'],
            ['product.id', 'product.restaurant_id'],
            name='fk_product_recipe_product_restaurant',
        ),
        db.ForeignKeyConstraint(
            ['inventory_item_id', 'restaurant_id'],
            ['inventory_item.id', 'inventory_item.restaurant_id'],
            name='fk_product_recipe_inventory_restaurant',
        ),
        db.CheckConstraint('quantity > 0', name='ck_product_recipe_positive_quantity'),
        db.UniqueConstraint(
            'restaurant_id', 'product_id', 'inventory_item_id',
            name='uq_product_recipe_ingredient',
        ),
    )

    product = db.relationship('Product', back_populates='recipes', overlaps='product_recipes')
    inventory_item = db.relationship(
        'InventoryItem',
        backref=db.backref('product_recipes', overlaps='recipes,product'),
        overlaps='recipes,product',
    )


class ProductVariant(db.Model):
    """Product variants: sizes, colors, configurations"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)  # e.g., "Small", "Large", "Red"
    sku = db.Column(db.String(64), nullable=True)
    price_adjustment = db.Column(db.Float, default=0.0)  # Add/subtract from base price
    cost_adjustment = db.Column(db.Float, default=0.0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class BarcodeMapping(db.Model):
    """Multiple barcodes per product with barcode nomenclature"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    barcode = db.Column(db.String(128), unique=True, nullable=False, index=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=True)
    embedded_price = db.Column(db.Float, nullable=True)  # Price embedded in barcode
    embedded_weight = db.Column(db.Float, nullable=True)  # Weight embedded in barcode
    loyalty_points = db.Column(db.Integer, nullable=True)  # Loyalty points in barcode
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    variant = db.relationship('ProductVariant', backref='barcodes')


# ============================================================================
# PAYMENT & CHECKOUT
# ============================================================================
class PaymentMethod(db.Model):
    """Payment methods: cash, cards, checks, etc."""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)  # Cash, Credit Card, Debit Card, Check, etc.
    payment_type = db.Column(db.String(20), nullable=False)  # cash, card, check, online, wallet
    requires_external_terminal = db.Column(db.Boolean, default=False)
    can_be_reused = db.Column(db.Boolean, default=True)
    currency_rounding = db.Column(db.Float, nullable=True)  # Smallest currency denomination
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    restaurant = db.relationship('Restaurant', backref='payment_methods')


class PaymentTransaction(db.Model):
    """Payment transactions for orders"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_method.id'), nullable=False)
    cash_register_id = db.Column(db.Integer, db.ForeignKey('cash_register.id'), nullable=True)
    cashier_id = db.Column(db.Integer, db.ForeignKey('cashier_account.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    reference_id = db.Column(db.String(128), nullable=True)  # External transaction ID
    is_offline = db.Column(db.Boolean, default=False)  # Processed offline
    synchronization_status = db.Column(db.String(20), default='synced')  # synced, pending_sync, failed_sync
    tip_amount = db.Column(db.Float, default=0.0)
    tip_type = db.Column(db.String(20), nullable=True)  # amount, percentage (of change)
    change_to_tip = db.Column(db.Boolean, default=False)  # Convert change to tip
    processed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    order = db.relationship('Order', backref='payments')
    payment_method = db.relationship('PaymentMethod')
    cash_register = db.relationship('CashRegister')
    cashier = db.relationship('CashierAccount')
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=True)
    __table_args__ = (
        db.Index(
            'uq_payment_transaction_restaurant_reference',
            'restaurant_id',
            'reference_id',
            unique=True,
        ),
    )


class Discount(db.Model):
    """Discounts: product-level or order-level"""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # percentage, fixed_amount
    value = db.Column(db.Float, nullable=False)
    applies_to = db.Column(db.String(20), default='product')  # product, order
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)  # For customer-specific discounts
    start_date = db.Column(db.DateTime, nullable=True)  # Time-limited
    end_date = db.Column(db.DateTime, nullable=True)
    min_quantity = db.Column(db.Integer, default=1)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    restaurant = db.relationship('Restaurant', backref='discounts')


class BillSplit(db.Model):
    """Bill splitting: split single order between multiple payment methods/parties"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    split_index = db.Column(db.Integer)  # Which split (1st, 2nd, etc.)
    amount = db.Column(db.Float, nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_method.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    order = db.relationship('Order', backref='bill_splits')
    payment_method = db.relationship('PaymentMethod')


class Receipt(db.Model):
    """Receipt printing and customization"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    receipt_number = db.Column(db.String(64), unique=True, nullable=True)
    header_text = db.Column(db.Text)  # Store promotions, hours, events
    footer_text = db.Column(db.Text)
    content = db.Column(db.Text)  # Full receipt content
    printed = db.Column(db.Boolean, default=False)
    printed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    order = db.relationship('Order', backref='receipts')


# ============================================================================
# RESTAURANT MANAGEMENT
# ============================================================================
class RestaurantFloorPlan(db.Model):
    """Custom floor plan for restaurant"""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False, unique=True)
    name = db.Column(db.String(128), default='Main Floor')
    layout_data = db.Column(db.Text)  # JSON: table positions, zones, etc.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    restaurant = db.relationship('Restaurant', backref='floor_plan', uselist=False)
    sections = db.relationship('TableSection', backref='floor_plan', cascade='all, delete-orphan')


class TableSection(db.Model):
    """Zones/sections in a restaurant (e.g., Indoor, Patio, Bar)"""
    id = db.Column(db.Integer, primary_key=True)
    floor_plan_id = db.Column(db.Integer, db.ForeignKey('restaurant_floor_plan.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)  # Indoor, Patio, Bar, etc.
    capacity = db.Column(db.Integer, default=0)  # Total seats in section
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    tables = db.relationship('Table', backref='section', cascade='all, delete-orphan')


class Table(db.Model):
    """Restaurant table"""
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('table_section.id'), nullable=False)
    table_number = db.Column(db.String(32), nullable=False)
    seats = db.Column(db.Integer, default=2)
    pos_x = db.Column(db.Float, nullable=True)  # Position in floor plan
    pos_y = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='available')  # available, occupied, reserved
    current_order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    reserved_by = db.Column(db.String(128), nullable=True)  # Reservation name
    reserved_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    current_order = db.relationship('Order', backref='table', uselist=False, foreign_keys=[current_order_id])


class TableBooking(db.Model):
    """Online table booking via Appointments"""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=False)
    customer_name = db.Column(db.String(128), nullable=False)
    customer_email = db.Column(db.String(128))
    customer_phone = db.Column(db.String(20))
    booking_date = db.Column(db.DateTime, nullable=False)
    party_size = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='confirmed')  # confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    table = db.relationship('Table', backref='bookings')


class KitchenPrinter(db.Model):
    """Kitchen and bar printers"""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)  # "Kitchen Printer 1", "Bar Printer"
    printer_type = db.Column(db.String(20), nullable=False)  # kitchen, bar
    ip_address = db.Column(db.String(15), nullable=True)  # Network printer IP
    device_name = db.Column(db.String(128), nullable=True)  # USB printer device
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class OrderNote(db.Model):
    """Notes for orders: customer preferences, allergies, special requests"""
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_item.id'), nullable=False)
    note_type = db.Column(db.String(20), nullable=False)  # preference, allergy, special_request
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    order_item = db.relationship('OrderItem', backref='notes')


class DelayedOrder(db.Model):
    """Delayed orders for different courses"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    course_number = db.Column(db.Integer, default=1)  # 1st course, 2nd course, etc.
    delay_minutes = db.Column(db.Integer, default=0)  # Delay before sending to kitchen
    sent_to_kitchen = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    order = db.relationship('Order', backref='delayed_orders')


class Kiosk(db.Model):
    """Self-service kiosk for customer orders"""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    kiosk_code = db.Column(db.String(32), unique=True, nullable=False)  # QR code reference
    location = db.Column(db.String(128))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    restaurant = db.relationship('Restaurant', backref='kiosks')


# ============================================================================
# CUSTOMER & LOYALTY
# ============================================================================
class Customer(db.Model):
    """Customer registration and profile"""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    vat_number = db.Column(db.String(64), nullable=True)  # B2B customer VAT
    credit_limit = db.Column(db.Float, default=0)  # 0 = no limit
    outstanding_balance = db.Column(db.Float, default=0)
    barcode = db.Column(db.String(128), unique=True, nullable=True)  # Loyalty card barcode
    registered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    restaurant = db.relationship('Restaurant', backref='customers')


class LoyaltyCard(db.Model):
    """Loyalty card for customer rewards"""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False, unique=True)
    card_number = db.Column(db.String(64), unique=True, nullable=False)
    points_balance = db.Column(db.Integer, default=0)
    tier = db.Column(db.String(20), default='standard')  # standard, silver, gold, platinum
    points_earned_total = db.Column(db.Integer, default=0)
    points_redeemed_total = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    customer = db.relationship('Customer', backref='loyalty_card', uselist=False)


class LoyaltyPoints(db.Model):
    """Points transaction history"""
    id = db.Column(db.Integer, primary_key=True)
    loyalty_card_id = db.Column(db.Integer, db.ForeignKey('loyalty_card.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    points = db.Column(db.Integer, nullable=False)  # Positive for earned, negative for redeemed
    earn_method = db.Column(db.String(20), nullable=False)  # product, order, amount
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    loyalty_card = db.relationship('LoyaltyCard', backref='points_history')


class LoyaltyReward(db.Model):
    """Rewards catalog: gifts or discounts for loyalty points"""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    points_required = db.Column(db.Integer, nullable=False)
    reward_type = db.Column(db.String(20), nullable=False)  # discount, gift, free_product
    reward_value = db.Column(db.Float, nullable=True)  # Discount amount or free product ID
    valid_until = db.Column(db.DateTime, nullable=True)
    stock = db.Column(db.Integer, nullable=True)  # Available rewards
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    restaurant = db.relationship('Restaurant', backref='loyalty_rewards')


class eWallet(db.Model):
    """Customer e-wallet for prepaid balance"""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False, unique=True)
    balance = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    customer = db.relationship('Customer', backref='wallet', uselist=False)


class eWalletTransaction(db.Model):
    """e-Wallet transaction history"""
    id = db.Column(db.Integer, primary_key=True)
    ewallet_id = db.Column(db.Integer, db.ForeignKey('e_wallet.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)  # Positive for top-up, negative for spending
    transaction_type = db.Column(db.String(20), nullable=False)  # topup, purchase, refund
    reference_id = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ewallet = db.relationship('eWallet', backref='transactions')


class PriceList(db.Model):
    """Dynamic pricing for products based on POS or customer type"""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)  # "Dine-in", "Takeaway", "VIP Customers"
    pricelist_type = db.Column(db.String(20), nullable=False)  # dine_in, takeaway, customer_specific
    valid_from = db.Column(db.DateTime, nullable=True)
    valid_until = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    restaurant = db.relationship('Restaurant', backref='pricelists')
    prices = db.relationship('PriceListItem', backref='pricelist', cascade='all, delete-orphan')


class PriceListItem(db.Model):
    """Price for a product in a specific pricelist"""
    id = db.Column(db.Integer, primary_key=True)
    pricelist_id = db.Column(db.Integer, db.ForeignKey('price_list.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    product = db.relationship('Product', backref='pricelist_items')


# ============================================================================
# STORE MANAGEMENT & HARDWARE
# ============================================================================
class CashierAccount(db.Model):
    """Cashier-specific account with badge or PIN"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pin_code = db.Column(db.String(128), nullable=True)  # Hashed PIN for security
    badge_id = db.Column(db.String(64), unique=True, nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref='cashier_account', uselist=False)


class CashRegister(db.Model):
    """Physical cash register/drawer"""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    register_name = db.Column(db.String(64), nullable=False)
    hardware_id = db.Column(db.String(64), unique=True, nullable=True)
    current_cashier_id = db.Column(db.Integer, db.ForeignKey('cashier_account.id'), nullable=True)
    opening_balance = db.Column(db.Float, default=0)
    current_balance = db.Column(db.Float, default=0)
    opened_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='closed')  # opened, closed
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    restaurant = db.relationship('Restaurant', backref='cash_registers')
    current_cashier = db.relationship('CashierAccount')


class CashFlow(db.Model):
    """Cash register adjustments and daily reconciliation"""
    id = db.Column(db.Integer, primary_key=True)
    cash_register_id = db.Column(db.Integer, db.ForeignKey('cash_register.id'), nullable=False)
    adjustment_type = db.Column(db.String(20), nullable=False)  # opening_balance, deposit, withdrawal, correction
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    recorded_by = db.Column(db.String(64))
    expected_balance = db.Column(db.Float, nullable=True)  # For end-of-day reconciliation
    actual_balance = db.Column(db.Float, nullable=True)
    variance = db.Column(db.Float, nullable=True)  # Difference between expected and actual
    recorded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    cash_register = db.relationship('CashRegister', backref='cash_flows')


class HardwareDevice(db.Model):
    """Connected hardware: barcode scanners, payment terminals, scales, etc."""
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    device_type = db.Column(db.String(20), nullable=False)  # barcode_scanner, payment_terminal, scale, cash_register
    name = db.Column(db.String(64), nullable=False)
    model = db.Column(db.String(64), nullable=True)
    device_id = db.Column(db.String(128), unique=True, nullable=True)  # MAC address or serial
    connection_type = db.Column(db.String(20), nullable=False)  # usb, network, bluetooth
    ip_address = db.Column(db.String(15), nullable=True)  # For network devices
    status = db.Column(db.String(20), default='disconnected')  # connected, disconnected, error
    last_seen = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    restaurant = db.relationship('Restaurant', backref='hardware_devices')
