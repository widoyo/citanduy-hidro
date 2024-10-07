import json
from flask import Blueprint, request, abort, render_template, jsonify
from peewee import DoesNotExist, fn
from playhouse.shortcuts import model_to_dict
from flask_wtf.csrf import generate_csrf

from app.models import RDaily, VENDORS, Pos, ManualDaily, Incoming
from app import get_sampling, csrf

bp = Blueprint('api', __name__, url_prefix='/api')
from app.api import pos


@bp.route('/token')
def get_token():
    return jsonify({'token': generate_csrf()})

@bp.route('/sensor', methods=['POST'])
@csrf.exempt
def sensor():
    out = {'ok': False}
    if request.is_json:
        data = request.get_json();
        ua = request.headers.get('User-Agent')
        new_incoming = Incoming.create(user_agent=ua, body=data)
        if new_incoming:
            out = {'ok': True, 'id': new_incoming.id}
    return jsonify(out)

@bp.route('/sensor/<uuid>')
def sensor_show(uuid):
    try:
        inc = Incoming.get(Incoming.id==uuid)
    except DoesNotExist:
        return jsonify({'ok': False, 'msg': 'Not found'})
    return jsonify(model_to_dict(inc))

@bp.route('/wlevel')
def wlevel():
    '''{pos: manual: telemetri: }'''
    get_newest = not request.args.get('s', None)
    (_s, s, s_) = get_sampling(request.args.get('s', None))
    pdas = Pos.select().where(Pos.tipe=='2').order_by(Pos.sungai, Pos.elevasi.desc())
    pids = [p.id for p in pdas]
    if not get_newest:
        rd = dict([(r.pos_id, r) for r in RDaily.select().where(RDaily.sampling==s.strftime('%Y-%m-%d'), 
                                  RDaily.pos_id.in_(pids))])
        md = dict([(m.pos_id, m) for m in ManualDaily.select().where(ManualDaily.sampling==s.strftime('%Y-%m-%d'),
                                       ManualDaily.pos_id.in_(pids))])
        for p in pdas:
            try:
                p.telemetri = json.loads(rd[p.id].raw) if rd[p.id].raw else []
                p.vendor = rd[p.id].vendor
            except KeyError:
                p.telemetri = []
                p.vendor = None
            try:
                p.manual = md[p.id]
            except KeyError:
                p.manual = []
    else:
        for p in pdas:
            r = p.rdaily_set.order_by(RDaily.sampling.desc()).first()
            m = p.manualdaily_set.order_by(ManualDaily.sampling.desc()).first()
            manual = []
            if m:
                for k, v in json.loads(m.tma).items():
                    if k in ('07', '12', '17'):
                        manual.append({'sampling': m.sampling.strftime('%Y-%m-%dT') + k, 'tma': v})
            p.telemetri = json.loads(r.raw) if r else []
            p.vendor = r.vendor if r else None
            p.manual = manual
            
    return jsonify({
        'meta': {
            'description': 'Tinggi Muka Air semua Pos Duga Air', 
            'sampling': s.strftime('%Y-%m-%d')}, 
        'items': [{'nama': p.nama, 
                   'elevasi': p.elevasi, 
                   'sungai': p.sungai,
                   'telemetri': p.telemetri,
                   'vendor': p.vendor,
                   'manual': p.manual} for p in pdas]
    })
    
    
@bp.route('/rain')
def rain():
    get_newest = request.args.get('s', None)
    (_s, s, s_) = get_sampling(request.args.get('s', None))
    rdaily = RDaily.select().where(RDaily.sampling==s.strftime('%Y-%m-%d'))
    mdaily = dict([(m.pos_id, m) for m in ManualDaily.select().where(ManualDaily.sampling==s.strftime('%Y-%m-%d'),
                                        )])
    out = []
    for r in rdaily:
        if not r._rain(): continue
        if r._rain()['rain24'] == 0: continue
        if r.pos and r.pos.tipe not in ('1', '3'): continue
        try:
            manual = mdaily[r.pos.id].ch
        except:
            manual = None
        row = {'pos': {'nama': r.pos and r.pos.nama or r.nama, 'id': r.pos and r.pos.id or None},
               'vendor': VENDORS[r.source],
               'telemetri':  {
                'count24': r._rain()['count24'], 
                'rain24': r._rain()['rain24'], 
                'rain': r._rain()['hourly'], 
                #'raw': r._rain()['raw']
                },
               'manual': manual
        }
        out.append(row)
    
    return jsonify({
        'meta': {
            'description': 'Hujan yang terjadi pada pos Hujan dan Klimat', 
            'sampling': s.strftime('%Y-%m-%d')},
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
                {'sampling': max.sampling if max else '-', 'ch': max.ch if max else '-'},
            'count': count,
            'first': 
                {'sampling': min.sampling if min else '-', 'ch': min.ch if min else '-'},
            'yearly': [{'tahun': y.tahun, 'ch': y.ch} for y in yearly]
        }
        })
    return jsonify({
        'ok': True,
        'id': id,
        'pos': dict_pos})