from flask import Blueprint, render_template, request
import datetime

from app.models import Pos
bp = Blueprint('pch', __name__, url_prefix='/pch')


@bp.route('/')
def index():
    s = request.args.get('s', None)
    try:
        sampling = datetime.datetime.strptime(s, '%Y-%m-%d')
        _sampling = sampling - datetime.timedelta(days=1)
        sampling_ = sampling + datetime.timedelta(days=1)
    except:
        sampling = datetime.date.today()
        _sampling = sampling - datetime.timedelta(days=1)
        sampling_ = None
    if sampling.date() >= datetime.date.today():
        sampling_ = None
    pchs = Pos.select().where(Pos.tipe=='1').order_by(Pos.elevasi.desc())
    return render_template('pch/index.html', pchs=pchs)