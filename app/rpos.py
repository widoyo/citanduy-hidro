from flask import Blueprint, render_template, request
import datetime
from app.models import OPos

bp = Blueprint('rpos', __name__, url_prefix='/rpos')

@bp.route('/')
def index():
    oposes = OPos.select().order_by(OPos.latest_sampling.desc())
    
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