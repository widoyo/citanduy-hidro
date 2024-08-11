import json
from flask import Blueprint, request, abort, render_template, jsonify

from app.models import RDaily
from app import get_sampling

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/rain')
def rain():
    (_s, s, s_) = get_sampling(request.args.get('s', None))
    rdaily = RDaily.select().where(RDaily.sampling==s.strftime('%Y-%m-%d'))
    out = []
    for r in rdaily:
        if not r._rain(): continue
        if r._rain()['rain24'] == 0: continue
        if r.pos and r.pos.tipe not in ('1', '3'): continue
        row = {'pos': r.pos and r.pos.nama or r.nama, 'sampling': r.sampling, 'rain24': r._rain()['rain24']}
        out.append(row)
    
    return jsonify(out)