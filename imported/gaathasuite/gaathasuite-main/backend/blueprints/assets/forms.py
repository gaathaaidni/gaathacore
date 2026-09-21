from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from models import Employee

class AssetForm(FlaskForm):
    name = StringField('Asset Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    category = SelectField('Category', choices=[
        ('computer', 'Computer/Laptop'),
        ('furniture', 'Furniture'),
        ('equipment', 'Equipment'),
        ('vehicle', 'Vehicle'),
        ('software', 'Software License'),
        ('tool', 'Tool'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    asset_tag = StringField('Asset Tag', validators=[Optional(), Length(max=50)])
    serial_number = StringField('Serial Number', validators=[Optional(), Length(max=100)])
    purchase_date = DateField('Purchase Date', validators=[Optional()])
    purchase_cost = DecimalField('Purchase Cost', validators=[Optional(), NumberRange(min=0)])
    current_value = DecimalField('Current Value', validators=[Optional(), NumberRange(min=0)])
    location = StringField('Location', validators=[Optional(), Length(max=200)])
    status = SelectField('Status', choices=[
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
        ('lost', 'Lost/Stolen')
    ], validators=[DataRequired()])
    assigned_to = SelectField('Assigned To', coerce=int, validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=1000)])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate assigned_to choices
        from flask_login import current_user
        from utils.auth import get_current_organization
        if current_user.is_authenticated:
            org = get_current_organization()
            employees = Employee.query.filter_by(organization_id=org.id).all()
            self.assigned_to.choices = [(0, '-- Not Assigned --')] + [(e.id, e.name) for e in employees]