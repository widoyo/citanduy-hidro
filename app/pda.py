from flask import Blueprint, render_template, request
import datetime

from app.models import Pos
bp = Blueprint('pda', __name__, url_prefix='/pda')


@bp.route('/<int:id>')
def show(id):
    pos = Pos.get(id)
    s = request.args.get('s', None)
    try:
        sampling = datetime.datetime.strptime(s, '%Y-%m-%d')
        _sampling = sampling - datetime.timedelta(days=1)
        sampling_ = sampling + datetime.timedelta(days=1)
    except:
        sampling = datetime.datetime.now()
        _sampling = sampling - datetime.timedelta(days=1)
        sampling_ = None
    if sampling.date() >= datetime.date.today():
        sampling_ = None
    ctx = {
        'pos': pos,
        'sampling': sampling,
        'sampling_': sampling_,
        '_sampling': _sampling
    }
    return render_template('pda/show.html', ctx=ctx)        

    
@bp.route('/')
def index():
    s = request.args.get('s', None)
    try:
        sampling = datetime.datetime.strptime(s, '%Y-%m-%d')
        _sampling = sampling - datetime.timedelta(days=1)
        sampling_ = sampling + datetime.timedelta(days=1)
    except:
        sampling = datetime.datetime.now()
        _sampling = sampling - datetime.timedelta(days=1)
        sampling_ = None
    if sampling.date() >= datetime.date.today():
        sampling_ = None
    pdas = Pos.select().where(Pos.tipe=='2').order_by(Pos.elevasi.desc())
    return render_template('pda/index.html', pdas=pdas, sampling=sampling, _sampling=_sampling, sampling_=sampling_)