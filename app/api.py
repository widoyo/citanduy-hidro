import json
from flask import Blueprint, request, abort, render_template, jsonify

from app.models import RDaily
from app import get_sampling

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/rain')
def rain():
    (_s, s, s_) = get_sampling(request.args.get('s', None))
    rdaily = RDaily.select().where(RDaily.sampling==s.strftime('%Y-%m-%d'))
    r_this_day = [r for r in rdaily if r._rain()]
    return jsonify([r._rain() for r in r_this_day])