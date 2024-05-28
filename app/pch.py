import datetime
from flask import Blueprint, render_template, request
from flask_login import current_user

from app.models import Pos
from app import get_sampling
bp = Blueprint('pch', __name__, url_prefix='/pch')


@bp.route('/<int:id>/<int:tahun>/<int:bulan>')
def show_month(id, tahun, bulan):
    samp = "{}-{}-1".format(tahun, bulan)
    print('samp', samp)
    (_sampling, sampling, sampling_) = get_sampling(samp)
    _sampling = sampling - datetime.timedelta(days=2)
    
    if sampling.strftime('%Y%m') >= datetime.date.today().strftime('%Y%m'):
        sampling_ = None
    else:
        delta = 31 - sampling.day
        sampling_ = sampling + datetime.timedelta(days=delta + 2)
    
    pos = Pos.get(id)
    ctx = {
        '_sampling': _sampling,
        'sampling': sampling,
        'sampling_': sampling_,
        'pos': pos
    }
    return render_template('pch/month.html', ctx=ctx)


@bp.route('/<id>')
def show(id):
    pos = Pos.get(int(id))
    
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    ctx = {'pos': pos,
           'sampling': sampling,
           '_sampling': _sampling,
           'sampling_': sampling_
           }
    return render_template('pch/show.html', ctx=ctx)

@bp.route('/')
def index():
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    user = current_user
    editable = user.is_admin and sampling.date() < datetime.date.today()
    pchs = Pos.select().where(Pos.tipe=='1').order_by(Pos.nama)
    return render_template('pch/index.html', pchs=pchs, 
                           sampling=sampling, _sampling=_sampling, 
                           sampling_=sampling_, editable=editable)