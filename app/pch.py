import datetime
from flask import Blueprint, render_template, request
from flask_login import current_user

from app.models import Pos, RDaily, ManualDaily, PosMap, PCH_MAP
from app import get_sampling
bp = Blueprint('pch', __name__, url_prefix='/pch')


@bp.route('/<int:id>/<int:tahun>/<int:bulan>')
def show_month(id, tahun, bulan):
    pos = Pos.get(id)
    samp = "{}-{}-1".format(tahun, bulan)
    pm = PosMap.get(PosMap.pos==pos)
    nama = pm.source
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
    
    t_month = None
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
        
    for k, v in days.items():
        print(k, v)
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
    pos = Pos.get(int(id))
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    pm = PosMap.get(PosMap.pos==pos)
    nama = pm.source
    this_day = None
    if nama:
        this_day = RDaily.select().where(RDaily.nama==nama, 
                                     RDaily.sampling.year == sampling.year,
                                     RDaily.sampling.month == sampling.month,
                                     RDaily.sampling.day == sampling.day).first()
    ctx = {'pos': pos,
           'sampling': sampling,
           '_sampling': _sampling,
           'sampling_': sampling_,
           'this_day': this_day
           }
    return render_template('pch/show.html', ctx=ctx)

@bp.route('/')
def index():
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    user = current_user
    if user.is_anonymous:
        editable = False
    else:
        editable = user.is_admin and sampling.date() < datetime.date.today()
    pchs = Pos.select().where(Pos.tipe=='1').order_by(Pos.nama)
    data_manual = dict([(m.pos.id, m.ch) for m in ManualDaily.select().where(ManualDaily.sampling==sampling.strftime('%Y-%m-%d'))])
    for p in pchs:
        if p.id in data_manual:
            p.ch = data_manual[p.id]
    return render_template('pch/index.html', pchs=pchs, 
                           sampling=sampling, _sampling=_sampling, 
                           sampling_=sampling_, editable=editable)