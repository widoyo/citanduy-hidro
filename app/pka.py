import datetime
from flask import Blueprint, render_template, request, abort
from flask_login import current_user
from peewee import DoesNotExist

from app import get_sampling
from app.models import Pos
bp = Blueprint('pka', __name__, url_prefix='/pka')


@bp.route('/map')
def map():
    poska = Pos.select().where(Pos.tipe=='4').order_by(Pos.sungai)
    ctx = {
        'poses': poska
    }
    return render_template('pka/map.html')

@bp.route('/')
def index():
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    poska = Pos.select().where(Pos.tipe=='4').order_by(Pos.sungai)
    ctx = {
        '_sampling': _sampling,
        'sampling': sampling,
        'sampling_': sampling_,
        'poses': poska
    }
    return render_template('pka/index.html', ctx=ctx)