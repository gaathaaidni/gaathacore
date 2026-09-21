from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, EmailField, SelectField
from wtforms.validators import DataRequired, Length, Email, Optional

class VendorForm(FlaskForm):
    name = StringField('Vendor Name', validators=[DataRequired(), Length(max=200)])
    email = EmailField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=500)])
    category = SelectField('Category', choices=[
        ('general', 'General'),
        ('office_supplies', 'Office Supplies'),
        ('software', 'Software & IT'),
        ('travel', 'Travel'),
        ('marketing', 'Marketing'),
        ('utilities', 'Utilities'),
        ('maintenance', 'Maintenance'),
        ('consulting', 'Consulting'),
        ('other', 'Other')
    ], validators=[DataRequired()])