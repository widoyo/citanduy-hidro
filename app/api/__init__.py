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
        data = request.get_json()
        ua = request.headers.get('User-Agent')
        new_incoming = Incoming.create(user_agent=ua, body=json.dumps(data))
        if new_incoming:
            out = {'ok': True, 'id': new_incoming.id}
            new_incoming.sb_to_daily()
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
    (_s, s, s_) = get_sampling(request.args.get('s', ''))
    pdas = Pos.select().where(Pos.tipe=='2').order_by(Pos.sungai, Pos.elevasi.desc())
    pids = [p.id for p in pdas]
    if not get_newest:
        rd = dict([(r.pos_id, r) for r in RDaily.select().where(RDaily.sampling==s.strftime('%Y-%m-%d'), 
                                  RDaily.pos_id.in_(pids))])
        md = dict([(m.pos_id, m) for m in ManualDaily.select().where(ManualDaily.sampling==s.strftime('%Y-%m-%d'),
                                       ManualDaily.pos_id.in_(pids))])
        for p in pdas:
            try:
                # Perhitungan trend Muka air thd 15 menit dan 60 menit sebelumnya
                t_raw = json.loads(rd[p.id].raw)
                p.telemetri = t_raw if rd[p.id].raw else []
                # ubah wlevel dari Meter ke Centimeter
                if p.telemetri != [] and rd[p.id].source in ('SB', 'SC') \
                    and p.telemetri[0].get('wlevel'):
                    p.telemetri = [{'sampling': r.get('sampling'), 'wlevel': r.get('wlevel') * 100} for r in p.telemetri if r.get('wlevel') is not None]
                p.vendor = rd[p.id].vendor
            except KeyError:
                p.telemetri = []
                p.vendor = None
            try:
                manual = []
                m = md[p.id]
                if m:
                    for k, v in json.loads(m.tma).items():
                        if k in ('07', '12', '17'):
                            manual.append({'sampling': m.sampling.strftime('%Y-%m-%dT') + k, 'tma': v})
                
                p.manual = manual
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
            # Perhitungan trend Muka air thd 15 menit dan 60 menit sebelumnya
            t_raw_3 = t_raw_12 = {}
            t_raw = json.loads(r.raw) if r and r.raw else []
            
            if t_raw:
                print(r.raw)
            p.telemetri = t_raw[-1] if r else {}
            
            if len(t_raw) >= 12:
                t_raw_3 = t_raw[-3]
                t_raw_12 = t_raw[-12]
                if r.source in ('SB',):
                    t_raw_3 = t_raw[-2]
                    t_raw_12 = t_raw[-5]
            wlevel_3 = t_raw_3.get('wlevel') if t_raw_3 else None
            sampling_3 = t_raw_3.get('sampling') if t_raw_3 else None
            try:
                delta_3 = p.telemetri.get('wlevel') - wlevel_3 if wlevel_3 else None
            except TypeError:
                delta_3 = None
            trend_3 = None
            if delta_3 is not None:
                trend_3 = "naik" if delta_3 and delta_3 > 0 else "turun" if delta_3 and delta_3 < 0 else "stabil"
            wlevel_12 = t_raw_12.get('wlevel') if t_raw_12 else None
            sampling_12 = t_raw_12.get('sampling') if t_raw_12 else None
            try:
                delta_12 = p.telemetri.get('wlevel') - wlevel_12 if wlevel_12 else None
            except TypeError:
                delta_12 = None
            trend_12 = None
            if delta_12 is not None:
                trend_12 = "naik" if delta_12 and delta_12 > 0 else "turun" if delta_12 and delta_12 < 0 else "stabil"
            wlevel_trends = {
                "t_15_min": {
                    "wlevel": wlevel_3,
                    "sampling": sampling_3,
                    "trend": trend_3,
                    "delta": delta_3
                },
                "t_60_min": {
                    "wlevel": wlevel_12,
                    "sampling": sampling_12,
                    "trend": trend_12,
                    "delta": delta_12
                }
            }
            # ubah wlevel dari Meter ke Centimeter
            if p.telemetri != {} and p.telemetri.get('wlevel') \
                and r.source in ('SB', 'SC'):
                p.telemetri['wlevel'] = (p.telemetri.get('wlevel', 0) * 100) if p.telemetri.get('wlevel') else None
                wlevel_trends['t_15_min']['wlevel'] = wlevel_trends['t_15_min']['wlevel'] * 100 if wlevel_trends['t_15_min']['wlevel'] else None
                wlevel_trends['t_60_min']['wlevel'] = wlevel_trends['t_60_min']['wlevel'] * 100 if wlevel_trends['t_60_min']['wlevel'] else None    
            p.telemetri['trend'] = wlevel_trends
            if t_raw:
                p.telemetri['raw'] = [{'sampling': t.get('sampling'), 'wlevel': t.get('wlevel')} for t in t_raw]
            if 'rain' in p.telemetri:
                del p.telemetri['rain']
            p.vendor = r.vendor if r else None
            p.manual = manual
            
    return jsonify({
        'meta': {
            'description': 'Tinggi Muka Air semua Pos Duga Air', 
            'sampling': s.strftime('%Y-%m-%d')}, 
        'items': [{'pos': {
            'nama': p.nama, 
            'latlon': p.ll, 
            'id': p.id, 
            'sungai': p.sungai, 
            'elevasi': p.elevasi,
            'sh': p.sh,
            'sk': p.sk,
            'sm': p.sm,
            'kabupaten': p.kabupaten,
            'kecamatan': p.kecamatan,
            'desa': p.desa,
            },
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
        row = {'pos': {'nama': r.pos and r.pos.nama or r.nama,
                       'id': r.pos and r.pos.id or None,
                       'latlon': r.pos and r.pos.ll or None,
                       'elevasi': r.pos and r.pos.elevasi or None,
                       'kabupaten': r.pos and r.pos.kabupaten or None,
                       'kecamatan': r.pos and r.pos.kecamatan or None,
                       'desa': r.pos and r.pos.desa or None},
               'vendor': VENDORS[r.source],
               'telemetri':  {
                'count24': r._rain()['count24'], 
                'rain24': r._rain()['rain24'], 
                'rain': r._rain()['hourly'], 
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
    rd = pos.rdaily_set.limit(1).first()
    max = ManualDaily.select().where(ManualDaily.pos==pos).order_by(ManualDaily.ch.desc()).first()
    min = ManualDaily.select().where(ManualDaily.pos==pos).order_by(ManualDaily.sampling).first()
    count = ManualDaily.select(fn.Count(ManualDaily.id)).scalar()
    yearly = ManualDaily.select(ManualDaily.sampling.year.alias('tahun'), fn.Sum(ManualDaily.ch).alias('ch')).where(ManualDaily.pos==pos).group_by(ManualDaily.sampling.year)
    pos.max = max
    pos.min = min
    pos.count = count
    vendor = VENDORS[rd.source]['nama'] if VENDORS[rd.source] else '-'
    dict_pos = model_to_dict(pos)
    dict_pos.update({
        'vendor': vendor,
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