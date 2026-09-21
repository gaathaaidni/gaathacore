from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Employee, Department, Payslip
from .forms import EmployeeForm, PayslipForm

bp = Blueprint('payroll', __name__, template_folder='templates')


@bp.route('/')
def dashboard():
    try:
        employees = Employee.query.all()
    except Exception:
        employees = []
    return render_template('payroll/employees.html', employees=employees, tab='employees')


@bp.route('/employees')
def employees():
    try:
        items = Employee.query.order_by(Employee.created_at.desc()).all()
    except Exception:
        items = []
    return render_template('payroll/list.html', items=items, title='Employees')


@bp.route('/employees/new', methods=['GET', 'POST'])
def employee_create():
    form = EmployeeForm()
    try:
        departments = Department.query.all()
    except Exception:
        departments = []
    if form.validate_on_submit():
        e = Employee(name=form.name.data, salary=form.salary.data)
        if hasattr(form, 'department') and form.department.data:
            e.department = form.department.data
        db.session.add(e)
        db.session.commit()
        flash('Employee created', 'success')
        return redirect(url_for('payroll.employees'))
    return render_template('payroll/form.html', form=form, title='New Employee', departments=departments)


@bp.route('/employees/<int:id>')
def employee_detail(id):
    it = Employee.query.get_or_404(id)
    try:
        payslips = Payslip.query.filter_by(employee_id=id).all()
    except Exception:
        payslips = []
    form = PayslipForm()
    return render_template('payroll/detail.html', item=it, payslips=payslips, form=form, title='Employee')


@bp.route('/employees/<int:id>/edit', methods=['GET', 'POST'])
def employee_edit(id):
    it = Employee.query.get_or_404(id)
    form = EmployeeForm()
    try:
        departments = Department.query.all()
    except Exception:
        departments = []
    if form.validate_on_submit():
        it.name = form.name.data
        it.salary = form.salary.data
        if hasattr(form, 'department') and form.department.data:
            it.department = form.department.data
        db.session.commit()
        flash('Employee updated', 'success')
        return redirect(url_for('payroll.employee_detail', id=id))
    elif request.method == 'GET':
        form.name.data = it.name
        form.salary.data = it.salary
    return render_template('payroll/form.html', form=form, item=it, title='Edit Employee', departments=departments)


@bp.route('/employees/<int:id>/delete', methods=['POST'])
def employee_delete(id):
    it = Employee.query.get_or_404(id)
    db.session.delete(it)
    db.session.commit()
    flash('Employee deleted', 'success')
    return redirect(url_for('payroll.employees'))


@bp.route('/employees/<int:id>/payslip', methods=['POST'])
def create_payslip(id):
    it = Employee.query.get_or_404(id)
    form = PayslipForm()
    if form.validate_on_submit():
        p = Payslip(employee_id=it.id, amount=form.amount.data)
        db.session.add(p)
        db.session.commit()
        flash('Payslip created', 'success')
    return redirect(url_for('payroll.employee_detail', id=id))


@bp.route('/payslips')
def payslips():
    try:
        payslips = Payslip.query.order_by(Payslip.created_at.desc()).all()
    except Exception:
        payslips = []
    return render_template('payroll/payslips.html', payslips=payslips)


@bp.route('/payslips/new', methods=['GET', 'POST'])
def payslip_create():
    form = PayslipForm()
    try:
        employees = Employee.query.all()
    except Exception:
        employees = []
    if form.validate_on_submit():
        p = Payslip(employee_id=form.employee_id.data, amount=form.amount.data)
        db.session.add(p)
        db.session.commit()
        flash('Payslip created', 'success')
        return redirect(url_for('payroll.payslips'))
    return render_template('payroll/payslip_form.html', form=form, employees=employees)
