from fastapi import APIRouter, Depends, HTTPException, status, Response, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from decimal import Decimal
from pydantic import BaseModel, Field
import os, logging
import glob
from datetime import date

from app.models.books import Account, Invoice, InvoiceLine, Entity, Payment
from app.models.crm import Customer
from app.models.organization import Organization
from app.models.audit import SettingsChangeLog
from app.models.user import User
from app.schemas.books import (
    AccountCreate, AccountRead,
    EntityCreate, EntityRead,
    InvoiceCreate, InvoiceRead, InvoiceUpdate
)
from app.utils.dependencies import get_org_db_session, require_roles
from app.utils.roles import (
    ROLE_AUDITOR,
    ROLE_LEAD,
    ROLE_MANAGER,
    ROLE_ORGADMIN,
    ROLE_SUPERADMIN,
)
from app.services.accounting import JournalValidationError, post_journal_entry
from app.services.pdf_service import PDFService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/books", tags=["Books (Accounting)"])
pdf_service = PDFService()


class PaymentPayload(BaseModel):
    amount: Decimal | None = Field(None, gt=0)
    method: str = "bank"
    reference: str = ""

@router.get("/accounts", response_model=List[AccountRead])
async def list_accounts(
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR, ROLE_MANAGER, ROLE_LEAD, ROLE_ORGADMIN, ROLE_SUPERADMIN
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    """List general ledger accounts. God Mode sees all."""
    db, org_id, is_god = db_context
    offset = (page - 1) * limit
    
    query = select(Account)
    if not is_god:
        query = query.where(Account.organization_id == org_id)
    
    result = await db.execute(query.offset(offset).limit(limit))
    return result.scalars().all()

@router.post("/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_in: AccountCreate,
    current_user: User = Depends(require_roles(
        ROLE_MANAGER, ROLE_LEAD, ROLE_ORGADMIN, ROLE_SUPERADMIN
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    db, org_id, is_god = db_context
    target_org_id = org_id if org_id else 1
    
    new_account = Account(**account_in.model_dump(), organization_id=target_org_id)
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    return new_account

@router.get("/entities", response_model=List[EntityRead])
async def list_entities(
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR, ROLE_MANAGER, ROLE_LEAD, ROLE_ORGADMIN, ROLE_SUPERADMIN
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    """List multi-entity accounting structures scoped to the organization."""
    db, org_id, is_god = db_context
    query = select(Entity)
    if not is_god:
        query = query.where(Entity.organization_id == org_id)

    result = await db.execute(query)
    return result.scalars().all()

@router.post("/entities", response_model=EntityRead, status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity_in: EntityCreate,
    current_user: User = Depends(require_roles(
        ROLE_MANAGER, ROLE_LEAD, ROLE_ORGADMIN, ROLE_SUPERADMIN
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    db, org_id, is_god = db_context
    target_org_id = org_id if org_id else 1

    new_entity = Entity(**entity_in.model_dump(), organization_id=target_org_id)
    db.add(new_entity)
    await db.commit()
    await db.refresh(new_entity)
    return new_entity

@router.get("/invoices", response_model=List[InvoiceRead])
async def list_invoices(
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR, ROLE_MANAGER, ROLE_LEAD, ROLE_ORGADMIN, ROLE_SUPERADMIN
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    """List invoices. God Mode sees all."""
    db, org_id, is_god = db_context
    offset = (page - 1) * limit
    
    query = select(Invoice)
    if not is_god:
        query = query.where(Invoice.organization_id == org_id)
    
    result = await db.execute(query.offset(offset).limit(limit))
    return result.scalars().all()

@router.post("/invoices", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_in: InvoiceCreate,
    current_user: User = Depends(require_roles(
        ROLE_MANAGER, ROLE_LEAD, ROLE_ORGADMIN, ROLE_SUPERADMIN
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    """Create an invoice with multiple line items and auto-calculate totals."""
    db, org_id, is_god = db_context
    target_org_id = org_id if org_id else 1

    customer = await db.scalar(
        select(Customer).where(
            Customer.id == invoice_in.customer_id,
            Customer.organization_id == target_org_id,
        )
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found in your organization")
    
    # Create the base invoice
    invoice_data = invoice_in.model_dump(exclude={"lines"})
    new_invoice = Invoice(**invoice_data, organization_id=target_org_id)
    
    total_amount = 0.0
    # Process line items
    for line_in in invoice_in.lines:
        line_total = line_in.qty * line_in.unit_price
        total_amount += line_total
        
        new_line = InvoiceLine(
            **line_in.model_dump(),
            organization_id=target_org_id,
            total=line_total,
            invoice=new_invoice
        )
        db.add(new_line)
    
    new_invoice.total_amount = total_amount
    db.add(new_invoice)
    
    await db.commit()
    await db.refresh(new_invoice)
    return new_invoice

@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR, ROLE_MANAGER, ROLE_LEAD, ROLE_ORGADMIN, ROLE_SUPERADMIN
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    db, org_id, is_god = db_context
    
    query = select(Invoice).where(Invoice.id == invoice_id)
    if not is_god:
        query = query.where(Invoice.organization_id == org_id)
    
    # Use selectinload to ensure related data is available for the PDF renderer
    result = await db.execute(query.options(selectinload(Invoice.lines), selectinload(Invoice.customer)))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.post("/invoices/{invoice_id}/pay", response_model=InvoiceRead)
async def pay_invoice(
    invoice_id: int,
    payload: PaymentPayload | None = None,
    current_user: User = Depends(require_roles(
        ROLE_MANAGER, ROLE_LEAD, ROLE_ORGADMIN, ROLE_SUPERADMIN
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    """
    Marks an invoice as paid and automatically posts a Journal Entry.
    Debit: Cash (1000), Credit: Accounts Receivable (1100).
    """
    db, org_id, is_god = db_context
    
    stmt = select(Invoice).where(Invoice.id == invoice_id)
    if not is_god:
        stmt = stmt.where(Invoice.organization_id == org_id)
    
    res = await db.execute(stmt)
    invoice = res.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if payload and payload.reference:
        existing_payment = await db.scalar(
            select(Payment).where(
                Payment.invoice_id == invoice.id,
                Payment.reference == payload.reference,
            )
        )
        if existing_payment:
            await db.refresh(invoice)
            return invoice

    outstanding = Decimal(str(invoice.total_amount)) - Decimal(str(invoice.paid_amount or 0))
    amount = payload.amount if payload and payload.amount is not None else outstanding
    if invoice.status == "paid" or outstanding <= 0:
        raise HTTPException(status_code=400, detail="Invoice is already paid")
    if amount > outstanding:
        raise HTTPException(status_code=400, detail="Payment exceeds invoice outstanding balance")

    try:
        async with db.begin_nested():
            invoice.paid_amount = invoice.paid_amount + amount
            invoice.status = "paid" if invoice.paid_amount >= invoice.total_amount else "partially_paid"
            payment_reference = (payload.reference if payload else "") or f"invoice-{invoice.id}-{date.today().isoformat()}"
            payment = Payment(
                organization_id=invoice.organization_id,
                amount=amount,
                date=date.today(),
                method=payload.method if payload else "bank",
                reference=payment_reference,
                invoice_id=invoice.id,
            )
            db.add(payment)
            await db.flush()

            acc_stmt = select(Account).where(Account.organization_id == (org_id or invoice.organization_id))
            acc_res = await db.execute(acc_stmt)
            accounts = {a.code: a.id for a in acc_res.scalars().all()}
            cash_acc_id = accounts.get("1000")
            ar_acc_id = accounts.get("1100")
            if not cash_acc_id:
                cash_account = Account(organization_id=invoice.organization_id, name="Cash", type="Asset", code="1000")
                db.add(cash_account)
                await db.flush()
                cash_acc_id = cash_account.id
            if not ar_acc_id:
                ar_account = Account(organization_id=invoice.organization_id, name="Accounts Receivable", type="Asset", code="1100")
                db.add(ar_account)
                await db.flush()
                ar_acc_id = ar_account.id

            await post_journal_entry(
                db=db,
                org_id=invoice.organization_id,
                description=f"Payment received for Invoice {invoice.number}",
                lines=[
                    {"account_id": cash_acc_id, "debit": float(amount)},
                    {"account_id": ar_acc_id, "credit": float(amount)},
                ],
            )

        await db.commit()
        await db.refresh(invoice)
        return invoice
    except JournalValidationError:
        await db.rollback()
        logger.error("Failed to process invoice payment: journal validation failed")
        raise HTTPException(status_code=400, detail="Accounting post failed: journal is unbalanced")
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to process invoice payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Accounting post failed")

@router.post("/logo", status_code=status.HTTP_200_OK)
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(
        ROLE_ORGADMIN, ROLE_SUPERADMIN
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    """Upload organization logo for use in invoices."""
    db, org_id, is_god = db_context
    if is_god:
        raise HTTPException(status_code=403, detail="Super Admin cannot upload logos directly. Use an Org context.")

    allowed_ext = {'png', 'jpg', 'jpeg'}
    ext = file.filename.split('.')[-1].lower()
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="Only PNG and JPG files are supported.")

    logo_dir = os.path.join("static", "uploads", "logos")
    os.makedirs(logo_dir, exist_ok=True)

    # Clean up any existing logos for this organization
    for existing in glob.glob(os.path.join(logo_dir, f"logo_{org_id}.*")):
        os.remove(existing)

    file_path = os.path.join(logo_dir, f"logo_{org_id}.{ext}")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Update organization's logo_url
    stmt = select(Organization).where(Organization.id == org_id)
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()
    if org:
        org.logo_url = f"/{file_path}"
        await db.commit()

    return {"status": "success", "message": "Logo uploaded successfully", "path": f"/{file_path}"}

@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: int,
    template: str = "modern",
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR, ROLE_MANAGER, ROLE_LEAD, ROLE_ORGADMIN, ROLE_SUPERADMIN
    )),
    db_context: tuple = Depends(get_org_db_session)
):
    """Generate and download a PDF invoice with template support."""
    db, org_id, is_god = db_context
    
    stmt = select(Invoice).where(Invoice.id == invoice_id).options(
        selectinload(Invoice.lines), 
        selectinload(Invoice.customer)
    )
    if not is_god:
        stmt = stmt.where(Invoice.organization_id == org_id)
        
    res = await db.execute(stmt)
    invoice = res.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check for organization logo
    logo_path = None
    logo_dir = os.path.join("static", "uploads", "logos")
    logo_pattern = os.path.join(logo_dir, f"logo_{org_id}.*")
    matches = glob.glob(logo_pattern)
    if matches:
        # Use absolute path for PDF engine
        logo_path = os.path.abspath(matches[0])
    
    pdf_buffer = pdf_service.generate_invoice_pdf(invoice, f"invoices/{template}.html", logo_path=logo_path)
    
    return Response(
        content=pdf_buffer.read(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_{invoice.number}.pdf"
        }
    )

@router.get("/settings/history")
async def get_settings_history(
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    db_context: tuple = Depends(get_org_db_session)
):
    """Get the history of changes to organization settings."""
    db, org_id, is_god = db_context
    
    query = (
        select(SettingsChangeLog)
        .where(SettingsChangeLog.organization_id == org_id)
        .options(selectinload(SettingsChangeLog.user))
        .order_by(SettingsChangeLog.changed_at.desc())
        .limit(20)
    )
    
    result = await db.execute(query)
    logs = result.scalars().all()
    return logs