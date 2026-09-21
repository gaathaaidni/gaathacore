from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.books import Invoice
from app.models.inventory import Item, StockRecord
from app.models.finance import Expense, ApprovalRequest
from app.models.user import User
from app.utils.dependencies import get_db, require_roles
from app.utils.roles import (
    ROLE_AUDITOR,
    ROLE_LEAD,
    ROLE_MANAGER,
    ROLE_ORGADMIN,
    ROLE_SUPERADMIN,
)
from app.schemas.dashboard import KPISummary

router = APIRouter(prefix="/api/v2/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=KPISummary)
async def get_kpi_summary(
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    org_id = current_user.organization_id

    # 1. Total Sales (All invoices sum)
    sales_stmt = select(func.sum(Invoice.total_amount)).where(Invoice.organization_id == org_id)
    sales_res = await db.execute(sales_stmt)
    total_sales = sales_res.scalar() or 0.0

    # 2. Paid Invoices Sum (Cash Flow indicator)
    paid_stmt = select(func.sum(Invoice.total_amount)).where(
        Invoice.organization_id == org_id, 
        Invoice.status == 'paid'
    )
    paid_res = await db.execute(paid_stmt)
    paid_sum = paid_res.scalar() or 0.0

    # 3. Low Stock Items Count
    # Items where total quantity across all warehouses < min_stock_level
    low_stock_stmt = (
        select(Item.id)
        .join(StockRecord)
        .where(Item.organization_id == org_id)
        .group_by(Item.id, Item.min_stock_level)
        .having(func.sum(StockRecord.quantity) < Item.min_stock_level)
    )
    low_stock_res = await db.execute(low_stock_stmt)
    low_stock_count = len(low_stock_res.all())

    # 4. Expense Breakdown
    expense_stmt = select(
        Expense.category, func.sum(Expense.amount)
    ).where(Expense.organization_id == org_id).group_by(Expense.category)
    expense_res = await db.execute(expense_stmt)
    expense_breakdown = {row[0]: row[1] for row in expense_res.all()}

    # 5. Pending Approvals Count
    approval_stmt = select(func.count(ApprovalRequest.id)).where(
        ApprovalRequest.organization_id == org_id,
        ApprovalRequest.status == 'pending'
    )
    approval_res = await db.execute(approval_stmt)
    pending_approvals = approval_res.scalar() or 0

    return {
        "total_sales": total_sales,
        "paid_invoices_sum": paid_sum,
        "low_stock_count": low_stock_count,
        "expense_breakdown": expense_breakdown,
        "pending_approvals_count": pending_approvals
    }