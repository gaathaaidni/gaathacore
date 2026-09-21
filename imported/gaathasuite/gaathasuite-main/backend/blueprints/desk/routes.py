from flask import Blueprint, render_template, redirect, url_for, flash, request
from extensions import db
from models import Ticket, TicketComment
from .forms import TicketForm, TicketCommentForm
from flask_login import current_user, login_required

bp = Blueprint('desk', __name__, template_folder='templates')


@bp.route('/tickets')
def tickets():
    try:
        items = Ticket.query.order_by(Ticket.created_at.desc()).all()
    except Exception:
        items = []
    return render_template('desk/list.html', items=items, title='Tickets')


@bp.route('/tickets/new', methods=['GET', 'POST'])
def ticket_create():
    form = TicketForm()
    customers = Customer.query.all()
    if form.validate_on_submit():
        t = Ticket(customer_id=form.customer_id.data, subject=form.subject.data, description=form.description.data, priority=form.priority.data)
        db.session.add(t)
        db.session.commit()
        flash('Ticket created', 'success')
        return redirect(url_for('desk.tickets'))
    return render_template('desk/form.html', form=form, title='New Ticket', customers=customers)


@bp.route('/tickets/<int:id>', methods=['GET', 'POST'])
def ticket_detail(id):
    t = Ticket.query.get_or_404(id)
    form = TicketCommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Login required to comment', 'warning')
            return redirect(url_for('auth.login'))
        c = TicketComment(ticket_id=t.id, message=form.message.data, user_id=current_user.id)
        db.session.add(c)
        db.session.commit()
        flash('Comment added', 'success')
        return redirect(url_for('desk.ticket_detail', id=t.id))
    return render_template('desk/detail.html', item=t, form=form, title='Ticket')
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Ticket, TicketComment, Customer
from blueprints.desk.forms import TicketForm, TicketCommentForm
from flask_login import current_user, login_required

desk_bp = Blueprint("desk", __name__, template_folder="templates")


@desk_bp.route("/")
def dashboard():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template("desk/list.html", tickets=tickets)


@desk_bp.route("/ticket/<int:id>", methods=["GET", "POST"])
def view_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    form = TicketCommentForm()
    
    if form.validate_on_submit() and current_user.is_authenticated:
        comment = TicketComment(
            ticket_id=id,
            user_id=current_user.id,
            body=form.body.data
        )
        db.session.add(comment)
        db.session.commit()
        flash("Comment added", "success")
        return redirect(url_for("desk.view_ticket", id=id))
    
    return render_template("desk/detail.html", ticket=ticket, form=form)


@desk_bp.route("/ticket/add", methods=["GET", "POST"])
def add_ticket():
    form = TicketForm()
    customers = Customer.query.all()
    
    if form.validate_on_submit():
        ticket = Ticket(
            customer_id=form.customer_id.data,
            subject=form.subject.data,
            description=form.description.data,
            priority=form.priority.data,
            status="open"
        )
        db.session.add(ticket)
        db.session.commit()
        flash("Ticket created", "success")
        return redirect(url_for("desk.view_ticket", id=ticket.id))
    
    return render_template("desk/form.html", form=form, customers=customers, edit=False)


@desk_bp.route("/ticket/<int:id>/edit", methods=["GET", "POST"])
def edit_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    form = TicketForm()
    customers = Customer.query.all()
    
    if form.validate_on_submit():
        ticket.customer_id = form.customer_id.data
        ticket.subject = form.subject.data
        ticket.description = form.description.data
        ticket.priority = form.priority.data
        db.session.commit()
        flash("Ticket updated", "success")
        return redirect(url_for("desk.view_ticket", id=id))
    elif request.method == "GET":
        form.customer_id.data = ticket.customer_id
        form.subject.data = ticket.subject
        form.description.data = ticket.description
        form.priority.data = ticket.priority
    
    return render_template("desk/form.html", form=form, ticket=ticket, customers=customers, edit=True)


@desk_bp.route("/ticket/<int:id>/status", methods=["POST"])
def update_ticket_status(id):
    ticket = Ticket.query.get_or_404(id)
    status = request.form.get("status")
    if status in ["open", "in_progress", "resolved", "closed"]:
        ticket.status = status
        db.session.commit()
        flash(f"Ticket status changed to {status}", "success")
    return redirect(url_for("desk.view_ticket", id=id))


@desk_bp.route("/ticket/<int:id>/delete", methods=["POST"])
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    db.session.delete(ticket)
    db.session.commit()
    flash("Ticket deleted", "success")
    return redirect(url_for("desk.dashboard"))
