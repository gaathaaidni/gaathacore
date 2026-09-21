from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date
from app.models.books import Invoice
from app.models.books import Account
from app.models.books import JournalLine
from app.models.finance import Expense
from app.models.user import User
from app.utils.dependencies import get_db, require_roles
from app.utils.roles import (
    ROLE_AUDITOR,
    ROLE_LEAD,
    ROLE_MANAGER,
    ROLE_ORGADMIN,
    ROLE_SUPERADMIN,
)
from app.services.pdf_service import PDFService

router = APIRouter(prefix="/api/v2/finance/reports", tags=["Finance - Reporting"])
pdf_service = PDFService()

@router.get("/profit-loss")
async def get_profit_loss(
    start_date: date = Query(..., description="Start date for the report"),
    end_date: date = Query(..., description="End date for the report"),
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """
    Generates a Profit & Loss statement for a specific period.
    Aggregates paid Invoices (Revenue) and paid Expenses (COGS/OpEx).
    """
    org_id = current_user.organization_id

    # 1. Total Revenue (Paid Invoices)
    rev_stmt = select(func.sum(Invoice.total_amount)).where(
        Invoice.organization_id == org_id,
        Invoice.status == 'paid',
        Invoice.date >= start_date,
        Invoice.date <= end_date
    )
    rev_res = await db.execute(rev_stmt)
    total_revenue = rev_res.scalar() or 0.0

    # 2. Total Costs (Paid Expenses)
    exp_stmt = select(func.sum(Expense.amount)).where(
        Expense.organization_id == org_id,
        Expense.status == 'paid',
        Expense.created_at >= start_date,
        Expense.created_at <= end_date
    )
    exp_res = await db.execute(exp_stmt)
    total_expenses = exp_res.scalar() or 0.0

    return {
        "period": {"start": start_date, "end": end_date},
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_income": total_revenue - total_expenses,
        "currency": "USD"
    }

@router.get("/profit-loss/pdf")
async def get_profit_loss_pdf(
    start_date: date = Query(..., description="Start date for the report"),
    end_date: date = Query(..., description="End date for the report"),
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """
    Generates and downloads a Profit & Loss statement as a PDF.
    """
    org_id = current_user.organization_id

    # Reuse P&L logic
    rev_stmt = select(func.sum(Invoice.total_amount)).where(
        Invoice.organization_id == org_id,
        Invoice.status == 'paid',
        Invoice.date >= start_date,
        Invoice.date <= end_date
    )
    total_revenue = (await db.execute(rev_stmt)).scalar() or 0.0

    exp_stmt = select(func.sum(Expense.amount)).where(
        Expense.organization_id == org_id,
        Expense.status == 'paid',
        Expense.created_at >= start_date,
        Expense.created_at <= end_date
    )
    total_expenses = (await db.execute(exp_stmt)).scalar() or 0.0

    report_data = {
        "period": {"start": start_date, "end": end_date},
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_income": total_revenue - total_expenses,
        "currency": "USD"
    }

    pdf_buffer = pdf_service.generate_pdf("reports/profit_loss.html", data=report_data)

    return Response(
        content=pdf_buffer.read(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=PL_Report_{start_date}_to_{end_date}.pdf"
        }
    )

@router.get("/chart-of-accounts")
async def get_chart_of_accounts(
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the organization's Chart of Accounts.
    """
    org_id = current_user.organization_id
    
    # Calculate balance: Sum(debit) - Sum(credit)
    stmt = (
        select(Account, func.sum(JournalLine.debit - JournalLine.credit).label("balance"))
        .outerjoin(JournalLine, Account.id == JournalLine.account_id)
        .where(Account.organization_id == org_id)
        .group_by(Account.id)
        .order_by(Account.code)
    )
    result = await db.execute(stmt)
    accounts_with_balance = [{"account": row[0], "balance": row[1] or 0.0} for row in result.all()]
    
    return {"organization_id": org_id, "accounts": accounts_with_balance}

@router.get("/chart-of-accounts/pdf")
async def get_chart_of_accounts_pdf(
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """
    Generates and downloads the Chart of Accounts as a PDF.
    """
    org_id = current_user.organization_id
    
    stmt = (
        select(Account, func.sum(JournalLine.debit - JournalLine.credit).label("balance"))
        .outerjoin(JournalLine, Account.id == JournalLine.account_id)
        .where(Account.organization_id == org_id)
        .group_by(Account.id)
        .order_by(Account.code)
    )
    result = await db.execute(stmt)
    accounts_with_balance = [{"account": row[0], "balance": row[1] or 0.0} for row in result.all()]

    report_data = {
        "accounts": accounts_with_balance,
        "generated_at": date.today()
    }

    pdf_buffer = pdf_service.generate_pdf("reports/chart_of_accounts.html", data=report_data)

    return Response(
        content=pdf_buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Chart_of_Accounts.pdf"}
    )

@router.get("/trial-balance")
async def get_trial_balance(
    current_user: User = Depends(require_roles(
        ROLE_AUDITOR,
        ROLE_LEAD,
        ROLE_MANAGER,
        ROLE_ORGADMIN,
        ROLE_SUPERADMIN,
    )),
    db: AsyncSession = Depends(get_db)
):
    """
    Aggregates total debits and credits for all accounts to verify ledger integrity.
    """
    org_id = current_user.organization_id
    
    stmt = (
        select(
            Account.code,
            Account.name,
            func.sum(JournalLine.debit).label("total_debit"),
            func.sum(JournalLine.credit).label("total_credit")
        )
        .join(JournalLine, Account.id == JournalLine.account_id)
        .where(Account.organization_id == org_id)
        .group_by(Account.id, Account.code, Account.name)
        .order_by(Account.code)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    report_items = []
    grand_debit = 0.0
    grand_credit = 0.0
    
    for row in rows:
        report_items.append({
            "code": row.code,
            "name": row.name,
            "debit": row.total_debit or 0.0,
            "credit": row.total_credit or 0.0
        })
        grand_debit += (row.total_debit or 0.0)
        grand_credit += (row.total_credit or 0.0)

    return {
        "organization_id": org_id,
        "generated_at": date.today(),
        "items": report_items,
        "totals": {"debit": grand_debit, "credit": grand_credit},
        "is_balanced": round(grand_debit, 2) == round(grand_credit, 2)
    }