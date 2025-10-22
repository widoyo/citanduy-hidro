import datetime
from flask import Blueprint, render_template, request, abort, jsonify, redirect
from flask_login import current_user, login_required
from peewee import DoesNotExist

from app import get_sampling
from app.models import Pos, Ticket
from app.forms import TicketForm
bp = Blueprint('ticket', __name__, url_prefix='/ticket')

@bp.route('/')
@login_required
def index():
    tickets = Ticket.select().order_by(Ticket.id.desc())
    ctx = {
        'tickets': tickets,
    }
    return render_template('ticket/index.html', ctx=ctx)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)
    form = TicketForm()
    if form.validate_on_submit():
        username = form.username.data
        subject = form.subject.data
        message = form.message.data
        pic = form.pic.data
        status = form.status.data
        tags = form.tags.data
        try:
            ticket = Ticket.create(
                username=username,
                subject=subject,
                message=message,
                pic=pic,
                status=status,
                tags=tags
            )
        except Exception as e:
            abort(500, 'Failed to create Ticket: {}'.format(str(e)))
        return redirect('/ticket')
    form.username.data = current_user.username
    ctx = {
        'form': form,
    }
    return render_template('ticket/add.html', ctx=ctx)


@bp.route('/<int:tic_id>')
@login_required
def show(tic_id):
    try:
        ticket = Ticket.get(Ticket.id==tic_id)
    except DoesNotExist:
        abort(404)
    ctx = {
        'ticket': ticket,
    }
    return render_template('ticket/show.html', ctx=ctx)


@bp.route('/<int:tic_id>', methods=['GET', 'POST'])
@login_required
def delete(tic_id):
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)
    try:
        pub = Ticket.get(Ticket.id==tic_id)
    except DoesNotExist:
        abort(404)
    try:
        pub.delete_instance()
    except Exception as e:
        abort(500, 'Failed to delete Ticket: {}'.format(str(e)))
    return jsonify({'message': 'Ticket deleted'}), 200
