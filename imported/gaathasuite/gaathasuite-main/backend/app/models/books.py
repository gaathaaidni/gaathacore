from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy import String, Integer, ForeignKey, Date, Float, Numeric, Text, UniqueConstraint, Boolean, JSON, select
from sqlalchemy import event, inspect
from datetime import date
from decimal import Decimal
from app.models.base import Base

class Invoice(Base):
    __tablename__ = 'invoice'
    
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'))
    date: Mapped[date] = mapped_column(Date, default=date.today)
    due_date: Mapped[date] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default='USD')
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(50), default='draft')
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="invoices")
    lines: Mapped[list["InvoiceLine"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")

    @property
    def outstanding_amount(self) -> Decimal:
        return Decimal(str(self.total_amount or 0)) - Decimal(str(self.paid_amount or 0))

class InvoiceLine(Base):
    __tablename__ = 'invoice_line'

    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey('invoice.id'))
    description: Mapped[str] = mapped_column(String(300))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)
    item_id: Mapped[int] = mapped_column(ForeignKey('items.id'), nullable=True)

    invoice: Mapped["Invoice"] = relationship(back_populates="lines")

class Account(Base):
    __tablename__ = 'account'
    __table_args__ = (UniqueConstraint('organization_id', 'code', name='uq_account_org_code'),)
    
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    type: Mapped[str] = mapped_column(String(50)) # Asset, Liability, Equity, Revenue, Expense
    code: Mapped[str] = mapped_column(String(50))

class JournalEntry(Base):
    __tablename__ = 'journal_entry'

    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    description: Mapped[str] = mapped_column(String(500))
    entry_date: Mapped[date] = mapped_column(Date, default=date.today)
    currency: Mapped[str] = mapped_column(String(3), default='USD')
    status: Mapped[str] = mapped_column(String(20), default='draft', nullable=False)

    lines: Mapped[list["JournalLine"]] = relationship(back_populates="entry", cascade="all, delete-orphan")

class JournalLine(Base):
    __tablename__ = 'journal_line'

    entry_id: Mapped[int] = mapped_column(ForeignKey('journal_entry.id'))
    account_id: Mapped[int] = mapped_column(ForeignKey('account.id'))
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    debit: Mapped[float] = mapped_column(Float, default=0.0)
    credit: Mapped[float] = mapped_column(Float, default=0.0)
    description: Mapped[str] = mapped_column(String(500), nullable=True)

    entry: Mapped["JournalEntry"] = relationship(back_populates="lines")
    account: Mapped["Account"] = relationship()


def _reject_posted_journal_mutation(session, flush_context, instances):
    """Keep posted accounting history immutable at the ORM write boundary."""
    protected_entries = {
        entry.id
        for entry in session.dirty.union(session.deleted)
        if isinstance(entry, JournalEntry) and entry.status == "posted"
    }

    for entry in session.dirty:
        if isinstance(entry, JournalEntry) and entry.status == "posted":
            state = inspect(entry)
            if any(
                state.attrs[attribute.key].history.has_changes()
                for attribute in state.mapper.column_attrs
            ):
                raise ValueError("Posted journal entries are immutable; create a reversal instead")

    for line in session.dirty:
        if isinstance(line, JournalLine):
            entry = session.get(JournalEntry, line.entry_id)
            if entry and entry.status == "posted":
                raise ValueError("Posted journal lines are immutable; create a reversal instead")

    for line in session.deleted:
        if isinstance(line, JournalLine):
            entry = session.get(JournalEntry, line.entry_id)
            if entry and entry.status == "posted":
                raise ValueError("Posted journal lines are immutable; create a reversal instead")

    for line in session.new:
        if isinstance(line, JournalLine):
            if line.entry in session.new:
                continue
            entry = session.get(JournalEntry, line.entry_id)
            if entry and entry.status == "posted":
                raise ValueError("Posted journal entries cannot receive new lines")

    for entry in session.deleted:
        if isinstance(entry, JournalEntry):
            status = _posted_entry_status(session.connection(), entry.id)
            if status == "posted" or entry.status == "posted":
                raise ValueError("Posted journal entries are immutable; create a reversal instead")


event.listen(Session, "before_flush", _reject_posted_journal_mutation)


def _posted_entry_status(connection, entry_id: int) -> str | None:
    return connection.execute(
        select(JournalEntry.status).where(JournalEntry.id == entry_id)
    ).scalar_one_or_none()


@event.listens_for(JournalEntry, "before_update")
def _reject_posted_entry_update(mapper, connection, target):
    state = inspect(target)
    was_posted = state.attrs.status.history.deleted == ["posted"]
    if target.status == "posted" or was_posted:
        raise ValueError("Posted journal entries are immutable; create a reversal instead")


@event.listens_for(JournalEntry, "before_delete")
def _reject_posted_entry_delete(mapper, connection, target):
    if target.status == "posted":
        raise ValueError("Posted journal entries are immutable; create a reversal instead")


@event.listens_for(JournalLine, "before_update")
def _reject_posted_line_update(mapper, connection, target):
    if _posted_entry_status(connection, target.entry_id) == "posted":
        raise ValueError("Posted journal lines are immutable; create a reversal instead")


@event.listens_for(JournalLine, "before_delete")
def _reject_posted_line_delete(mapper, connection, target):
    if _posted_entry_status(connection, target.entry_id) == "posted":
        raise ValueError("Posted journal lines are immutable; create a reversal instead")



class Entity(Base):
    __tablename__ = 'entity'
    __table_args__ = (UniqueConstraint('organization_id', 'name', name='uq_entity_org_name'),)

    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), default='Subsidiary')
    base_currency: Mapped[str] = mapped_column(String(3), default='USD')
    supported_currencies: Mapped[list[str]] = mapped_column(JSON, default=['USD'])
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class InvoiceSequence(Base):
    __tablename__ = 'invoice_sequence'
    
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    last_number: Mapped[int] = mapped_column(Integer, default=0)

class Asset(Base):
    """Legacy accounting-book asset model.

    This class is intentionally isolated as a legacy compatibility model.
    The authoritative runtime model is app.models.asset.Asset, which is the
    model bound to the active User.assets relationship and the main FastAPI
    CRUD flows.
    """
    __tablename__ = 'asset'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(100))
    assigned_to_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    purchased_on: Mapped[date] = mapped_column(Date)

    assigned_to: Mapped["User"] = relationship("User", foreign_keys=[assigned_to_id])
    depreciation_entries: Mapped[list["DepreciationEntry"]] = relationship(back_populates="asset")

class DepreciationEntry(Base):
    __tablename__ = 'depreciation_entry'
    
    org_id: Mapped[int] = mapped_column(Integer)
    asset_id: Mapped[int] = mapped_column(ForeignKey('asset.id'))
    entry_date: Mapped[date] = mapped_column(Date)
    depreciation_amount: Mapped[float] = mapped_column(Float)
    accumulated_depreciation: Mapped[float] = mapped_column(Float)
    book_value_after_depreciation: Mapped[float] = mapped_column(Float)
    
    asset: Mapped["Asset"] = relationship(
        "app.models.books.Asset", back_populates="depreciation_entries"
    )

class Payment(Base):
    __tablename__ = 'payment'

    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    date: Mapped[date] = mapped_column(Date)
    method: Mapped[str] = mapped_column(String(100))
    reference: Mapped[str] = mapped_column(String(255))
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey('invoice.id'))
    
    invoice: Mapped["Invoice"] = relationship(back_populates="payments")