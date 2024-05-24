from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import current_user

from app.models import Pos, ManualDaily
from app import get_sampling
from app.forms import CurahHujanForm, TmaForm
bp = Blueprint('pos', __name__, url_prefix='/pos')

@bp.route('/manual')
def manual():
    formhujan = CurahHujanForm()
    if current_user.is_anonymous:
        abort(404)
    if not current_user.is_admin:
        abort(404)
    (_s, s, s_) = get_sampling(request.args.get('s', None))
    data = ManualDaily.select().where(ManualDaily.sampling==s)
    data_manual_pch = dict([(p.pos.id, p.ch) for p in data if p.pos.tipe=='1'])
    data_manual_pda = dict([(p.pos.id, p.tma) for p in data if p.pos.tipe=='2'])
    data = Pos.select().order_by(Pos.tipe, Pos.nama)
    pch = [p for p in data if p.tipe=='1']
    for p in pch:
        if p.id in data_manual_pch:
            p.ch = data_manual_pch[p.id]
        else:
            p.ch = '-99'
    pda = [p for p in data if p.tipe=='2']
    for p in pda:
        if p.id in data_manual_pda:
            p.tma = data_manual_pda[p.id]
        else:
            p.tma = '-99'
        
    ctx = {
        '_sampling': _s,
        'sampling': s,
        'sampling_': s_,
        'pch': pch,
        'pda': pda,
        'formhujan': formhujan
    }
    return render_template('pos/manual/index.html', ctx=ctx)

@bp.route('/<int:id>/manual', methods=['POST'])
def upsert_manual(id):
    pos = Pos.get(id)
    if pos.tipe == '1':
        form = CurahHujanForm()
        if form.validate_on_submit():
            ret = {'ok': True, 'ch': form.ch.data, 
                   'sampling': form.sampling.data, 
                   'pos': pos.id,
                   'username': current_user.username}
            md = ManualDaily.create(**ret)
            print('ret', ret)
        else:
            print(form.errors)
            ret = {'ok': False, 'error': form.errors}
    return jsonify(ret)

@bp.route('/')
def index():
    poses = Pos.select().order_by(Pos.tipe, Pos.nama, Pos.elevasi.desc())
    return render_template('pos/index.html', poses=poses)