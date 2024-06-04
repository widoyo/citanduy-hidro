from flask import Blueprint, render_template, request
import json

from app.models import Pos, ManualDaily, RDaily, PosMap
from app import get_sampling
bp = Blueprint('pda', __name__, url_prefix='/pda')


@bp.route('/<int:id>')
def show(id):
    pos = Pos.get(id)
    pm = PosMap.select().where(PosMap.pos==pos).first()
    rdailies = RDaily.select().where(RDaily.nama==pm.nama)
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
    pos_sources = dict([(p.source, p.pos.id) for p in PosMap.select().where(PosMap.pos.in_([p for p in pdas]))])
    rdailies = dict([(pos_sources[r.nama], r) for r in RDaily.select()
                     .where(RDaily.nama.in_(list(pos_sources.keys())), 
                            RDaily.sampling==sampling.strftime('%Y-%m-%d'))])
    mds = dict([(m.pos.id, m.tma) for m in ManualDaily.select().where(
        ManualDaily.sampling==sampling.strftime('%Y-%m-%d'), 
        ManualDaily.tma.is_null(False))])
    for p in pdas:
        if p.id in mds:
            tma = json.loads(mds.get(p.id))
            for k, v in tma.items():
                setattr(p, 'm_tma_' + k, v)
        if p.id in rdailies:
            tma = rdailies[p.id]._tma()
            for k, v in tma.items():
                jam = str(k).zfill(2)
                setattr(p, 'tma_' + jam, v.get('wlevel'))
    ctx = {
        'pdas': pdas,
        'sampling': sampling,
        '_sampling': _sampling,
        'sampling_': sampling_
    }
    
    return render_template('pda/index.html', ctx=ctx)