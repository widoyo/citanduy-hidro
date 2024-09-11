import json
from flask import Blueprint, request, abort, render_template, jsonify
from peewee import DoesNotExist, fn
from playhouse.shortcuts import model_to_dict
from flask_wtf.csrf import generate_csrf

from app.models import RDaily, VENDORS, Pos, ManualDaily
from app import get_sampling, csrf

bp = Blueprint('api', __name__, url_prefix='/api')
from app.api import pos


@bp.route('/token')
def get_token():
    return jsonify({'token': generate_csrf()})

@bp.route('/sensor', methods=['POST'])
@csrf.exempt
def sensor():
    return jsonify({'ok': True})


@bp.route('/rain')
def rain():
    (_s, s, s_) = get_sampling(request.args.get('s', None))
    rdaily = RDaily.select().where(RDaily.sampling==s.strftime('%Y-%m-%d'))
    out = []
    for r in rdaily:
        if not r._rain(): continue
        if r._rain()['rain24'] == 0: continue
        if r.pos and r.pos.tipe not in ('1', '3'): continue
        
        row = {'pos': {'nama': r.pos and r.pos.nama or r.nama, 'id': r.pos and r.pos.id or None},
               'vendor': VENDORS[r.source], 
               'count24': r._rain()['count24'], 
               'rain24': r._rain()['rain24'], 
               'rain': r._rain()['hourly'], 
               'raw': r._rain()['raw']}
        out.append(row)
    
    return jsonify({
        'meta': {
            'description': 'Hujan yang terjadi pada pos Hujan dan Klimat', 
            'sampling': s.isoformat()}, 
        'items': out})


@bp.route('/pch/<int:id>')
def pch_show(id: int):
    try:
        pos = Pos.get(id)
        if pos.tipe not in ('1', '3'): raise DoesNotExist
    except DoesNotExist:
        return jsonify({
            'code': 404,
            'ok': False})
    max = ManualDaily.select().where(ManualDaily.pos==pos).order_by(ManualDaily.ch.desc()).first()
    min = ManualDaily.select().where(ManualDaily.pos==pos).order_by(ManualDaily.sampling).first()
    count = ManualDaily.select(fn.Count(ManualDaily.id)).scalar()
    yearly = ManualDaily.select(ManualDaily.sampling.year.alias('tahun'), fn.Sum(ManualDaily.ch).alias('ch')).where(ManualDaily.pos==pos).group_by(ManualDaily.sampling.year)
    pos.max = max
    pos.min = min
    pos.count = count
    dict_pos = model_to_dict(pos)
    dict_pos.update({
        'manual': {
            'max': 
                {'sampling': max.sampling, 'ch': max.ch},
            'count': count,
            'first': 
                {'sampling': min.sampling, 'ch': min.ch},
            'yearly': [{'tahun': y.tahun, 'ch': y.ch} for y in yearly]
        }
        })
    return jsonify({
        'ok': True,
        'id': id,
        'pos': dict_pos})