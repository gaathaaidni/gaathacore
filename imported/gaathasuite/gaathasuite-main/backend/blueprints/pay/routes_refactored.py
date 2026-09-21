from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from app.db import AsyncSessionLocal
from app.models.books import Invoice, Payment
from app.utils.dependencies import get_db, require_roles
from app.utils.roles import ROLE_SUPERADMIN
from pydantic import BaseModel
from datetime import date
import os
import re
import uuid
import json
import hmac
import hashlib
import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pay", tags=["Payments"])

def get_cashfree_api_base() -> str:
    env = os.environ.get("CASHFREE_ENV", "TEST").upper()
    return "https://api.cashfree.com/pg/v1" if env == "PROD" else "https://sandbox.cashfree.com/pg/v1"

def verify_cashfree_signature(payload: bytes, signature: str, secret: str) -> bool:
    try:
        computed_signature = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(computed_signature, signature)
    except Exception as e:
        logger.error(f"Cashfree signature verification failed: {e}")
        return False

class CashfreeOrderRequest(BaseModel):
    invoice_id: int
    return_url: Optional[str] = None

def build_cashfree_order_id(invoice_id: int) -> str:
    return f"inv_{invoice_id}_{uuid.uuid4().hex[:8]}"

@router.post("/cashfree/create-order")
async def create_cashfree_order(
    order_request: CashfreeOrderRequest,
    current_user = Depends(require_roles(ROLE_SUPERADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Create a Cashfree order link for an invoice."""
    client_id = os.environ.get("CASHFREE_CLIENT_ID")
    client_secret = os.environ.get("CASHFREE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Cashfree credentials not configured")

    stmt = select(Invoice).where(Invoice.id == order_request.invoice_id)
    result = await db.execute(stmt.options(selectinload(Invoice.customer)))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "paid":
        raise HTTPException(status_code=400, detail="Invoice is already paid")

    customer = getattr(invoice, "customer", None)
    order_id = build_cashfree_order_id(invoice.id)
    return_url = order_request.return_url or os.environ.get(
        "CASHFREE_RETURN_URL",
        "https://gaathasuite.gaatha.tech/pay/cashfree/return"
    )

    payload = {
        "order_id": order_id,
        "order_amount": float(invoice.total_amount),
        "order_currency": "INR",
        "order_note": f"Payment for invoice {invoice.number}",
        "customer_details": {
            "customer_id": str(invoice.id),
            "customer_name": getattr(customer, "name", "Customer"),
            "customer_email": getattr(customer, "email", ""),
            "customer_phone": getattr(customer, "phone", "")
        },
        "return_url": return_url,
        "notify_url": os.environ.get(
            "CASHFREE_NOTIFY_URL",
            "https://gaathasuite.gaatha.tech/pay/webhook/cashfree"
        )
    }

    base_url = get_cashfree_api_base()
    response = requests.post(
        f"{base_url}/orders",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-version": "2022-01-01",
            "x-client-id": client_id,
            "x-client-secret": client_secret,
        },
        timeout=30,
    )

    if response.status_code != 200:
        logger.error("Cashfree order create failed: %s", response.text)
        raise HTTPException(status_code=502, detail="Failed to create Cashfree order")

    data = response.json()
    if data.get("status") != "OK":
        logger.error("Cashfree order response error: %s", data)
        raise HTTPException(status_code=502, detail=data.get("message", "Cashfree order creation failed"))

    return {
        "order_id": data.get("order_id"),
        "payment_link": data.get("payment_link"),
        "status": data.get("status"),
        "invoice_id": invoice.id
    }

@router.get("/cashfree/return")
async def cashfree_return(
    order_id: Optional[str] = None,
    order_amount: Optional[float] = None,
    order_currency: Optional[str] = None,
    reference_id: Optional[str] = None,
    tx_status: Optional[str] = None
):
    return {
        "provider": "cashfree",
        "order_id": order_id,
        "reference_id": reference_id,
        "tx_status": tx_status,
        "order_amount": order_amount,
        "order_currency": order_currency
    }

@router.post("/webhook/cashfree")
async def cashfree_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("x-cashfree-signature")
    secret = os.environ.get("CASHFREE_CLIENT_SECRET")

    if not signature or not secret or not verify_cashfree_signature(payload, signature, secret):
        raise HTTPException(status_code=400, detail="Invalid Cashfree signature")

    event = json.loads(payload)
    order_id = event.get("orderId") or event.get("order_id")
    amount = float(event.get("orderAmount") or event.get("order_amount") or 0)
    tx_status = event.get("txStatus") or event.get("status")
    reference_id = event.get("referenceId") or event.get("reference_id")

    invoice_id = None
    if order_id:
        match = re.match(r"inv_(\d+)_", order_id)
        if match:
            invoice_id = int(match.group(1))

    if tx_status == "SUCCESS" and invoice_id:
        await process_payment(db, invoice_id, amount, "cashfree", reference_id or order_id)

    return {"status": "ok"}

async def process_payment(db: AsyncSession, invoice_id: int, amount: float, method: str, reference: str):
    """Process payment and update invoice status"""
    # Get invoice
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        logger.error(f"Invoice {invoice_id} not found")
        return
    
    # Create payment record
    payment = Payment(
        invoice_id=invoice_id,
        amount=amount,
        date=date.today(),
        method=method,
        reference=reference
    )
    db.add(payment)
    
    # Calculate total paid
    result = await db.execute(
        select(func.sum(Payment.amount)).where(Payment.invoice_id == invoice_id)
    )
    total_paid = result.scalar() or 0
    total_paid += amount
    
    # Update invoice status
    if total_paid >= invoice.total_amount:
        invoice.status = 'paid'
    else:
        invoice.status = 'partially_paid'
    
    await db.commit()
    logger.info(f"Payment processed for invoice {invoice_id}: {amount} via {method}")

# Additional payment endpoints can be added here