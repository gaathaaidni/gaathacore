from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models.crm import Customer
from app.models.expenses import Vendor
from app.models.inventory import Item, StockRecord, StockTransaction, Warehouse
from app.models.purchase_order import PurchaseOrder
from app.models.books import Account, Invoice, InvoiceLine
from app.models.transactions import (
    Fulfillment, PurchaseReceipt, PurchaseReceiptLine, Quotation, QuotationLine,
    SalesOrder, SalesOrderLine, VendorBill, VendorBillPayment,
)
from app.models.user import User
from app.schemas.transactions import (
    FulfillmentCreate, PurchaseReceiptCreate, QuotationCreate, QuotationRead,
    SalesOrderCreate, SalesOrderRead, StatusUpdate, VendorBillCreate,
    BillPaymentCreate,
)
from app.utils.dependencies import get_current_org_id, get_current_user, require_roles
from app.utils.roles import ROLE_LEAD, ROLE_MANAGER, ROLE_ORGADMIN, ROLE_SUPERADMIN
from app.services.accounting import JournalValidationError, post_journal_entry

router = APIRouter(prefix="/api/v2/transactions", tags=["ERP Transactions"])
WRITE = (ROLE_LEAD, ROLE_MANAGER, ROLE_ORGADMIN, ROLE_SUPERADMIN)


async def owned(db, model, record_id: int, org_id: int):
    org_column = model.organization_id if hasattr(model, "organization_id") else model.org_id
    result = await db.execute(select(model).where(model.id == record_id, org_column == org_id))
    return result.scalar_one_or_none()


async def validate_lines(db, lines, org_id):
    if not lines:
        raise HTTPException(422, "At least one line is required")
    for line in lines:
        item = await owned(db, Item, line.item_id, org_id)
        if not item:
            raise HTTPException(404, "Item not found in your organization")


def totals(lines):
    subtotal = sum((line.quantity * line.unit_price for line in lines), Decimal("0"))
    tax = sum((line.tax for line in lines), Decimal("0"))
    return subtotal, tax, subtotal + tax


@router.post("/quotations", response_model=QuotationRead, status_code=201)
async def create_quotation(payload: QuotationCreate, db: AsyncSession = Depends(get_db), org_id: int = Depends(get_current_org_id), _=Depends(require_roles(*WRITE))):
    if not await owned(db, Customer, payload.customer_id, org_id):
        raise HTTPException(404, "Customer not found in your organization")
    await validate_lines(db, payload.lines, org_id)
    subtotal, tax, total = totals(payload.lines)
    quotation = Quotation(**payload.model_dump(exclude={"lines"}), organization_id=org_id, created_by=_.id, subtotal=subtotal, tax=tax, total=total)
    db.add(quotation)
    await db.flush()
    for line in payload.lines:
        db.add(QuotationLine(**line.model_dump(), quotation_id=quotation.id, line_total=line.quantity * line.unit_price + line.tax))
    await db.commit(); await db.refresh(quotation)
    return quotation


@router.patch("/quotations/{quotation_id}", response_model=QuotationRead)
async def update_quotation(quotation_id: int, payload: StatusUpdate, db: AsyncSession = Depends(get_db), org_id: int = Depends(get_current_org_id), _=Depends(require_roles(*WRITE))):
    quotation = await owned(db, Quotation, quotation_id, org_id)
    if not quotation: raise HTTPException(404, "Quotation not found")
    if payload.status not in {"draft", "sent", "accepted", "rejected", "expired", "cancelled"}: raise HTTPException(422, "Invalid quotation status")
    quotation.status = payload.status
    await db.commit(); await db.refresh(quotation)
    return quotation


@router.post("/quotations/{quotation_id}/convert", response_model=SalesOrderRead, status_code=201)
async def convert_quotation(quotation_id: int, payload: SalesOrderCreate, db: AsyncSession = Depends(get_db), org_id: int = Depends(get_current_org_id), _=Depends(require_roles(*WRITE))):
    quotation = await owned(db, Quotation, quotation_id, org_id)
    if not quotation or quotation.status != "accepted": raise HTTPException(409, "Only an accepted quotation can be converted")
    if payload.customer_id != quotation.customer_id: raise HTTPException(422, "Customer must match quotation")
    await validate_lines(db, payload.lines, org_id)
    subtotal, tax, total = totals(payload.lines)
    order = SalesOrder(**payload.model_dump(exclude={"lines", "quotation_id"}), quotation_id=quotation.id, organization_id=org_id, created_by=_.id, subtotal=subtotal, tax=tax, total=total)
    db.add(order); await db.flush()
    for line in payload.lines:
        db.add(SalesOrderLine(**line.model_dump(), sales_order_id=order.id, line_total=line.quantity * line.unit_price + line.tax))
    await db.commit(); await db.refresh(order)
    return order


@router.patch("/sales-orders/{order_id}", response_model=SalesOrderRead)
async def update_order(order_id: int, payload: StatusUpdate, db: AsyncSession = Depends(get_db), org_id: int = Depends(get_current_org_id), _=Depends(require_roles(*WRITE))):
    order = (await db.execute(select(SalesOrder).options(selectinload(SalesOrder.lines)).where(SalesOrder.id == order_id, SalesOrder.organization_id == org_id))).scalar_one_or_none()
    if not order: raise HTTPException(404, "Sales order not found")
    if payload.status not in {"draft", "confirmed", "fulfilled", "cancelled"}: raise HTTPException(422, "Invalid sales order status")
    order.status = payload.status
    await db.commit(); await db.refresh(order)
    return order


@router.post("/sales-orders/{order_id}/invoice", status_code=201)
async def invoice_order(order_id: int, number: str, db: AsyncSession = Depends(get_db), org_id: int = Depends(get_current_org_id), _=Depends(require_roles(*WRITE))):
    order = (await db.execute(select(SalesOrder).options(selectinload(SalesOrder.lines)).where(SalesOrder.id == order_id, SalesOrder.organization_id == org_id))).scalar_one_or_none()
    if not order or order.status != "fulfilled": raise HTTPException(409, "Only a fulfilled order can be invoiced")
    if await db.scalar(select(Invoice).where(Invoice.number == number)): raise HTTPException(409, "Invoice number already exists")
    invoice = Invoice(organization_id=org_id, number=number, customer_id=order.customer_id, date=order.order_date, currency=order.currency, total_amount=float(order.total), status="unpaid", notes=order.notes)
    db.add(invoice); await db.flush()
    for line in order.lines:
        db.add(InvoiceLine(organization_id=org_id, invoice_id=invoice.id, item_id=line.item_id, description=line.description, qty=float(line.quantity), unit_price=float(line.unit_price), total=float(line.line_total)))
    await db.commit(); await db.refresh(invoice)
    return {"id": invoice.id, "number": invoice.number, "total": invoice.total_amount, "status": invoice.status}


@router.post("/sales-orders/{order_id}/fulfill", status_code=201)
async def fulfill_order(order_id: int, payload: FulfillmentCreate, db: AsyncSession = Depends(get_db), org_id: int = Depends(get_current_org_id), _=Depends(require_roles(*WRITE))):
    order = (await db.execute(select(SalesOrder).options(selectinload(SalesOrder.lines)).where(SalesOrder.id == order_id, SalesOrder.organization_id == org_id))).scalar_one_or_none()
    if not order or order.status != "confirmed": raise HTTPException(409, "Only a confirmed order can be fulfilled")
    warehouse = await owned(db, Warehouse, payload.warehouse_id, org_id)
    if not warehouse: raise HTTPException(404, "Warehouse not found in your organization")
    if await db.scalar(select(Fulfillment).where(Fulfillment.sales_order_id == order.id)): raise HTTPException(409, "Sales order was already fulfilled")
    for line in order.lines:
        record = (await db.execute(select(StockRecord).where(StockRecord.organization_id == org_id, StockRecord.item_id == line.item_id, StockRecord.warehouse_id == warehouse.id).with_for_update())).scalar_one_or_none()
        if not record or record.quantity < float(line.quantity): raise HTTPException(409, "Insufficient stock")
        record.quantity -= float(line.quantity); line.fulfilled_quantity = line.quantity
        db.add(StockTransaction(organization_id=org_id, item_id=line.item_id, warehouse_id=warehouse.id, quantity=-float(line.quantity), transaction_type="SALE", note=order.order_number))
    order.status = "fulfilled"
    fulfillment = Fulfillment(organization_id=org_id, sales_order_id=order.id, warehouse_id=warehouse.id, fulfillment_number=payload.fulfillment_number)
    db.add(fulfillment); await db.commit(); await db.refresh(fulfillment)
    return {"id": fulfillment.id, "status": fulfillment.status, "sales_order_id": order.id}


@router.post("/purchase-receipts", status_code=201)
async def create_purchase_receipt(payload: PurchaseReceiptCreate, db: AsyncSession = Depends(get_db), org_id: int = Depends(get_current_org_id), _=Depends(require_roles(*WRITE))):
    po = await owned(db, PurchaseOrder, payload.purchase_order_id, org_id)
    if not po or po.status not in {"ordered", "received"}: raise HTTPException(409, "Purchase order is not ready for receipt")
    warehouse = await owned(db, Warehouse, payload.warehouse_id, org_id)
    if not warehouse: raise HTTPException(404, "Warehouse not found in your organization")
    if await db.scalar(select(PurchaseReceipt).where(PurchaseReceipt.purchase_order_id == po.id)): raise HTTPException(409, "Purchase order was already received")
    receipt = PurchaseReceipt(organization_id=org_id, purchase_order_id=po.id, vendor_id=po.vendor_id, warehouse_id=warehouse.id, receipt_number=payload.receipt_number)
    db.add(receipt); await db.flush()
    for line in payload.lines:
        if not await owned(db, Item, line.item_id, org_id): raise HTTPException(404, "Item not found in your organization")
        record = (await db.execute(select(StockRecord).where(StockRecord.organization_id == org_id, StockRecord.item_id == line.item_id, StockRecord.warehouse_id == warehouse.id).with_for_update())).scalar_one_or_none()
        if record: record.quantity += float(line.received_quantity)
        else: db.add(StockRecord(organization_id=org_id, item_id=line.item_id, warehouse_id=warehouse.id, quantity=line.received_quantity))
        db.add(PurchaseReceiptLine(receipt_id=receipt.id, item_id=line.item_id, ordered_quantity=line.received_quantity, received_quantity=line.received_quantity))
        db.add(StockTransaction(organization_id=org_id, item_id=line.item_id, warehouse_id=warehouse.id, quantity=line.received_quantity, transaction_type="PURCHASE_RECEIPT", note=po.reference_number))
    po.status = "received"; await db.commit(); await db.refresh(receipt)
    return {"id": receipt.id, "status": receipt.status, "purchase_order_id": po.id}


@router.post("/vendor-bills", status_code=201)
async def create_vendor_bill(payload: VendorBillCreate, db: AsyncSession = Depends(get_db), org_id: int = Depends(get_current_org_id), _=Depends(require_roles(*WRITE))):
    vendor = await owned(db, Vendor, payload.vendor_id, org_id)
    if not vendor: raise HTTPException(404, "Vendor not found in your organization")
    if payload.purchase_order_id:
        purchase_order = await owned(db, PurchaseOrder, payload.purchase_order_id, org_id)
        if not purchase_order:
            raise HTTPException(404, "Purchase order not found in your organization")
        if purchase_order.vendor_id != vendor.id:
            raise HTTPException(422, "Purchase order vendor does not match bill vendor")
    total = payload.subtotal + payload.tax
    bill = VendorBill(**payload.model_dump(), organization_id=org_id, total=total)
    db.add(bill); await db.commit(); await db.refresh(bill)
    return {"id": bill.id, "status": bill.status, "total": bill.total, "outstanding": bill.total - bill.paid_amount}


@router.post("/vendor-bills/{bill_id}/pay")
async def pay_vendor_bill(bill_id: int, payload: BillPaymentCreate, db: AsyncSession = Depends(get_db), org_id: int = Depends(get_current_org_id), _=Depends(require_roles(*WRITE))):
    bill = await owned(db, VendorBill, bill_id, org_id)
    if not bill: raise HTTPException(404, "Vendor bill not found")
    reference = payload.reference.strip() or f"vendor-bill-{bill.id}"
    existing_payment = await db.scalar(
        select(VendorBillPayment).where(
            VendorBillPayment.vendor_bill_id == bill.id,
            VendorBillPayment.reference == reference,
        )
    )
    if existing_payment:
        await db.refresh(bill)
        return {"id": bill.id, "status": bill.status, "paid_amount": bill.paid_amount, "outstanding": bill.total - bill.paid_amount}
    outstanding = bill.total - bill.paid_amount
    if payload.amount > outstanding: raise HTTPException(400, "Payment exceeds bill outstanding balance")
    try:
        async with db.begin_nested():
            bill.paid_amount += payload.amount
            bill.status = "paid" if bill.paid_amount == bill.total else "partially_paid"
            db.add(
                VendorBillPayment(
                    organization_id=org_id,
                    vendor_bill_id=bill.id,
                    amount=payload.amount,
                    reference=reference,
                )
            )

            account_result = await db.execute(
                select(Account).where(Account.organization_id == org_id)
            )
            accounts = {account.code: account for account in account_result.scalars()}
            cash_account = accounts.get("1000")
            payable_account = accounts.get("2000")
            if cash_account is None:
                cash_account = Account(organization_id=org_id, name="Cash", type="Asset", code="1000")
                db.add(cash_account)
                await db.flush()
            if payable_account is None:
                payable_account = Account(organization_id=org_id, name="Accounts Payable", type="Liability", code="2000")
                db.add(payable_account)
                await db.flush()

            await post_journal_entry(
                db=db,
                org_id=org_id,
                description=f"Payment made for Vendor Bill {bill.bill_number}",
                lines=[
                    {"account_id": payable_account.id, "debit": float(payload.amount)},
                    {"account_id": cash_account.id, "credit": float(payload.amount)},
                ],
            )
        await db.commit()
        await db.refresh(bill)
        return {"id": bill.id, "status": bill.status, "paid_amount": bill.paid_amount, "outstanding": bill.total - bill.paid_amount}
    except JournalValidationError as exc:
        await db.rollback()
        raise HTTPException(422, str(exc)) from exc
