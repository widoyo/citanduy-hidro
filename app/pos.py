from flask import Blueprint, render_template

from app.models import Pos
bp = Blueprint('pch', __name__, url_prefix='/pch')


@bp.route('/')
def index():
    pchs = Pos.select().where(Pos.tipe=='1').order_by(Pos.elevasi.desc())
    return render_template('pch/index.html', pchs=pchs)