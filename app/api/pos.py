from flask import abort, jsonify
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from app.api import bp
from app.models import Pos


@bp.route('/pos')
def index():
    return jsonify([{'id': p.id, 'nama': p.nama} for p in Pos.select().where(Pos.tipe.in_(('1', '2', '3')))])

@bp.route('/pos/<int:id>', methods=['GET'])
def pos(id):
    try:
        pos = Pos.get(id)
        pt = pos.petugas_set.first()
        if pt:
            petugas = {"nama": pt.nama, "hp": pt.hp}
        else:
            petugas = None
    except DoesNotExist:
        return abort(404)
    out = {
        'nama': pos.nama,
        'll': pos.ll,
        'petugas': petugas,
        'tipe': pos.tipe,
        'id': pos.id,
        'elevasi': pos.elevasi
    }
    return jsonify(out)

@bp.route('/pos/<int:id>', methods=['PUT'])
def update_pos(id):
    pass