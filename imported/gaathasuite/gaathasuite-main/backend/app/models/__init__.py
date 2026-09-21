"""Import runtime SQLAlchemy models so relationships resolve eagerly.

FastAPI routes often import a single model (for example ``User`` during
login). SQLAlchemy configures all known mappers lazily on the first ORM query,
so relationship targets referenced by string must already be imported into the
shared declarative registry.
"""
from .organization import Organization
from .asset import Asset
from .user import APIKey, OTP, RefreshToken, User
from .coupon import Coupon
from .inventory import Item, StockRecord, StockTransaction, Warehouse
from .expenses import Expense, Vendor
from .purchase_order import POLineItem, PurchaseOrder
from .approvals import ApprovalRequest
from .books import (
    Account,
    DepreciationEntry,
    Entity,
    Invoice,
    InvoiceLine,
    JournalEntry,
    JournalLine,
    Payment,
    InvoiceSequence,
)
from .crm import Customer, Lead, Opportunity
from .hr import AttendanceRecord, Department, Employee, Payslip, PerformanceReview
from .notifications import Notification
from .preferences import NotificationPreference
from .legal import LegalAcceptance, LegalDocument
from .audit import SettingsChangeLog
from .transactions import (
    Fulfillment,
    PurchaseReceipt,
    PurchaseReceiptLine,
    Quotation,
    QuotationLine,
    SalesOrder,
    SalesOrderLine,
    VendorBill,
    VendorBillPayment,
)

try:
    from blueprints.ai_assistant.models import AIAssistantEmployee
except ImportError:  # pragma: no cover - optional legacy blueprint during tooling
    AIAssistantEmployee = None

__all__ = [
    "Organization",
    "Asset",
    "User",
    "APIKey",
    "OTP",
    "RefreshToken",
    "Coupon",
    "Item",
    "StockRecord",
    "StockTransaction",
    "Warehouse",
    "Expense",
    "Vendor",
    "POLineItem",
    "PurchaseOrder",
    "ApprovalRequest",
    "Account",
    "DepreciationEntry",
    "Entity",
    "Invoice",
    "InvoiceLine",
    "JournalEntry",
    "JournalLine",
    "Payment",
    "InvoiceSequence",
    "Customer",
    "Lead",
    "Opportunity",
    "AttendanceRecord",
    "Department",
    "Employee",
    "Payslip",
    "PerformanceReview",
    "Notification",
    "NotificationPreference",
    "LegalDocument",
    "LegalAcceptance",
    "SettingsChangeLog",
    "Quotation",
    "QuotationLine",
    "SalesOrder",
    "SalesOrderLine",
    "Fulfillment",
    "PurchaseReceipt",
    "PurchaseReceiptLine",
    "VendorBill",
    "VendorBillPayment",
    "AIAssistantEmployee",
]
