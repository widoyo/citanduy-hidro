import datetime
from flask import Blueprint, render_template, request
from flask_login import current_user

from app.models import Pos
from app import get_sampling
bp = Blueprint('pch', __name__, url_prefix='/pch')


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