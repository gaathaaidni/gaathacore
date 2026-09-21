from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, TimeField, TextAreaField, ValidationError
from wtforms.validators import DataRequired, Optional
from models import Employee

class AttendanceForm(FlaskForm):
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    check_in = TimeField('Check In Time', validators=[DataRequired()])
    check_out = TimeField('Check Out Time')
    status = SelectField('Status', choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('leave', 'On Leave')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes')

    def validate_check_out(self, field):
        if self.check_in.data and field.data:
            if field.data <= self.check_in.data:
                raise ValidationError('Check-out time must be later than check-in time.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate employee choices
        from flask_login import current_user
        from utils.auth import get_current_organization
        if current_user.is_authenticated:
            org = get_current_organization()
            employees = Employee.query.filter_by(organization_id=org.id).all()
            self.employee_id.choices = [(e.id, e.name) for e in employees]