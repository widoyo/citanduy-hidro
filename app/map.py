from flask import Blueprint, render_template, request
import datetime

from app.models import Pos
bp = Blueprint('map', __name__, url_prefix='/map')


@bp.route('/')
def index():
    poses = Pos.select().order_by(Pos.tipe, Pos.nama)
    pchs = [p for p in poses if p.tipe == '1']
    pdas = [p for p in poses if p.tipe=='2']
    pklimats = [p for p in poses if p.tipe=='3']
    ctx = {
        'pos_ch': pchs,
        'pos_da': pdas,
        'pos_klimats': pklimats
    }
    return render_template('map/index.html', ctx=ctx)