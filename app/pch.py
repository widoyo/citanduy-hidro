import datetime
from flask import Blueprint, render_template, request, abort
from flask_login import current_user
from peewee import DoesNotExist

from app.models import Pos, RDaily, ManualDaily, PosMap
from app import get_sampling
bp = Blueprint('pch', __name__, url_prefix='/pch')


@bp.route('/<int:id>/<int:tahun>/<int:bulan>')
def show_month(id, tahun, bulan):
    try:
        pos = Pos.get(id)
    except DoesNotExist:
        abort(404)
    samp = "{}-{}-1".format(tahun, bulan)
    try:
        pm = PosMap.get(PosMap.pos==pos)
        nama = pm.source
    except DoesNotExist:
        nama = None
    (_sampling, sampling, sampling_) = get_sampling(samp)
    _sampling = sampling - datetime.timedelta(days=2)
    if sampling.strftime('%Y%m') >= datetime.date.today().strftime('%Y%m'):
        sampling_ = None
    else:
        sampling_ = (sampling + datetime.timedelta(days=32)).replace(day=1)
    today = datetime.date.today()
    if sampling_ and sampling_.date() < today:
        days = dict([(i+1, {'count': 0, 'rain': 0, 'mrain': 0}) for i in range((sampling_.date() - sampling.date()).days)])
    else:
        days = dict([(i+1, {'count': 0, 'rain': 0, 'mrain': 0}) for i in range(today.day)])
    
    t_month = []
    if nama:
        t_month = RDaily.select().where(RDaily.nama==nama, 
                                     RDaily.sampling.year == sampling.year, 
                                     RDaily.sampling.month == sampling.month)
    m_month = ManualDaily.select().where(ManualDaily.pos==pos,
                                         ManualDaily.sampling.year==sampling.year,
                                         ManualDaily.sampling.month==sampling.month)
    for m in m_month:
        if m.sampling.day in days:
            days[m.sampling.day]['mrain'] = m.ch
            
    for r in t_month:
        if r.sampling.day in days:
            days[r.sampling.day]['count'] = r._rain().get('count24')
            days[r.sampling.day]['rain'] = r._rain().get('rain24')
        
    ctx = {
        '_sampling': _sampling,
        'sampling': sampling,
        'sampling_': sampling_,
        'pos': pos,
        'days': days
    }
    return render_template('pch/month.html', ctx=ctx)


@bp.route('/<id>')
def show(id):
    try:
        pos = Pos.get(int(id))
    except DoesNotExist:
        abort(404)
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    this_day = None
    nama = None
    try:
        pm = PosMap.get(PosMap.pos==pos)
        nama = pm.source
        this_day = RDaily.select().where(RDaily.nama==nama, 
                                     RDaily.sampling == sampling.strftime('%Y-%m-%d')).first()
    except DoesNotExist:
        pass
    
    ctx = {'pos': pos,
           'sampling': sampling,
           '_sampling': _sampling,
           'sampling_': sampling_,
           'this_day': this_day
           }
    return render_template('pch/show.html', ctx=ctx)

@bp.route('/')
def index():
    if not request.args.get('s'):
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        (_sampling, sampling, sampling_) = get_sampling(yesterday)
    else:
        (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))

    pos_sources = dict([(p.source, p.pos.id) for p in PosMap.select() if p.pos.tipe=='1'])
    rdailies = dict([(pos_sources[r.nama], r) for r in RDaily.select()
                     .where(RDaily.nama.in_(list(pos_sources.keys())), 
                            RDaily.sampling==sampling.strftime('%Y-%m-%d'))])

    pchs = Pos.select().where(Pos.tipe.in_(('1', '3'))).order_by(Pos.kabupaten, Pos.nama)
    data_manual = dict([(m.pos.id, m.ch) for m in ManualDaily.select().where(ManualDaily.pos.in_([p for p in pchs]), ManualDaily.sampling==sampling.strftime('%Y-%m-%d'))])

    for p in pchs:
        if p.id in data_manual:
            p.m_ch = data_manual[p.id]
        if p.id in rdailies:
            rd = rdailies[p.id]._rain()
            p.pagi = sum([v.get('rain') for k, v in rd.get('hourly').items() if k >=7 and k < 13])
            p.siang = sum([v.get('rain') for k, v in rd.get('hourly').items() if k >=13 and k < 19])
            p.malam = sum([v.get('rain') for k, v in rd.get('hourly').items() if k >=19 and k < 24]) + \
                sum([v.get('rain') for k, v in rd.get('hourly').items() if k >=0 and k < 1])
            p.dini = sum([v.get('rain') for k, v in rd.get('hourly').items() if k >=1 and k < 7])
            p.ch = rd.get('rain24')
            p.count = rd.get('count24')
            p.source = rdailies[p.id].source
            p.v_name = rdailies[p.id].nama
            max_count = 288
            if rdailies[p.id].source == 'SB':
                max_count = 96
            p.sehat = (p.count / max_count) * 100
    kabs = set([p.kabupaten for p in pchs])
    wils = {}
    for k in kabs:
        wils.update({k: [p for p in pchs if p.kabupaten == k]})
    kabs = {'b': [], 'xanu': [], 'c': []}
    ctx = {
        '_sampling': _sampling,
        'sampling': sampling,
        'sampling_': sampling_,
        'pchs': pchs,
        'wilayah': wils,
        'kabs': kabs
    }
    return render_template('pch/index.html', ctx=ctx)