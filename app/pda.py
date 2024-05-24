from flask import Blueprint, render_template, request
import datetime

from app.models import Pos
from app import get_sampling
bp = Blueprint('pda', __name__, url_prefix='/pda')


@bp.route('/<int:id>')
def show(id):
    pos = Pos.get(id)
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    ctx = {
        'pos': pos,
        'sampling': sampling,
        'sampling_': sampling_,
        '_sampling': _sampling
    }
    return render_template('pda/show.html', ctx=ctx)        

    
@bp.route('/')
def index():
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    pdas = Pos.select().where(Pos.tipe=='2').order_by(Pos.elevasi.desc())
    return render_template('pda/index.html', pdas=pdas, sampling=sampling, _sampling=_sampling, sampling_=sampling_)