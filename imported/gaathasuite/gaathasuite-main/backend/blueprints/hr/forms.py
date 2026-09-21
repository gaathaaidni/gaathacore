from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class DepartmentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Save')


class EmployeeProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    position = StringField('Position')
    submit = SubmitField('Save')
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, IntegerField, FloatField
from wtforms.validators import DataRequired, Optional


class DepartmentForm(FlaskForm):
    name = StringField("Department Name", validators=[DataRequired()])
    manager_id = IntegerField("Manager", validators=[Optional()])


class EmployeeProfileForm(FlaskForm):
    employee_code = StringField("Employee Code", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email")
    phone = StringField("Phone")
    department_id = IntegerField("Department", validators=[Optional()])
    position = StringField("Position")
    hired_date = DateField("Hired Date", validators=[Optional()])
    salary = FloatField("Salary", default=0.0, validators=[DataRequired()])
