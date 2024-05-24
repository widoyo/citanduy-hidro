from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required

from app.models import User, Pos
from app.forms import UserForm

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/<username>/update')

@bp.route('/add', methods=['POST'])
def add():
    form = UserForm()
    form.pos.choices = [('', 'Kantor')] + [(p.id, p.nama) for p in Pos.select().order_by(Pos.nama)]
    if form.validate_on_submit():
        if form.data.get('pos') == '':
            new_data = form.data
            new_data.update({'pos': None})
        else:
            new_data = form.data
        print(form.data)
        new_user = User.create(**new_data)
        new_user.set_password(new_data.get('password'))
        flash('Sukses')
        return redirect(url_for('user.index'))
    else:
        print(form.data)
        return render_template('user/add.html', form=form)


@bp.route('/')
@login_required
def index():
    users = User.select().order_by(User.pos_id)
    userform = UserForm()
    userform.pos.choices = [('', 'Kantor')] + [(p.id, p.nama) for p in Pos.select().order_by(Pos.nama)]
    
    return render_template('user/index.html', users=users, form=userform)