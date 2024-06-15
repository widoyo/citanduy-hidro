from flask import Blueprint, render_template, request
import datetime
from peewee import DoesNotExist
from app.models import RDaily, OPos, PosMap
from app import get_sampling
from app.config import SDATELEMETRY_POS_EXCLUDES

bp = Blueprint('rdaily', __name__, url_prefix='/rdaily')

@bp.route('/<pos_name>/')
def show(pos_name):
    (_s, s, s_) = get_sampling(request.args.get('s', None))
    
    try:
        pos = OPos.get(OPos.nama==pos_name)
    except DoesNotExist:
        pos = OPos()
    try:
        this_day = RDaily.select().where(RDaily.nama==pos_name, 
                                     RDaily.sampling==s.strftime('%Y-%m-%d')).first()
        this_day.tipe = (type(pos) != type(OPos())) and pos.tipe or ''
    except DoesNotExist:
        this_day = []
    ctx = {
        '_sampling': _s,
        'sampling': s,
        'sampling_': s_,
        'opos': pos,
        'this_day': this_day
    }
    return render_template('rdaily/show.html', ctx=ctx)

@bp.route('/')
def index():
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    
    mapped_pos = [p for p in PosMap.select()]
    poses = dict([(p.nama, p) for p in OPos.select()])
    sa_dailies = RDaily.select().where(RDaily.source=='SA', 
                                       RDaily.sampling == sampling.strftime('%Y-%m-%d'))
    
    pos_excludes = SDATELEMETRY_POS_EXCLUDES.split(';')
    sa_dailies = [s for s in sa_dailies if s.nama not in pos_excludes]
    for s in sa_dailies:
        s.tipe = poses[s.nama].tipe
    sb_dailies = RDaily.select().where(RDaily.source=='SB', 
                                       RDaily.sampling == sampling.strftime('%Y-%m-%d'))
    for s in sb_dailies:
        try:
            s.tipe = poses[s.nama].tipe
        except:
            s.tipe = ''
    sc_dailies = RDaily.select().where(RDaily.source=='SC', 
                                       RDaily.sampling == sampling.strftime('%Y-%m-%d'))
    return render_template('rdaily/index.html', 
                           sa_dailies=sa_dailies,
                           sb_dailies=sb_dailies,
                           sc_dailies=sc_dailies, 
                           sampling=sampling, 
                           _sampling=_sampling,
                           sampling_=sampling_)