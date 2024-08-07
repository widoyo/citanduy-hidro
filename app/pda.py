from flask import Blueprint, render_template, request, abort
from peewee import DoesNotExist
import json
import datetime

from app.models import Pos, ManualDaily, RDaily, PosMap
from app import get_sampling
bp = Blueprint('pda', __name__, url_prefix='/pda')

PDAPCH = {
    6: (44, 19), # bojongsalawe_6: ciamis_44, janggala_19
    5: (52, 56, 19, 66), # binangun_5: cineam_52, gnputri_56, janggala_19, sidamulih_66
    31: (45, 20, 58, 62, 63, 64, 65), # bandaruka_31: cibariwal_45, danasari_20, kawali_58, panawangan_62, panjalu_63, rancah_64, sadananya_65
    1: (20, 64, 67), # batununggul_1: danasari_20, rancah_64, tanjungjaya_67
    2: (54, 55, 30, 67), # bebedahan_2: dayeuhluhur_54, gnbabakan_55, kaso_30, tanjungjaya_67
    3: (86, 50, 56, 25, 66, 60), # bdciputrahaji_3: ciawitali_86, cikupa_50, gnputri_56, pdaherang_25, padaringan_60, sidamulih_66
    7: (44, 45, 20, 63, 65), # bunar_7: ciamis_44, cibariwal_45, danasari_20, panjalu_63, sadananya_65
    32: (20, 58, 64, 67), # bunter_32: danasari_20, kawali_58, rancah_64, tanjungjaya_67
    
}
@bp.route('/<int:id>/<int:tahun>')
def show_year(id, tahun):
    try:
        pos = Pos.get(id)
    except DoesNotExist:
        abort(404)
    samp = "{}-1-1".format(tahun)
    try:
        pm = PosMap.get(PosMap.pos==pos)
        nama = pm.nama
    except DoesNotExist:
        nama = None
    ctx = {
        'pos': pos
    }
    return render_template('pda/year.html', ctx=ctx)

@bp.route('/<int:id>/<int:tahun>/<int:bulan>')
def show_month(id, tahun, bulan):
    try:
        pos = Pos.get(id)
    except DoesNotExist:
        abort(404)
    pchs = Pos.select().where(Pos.id.in_(PDAPCH[pos.id]))
    samp = "{}-{}-1".format(tahun, bulan)
    try:
        pm = PosMap.get(PosMap.pos==pos)
        nama = pm.nama
    except DoesNotExist:
        nama = None
    (_sampling, sampling, sampling_) = get_sampling(samp)
    _sampling = sampling - datetime.timedelta(days=2)
    if sampling.strftime('%Y%m') >= datetime.date.today().strftime('%Y%m'):
        sampling_ = None
    else:
        sampling_ = (sampling + datetime.timedelta(days=32)).replace(day=1)
    ctx = {
        'pos': pos,
        'pchs': pchs,
        'sampling': sampling,
        '_sampling': _sampling,
        'sampling_': sampling_
    }
    return render_template('pda/month.html', ctx=ctx)

@bp.route('/<int:id>')
def show(id):
    try:
        pos = Pos.get(id)
    except DoesNotExist:
        return abort(404)
    try:
        pchs = Pos.select().where(Pos.id.in_(PDAPCH[pos.id]))
    except KeyError:
        pchs = []
    rdailies = None
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    try:
        pm = PosMap.select().where(PosMap.pos==pos).first()
        if pm:
            rdailies = RDaily.select().where(RDaily.nama==pm.nama, 
                                             RDaily.sampling==sampling.strftime('%Y-%m-%d')).first()
    except DoesNotExist:
        pass
    md = ManualDaily.select().where(ManualDaily.pos==pos,
                                    ManualDaily.sampling==sampling.strftime('%Y-%m-%d')).first()
    pos.telemetri = rdailies and rdailies._24jam() or {}
    pos.manual = md and md._tma or {}

    ctx = {
        'pos': pos,
        'pchs': pchs,
        'sampling': sampling,
        'sampling_': sampling_,
        '_sampling': _sampling
    }
    return render_template('pda/show.html', ctx=ctx)        

    
@bp.route('/')
def index():
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    pdas = Pos.select().where(Pos.tipe=='2').order_by(Pos.elevasi.desc())

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
            p.source = rdailies[p.id].source
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