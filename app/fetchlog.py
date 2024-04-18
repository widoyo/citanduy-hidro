from flask import Blueprint, render_template, request
import datetime
from app.models import FetchLog

bp = Blueprint('flog', __name__, url_prefix='/flog')

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
    flogs = FetchLog.select().where(FetchLog.cdate.year==sampling.year, FetchLog.cdate.month==sampling.month, FetchLog.cdate.day==sampling.day)
    return render_template('flog/index.html', 
                           flogs=flogs, 
                           sampling=sampling, 
                           _sampling=_sampling,
                           sampling_=sampling_)