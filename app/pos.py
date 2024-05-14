from flask import Blueprint, render_template

from app.models import Pos
bp = Blueprint('pos', __name__, url_prefix='/pos')


@bp.route('/')
def index():
    poses = Pos.select().order_by(Pos.tipe, Pos.nama, Pos.elevasi.desc())
    return render_template('pos/index.html', poses=poses)