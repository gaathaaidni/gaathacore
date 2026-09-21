from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Optional


class TicketForm(FlaskForm):
    customer_id = IntegerField("Customer", validators=[DataRequired()])
    subject = StringField("Subject", validators=[DataRequired()])
    description = TextAreaField("Description")
    priority = SelectField("Priority", choices=[("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")])


class TicketCommentForm(FlaskForm):
    body = TextAreaField("Comment", validators=[DataRequired()])
