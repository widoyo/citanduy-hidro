from flask import Blueprint, render_template, request
import datetime

from app.models import Pos
from app import get_sampling
bp = Blueprint('map', __name__, url_prefix='/map')


@bp.route('/pos')
def pos():
    (_s, s, s_) = get_sampling(request.args.get('s'))
    poses = Pos.select().order_by(Pos.tipe, Pos.nama)
    pchs = [p for p in poses if p.tipe == '1']
    pdas = [p for p in poses if p.tipe=='2']
    pklimats = [p for p in poses if p.tipe=='3']
    ctx = {
        '_s': _s,
        's': s,
        's_': s_,
        'pos_ch': pchs,
        'pos_da': pdas,
        'pos_klimats': pklimats
    }
    return render_template('map/pos.html', ctx=ctx)


@bp.route('/sungai')
def sungai():
    (_s, s, s_) = get_sampling(request.args.get('s'))
    poses = Pos.select().order_by(Pos.tipe, Pos.nama)
    pchs = [p for p in poses if p.tipe == '1']
    pdas = [p for p in poses if p.tipe=='2']
    pklimats = [p for p in poses if p.tipe=='3']
    ctx = {
        '_s': _s,
        's': s,
        's_': s_,
        'pos_ch': pchs,
        'pos_da': pdas,
        'pos_klimats': pklimats
    }
    return render_template('map/sungai.html', ctx=ctx)


@bp.route('/hujan')
def hujan():
    (_s, s, s_) = get_sampling(request.args.get('s'))
    poses = Pos.select().order_by(Pos.tipe, Pos.nama)
    pchs = [p for p in poses if p.tipe == '1']
    pdas = [p for p in poses if p.tipe=='2']
    pklimats = [p for p in poses if p.tipe=='3']
    ctx = {
        '_s': _s,
        's': s,
        's_': s_,
        'pos_ch': pchs,
        'pos_da': pdas,
        'pos_klimats': pklimats
    }
    return render_template('map/hujan.html', ctx=ctx)

@bp.route('/spi')
def spi():
    (_s, s, s_) = get_sampling(request.args.get('s'))
    poses = Pos.select().order_by(Pos.tipe, Pos.nama)
    pchs = [p for p in poses if p.tipe == '1']
    ctx = {
        '_s': _s,
        's': s,
        's_': s_,
        'pos_ch': pchs,
    }
    return render_template('map/spi.html', ctx=ctx)

@bp.route('/')
def index():
    (_s, s, s_) = get_sampling(request.args.get('s'))
    poses = Pos.select().order_by(Pos.tipe, Pos.nama)
    pchs = [p for p in poses if p.tipe == '1']
    pdas = [p for p in poses if p.tipe=='2']
    pklimats = [p for p in poses if p.tipe=='3']
    ctx = {
        '_s': _s,
        's': s,
        's_': s_,
        'pos_ch': pchs,
        'pos_da': pdas,
        'pos_klimats': pklimats
    }
    return render_template('map/index.html', ctx=ctx)