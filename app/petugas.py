from flask import Blueprint, render_template, request
from flask_login import login_required

from app.models import Petugas
from app import admin_required

bp = Blueprint('petugas', __name__, url_prefix='/petugas')


@bp.route('/')
@login_required
@admin_required
def index():
    ptgs = Petugas.select().order_by(Petugas.tipe, Petugas.nama)
    return render_template('petugas/index.html', petugas=ptgs)