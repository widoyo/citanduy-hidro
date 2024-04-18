from flask import Blueprint, render_template, request
from flask_login import login_required

from app.models import User

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/')
@login_required
def index():
    users = User.select()
    return render_template('user/index.html', users=users)