from flask import Blueprint, render_template, request
import datetime
import json

from app.models import Pos, RDaily, VENDORS
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
    '''
    Warna:
     orde 1: #1f56b5 rgb(31, 86, 181)
     orde 2: #3e83fa rgb(62, 131, 250)
     orde 3: #76a4f5 rbg(181, 208, 255)
    '''
    (_s, s, s_) = get_sampling(request.args.get('s'))
    poses = Pos.select().where(Pos.tipe=='2').order_by(Pos.nama)
    for p in poses:
        try:
            rd = p.rdaily_set.where(RDaily.sampling==s).first()
            raw = json.loads(rd.raw)
            p.latest_sampling = raw[-1]['sampling']
            p.latest_tma = raw[-1]['wlevel']
            if rd.source != 'SA':
                p.latest_tma = raw[-1]['wlevel'] * 100
            p.vendor = VENDORS[rd.source].get('nama')
        except:
            pass
    ctx = {
        '_s': _s,
        's': s,
        's_': s_,
        'pos_da': poses,
    }
    return render_template('map/sungai.html', ctx=ctx)


@bp.route('/hujan')
def hujan():
    (_s, s, s_) = get_sampling(request.args.get('s'))
    poses = Pos.select().order_by(Pos.tipe, Pos.nama)
    pchs = [p for p in poses if p.tipe == '1']
    pklimats = [p for p in poses if p.tipe=='3']
    ctx = {
        '_s': _s,
        's': s,
        's_': s_,
        'pos_ch': pchs,
        'pos_klimat': pklimats
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