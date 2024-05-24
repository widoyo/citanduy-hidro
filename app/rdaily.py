from flask import Blueprint, render_template, request
import datetime
from app.models import RDaily, OPos
from app import get_sampling

bp = Blueprint('rdaily', __name__, url_prefix='/rdaily')

@bp.route('/<pos_name>/')
def show(pos_name):
    (_s, s, s_) = get_sampling(request.args.get('s', None))
    
    pos = OPos.get(OPos.nama==pos_name)    
    this_day = RDaily.select().where(RDaily.nama==pos_name, RDaily.sampling==s).first()
    this_day.tipe = pos.tipe
    ctx = {
        '_sampling': _s,
        'sampling': s,
        'sampling_': s_,
        'this_day': this_day
    }
    return render_template('rdaily/show.html', ctx=ctx)

@bp.route('/')
def index():
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    
    poses = dict([(p.nama, p) for p in OPos.select()])
    sa_dailies = RDaily.select().where(RDaily.source=='SA', 
                                       RDaily.sampling.year==sampling.year, 
                                       RDaily.sampling.month==sampling.month, 
                                       RDaily.sampling.day==sampling.day)
    for s in sa_dailies:
        s.tipe = poses[s.nama].tipe
    sb_dailies = RDaily.select().where(RDaily.source=='SB', 
                                       RDaily.sampling.year==sampling.year, 
                                       RDaily.sampling.month==sampling.month, 
                                       RDaily.sampling.day==sampling.day)
    for s in sb_dailies:
        try:
            s.tipe = poses[s.nama].tipe
        except:
            s.tipe = ''
    sc_dailies = RDaily.select().where(RDaily.source=='SC', 
                                       RDaily.sampling.year==sampling.year, 
                                       RDaily.sampling.month==sampling.month, 
                                       RDaily.sampling.day==sampling.day)
    return render_template('rdaily/index.html', 
                           sa_dailies=sa_dailies,
                           sb_dailies=sb_dailies,
                           sc_dailies=sc_dailies, 
                           sampling=sampling, 
                           _sampling=_sampling,
                           sampling_=sampling_)