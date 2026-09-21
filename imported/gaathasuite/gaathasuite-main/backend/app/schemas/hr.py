from __future__ import annotations
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    manager_id: Optional[int] = None


class DepartmentRead(DepartmentCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeBase(BaseModel):
    employee_code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    department_id: Optional[int] = None
    organization_id: Optional[int] = None
    position: Optional[str] = Field(None, max_length=255)
    hired_date: Optional[date] = None
    salary: float = Field(0.0, ge=0)
    is_active: Optional[bool] = True


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    department_id: Optional[int] = None
    organization_id: Optional[int] = None
    position: Optional[str] = Field(None, max_length=255)
    hired_date: Optional[date] = None
    salary: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class EmployeeRead(EmployeeBase):
    id: int
    created_at: datetime
    department_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PayslipBase(BaseModel):
    employee_id: int
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    gross: float = Field(0.0, ge=0)
    net: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field('draft', max_length=50)


class PayslipCreate(PayslipBase):
    pass


class PayslipRead(PayslipBase):
    id: int
    created_at: datetime
    employee_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PayslipCalculationCreate(BaseModel):
    employee_id: int
    period_start: date
    period_end: date
    pay_type: Optional[str] = Field('monthly', pattern='^(monthly|hourly|piece-rate)$')
    hourly_rate: Optional[float] = Field(None, ge=0)
    pieces: Optional[int] = Field(None, ge=0)
    rate_per_piece: Optional[float] = Field(None, ge=0)
    loan_repayment: Optional[float] = Field(0.0, ge=0)
    extra_deductions: Optional[float] = Field(0.0, ge=0)


class PayslipCalculationRead(PayslipRead):
    tax_deductions: float = Field(0.0, ge=0)
    social_security: float = Field(0.0, ge=0)
    insurance_deductions: float = Field(0.0, ge=0)
    loan_repayment: float = Field(0.0, ge=0)
    total_hours: float = Field(0.0, ge=0)

    model_config = ConfigDict(from_attributes=True)


class PayrollSummary(BaseModel):
    total_employees: int
    total_payslips: int
    draft_payslips: int
    processed_payroll_gross: float
    processed_payroll_net: float
    attendance_hours: float


class AttendanceBase(BaseModel):
    employee_id: int
    organization_id: Optional[int] = None
    date: Optional[date] = None
    status: Optional[str] = Field('present', max_length=50)
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    hours_worked: Optional[float] = None
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceRead(AttendanceBase):
    id: int
    created_at: datetime
    employee_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PerformanceReviewBase(BaseModel):
    employee_id: int
    reviewer_id: Optional[int] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    rating: float = Field(0.0, ge=0, le=5)
    goals: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = Field('pending', max_length=50)


class PerformanceReviewCreate(PerformanceReviewBase):
    pass


class PerformanceReviewUpdate(BaseModel):
    reviewer_id: Optional[int] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    goals: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)


class PerformanceReviewRead(PerformanceReviewBase):
    id: int
    created_at: datetime
    employee_name: Optional[str] = None
    reviewer_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
