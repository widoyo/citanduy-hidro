import datetime
from flask import Blueprint, render_template, request, abort
from flask_login import current_user, login_required
from peewee import DoesNotExist

from app.models import Pos, RDaily, ManualDaily, PosMap
from app import get_sampling, admin_required
bp = Blueprint('kinerja', __name__, url_prefix='/kinerja')

@bp.route('')
@login_required
@admin_required
def index():
    poses = [p.id for p in Pos.select().order_by(Pos.tipe, Pos.nama)]
    (_s, s, s_) = get_sampling(request.args.get('s', None))
    manual_today = ManualDaily.select().where(ManualDaily.sampling==s.strftime('%Y-%m-%d'))
    manual_month = ManualDaily.select().where(ManualDaily.sampling.year==s.year)
    
    ctx = {
        'td': len(manual_today),
        'atd': len(poses),
        'tm': len(manual_month)
    }
    
    return render_template('kinerja/index.html', ctx=ctx)