import datetime
from flask import Blueprint, render_template, request
from flask_login import current_user

from app.models import Pos
from app import get_sampling
bp = Blueprint('pklimat', __name__, url_prefix='/pklimat')

@bp.route('/')
def index():
    ctx = {
        'pklimats': []
    }
    return render_template('pklimat/index.html', ctx=ctx)