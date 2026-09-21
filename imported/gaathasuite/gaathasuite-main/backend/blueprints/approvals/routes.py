from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import ApprovalRequest, ApprovalWorkflow
from blueprints.approvals.forms import ApprovalRequestForm  # We'll create this
from utils.auth import require_permission, get_current_organization
from services.activity_service import log_activity
from datetime import datetime

approvals_bp = Blueprint('approvals', __name__, url_prefix='/approvals')

@approvals_bp.route('/')
@login_required
@require_permission('approvals.view')
def list_approvals():
    org = get_current_organization()
    page = request.args.get('page', 1, type=int)
    per_page = 25

    query = ApprovalRequest.query.filter_by(organization_id=org.id)

    # Filters
    status = request.args.get('status')
    request_type = request.args.get('request_type')
    requester_id = request.args.get('requester_id')

    if status:
        query = query.filter_by(status=status)
    if request_type:
        query = query.filter_by(request_type=request_type)
    if requester_id:
        query = query.filter_by(requester_id=int(requester_id))

    approvals = query.order_by(ApprovalRequest.created_at.desc()).paginate(page=page, per_page=per_page)

    return render_template('approvals/list.html', approvals=approvals, filters=request.args)

@approvals_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('approvals.create')
def create_approval():
    org = get_current_organization()
    form = ApprovalRequestForm()

    if form.validate_on_submit():
        approval = ApprovalRequest(
            organization_id=org.id,
            requester_id=current_user.id,
            request_type=form.request_type.data,
            title=form.title.data,
            description=form.description.data,
            amount=form.amount.data if hasattr(form, 'amount') and form.amount.data else None,
            priority=form.priority.data,
            due_date=form.due_date.data,
            status='pending'
        )

        db.session.add(approval)
        db.session.commit()

        # Trigger approval workflow
        _trigger_approval_workflow(approval)

        log_activity(org.id, 'approval_created', f'Approval request created: {approval.title}', current_user.id, approval.id, 'approval')

        flash('Approval request created successfully!', 'success')
        return redirect(url_for('approvals.list_approvals'))

    return render_template('approvals/form.html', form=form, action='Create')

@approvals_bp.route('/<int:id>')
@login_required
@require_permission('approvals.view')
def view_approval(id):
    org = get_current_organization()
    approval = ApprovalRequest.query.filter_by(id=id, organization_id=org.id).first_or_404()

    return render_template('approvals/view.html', approval=approval)

@approvals_bp.route('/<int:id>/approve', methods=['POST'])
@login_required
@require_permission('approvals.approve')
def approve_approval(id):
    org = get_current_organization()
    approval = ApprovalRequest.query.filter_by(id=id, organization_id=org.id).first_or_404()

    approval.status = 'approved'
    approval.approved_by = current_user.id
    approval.approved_at = datetime.utcnow()

    db.session.commit()

    log_activity(org.id, 'approval_approved', f'Approval approved: {approval.title}', current_user.id, approval.id, 'approval')

    flash('Approval request approved!', 'success')
    return redirect(url_for('approvals.view_approval', id=id))

@approvals_bp.route('/<int:id>/reject', methods=['POST'])
@login_required
@require_permission('approvals.approve')
def reject_approval(id):
    org = get_current_organization()
    approval = ApprovalRequest.query.filter_by(id=id, organization_id=org.id).first_or_404()

    approval.status = 'rejected'
    approval.rejected_by = current_user.id
    approval.rejected_at = datetime.utcnow()

    db.session.commit()

    log_activity(org.id, 'approval_rejected', f'Approval rejected: {approval.title}', current_user.id, approval.id, 'approval')

    flash('Approval request rejected!', 'warning')
    return redirect(url_for('approvals.view_approval', id=id))

def _trigger_approval_workflow(approval):
    """Trigger the appropriate approval workflow based on request type and amount"""
    # This would integrate with the workflow engine
    # For now, we'll create a simple approval workflow
    workflow = ApprovalWorkflow(
        organization_id=approval.organization_id,
        approval_request_id=approval.id,
        current_step=1,
        total_steps=2,  # Manager -> Director
        status='in_progress'
    )
    db.session.add(workflow)
    db.session.commit()

# API endpoints
@approvals_bp.route('/api/stats')
@login_required
@require_permission('approvals.view')
def get_approval_stats():
    org = get_current_organization()
    stats = db.session.query(
        ApprovalRequest.status,
        db.func.count(ApprovalRequest.id).label('count')
    ).filter_by(organization_id=org.id).group_by(ApprovalRequest.status).all()

    return jsonify({
        'stats': [
            {'status': s.status, 'count': s.count}
            for s in stats
        ]
    })