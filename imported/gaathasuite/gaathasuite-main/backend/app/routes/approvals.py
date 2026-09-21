from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.approvals import ApprovalRequest
from app.models.expenses import Expense
from app.models.purchase_order import PurchaseOrder
from app.schemas.approvals import ApprovalRequestCreate, ApprovalRequestRead
from app.utils.dependencies import get_current_org_id, get_current_user_id, require_roles
from app.utils.roles import ROLE_MANAGER, ROLE_ORGADMIN, ROLE_SUPERADMIN


class RejectionPayload(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("/requests", response_model=List[ApprovalRequestRead])
async def list_approval_requests(
    db: AsyncSession = Depends(get_db), org_id: int = Depends(get_current_org_id)
):
    # In a real system, this would be filtered by user's approval permissions
    result = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.org_id == org_id, ApprovalRequest.status == "pending"
        )
    )
    return result.scalars().all()


@router.post("/requests", response_model=ApprovalRequestRead, status_code=201)
async def create_approval_request(
    payload: ApprovalRequestCreate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    user_id: int = Depends(get_current_user_id),
    _approver=Depends(require_roles(ROLE_MANAGER, ROLE_ORGADMIN, ROLE_SUPERADMIN)),
):
    approval_request = ApprovalRequest(
        org_id=org_id,
        document_type=payload.document_type,
        document_id=payload.document_id,
        amount=payload.amount,
        status=payload.status,
        rejection_reason=payload.reason,
    )
    db.add(approval_request)
    await db.commit()
    await db.refresh(approval_request)
    return approval_request


@router.post("/requests/{request_id}/approve", response_model=ApprovalRequestRead)
async def approve_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    user_id: int = Depends(get_current_user_id),  # User performing the approval
    _approver=Depends(require_roles(ROLE_MANAGER, ROLE_ORGADMIN, ROLE_SUPERADMIN)),
):
    result = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.id == request_id, ApprovalRequest.org_id == org_id
        )
    )
    approval_request = result.scalar_one_or_none()

    if not approval_request or approval_request.status != "pending":
        raise HTTPException(
            status_code=404, detail="Approval request not found or not pending"
        )

    # Update approval request status
    approval_request.status = "approved"
    approval_request.approved_by_user_id = user_id

    # Update associated expense status
    if approval_request.document_type == "expense":
        expense_result = await db.execute(
            select(Expense).where(
                Expense.id == approval_request.document_id,
                Expense.org_id == org_id,
            )
        )
        expense = expense_result.scalar_one_or_none()
        if expense is None:
            raise HTTPException(status_code=409, detail="Linked expense was not found")
        expense.status = "approved"

    elif approval_request.document_type == "purchase_order":
        po_result = await db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.id == approval_request.document_id,
                PurchaseOrder.org_id == org_id,
            )
        )
        po = po_result.scalar_one_or_none()
        if po is None:
            raise HTTPException(status_code=409, detail="Linked purchase order was not found")
        po.status = "ordered"

    elif approval_request.document_type not in {"expense", "purchase_order"}:
        raise HTTPException(status_code=409, detail="Unsupported approval document type")

    await db.commit()
    await db.refresh(approval_request)
    return approval_request


@router.post("/requests/{request_id}/reject", response_model=ApprovalRequestRead)
async def reject_request(
    request_id: int,
    payload: RejectionPayload,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    user_id: int = Depends(get_current_user_id),
    _approver=Depends(require_roles(ROLE_MANAGER, ROLE_ORGADMIN, ROLE_SUPERADMIN)),
):
    result = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.id == request_id,
            ApprovalRequest.org_id == org_id,
        )
    )
    approval_request = result.scalar_one_or_none()

    if not approval_request or approval_request.status != "pending":
        raise HTTPException(
            status_code=404, detail="Approval request not found or not pending"
        )

    approval_request.status = "rejected"
    approval_request.rejection_reason = payload.reason
    approval_request.approved_by_user_id = user_id
    await db.commit()
    await db.refresh(approval_request)
    return approval_request