import datetime
import json
from flask import Blueprint, render_template, request
from flask_login import current_user

from app.models import Pos, RDaily
from app import get_sampling
bp = Blueprint('pklimat', __name__, url_prefix='/pklimat')

'''
Pengukuran Manual Klimat:
Curah Hujan (mm)
Thermometer Max (7, 12, 17)
Thermometer Min (7, 12, 17)
Bola Kering (7, 12, 17)
Bola Basah (7, 12, 17)
Thermometer Apung Max, Min
Pembacaan Hoog (naik/Turun)
Lama Penyinaran (jam)
Anemomter Speedometer
Anemometer Km/Hari
Penguapan
'''
@bp.route('/')
def index():
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    pos_klimats = []
    for p in Pos.select().where(Pos.tipe=='3').order_by(Pos.nama):
        # Cari data klimat hari ini
        klimat = p.rdaily_set.where(RDaily.sampling==sampling.strftime('%Y-%m-%d')).first()
        if klimat:
            data = json.loads(klimat.raw)
            p.klimat = data[-1]
        else:
            p.klimat = None
        pos_klimats.append(p)
    ctx = {
        'pklimats': pos_klimats,
        '_sampling': _sampling,
        'sampling': sampling,
        'sampling_': sampling_
    }
    return render_template('pklimat/index.html', ctx=ctx)

@bp.route('/<int:id>')
def show(id):
    try:
        pos = Pos.get(Pos.id==id, Pos.tipe=='3')
    except Pos.DoesNotExist:
        abort(404)
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    _sampling = sampling.replace(year=sampling.year - 1)
    sampling_ = sampling.replace(year=sampling.year + 1)
    if datetime.date.today().year == sampling.year:
        sampling_ = None
    all_years = (RDaily.select(RDaily.sampling.year.alias('tahun'), 
                              RDaily.sampling.month.alias('bulan'))
                 .where(RDaily.pos==pos)
                 .order_by(RDaily.sampling.year, RDaily.sampling.month))
    this_year = [ay for ay in all_years if ay.tahun==sampling.year]
    all_year = {}

    ctx = {
        'pos': pos,
        'this_year': this_year,
        'all_year': all_year,
        'sampling': sampling,
        '_sampling': _sampling,
        'sampling_': sampling_
    }
    return render_template('pklimat/show.html', ctx=ctx)