from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class PaymentForm(FlaskForm):
    invoice_id = StringField('Invoice ID', validators=[DataRequired()])
    amount = DecimalField('Amount', places=2, validators=[NumberRange(min=0)])
    submit = SubmitField('Pay')
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SelectField, DateField
from wtforms.validators import DataRequired, Optional


class PaymentForm(FlaskForm):
    invoice_id = IntegerField("Invoice", validators=[DataRequired()])
    amount = FloatField("Amount", validators=[DataRequired()])
    date = DateField("Date", validators=[Optional()])
    method = SelectField("Method", choices=[("card", "Card"), ("bank", "Bank"), ("cash", "Cash")])
    reference = StringField("Reference")
