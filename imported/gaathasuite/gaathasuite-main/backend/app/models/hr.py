from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

from app.models.base import Base


class Department(Base):
    __tablename__ = 'department'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), nullable=False, index=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=True)

    organization = relationship('Organization', lazy='selectin')
    manager = relationship('User', backref=backref('managed_departments', lazy='selectin'))
    employees = relationship('Employee', back_populates='department', lazy='selectin')


class Employee(Base):
    __tablename__ = 'employee'

    employee_code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    department_id: Mapped[int] = mapped_column(ForeignKey('department.id'), nullable=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), nullable=False, index=True)
    position: Mapped[str] = mapped_column(String(255), nullable=True)
    hired_date: Mapped[date] = mapped_column(Date, nullable=True)
    salary: Mapped[float] = mapped_column(Float, default=0.0)

    department = relationship('Department', back_populates='employees', lazy='selectin')
    organization = relationship('Organization', lazy='selectin')
    payslips = relationship('Payslip', back_populates='employee', lazy='selectin')
    attendance_records = relationship('AttendanceRecord', back_populates='employee', lazy='selectin')

    @property
    def department_name(self) -> str | None:
        return self.department.name if self.department else None


class Payslip(Base):
    __tablename__ = 'payslip'

    employee_id: Mapped[int] = mapped_column(ForeignKey('employee.id'), nullable=False, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=True)
    gross: Mapped[float] = mapped_column(Float, default=0.0)
    net: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default='draft')

    employee = relationship('Employee', back_populates='payslips', lazy='selectin')
    organization = relationship('Organization', lazy='selectin')


class AttendanceRecord(Base):
    __tablename__ = 'attendance_record'

    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey('employee.id'), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='present')
    check_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    hours_worked: Mapped[float] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    employee = relationship('Employee', back_populates='attendance_records', lazy='selectin')

    @property
    def employee_name(self) -> str | None:
        return self.employee.name if self.employee else None


class PerformanceReview(Base):
    __tablename__ = 'performance_review'

    employee_id: Mapped[int] = mapped_column(ForeignKey('employee.id'), nullable=False, index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    goals: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='pending')

    employee = relationship('Employee', lazy='selectin')
    reviewer = relationship('User', lazy='selectin')
    organization = relationship('Organization', lazy='selectin')

    @property
    def employee_name(self) -> str | None:
        return self.employee.name if self.employee else None

    @property
    def reviewer_name(self) -> str | None:
        return self.reviewer.username if self.reviewer else None
