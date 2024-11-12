from flask import Blueprint, render_template, request, redirect
from flask_login import login_required, current_user

from app.models import Notes
from app.forms import NoteForm
from app import get_sampling

bp = Blueprint('note', __name__, url_prefix='/note')

@bp.route('/')
@login_required
def index():
    form = NoteForm()
    ctx = {
        'msgs': Notes.select().order_by(Notes.cdate.desc()),
        'form': form
    }
    return render_template('note/index.html', ctx=ctx)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = NoteForm(request.form)
    if form.validate_on_submit():
        new_note = Notes.create(username=current_user.username, 
                                obj_name=form.obj_name.data,
                                obj_id=form.obj_id.data,
                                msg=form.msg.data)
        return redirect('/note/')
    else:
        return render_template('note/add.html')