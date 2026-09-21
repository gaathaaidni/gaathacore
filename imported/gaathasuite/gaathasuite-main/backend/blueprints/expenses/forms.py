from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from models import Vendor

class ExpenseForm(FlaskForm):
    vendor_id = SelectField('Vendor', coerce=int, validators=[Optional()])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)])
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    category = SelectField('Category', choices=[
        ('office_supplies', 'Office Supplies'),
        ('travel', 'Travel'),
        ('meals', 'Meals & Entertainment'),
        ('software', 'Software & Tools'),
        ('hardware', 'Hardware'),
        ('marketing', 'Marketing'),
        ('utilities', 'Utilities'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    date = DateField('Expense Date', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate vendor choices
        from flask_login import current_user
        from utils.auth import get_current_org
        if current_user.is_authenticated:
            org = get_current_org()
            vendors = Vendor.query.filter_by(organization_id=org.id).all()
            self.vendor_id.choices = [(0, '-- Select Vendor --')] + [(v.id, v.name) for v in vendors]