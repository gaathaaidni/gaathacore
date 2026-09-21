from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, SelectField, DateField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class ApprovalRequestForm(FlaskForm):
    request_type = SelectField('Request Type', choices=[
        ('expense', 'Expense Approval'),
        ('leave', 'Leave Request'),
        ('purchase', 'Purchase Request'),
        ('budget', 'Budget Approval'),
        ('policy', 'Policy Exception'),
        ('other', 'Other')
    ], validators=[DataRequired()])

    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=1000)])

    amount = DecimalField('Amount (if applicable)', validators=[Optional(), NumberRange(min=0)])

    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], validators=[DataRequired()])

    due_date = DateField('Due Date', validators=[Optional()])