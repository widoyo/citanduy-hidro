from flask import Blueprint, render_template, request
import datetime

from app.models import Pos
bp = Blueprint('map', __name__, url_prefix='/peta')


@bp.route('/')
def index():
    poses = Pos.select().order_by(Pos.elevasi.desc())
    return render_template('map/index.html', poses=poses)