from flask import Blueprint, render_template, redirect, url_for, flash, request
from extensions import db
from models import Department, Employee
from .forms import DepartmentForm, EmployeeProfileForm

bp = Blueprint('hr', __name__, template_folder='templates')


@bp.route('/departments')
def departments():
    items = Department.query.order_by(Department.created_at.desc()).all()
    return render_template('hr/list.html', items=items, title='Departments')


@bp.route('/employees')
def employees():
    try:
        items = Employee.query.order_by(Employee.created_at.desc()).all()
    except Exception:
        items = []
    return render_template('hr/employees.html', items=items, title='Employees')
import csv
from io import BytesIO
from flask import Response


@bp.route("/")
def dashboard():
    employees = Employee.query.all()
    departments = Department.query.all()
    return render_template("hr/dashboard.html", employees=employees, departments=departments, tab="employees")


@bp.route("/employees")
def employees_list():
    employees = Employee.query.order_by(Employee.name).all()
    return render_template("hr/employees.html", employees=employees)


@bp.route('/employees/export')
def export_employees():
    fmt = (request.args.get('format') or 'csv').lower()
    employees = Employee.query.order_by(Employee.name).all()
    if fmt == 'csv':
        import io as _io
        output = _io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['id', 'employee_code', 'name', 'email', 'position', 'department_id', 'hired_date'])
        for e in employees:
            writer.writerow([e.id, e.employee_code or '', e.name or '', e.email or '', e.position or '', e.department_id or '', e.hired_date.isoformat() if e.hired_date else ''])
        return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=employees.csv'})
    if fmt == 'excel':
        try:
            from openpyxl import Workbook
        except Exception:
            flash('Excel export requires openpyxl (pip install openpyxl)', 'danger')
            return redirect(url_for('hr.employees'))
        wb = Workbook()
        ws = wb.active
        ws.append(['id', 'employee_code', 'name', 'email', 'position', 'department_id', 'hired_date'])
        for e in employees:
            ws.append([e.id, e.employee_code or '', e.name or '', e.email or '', e.position or '', e.department_id or '', e.hired_date.isoformat() if e.hired_date else ''])
        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)
        return Response(bio.read(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment;filename=employees.xlsx'})
    flash('Export format not supported', 'danger')
    return redirect(url_for('hr.employees'))


@bp.route("/employee/<int:id>")
def view_employee(id):
    employee = Employee.query.get_or_404(id)
    department = Department.query.get(employee.department_id) if employee.department_id else None
    return render_template("hr/employee_detail.html", employee=employee, department=department)


@bp.route("/employee/add", methods=["GET", "POST"])
def add_employee():
    form = EmployeeProfileForm()
    departments = Department.query.all()
    
    if form.validate_on_submit():
        employee = Employee(
            employee_code=form.employee_code.data,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            department_id=form.department_id.data,
            position=form.position.data,
            hired_date=form.hired_date.data,
            salary=form.salary.data
        )
        db.session.add(employee)
        db.session.commit()
        flash("Employee added", "success")
        return redirect(url_for("hr.view_employee", id=employee.id))
    
    return render_template("hr/employee_form.html", form=form, departments=departments, edit=False)


@bp.route("/employee/<int:id>/edit", methods=["GET", "POST"])
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeProfileForm()
    departments = Department.query.all()
    
    if form.validate_on_submit():
        employee.employee_code = form.employee_code.data
        employee.name = form.name.data
        employee.email = form.email.data
        employee.phone = form.phone.data
        employee.department_id = form.department_id.data
        employee.position = form.position.data
        employee.hired_date = form.hired_date.data
        employee.salary = form.salary.data
        db.session.commit()
        flash("Employee updated", "success")
        return redirect(url_for("hr.view_employee", id=id))
    elif request.method == "GET":
        form.employee_code.data = employee.employee_code
        form.name.data = employee.name
        form.email.data = employee.email
        form.phone.data = employee.phone
        form.department_id.data = employee.department_id
        form.position.data = employee.position
        form.hired_date.data = employee.hired_date
        form.salary.data = employee.salary
    
    return render_template("hr/employee_form.html", form=form, employee=employee, departments=departments, edit=True)


@bp.route("/employee/<int:id>/delete", methods=["POST"])
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    flash("Employee deleted", "success")
    return redirect(url_for("hr.employees_list"))


@bp.route("/departments")
def departments_list():
    departments = Department.query.all()
    return render_template("hr/departments.html", departments=departments)


@bp.route("/department/add", methods=["GET", "POST"])
def add_department():
    form = DepartmentForm()
    employees = Employee.query.all()
    
    if form.validate_on_submit():
        department = Department(
            name=form.name.data,
            manager_id=form.manager_id.data
        )
        db.session.add(department)
        db.session.commit()
        flash("Department added", "success")
        return redirect(url_for("hr.departments_list"))
    
    return render_template("hr/department_form.html", form=form, employees=employees, edit=False)


@bp.route("/department/<int:id>/edit", methods=["GET", "POST"])
def edit_department(id):
    department = Department.query.get_or_404(id)
    form = DepartmentForm()
    employees = Employee.query.all()
    
    if form.validate_on_submit():
        department.name = form.name.data
        department.manager_id = form.manager_id.data
        db.session.commit()
        flash("Department updated", "success")
        return redirect(url_for("hr.departments_list"))
    elif request.method == "GET":
        form.name.data = department.name
        form.manager_id.data = department.manager_id
    
    return render_template("hr/department_form.html", form=form, department=department, employees=employees, edit=True)


@bp.route("/department/<int:id>/delete", methods=["POST"])
def delete_department(id):
    department = Department.query.get_or_404(id)
    db.session.delete(department)
    db.session.commit()
    flash("Department deleted", "success")
    return redirect(url_for("hr.departments_list"))
