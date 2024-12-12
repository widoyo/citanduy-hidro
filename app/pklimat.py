import datetime
from flask import Blueprint, render_template, request
from flask_login import current_user

from app.models import Pos
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
    ctx = {
        'pklimats': Pos.select().where(Pos.tipe=='3').order_by(Pos.nama),
        '_sampling': _sampling,
        'sampling': sampling,
        'sampling_': sampling_
    }
    return render_template('pklimat/index.html', ctx=ctx)