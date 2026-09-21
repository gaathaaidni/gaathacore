from flask import Blueprint, render_template, redirect, url_for, flash, request
from extensions import db
from models import Project, Task
from utils.auth import require_organization_access, require_projects_access
from services.activity_service import ActivityService
from services.workflow_service import WorkflowService
from flask_login import current_user, login_required
from .forms import ProjectForm, TaskForm

bp = Blueprint('projects', __name__, template_folder='templates')


@bp.route('/projects')
@login_required
@require_organization_access()
@require_projects_access('view')
def projects():
    try:
        projects = Project.query.filter_by(organization_id=current_user.organization_id).all()
    except:
        projects = []
    return render_template('projects/list.html', projects=projects, title='Projects')


@bp.route('/projects/new', methods=['GET', 'POST'])
@login_required
@require_organization_access()
@require_projects_access('create')
def project_create():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            organization_id=current_user.organization_id,
            name=form.name.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            budget=form.budget.data,
            customer_id=form.customer_id.data,
            manager_id=form.manager_id.data,
            created_by=current_user.id
        )
        db.session.add(project)
        db.session.commit()

        # Log activity
        ActivityService.log_model_change(project, 'created')

        # Trigger workflow
        WorkflowService.create_event('projects', 'project.created', project.id, 'project', {
            'organization_id': current_user.organization_id,
            'record': project,
            'user_id': current_user.id
        })

        flash('Project created successfully', 'success')
        return redirect(url_for('projects.projects'))

    return render_template('projects/form.html', form=form, title='New Project')


@bp.route('/projects/<int:id>')
@login_required
@require_organization_access()
@require_projects_access('view')
def project_detail(id):
    project = Project.query.filter_by(
        id=id,
        organization_id=current_user.organization_id
    ).first_or_404()

    tasks = Task.query.filter_by(project_id=id).all()
    return render_template('projects/detail.html', project=project, tasks=tasks, title=project.name)


@bp.route('/projects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_organization_access()
@require_projects_access('edit')
def project_edit(id):
    project = Project.query.filter_by(
        id=id,
        organization_id=current_user.organization_id
    ).first_or_404()

    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        old_values = {
            'name': project.name,
            'status': project.status,
            'priority': project.priority
        }

        project.name = form.name.data
        project.description = form.description.data
        project.status = form.status.data
        project.priority = form.priority.data
        project.start_date = form.start_date.data
        project.end_date = form.end_date.data
        project.budget = form.budget.data
        project.customer_id = form.customer_id.data
        project.manager_id = form.manager_id.data

        db.session.commit()

        # Log activity
        ActivityService.log_model_change(project, 'updated', old_values)

        # Trigger workflow
        WorkflowService.create_event('projects', 'project.updated', project.id, 'project', {
            'organization_id': current_user.organization_id,
            'record': project,
            'changes': {'old': old_values, 'new': project.__dict__},
            'user_id': current_user.id
        })

        flash('Project updated successfully', 'success')
        return redirect(url_for('projects.project_detail', id=id))

    return render_template('projects/form.html', form=form, project=project, title='Edit Project')


@bp.route('/projects/<int:id>/delete', methods=['POST'])
@login_required
@require_organization_access()
@require_projects_access('delete')
def project_delete(id):
    project = Project.query.filter_by(
        id=id,
        organization_id=current_user.organization_id
    ).first_or_404()

    # Log activity before deletion
    ActivityService.log_model_change(project, 'deleted')

    db.session.delete(project)
    db.session.commit()

    flash('Project deleted successfully', 'success')
    return redirect(url_for('projects.projects'))


# Task routes
@bp.route('/projects/<int:project_id>/tasks/new', methods=['GET', 'POST'])
@login_required
@require_organization_access()
@require_projects_access('create')
def task_create(project_id):
    project = Project.query.filter_by(
        id=project_id,
        organization_id=current_user.organization_id
    ).first_or_404()

    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            organization_id=current_user.organization_id,
            project_id=project_id,
            name=form.name.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            assigned_to=form.assigned_to.data,
            due_date=form.due_date.data,
            estimated_hours=form.estimated_hours.data,
            created_by=current_user.id
        )
        db.session.add(task)
        db.session.commit()

        # Log activity
        ActivityService.log_model_change(task, 'created')

        # Trigger workflow
        WorkflowService.create_event('projects', 'task.created', task.id, 'task', {
            'organization_id': current_user.organization_id,
            'record': task,
            'user_id': current_user.id
        })

        flash('Task created successfully', 'success')
        return redirect(url_for('projects.project_detail', id=project_id))

    return render_template('projects/task_form.html', form=form, project=project, title='New Task')


@bp.route('/tasks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_organization_access()
@require_projects_access('edit')
def task_edit(id):
    task = Task.query.join(Project).filter(
        Task.id == id,
        Project.organization_id == current_user.organization_id
    ).first_or_404()

    form = TaskForm(obj=task)
    if form.validate_on_submit():
        old_values = {
            'status': task.status,
            'assigned_to': task.assigned_to
        }

        task.name = form.name.data
        task.description = form.description.data
        task.status = form.status.data
        task.priority = form.priority.data
        task.assigned_to = form.assigned_to.data
        task.due_date = form.due_date.data
        task.estimated_hours = form.estimated_hours.data
        task.actual_hours = form.actual_hours.data

        db.session.commit()

        # Log activity
        ActivityService.log_model_change(task, 'updated', old_values)

        flash('Task updated successfully', 'success')
        return redirect(url_for('projects.project_detail', id=task.project_id))

    return render_template('projects/task_form.html', form=form, task=task, title='Edit Task')


@bp.route('/tasks/<int:id>/delete', methods=['POST'])
@login_required
@require_organization_access()
@require_projects_access('delete')
def task_delete(id):
    task = Task.query.join(Project).filter(
        Task.id == id,
        Project.organization_id == current_user.organization_id
    ).first_or_404()

    project_id = task.project_id

    # Log activity before deletion
    ActivityService.log_model_change(task, 'deleted')

    db.session.delete(task)
    db.session.commit()

    flash('Task deleted successfully', 'success')
    return redirect(url_for('projects.project_detail', id=project_id))