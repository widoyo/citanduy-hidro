from flask import Blueprint, render_template, request
import datetime

from app.models import Pos
bp = Blueprint('map', __name__, url_prefix='/map')


@bp.route('/')
def index():
    pchs = Pos.select().where(Pos.tipe=='1')
    pdas = Pos.select().where(Pos.tipe=='2')
    ctx = {
        'pos_ch': pchs,
        'pos_da': pdas
    }
    return render_template('map/index.html', ctx=ctx)