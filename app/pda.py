from flask import Blueprint, render_template, request
import json

from app.models import Pos, ManualDaily
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
    pdas = Pos.select().where(Pos.tipe=='2').order_by(Pos.nama, Pos.elevasi.desc())
    mds = dict([(m.pos.id, m.tma) for m in ManualDaily.select().where(
        ManualDaily.sampling==sampling.strftime('%Y-%m-%d'), 
        ManualDaily.tma.is_null(False))])
    for p in pdas:
        if p.id in mds:
            tma = json.loads(mds.get(p.id))
            for k, v in tma.items():
                setattr(p, 'm_tma_' + k, v)
    ctx = {
        'pdas': pdas,
        'sampling': sampling,
        '_sampling': _sampling,
        'sampling_': sampling_
    }
    
    return render_template('pda/index.html', ctx=ctx)