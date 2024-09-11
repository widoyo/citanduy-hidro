from flask import abort, jsonify
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from app.api import bp
from app.models import Pos


@bp.route('/pos')
def index():
    return jsonify([p.id for p in Pos.select()])

@bp.route('/pos/<int:id>', methods=['GET'])
def pos(id):
    try:
        pos = Pos.get(id)
    except DoesNotExist:
        return abort(404)
    return jsonify(model_to_dict(pos))

@bp.route('/pos/<int:id>', methods=['PUT'])
def update_pos(id):
    pass