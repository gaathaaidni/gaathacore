from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import AttendanceRecord, Employee
from blueprints.attendance.forms import AttendanceForm  # We'll create this
from utils.auth import require_permission, get_current_organization
from services.activity_service import log_activity
from datetime import datetime, date, time

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/')
@login_required
@require_permission('attendance.view')
def list_attendance():
    org = get_current_organization()
    page = request.args.get('page', 1, type=int)
    per_page = 25

    query = AttendanceRecord.query.filter_by(organization_id=org.id)

    # Filters
    employee_id = request.args.get('employee_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')

    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if date_from:
        query = query.filter(AttendanceRecord.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(AttendanceRecord.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    if status:
        query = query.filter_by(status=status)

    attendance = query.order_by(AttendanceRecord.date.desc()).paginate(page=page, per_page=per_page)
    employees = Employee.query.filter_by(organization_id=org.id).all()

    # Find current user's record for today to toggle UI buttons
    today_record = None
    if current_user.is_authenticated:
        employee = Employee.query.filter_by(organization_id=org.id, user_id=current_user.id).first()
        if employee:
            today_record = AttendanceRecord.query.filter_by(
                organization_id=org.id, 
                employee_id=employee.id, 
                date=date.today()
            ).first()

    return render_template('attendance/list.html', attendance=attendance, employees=employees, filters=request.args, today_record=today_record)

@attendance_bp.route('/clock-in', methods=['POST'])
@login_required
def clock_in():
    org = get_current_organization()

    # Check if user is an employee
    employee = Employee.query.filter_by(organization_id=org.id, user_id=current_user.id).first()
    if not employee:
        flash('You are not registered as an employee!', 'danger')
        return redirect(url_for('attendance.list_attendance'))

    # Check if already clocked in today
    today = date.today()
    existing = AttendanceRecord.query.filter_by(
        organization_id=org.id,
        employee_id=employee.id,
        date=today
    ).first()

    if existing:
        flash('You have already clocked in today!', 'warning')
        return redirect(url_for('attendance.list_attendance'))

    attendance = AttendanceRecord(
        organization_id=org.id,
        employee_id=employee.id,
        date=today,
        check_in=datetime.now(),
        status='present'
    )

    db.session.add(attendance)
    db.session.commit()

    log_activity(org.id, 'clock_in', f'Employee clocked in: {employee.name}', current_user.id, attendance.id, 'attendance')

    flash('Successfully clocked in!', 'success')
    return redirect(url_for('attendance.list_attendance'))

@attendance_bp.route('/clock-out', methods=['POST'])
@login_required
def clock_out():
    org = get_current_organization()

    employee = Employee.query.filter_by(organization_id=org.id, user_id=current_user.id).first()
    if not employee:
        flash('You are not registered as an employee!', 'danger')
        return redirect(url_for('attendance.list_attendance'))

    today = date.today()
    attendance = AttendanceRecord.query.filter_by(
        organization_id=org.id,
        employee_id=employee.id,
        date=today
    ).first()

    if not attendance:
        flash('You need to clock in first!', 'warning')
        return redirect(url_for('attendance.list_attendance'))

    if attendance.check_out:
        flash('You have already clocked out today!', 'warning')
        return redirect(url_for('attendance.list_attendance'))

    attendance.check_out = datetime.now()

    # Calculate hours worked
    if attendance.check_in:
        hours_worked = (attendance.check_out - attendance.check_in).total_seconds() / 3600
        attendance.hours_worked = round(hours_worked, 2)

    db.session.commit()

    log_activity(org.id, 'clock_out', f'Employee clocked out: {employee.name}', current_user.id, attendance.id, 'attendance')

    flash('Successfully clocked out!', 'success')
    return redirect(url_for('attendance.list_attendance'))

@attendance_bp.route('/<int:id>')
@login_required
@require_permission('attendance.view')
def view_attendance(id):
    org = get_current_organization()
    attendance = AttendanceRecord.query.filter_by(id=id, organization_id=org.id).first_or_404()
    return render_template('attendance/view.html', attendance=attendance)

@attendance_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('attendance.manage')
def create_attendance():
    org = get_current_organization()
    form = AttendanceForm()

    if form.validate_on_submit():
        # Combine date and time for model fields
        check_in = datetime.combine(form.date.data, form.check_in.data) if form.check_in.data else None
        check_out = datetime.combine(form.date.data, form.check_out.data) if form.check_out.data else None

        attendance = AttendanceRecord(
            organization_id=org.id,
            employee_id=form.employee_id.data,
            date=form.date.data,
            check_in=check_in,
            check_out=check_out,
            status=form.status.data,
            notes=form.notes.data
        )

        # Calculate hours worked
        if attendance.check_in and attendance.check_out:
            hours_worked = (attendance.check_out - attendance.check_in).total_seconds() / 3600
            attendance.hours_worked = round(hours_worked, 2)

        db.session.add(attendance)
        db.session.commit()

        log_activity(org.id, 'attendance_created', f'Attendance record created for employee ID: {attendance.employee_id}', current_user.id, attendance.id, 'attendance')

        flash('Attendance record created successfully!', 'success')
        return redirect(url_for('attendance.list_attendance'))

    employees = Employee.query.filter_by(organization_id=org.id).all()
    return render_template('attendance/form.html', form=form, employees=employees, action='Create')

@attendance_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('attendance.manage')
def edit_attendance(id):
    org = get_current_organization()
    attendance = AttendanceRecord.query.filter_by(id=id, organization_id=org.id).first_or_404()

    form = AttendanceForm()

    if form.validate_on_submit():
        attendance.employee_id = form.employee_id.data
        attendance.date = form.date.data
        attendance.check_in = datetime.combine(form.date.data, form.check_in.data) if form.check_in.data else None
        attendance.check_out = datetime.combine(form.date.data, form.check_out.data) if form.check_out.data else None
        attendance.status = form.status.data
        attendance.notes = form.notes.data

        # Recalculate hours worked
        if attendance.check_in and attendance.check_out:
            hours_worked = (attendance.check_out - attendance.check_in).total_seconds() / 3600
            attendance.hours_worked = round(hours_worked, 2)

        db.session.commit()

        log_activity(org.id, 'attendance_updated', f'Attendance record updated for employee ID: {attendance.employee_id}', current_user.id, attendance.id, 'attendance')

        flash('Attendance record updated successfully!', 'success')
        return redirect(url_for('attendance.list_attendance'))

    # Pre-populate form
    form.employee_id.data = attendance.employee_id
    form.date.data = attendance.date
    form.check_in.data = attendance.check_in.time() if attendance.check_in else None
    form.check_out.data = attendance.check_out.time() if attendance.check_out else None
    form.status.data = attendance.status
    form.notes.data = attendance.notes

    employees = Employee.query.filter_by(organization_id=org.id).all()
    return render_template('attendance/form.html', form=form, employees=employees, attendance=attendance, action='Edit')

@attendance_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@require_permission('attendance.manage')
def delete_attendance(id):
    org = get_current_organization()
    attendance = AttendanceRecord.query.filter_by(id=id, organization_id=org.id).first_or_404()

    db.session.delete(attendance)
    db.session.commit()

    log_activity(org.id, 'attendance_deleted', f'Attendance record deleted for employee ID: {attendance.employee_id}', current_user.id, attendance.id, 'attendance')

    flash('Attendance record deleted successfully!', 'success')
    return redirect(url_for('attendance.list_attendance'))

# API endpoints
@attendance_bp.route('/api/today')
@login_required
def get_today_attendance():
    org = get_current_organization()
    today = date.today()

    attendance = AttendanceRecord.query.filter_by(
        organization_id=org.id,
        date=today
    ).all()

    return jsonify([
        {
            'id': a.id,
            'employee_name': a.employee.name if a.employee else 'Unknown',
            'clock_in': a.check_in.strftime('%H:%M') if a.check_in else None,
            'clock_out': a.check_out.strftime('%H:%M') if a.check_out else None,
            'status': a.status
        }
        for a in attendance
    ])

@attendance_bp.route('/api/stats')
@login_required
@require_permission('attendance.view')
def get_attendance_stats():
    org = get_current_organization()

    # Get stats for current month
    start_of_month = date.today().replace(day=1)

    status_stats = db.session.query(
        AttendanceRecord.status,
        db.func.count(AttendanceRecord.id).label('count')
    ).filter(
        AttendanceRecord.organization_id == org.id,
        AttendanceRecord.date >= start_of_month
    ).group_by(AttendanceRecord.status).all()

    # Calculate average hours worked per employee for the current month
    avg_hours_per_employee = db.session.query(
        Employee.name,
        db.func.avg(AttendanceRecord.hours_worked).label('average_hours')
    ).join(Employee, AttendanceRecord.employee_id == Employee.id).filter(
        AttendanceRecord.organization_id == org.id,
        AttendanceRecord.date >= start_of_month,
        AttendanceRecord.hours_worked.isnot(None) # Only consider records with hours worked
    ).group_by(Employee.name).all()

    return jsonify({
        'status_breakdown': [
            {'status': s.status, 'count': s.count}
            for s in status_stats
        ],
        'average_hours_per_employee': [
            {'employee_name': e.name, 'average_hours': round(e.average_hours, 2)}
            for e in avg_hours_per_employee
        ]
    })