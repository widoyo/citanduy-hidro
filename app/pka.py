import datetime
from flask import Blueprint, render_template, request, abort
from flask_login import current_user
from peewee import DoesNotExist

from app import get_sampling
from app.models import Pos, HasilUjiKualitasAir
bp = Blueprint('pka', __name__, url_prefix='/pka')


@bp.route('/map')
def map():
    poska = Pos.select().where(Pos.tipe=='4').order_by(Pos.sungai)
    ctx = {
        'poses': poska
    }
    return render_template('pka/map.html', ctx=ctx)

@bp.route('/')
def index():
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    poska = Pos.select().where(Pos.tipe=='4').order_by(Pos.sungai)
    if sampling.month < 7:
        sampling = sampling.replace(month=1)
        _sampling = _sampling.replace(month=7, year=sampling.year - 1)
        if sampling_:
            sampling_ = sampling_.replace(month=7)
    else:
        sampling = sampling.replace(month=7)
        _sampling = _sampling.replace(month=1)
        if sampling_:
            sampling_ = sampling_.replace(month=1, year=sampling.year + 1)
    sungai = set([p.sungai for p in poska])
    months = [sampling.month + m for m in range(6)]
    huka = (HasilUjiKualitasAir.select()
            .where(HasilUjiKualitasAir.sampling.year==sampling.year,
                   HasilUjiKualitasAir.sampling.month.in_(months))
            .order_by(HasilUjiKualitasAir.sampling))
    hasil_uji = {}
    for hu in huka:
        hasil_uji.update({'{}_{}'.format(hu.pos_id, hu.sampling.month):  hu})
    
    out = {}
    for s in sungai:
        out.update({s: [p for p in poska if p.sungai==s]})
    ctx = {
        '_sampling': _sampling,
        'sampling': sampling,
        'sampling_': sampling_,
        'poses': poska,
        'sungai': out,
        'hasil_uji': hasil_uji
    }
    return render_template('pka/index.html', ctx=ctx)