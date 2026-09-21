from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired, Optional, NumberRange


class InvoiceLineForm(FlaskForm):
    description = StringField("Description", validators=[DataRequired()])
    qty = FloatField("Quantity", default=1.0, validators=[DataRequired(), NumberRange(min=0.1)])
    unit_price = FloatField("Unit Price", default=0.0, validators=[DataRequired(), NumberRange(min=0)])


class InvoiceForm(FlaskForm):
    number = StringField("Invoice Number", validators=[DataRequired()])
    customer_id = IntegerField("Customer", validators=[DataRequired()])
    date = DateField("Date", validators=[Optional()])
    due_date = DateField("Due Date", validators=[Optional()])
    status = SelectField("Status", choices=[("draft", "Draft"), ("sent", "Sent"), ("paid", "Paid")])
    lines = FieldList(FormField(InvoiceLineForm), min_entries=1)
