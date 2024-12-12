from flask import Blueprint, render_template, abort
from flask_login import login_required
import datetime
from app.models import OPos

bp = Blueprint('rpos', __name__, url_prefix='/rpos')

@bp.route('/<int:id>/del', methods=['GET', 'POST'])
@login_required
def delete_(id):
    try:
        opos = OPos.get(id)
    except:
        return abort(404)
    ctx = {
        'opos': opos
    }
    
    return render_template('rpos/del_.html', ctx=ctx)

@bp.route('/')
@login_required
def index():
    oposes = OPos.select().where(OPos.aktif==True).order_by(OPos.latest_sampling)
    
    ctx = {
        'poses': oposes,
        'sa': {
            'all': [p for p in oposes if p.source == 'SA'],
            'pch': [p for p in oposes if p.source == 'SA' and p.tipe=='PCH'],
            'pda': [p for p in oposes if p.source == 'SA' and p.tipe=='PDA'],
            'aktif': [p for p in oposes if p.source == 'SA' and p.aktif==True],
        },
        'sb': {
            'all': [p for p in oposes if p.source == 'SB'],
            'pch': [p for p in oposes if p.source == 'SB' and p.tipe=='Rain Fall'],
            'pda': [p for p in oposes if p.source == 'SB' and p.tipe=='PDA'],
            'aktif': [p for p in oposes if p.source == 'SB' and p.aktif==True],         
        }
    }
    return render_template('rpos/index.html', ctx=ctx)