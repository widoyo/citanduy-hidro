from flask import Blueprint, render_template, request
from peewee import DoesNotExist
import json

from app.models import Pos, ManualDaily, RDaily, PosMap
from app import get_sampling
bp = Blueprint('pda', __name__, url_prefix='/pda')


@bp.route('/<int:id>')
def show(id):
    pos = Pos.get(id)
    rdailies = None
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    try:
        pm = PosMap.select().where(PosMap.pos==pos).first()
        if pm:
            rdailies = RDaily.select().where(RDaily.nama==pm.source, 
                                             RDaily.sampling==sampling.strftime('%Y-%m-%d')).first()
    except DoesNotExist:
        pass
    md = ManualDaily.select().where(ManualDaily.pos==pos,
                                    ManualDaily.sampling==sampling.strftime('%Y-%m-%d')).first()
    pos.telemetri = rdailies and rdailies._24jam() or {}
    pos.manual = md and md._tma or {}

    print('rdailies: ', pos.telemetri)
    print('md: ', pos.manual)
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

    rdailies = dict([(r.pos_id, r) for r in RDaily.select()
                     .where(RDaily.sampling==sampling.strftime('%Y-%m-%d'))])
    mds = dict([(m.pos.id, m.tma) for m in ManualDaily.select().where(
        ManualDaily.sampling==sampling.strftime('%Y-%m-%d'), 
        ManualDaily.tma.is_null(False))])
    for p in pdas:
        if p.id in mds:
            tma = json.loads(mds.get(p.id))
            for k, v in tma.items():
                setattr(p, 'm_tma_' + k, '{:.1f}'.format(float(v)))
        if p.id in rdailies:
            tma = rdailies[p.id]._tma()
            for k, v in tma.items():
                jam = str(k).zfill(2)
                setattr(p, 'tma_' + jam, '{:.1f}'.format(float(v.get('wlevel'))))
    sungai = set([p.sungai for p in pdas])
    ruas = {}
    for s in sungai:
        ruas.update({s: [p for p in pdas if p.sungai==s]})
    print(ruas)
    ctx = {
        'pdas': pdas,
        'sungai': ruas,
        'sampling': sampling,
        '_sampling': _sampling,
        'sampling_': sampling_
    }
    
    return render_template('pda/index.html', ctx=ctx)