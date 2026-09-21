from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from utils.auth import require_organization_access, get_current_organization
from services.organization_service import OrganizationService
from extensions import db
from models import Organization, OrganizationUser, Invitation, User
from utils.audit import log_activity
from .forms import InviteForm, AcceptInviteForm
from flask_login import login_user
from utils.auth import require_admin

from . import bp


@bp.route('/<int:org_id>/manage', methods=['GET', 'POST'])
@login_required
@require_organization_access()
def manage(org_id):
    org = Organization.query.get_or_404(org_id)
    form = InviteForm()
    members = OrganizationUser.query.filter_by(organization_id=org.id).all()

    if form.validate_on_submit():
        email = form.email.data
        role = form.role.data
        try:
            inv = OrganizationService.invite_user(org.id, email, role_name=role, invited_by=current_user)
            flash('Invitation created/sent', 'success')
            log_activity(current_user.id, org.id, 'invite_user', 'organization', record_id=org.id, record_type='invitation', new_values={'email': email, 'role': role})
        except Exception as e:
            flash('Failed to invite user: ' + str(e), 'danger')
        return redirect(url_for('organization.manage', org_id=org.id))

    invites = Invitation.query.filter_by(organization_id=org.id).order_by(Invitation.created_at.desc()).all()
    return render_template('organization/dashboard.html', org=org, members=members, invites=invites, form=form)


@bp.route('/invite/accept/<token>', methods=['GET', 'POST'])
def accept_invite(token):
    inv = Invitation.query.filter_by(token=token).first_or_404()
    if not inv.is_valid():
        flash('Invitation is no longer valid', 'danger')
        return redirect(url_for('index'))

    form = AcceptInviteForm()
    if request.method == 'POST' and form.validate_on_submit():
        # If user exists, ensure email matches; otherwise create account
        user = User.query.filter_by(email=inv.email).first()
        try:
            if not user:
                # create user
                u = User(username=form.username.data, email=inv.email, name=form.name.data)
                u.set_password(form.password.data)
                db.session.add(u)
                db.session.commit()
                user = u

            # add user to organization
            OrganizationService.invite_user(inv.organization_id, inv.email, role_name=inv.role, invited_by=None)
            inv.status = 'accepted'
            db.session.commit()
            log_activity(user.id, inv.organization_id, 'accept_invite', 'organization', record_id=inv.id, record_type='invitation')
            # auto-login
            try:
                login_user(user)
            except Exception:
                pass
            flash('You have been added to the organization', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash('Failed to accept invitation: ' + str(e), 'danger')
            return redirect(url_for('index'))

    return render_template('organization/invite_accept.html', invite=inv, form=form)


@bp.route('/<int:org_id>/member/<int:user_id>/role', methods=['POST'])
@login_required
@require_admin()
@require_organization_access()
def set_member_role(org_id, user_id):
    role = request.form.get('role')
    ou = OrganizationUser.query.filter_by(organization_id=org_id, user_id=user_id).first_or_404()
    old = ou.role
    ou.role = role
    db.session.commit()
    # sync UserRole entries
    try:
        from models import Role, UserRole
        role_obj = Role.query.filter_by(organization_id=org_id, name=role).first()
        if role_obj:
            ur = UserRole.query.filter_by(user_id=user_id, organization_id=org_id).first()
            if ur:
                ur.role_id = role_obj.id
            else:
                ur = UserRole(user_id=user_id, role_id=role_obj.id, organization_id=org_id)
                db.session.add(ur)
            db.session.commit()
    except Exception:
        pass
    log_activity(current_user.id, org_id, 'set_member_role', 'organization', record_id=ou.id, record_type='organization_user', old_values={'role': old}, new_values={'role': role})
    flash('Role updated', 'success')
    return redirect(url_for('organization.manage', org_id=org_id))


@bp.route('/<int:org_id>/member/<int:user_id>/remove', methods=['POST'])
@login_required
@require_admin()
@require_organization_access()
def remove_member(org_id, user_id):
    try:
        OrganizationService.remove_user_from_organization(org_id, user_id, current_user)
        log_activity(current_user.id, org_id, 'remove_member', 'organization', record_id=user_id, record_type='user')
        flash('Member removed', 'success')
    except Exception as e:
        flash('Failed to remove member: ' + str(e), 'danger')
    return redirect(url_for('organization.manage', org_id=org_id))
