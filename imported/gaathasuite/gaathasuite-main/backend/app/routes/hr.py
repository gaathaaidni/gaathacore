from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hr import Department, Employee, Payslip, AttendanceRecord, PerformanceReview
from app.models.user import User
from app.schemas.hr import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeUpdate,
    PayslipCreate,
    PayslipRead,
    PayslipCalculationCreate,
    PayslipCalculationRead,
    PayrollSummary,
    AttendanceCreate,
    AttendanceRead,
    PerformanceReviewCreate,
    PerformanceReviewRead,
    PerformanceReviewUpdate,
)
from app.utils.dependencies import get_db, get_current_user, get_current_org_id, require_roles
from app.utils.roles import ROLE_ORGADMIN, ROLE_SUPERADMIN, ROLE_MANAGER

router = APIRouter(prefix="/api/v2/hr", tags=["HR"])


@router.get("/employees", response_model=List[EmployeeRead])
async def list_employees(
    current_user: User = Depends(get_current_user),
    current_org_id: int = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Employee).options(selectinload(Employee.department)).order_by(Employee.name)
    if getattr(current_user, 'role', '') != ROLE_SUPERADMIN:
        stmt = stmt.where(Employee.organization_id == current_org_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/employees/{employee_id}", response_model=EmployeeRead)
async def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    current_org_id: int = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Employee).options(selectinload(Employee.department)).where(Employee.id == employee_id)
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    if not employee or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and employee.organization_id != current_org_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.post("/employees", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN, ROLE_MANAGER)),
    current_org_id: Optional[int] = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    if employee_data.department_id is not None:
        dept_stmt = select(Department).where(Department.id == employee_data.department_id)
        dept = (await db.execute(dept_stmt)).scalar_one_or_none()
        if not dept or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and dept.organization_id != current_org_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department for the current organization")

    employee = Employee(**employee_data.model_dump())
    if getattr(current_user, 'role', '') == ROLE_SUPERADMIN:
        if employee.organization_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="organization_id is required for superadmins")
    else:
        employee.organization_id = current_org_id

    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    return employee


@router.put("/employees/{employee_id}", response_model=EmployeeRead)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN, ROLE_MANAGER)),
    current_org_id: Optional[int] = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    if not employee or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and employee.organization_id != current_org_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if employee_data.department_id is not None:
        dept_stmt = select(Department).where(Department.id == employee_data.department_id)
        dept = (await db.execute(dept_stmt)).scalar_one_or_none()
        if not dept or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and dept.organization_id != current_org_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department for the current organization")

    if employee_data.organization_id is not None:
        if getattr(current_user, 'role', '') != ROLE_SUPERADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change organization")
        employee.organization_id = employee_data.organization_id

    for field, value in employee_data.model_dump(exclude_unset=True, exclude={'organization_id'}).items():
        setattr(employee, field, value)

    await db.commit()
    await db.refresh(employee)
    return employee


@router.delete("/employees/{employee_id}")
async def delete_employee(
    employee_id: int,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN)),
    current_org_id: int = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Employee).where(Employee.id == employee_id)
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    if not employee or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and employee.organization_id != current_org_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    await db.delete(employee)
    await db.commit()
    return {"deleted": True}


@router.get("/payslips", response_model=List[PayslipRead])
async def list_payslips(
    employee_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    current_org_id: int = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Payslip).options(selectinload(Payslip.employee)).order_by(Payslip.created_at.desc())
    if employee_id:
        stmt = stmt.where(Payslip.employee_id == employee_id)
    if getattr(current_user, 'role', '') != ROLE_SUPERADMIN:
        stmt = stmt.where(Payslip.organization_id == current_org_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/payslips", response_model=PayslipRead, status_code=status.HTTP_201_CREATED)
async def create_payslip(
    payslip_data: PayslipCreate,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN, ROLE_MANAGER)),
    current_org_id: int = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Employee).where(Employee.id == payslip_data.employee_id)
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    if not employee or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and employee.organization_id != current_org_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    payload = payslip_data.model_dump(exclude_unset=True)
    if payload.get("net") is None:
        payload["net"] = payload.get("gross", 0.0)
    payload["organization_id"] = employee.organization_id
    payslip = Payslip(**payload)
    db.add(payslip)
    await db.commit()
    await db.refresh(payslip)
    return payslip


@router.post("/payslips/{payslip_id}/process", response_model=PayslipRead)
async def process_payslip(
    payslip_id: int,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN, ROLE_MANAGER)),
    current_org_id: int = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Payslip).where(Payslip.id == payslip_id)
    result = await db.execute(stmt)
    payslip = result.scalar_one_or_none()
    if not payslip or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and payslip.organization_id != current_org_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payslip not found")
    payslip.status = 'processed'
    await db.commit()
    await db.refresh(payslip)
    return payslip


def compute_payroll_from_attendance(employee: Employee, data: PayslipCalculationCreate, total_hours: float) -> dict:
    pay_type = (data.pay_type or 'monthly').lower()
    if pay_type == 'hourly':
        hourly_rate = data.hourly_rate if data.hourly_rate is not None else employee.salary
        gross = total_hours * hourly_rate
    elif pay_type == 'piece-rate':
        gross = (data.pieces or 0) * (data.rate_per_piece or 0.0)
    else:
        gross = employee.salary / 12.0

    tax_deductions = round(gross * 0.12, 2)
    social_security = round(gross * 0.05, 2)
    insurance_deductions = round(gross * 0.02, 2)
    loan_repayment = data.loan_repayment or 0.0
    extra_deductions = data.extra_deductions or 0.0
    net = round(max(0.0, gross - tax_deductions - social_security - insurance_deductions - loan_repayment - extra_deductions), 2)

    return {
        'gross': round(gross, 2),
        'net': net,
        'tax_deductions': tax_deductions,
        'social_security': social_security,
        'insurance_deductions': insurance_deductions,
        'loan_repayment': loan_repayment,
        'total_hours': round(total_hours, 2),
    }


@router.post("/payslips/calculate", response_model=PayslipCalculationRead, status_code=status.HTTP_201_CREATED)
async def calculate_payslip(
    payslip_data: PayslipCalculationCreate,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN, ROLE_MANAGER)),
    current_org_id: int = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Employee).where(Employee.id == payslip_data.employee_id)
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    if not employee or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and employee.organization_id != current_org_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    attendance_stmt = select(func.coalesce(func.sum(AttendanceRecord.hours_worked), 0.0)).where(
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.organization_id == current_org_id,
        AttendanceRecord.date >= payslip_data.period_start,
        AttendanceRecord.date <= payslip_data.period_end,
    )
    attendance_result = await db.execute(attendance_stmt)
    total_hours = attendance_result.scalar_one() or 0.0

    payroll_values = compute_payroll_from_attendance(employee, payslip_data, total_hours)
    payslip_payload = {
        'employee_id': employee.id,
        'period_start': payslip_data.period_start,
        'period_end': payslip_data.period_end,
        'gross': payroll_values['gross'],
        'net': payroll_values['net'],
        'status': 'draft',
    }

    payslip = Payslip(**payslip_payload)
    db.add(payslip)
    await db.commit()
    await db.refresh(payslip)

    return {
        **payslip_payload,
        'id': payslip.id,
        'created_at': payslip.created_at,
        'employee_name': employee.name,
        **payroll_values,
    }


@router.get("/payroll/summary", response_model=PayrollSummary)
async def get_payroll_summary(
    current_user: User = Depends(get_current_user),
    current_org_id: Optional[int] = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    total_employees_stmt = select(func.count(Employee.id))
    total_payslips_stmt = select(func.count(Payslip.id))
    draft_payslips_stmt = select(func.count(Payslip.id)).where(Payslip.status == 'draft')
    processed_gross_stmt = select(func.coalesce(func.sum(Payslip.gross), 0.0)).where(Payslip.status == 'processed')
    processed_net_stmt = select(func.coalesce(func.sum(Payslip.net), 0.0)).where(Payslip.status == 'processed')
    attendance_hours_stmt = select(func.coalesce(func.sum(AttendanceRecord.hours_worked), 0.0))

    if getattr(current_user, 'role', '') != ROLE_SUPERADMIN:
        total_employees_stmt = total_employees_stmt.where(Employee.organization_id == current_org_id)
        total_payslips_stmt = total_payslips_stmt.where(Payslip.organization_id == current_org_id)
        draft_payslips_stmt = draft_payslips_stmt.where(Payslip.organization_id == current_org_id)
        processed_gross_stmt = processed_gross_stmt.where(Payslip.organization_id == current_org_id)
        processed_net_stmt = processed_net_stmt.where(Payslip.organization_id == current_org_id)
        attendance_hours_stmt = attendance_hours_stmt.where(AttendanceRecord.organization_id == current_org_id)

    total_employees = (await db.execute(total_employees_stmt)).scalar_one()
    total_payslips = (await db.execute(total_payslips_stmt)).scalar_one()
    draft_payslips = (await db.execute(draft_payslips_stmt)).scalar_one()
    processed_gross = (await db.execute(processed_gross_stmt)).scalar_one() or 0.0
    processed_net = (await db.execute(processed_net_stmt)).scalar_one() or 0.0
    attendance_hours = (await db.execute(attendance_hours_stmt)).scalar_one() or 0.0

    return PayrollSummary(
        total_employees=total_employees,
        total_payslips=total_payslips,
        draft_payslips=draft_payslips,
        processed_payroll_gross=round(processed_gross, 2),
        processed_payroll_net=round(processed_net, 2),
        attendance_hours=round(attendance_hours, 2),
    )


@router.get("/reviews", response_model=List[PerformanceReviewRead])
async def list_performance_reviews(
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    current_org_id: int = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PerformanceReview)
    if employee_id:
        stmt = stmt.where(PerformanceReview.employee_id == employee_id)
    if getattr(current_user, 'role', '') != ROLE_SUPERADMIN:
        stmt = stmt.where(PerformanceReview.organization_id == current_org_id)
    if status:
        stmt = stmt.where(PerformanceReview.status == status)
    stmt = stmt.order_by(PerformanceReview.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/reviews", response_model=PerformanceReviewRead, status_code=status.HTTP_201_CREATED)
async def create_performance_review(
    review_data: PerformanceReviewCreate,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN, ROLE_MANAGER)),
    current_org_id: int = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    employee_stmt = select(Employee).where(Employee.id == review_data.employee_id)
    employee_result = await db.execute(employee_stmt)
    employee = employee_result.scalar_one_or_none()
    if not employee or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and employee.organization_id != current_org_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    review_payload = review_data.model_dump(exclude_unset=True)
    review_payload['organization_id'] = employee.organization_id
    review = PerformanceReview(**review_payload)
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@router.put("/reviews/{review_id}", response_model=PerformanceReviewRead)
async def update_performance_review(
    review_id: int,
    review_data: PerformanceReviewUpdate,
    current_user: User = Depends(require_roles(ROLE_ORGADMIN, ROLE_SUPERADMIN, ROLE_MANAGER)),
    current_org_id: int = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PerformanceReview).where(PerformanceReview.id == review_id)
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()
    if not review or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and review.organization_id != current_org_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Performance review not found")

    for field, value in review_data.model_dump(exclude_unset=True).items():
        setattr(review, field, value)
    await db.commit()
    await db.refresh(review)
    return review


@router.get("/attendance", response_model=List[AttendanceRead])
async def list_attendance(
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    current_org_id: Optional[int] = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AttendanceRecord).options(selectinload(AttendanceRecord.employee))
    if getattr(current_user, 'role', '') != ROLE_SUPERADMIN:
        stmt = stmt.where(AttendanceRecord.organization_id == current_org_id)
    if employee_id:
        stmt = stmt.where(AttendanceRecord.employee_id == employee_id)
    if status:
        stmt = stmt.where(AttendanceRecord.status == status)
    if date_from:
        stmt = stmt.where(AttendanceRecord.date >= date_from)
    if date_to:
        stmt = stmt.where(AttendanceRecord.date <= date_to)
    stmt = stmt.order_by(AttendanceRecord.date.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/attendance", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    attendance_data: AttendanceCreate,
    current_org_id: Optional[int] = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payload = attendance_data.model_dump(exclude_unset=True)
    if payload.get("employee_id") is not None:
        employee_stmt = select(Employee).where(Employee.id == payload["employee_id"])
        employee = (await db.execute(employee_stmt)).scalar_one_or_none()
        if not employee or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and employee.organization_id != current_org_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee for the current organization")
        payload["organization_id"] = employee.organization_id
    else:
        payload["organization_id"] = current_org_id

    if payload.get("check_in") and payload.get("check_out"):
        duration = payload["check_out"] - payload["check_in"]
        payload["hours_worked"] = round(duration.total_seconds() / 3600, 2)
    attendance = AttendanceRecord(**payload)
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.post("/attendance/clock-in", response_model=AttendanceRead)
async def clock_in(
    current_user: User = Depends(get_current_user),
    current_org_id: Optional[int] = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    employee_stmt = select(Employee).where(Employee.email == current_user.email)
    employee_res = await db.execute(employee_stmt)
    employee = employee_res.scalar_one_or_none()
    if not employee or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and employee.organization_id != current_org_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No employee record found for current user")

    today = date.today()
    existing_stmt = select(AttendanceRecord).where(
        AttendanceRecord.organization_id == current_org_id,
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.date == today,
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing and existing.check_in:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already clocked in today")

    attendance = AttendanceRecord(
        organization_id=current_org_id,
        employee_id=employee.id,
        date=today,
        check_in=datetime.utcnow(),
        status='present'
    )
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.post("/attendance/clock-out", response_model=AttendanceRead)
async def clock_out(
    current_user: User = Depends(get_current_user),
    current_org_id: Optional[int] = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    employee_stmt = select(Employee).where(Employee.email == current_user.email)
    employee_res = await db.execute(employee_stmt)
    employee = employee_res.scalar_one_or_none()
    if not employee or (getattr(current_user, 'role', '') != ROLE_SUPERADMIN and employee.organization_id != current_org_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No employee record found for current user")

    today = date.today()
    attendance_stmt = select(AttendanceRecord).where(
        AttendanceRecord.organization_id == current_org_id,
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.date == today,
    )
    attendance = (await db.execute(attendance_stmt)).scalar_one_or_none()
    if not attendance or attendance.check_out:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active check-in found for today")

    attendance.check_out = datetime.utcnow()
    if attendance.check_in:
        attendance.hours_worked = round((attendance.check_out - attendance.check_in).total_seconds() / 3600, 2)
    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.get("/attendance/today", response_model=List[AttendanceRead])
async def get_today_attendance(
    current_user: User = Depends(get_current_user),
    current_org_id: int = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    stmt = select(AttendanceRecord).options(selectinload(AttendanceRecord.employee)).where(
        AttendanceRecord.organization_id == current_org_id,
        AttendanceRecord.date == today,
    )
    result = await db.execute(stmt)
    return result.scalars().all()
