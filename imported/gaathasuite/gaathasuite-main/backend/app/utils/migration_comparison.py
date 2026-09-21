"""Canonical Alembic comparison contract.

The tables listed here are preserved compatibility tables. They remain
available to legacy runtime paths, but their historical schema is not part of
the active SQLAlchemy migration contract. Canonical tables remain fully
subject to Alembic comparison.
"""


LEGACY_COMPATIBILITY_TABLES = {
    "user",
    "customer",
    "organization",
    "coupon",
    "invitation",
    "organization_payment",
    "department",
    "invoice",
    "invoice_line",
    "invoice_sequence",
    "notification_preferences",
}


def include_name(name, type_, parent_names):
    """Exclude legacy tables before Alembic reflects their child objects."""
    return not (type_ == "table" and name in LEGACY_COMPATIBILITY_TABLES)


def include_object(object_, name, type_, reflected, compare_to):
    """Keep legacy compatibility tables outside the canonical schema contract."""
    return not (type_ == "table" and name in LEGACY_COMPATIBILITY_TABLES)