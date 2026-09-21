from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange


class ItemForm(FlaskForm):
    sku = StringField("SKU", validators=[DataRequired()])
    name = StringField("Item Name", validators=[DataRequired()])
    description = StringField("Description")
    unit_cost = FloatField("Unit Cost", default=0.0, validators=[DataRequired(), NumberRange(min=0)])
    unit_price = FloatField("Unit Price", default=0.0, validators=[DataRequired(), NumberRange(min=0)])
    quantity_on_hand = FloatField("Qty on Hand", default=0.0)


class StockTransactionForm(FlaskForm):
    item_id = IntegerField("Item", validators=[DataRequired()])
    warehouse_from = IntegerField("From Warehouse", validators=[])
    warehouse_to = IntegerField("To Warehouse", validators=[])
    qty = FloatField("Quantity", validators=[DataRequired(), NumberRange(min=0.1)])
    txn_type = SelectField("Type", choices=[("in", "In"), ("out", "Out"), ("transfer", "Transfer")])
    note = StringField("Note")
