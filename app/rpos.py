from flask import Blueprint, render_template, request
import datetime
from app.models import OPos

bp = Blueprint('rpos', __name__, url_prefix='/rpos')

@bp.route('/')
def index():
    oposes = OPos.select().order_by(OPos.latest_sampling.desc())
    return render_template('rpos/index.html', 
                           poses=oposes)