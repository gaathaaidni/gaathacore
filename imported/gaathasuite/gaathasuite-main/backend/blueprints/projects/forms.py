from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, FloatField, IntegerField
from wtforms.validators import DataRequired, Optional
from models import Customer, User


class ProjectForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    status = SelectField('Status', choices=[
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='planning')
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    budget = FloatField('Budget', validators=[Optional()])
    customer_id = SelectField('Customer', coerce=int, validators=[Optional()])
    manager_id = SelectField('Project Manager', coerce=int, validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate customer choices
        try:
            from flask_login import current_user
            if current_user.is_authenticated and hasattr(current_user, 'organization_id'):
                customers = Customer.query.filter_by(organization_id=current_user.organization_id).all()
                self.customer_id.choices = [(0, '-- Select Customer --')] + [(c.id, c.name) for c in customers]

                # Get organization users for manager selection
                from models import OrganizationUser
                org_users = OrganizationUser.query.filter_by(
                    organization_id=current_user.organization_id,
                    is_active=True
                ).all()
                self.manager_id.choices = [(0, '-- Select Manager --')] + [(ou.user_id, ou.user.name) for ou in org_users]
            else:
                self.customer_id.choices = [(0, '-- Select Customer --')]
                self.manager_id.choices = [(0, '-- Select Manager --')]
        except:
            self.customer_id.choices = [(0, '-- Select Customer --')]
            self.manager_id.choices = [(0, '-- Select Manager --')]


class TaskForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    status = SelectField('Status', choices=[
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done')
    ], default='todo')
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    assigned_to = SelectField('Assigned To', coerce=int, validators=[Optional()])
    due_date = DateField('Due Date', validators=[Optional()])
    estimated_hours = FloatField('Estimated Hours', validators=[Optional()])
    actual_hours = FloatField('Actual Hours', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate assigned_to choices
        try:
            from flask_login import current_user
            if current_user.is_authenticated and hasattr(current_user, 'organization_id'):
                from models import OrganizationUser
                org_users = OrganizationUser.query.filter_by(
                    organization_id=current_user.organization_id,
                    is_active=True
                ).all()
                self.assigned_to.choices = [(0, '-- Unassigned --')] + [(ou.user_id, ou.user.name) for ou in org_users]
            else:
                self.assigned_to.choices = [(0, '-- Unassigned --')]
        except:
            self.assigned_to.choices = [(0, '-- Unassigned --')]