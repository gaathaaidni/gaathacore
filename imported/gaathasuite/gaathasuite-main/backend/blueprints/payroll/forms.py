from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, DateField
from wtforms.validators import DataRequired, Optional


class EmployeeForm(FlaskForm):
    employee_code = StringField("Employee Code", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email")
    phone = StringField("Phone")
    department_id = IntegerField("Department", validators=[Optional()])
    position = StringField("Position")
    hired_date = DateField("Hired Date", validators=[Optional()])
    salary = FloatField("Salary", default=0.0, validators=[DataRequired()])


class PayslipForm(FlaskForm):
    employee_id = IntegerField("Employee", validators=[DataRequired()])
    period_start = DateField("Period Start", validators=[Optional()])
    period_end = DateField("Period End", validators=[Optional()])
    gross = FloatField("Gross", validators=[DataRequired()])
