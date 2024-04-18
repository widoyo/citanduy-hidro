from flask import Blueprint, render_template, request
import datetime
from app.models import RDaily

bp = Blueprint('rdaily', __name__, url_prefix='/rdaily')

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
    sa_dailies = RDaily.select().where(RDaily.source=='SA', 
                                       RDaily.sampling.year==sampling.year, 
                                       RDaily.sampling.month==sampling.month, 
                                       RDaily.sampling.day==sampling.day)
    sb_dailies = RDaily.select().where(RDaily.source=='SB', 
                                       RDaily.sampling.year==sampling.year, 
                                       RDaily.sampling.month==sampling.month, 
                                       RDaily.sampling.day==sampling.day)
    return render_template('rdaily/index.html', 
                           sa_dailies=sa_dailies,
                           sb_dailies=sb_dailies,
                           sampling=sampling, 
                           _sampling=_sampling,
                           sampling_=sampling_)