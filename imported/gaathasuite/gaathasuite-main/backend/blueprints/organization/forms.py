from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired, Email

class InviteForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('member','Member'), ('admin','Admin')], default='member')


class AcceptInviteForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Full name')
    password = StringField('Password', validators=[DataRequired()])
