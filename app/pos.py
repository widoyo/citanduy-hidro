from flask import Blueprint, render_template, jsonify, request, abort, redirect
from flask_login import current_user, login_required
import json
import datetime
from peewee import DoesNotExist, fn

from app.models import Pos, ManualDaily, PosMap, OPos, LengkungDebit
from app import get_sampling
from app.forms import CurahHujanForm, TmaForm
bp = Blueprint('pos', __name__, url_prefix='/pos')


@bp.route('/manual/kinerja')
def kinerja_manual():
    sampling = request.args.get('s', None) == None and \
        datetime.datetime.now() or \
            datetime.datetime.strptime(request.args.get('s'), '%Y-%m-%d')
    
    (_s, s, s_) = get_sampling(sampling.strftime('%Y-%m-1'))
    _s = s - datetime.timedelta(days=2)
    if s.strftime('%Y%m') >= datetime.date.today().strftime('%Y%m'):
        s_ = None
    else:
        s_ = (s + datetime.timedelta(days=32)).replace(day=1)
        
    num_hari = (s_ and (s_ - s) or (datetime.datetime.now() - s)).days
    all_pos = (Pos.select().where(Pos.tipe.in_(('1','2','3')))
               .order_by(Pos.tipe, Pos.nama))
    mdaily = (ManualDaily.select()
              .where(ManualDaily.sampling.year==s.year, 
                     ManualDaily.sampling.month==s.month)
              .order_by(ManualDaily.pos, ManualDaily.sampling))
    pchs = []
    pdas = []
    for p in all_pos:
        if p.tipe == '1':
            pchs.append(p)
            num_data = len([m for m in mdaily if m.pos_id==p.id])
            banyak_data = num_hari
        elif p.tipe == '2':
            pdas.append(p)
            num_data = sum([len(json.loads(m.tma)) / 2 for m in mdaily if m.pos_id==p.id])
            banyak_data = num_hari * 3
        delta_entry = sum([(m.cdate - (datetime.datetime.combine(m.sampling, datetime.time(7, 0)) + datetime.timedelta(days=1)).replace(hour=7, minute=0, second=0)).total_seconds() for m in mdaily if m.pos_id==p.id])
        p.delta_entry = datetime.timedelta(seconds=delta_entry)
        p.diterima = num_data
        p.seharusnya = banyak_data
        p.persen = ((num_data / banyak_data) * 100) if banyak_data else 0
    
    pch_diterima = sum([p.diterima for p in pchs])
    pch_seharusnya = sum([p.seharusnya for p in pchs])
    pda_diterima = sum([p.diterima for p in pdas])
    pda_seharusnya = sum([p.seharusnya for p in pdas])
        
    ctx = {
        's': s,
        '_s': _s,
        's_': s_,
        'all_pos': all_pos,
        'pchs': {'diterima': pch_diterima, 'seharusnya': pch_seharusnya, 'banyak_pos': len(pchs)},
        'pdas': {'diterima': pda_diterima, 'seharusnya': pda_seharusnya, 'banyak_pos': len(pdas)},
        'num_hari': num_hari
    }
    return render_template('pos/manual/kinerja.html', ctx=ctx)


@bp.route('/manual')
def manual():
    formhujan = CurahHujanForm()
    if current_user.is_anonymous:
        abort(404)
    if not current_user.is_admin:
        abort(404)
    (_s, s, s_) = get_sampling(request.args.get('s', None))
    data_pch = ManualDaily.select().where(ManualDaily.sampling==_s.strftime('%Y-%m-%d'))
    data_other = ManualDaily.select().where(ManualDaily.sampling==s.strftime('%Y-%m-%d'))

    data_manual_pch = dict([(p.pos.id, p.ch) for p in data_pch if p.pos.tipe in ('1', '3')])
    data_manual_pda = dict([(p.pos.id, p._tma) for p in data_other if p.pos.tipe=='2'])

    data = Pos.select().order_by(Pos.tipe, Pos.nama)
    pch = [p for p in data if p.tipe in ('1', '3')]

    for p in pch:
        if p.petugas_set:
            p.petugas = p.petugas_set[0].nama
        else:
            p.petugas = None
        if p.id in data_manual_pch:
            p.ch = data_manual_pch[p.id]
        else:
            p.ch = ''
    pda = [p for p in data if p.tipe=='2']
    for p in pda:
        if p.petugas_set:
            p.petugas = p.petugas_set[0].nama
        else:
            p.petugas = None
        if p.id in data_manual_pda:
            p.tma = data_manual_pda[p.id]
        else:
            p.tma = None
    ctx = {
        '_sampling': _s,
        'sampling': s,
        'sampling_': s_,
        'pch': pch,
        'pda': pda,
        'formhujan': formhujan
    }
    return render_template('pos/manual/index.html', ctx=ctx)


@bp.route('/<int:pos_id>/manual/<int:tahun>/<int:bulan>')
@login_required
def show_manual(pos_id, tahun=datetime.date.today().year, bulan=datetime.date.today().month):
    try:
        pos = Pos.get(pos_id)
    except DoesNotExist:
        return abort(404)
    samp = "{}-{}-1".format(tahun, bulan)
    (_s, s, s_) = get_sampling(samp)
    _s = s - datetime.timedelta(days=2)
    if s.strftime('%Y%m') >= datetime.date.today().strftime('%Y%m'):
        s_ = None
    else:
        s_ = (s + datetime.timedelta(days=32)).replace(day=1)
    mdaily = ManualDaily.select().where(ManualDaily.pos_id==pos_id, 
                                        ManualDaily.sampling.year==s.year,
                                        ManualDaily.sampling.month==s.month).order_by(ManualDaily.sampling)
    delta_time = datetime.timedelta()
    for m in mdaily:
        m.delta_entry = m.cdate - (datetime.datetime.combine(m.sampling, datetime.time(7, 0)) + datetime.timedelta(days=1)).replace(hour=7, minute=0, second=0)
        delta_time += m.delta_entry
    
    by_petugas = [i for i in mdaily if i.is_by_petugas]
    by_other = [i for i in mdaily if not i.is_by_petugas]

    entry_count = (ManualDaily
                   .select(ManualDaily.cdate.year, 
                           ManualDaily.cdate.month, 
                           ManualDaily.cdate.day, fn.Count(ManualDaily.cdate))
                   .where(ManualDaily.pos_id==pos.id, 
                          ManualDaily.sampling.year==s.year,
                          ManualDaily.sampling.month==s.month)
                   .group_by(ManualDaily.cdate.year,
                             ManualDaily.cdate.month,
                             ManualDaily.cdate.day)
                   .order_by(ManualDaily.cdate.day).tuples())
    ec = [(datetime.date(int(a), int(b), int(c)), int(d)) for a, b, c, d in entry_count]
        
    ctx = {
        'pos': pos,
        'mdaily': mdaily,
        'num_hari': (s_ and (s_ - s) or (datetime.datetime.now() - s)).days,
        'entry_count': ec,
        'delta_time': delta_time,
        'by_petugas': len(mdaily) != 0 and (len(by_petugas) / len(mdaily) * 100, datetime.timedelta(seconds=sum([i.delta_entry.total_seconds() for i in mdaily if i.is_by_petugas]))) or 0,
        'by_other': len(mdaily) != 0 and (len(by_other) / len(mdaily) * 100,  datetime.timedelta(seconds=sum([i.delta_entry.total_seconds() for i in mdaily if not i.is_by_petugas]))) or 0,
        '_s': _s,
        's': s,
        's_': s_
    }
    return render_template('pos/manual/show.html', ctx=ctx)

@bp.route('/<int:id>/manual', methods=['POST'])
def upsert_manual(id):
    pos = Pos.get(id)
    if pos.tipe in ('1', '3'):
        form = CurahHujanForm()
        if form.validate_on_submit():
            ret = {'ok': True, 'ch': form.ch.data, 
                'sampling': form.sampling.data, 
                'pos': pos.id,
                'username': current_user.username}
            md = ManualDaily.select().where(
                ManualDaily.pos==pos, 
                ManualDaily.sampling==form.sampling.data).first()
            if md:
                md.ch = form.ch.data
                md.save()
            else:
                md = ManualDaily.create(**ret)
        else:
            print(form.errors)
            ret = {'ok': False, 'error': form.errors}
    elif pos.tipe == '2':
        form = TmaForm()
        if form.validate_on_submit():
            md = ManualDaily.select().where(
                ManualDaily.pos==pos, 
                ManualDaily.sampling==form.sampling.data).first()
            if md:
                tma = json.loads(md.tma)
                if 'cdate_'+str(form.jam.data) in tma:
                    tma.update({str(form.jam.data): form.tma.data})
                else:
                    tma.update({str(form.jam.data): form.tma.data, 
                                'cdate_'+str(form.jam.data): datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
                md.tma = json.dumps(tma)
                md.save()
                ret = {'ok': True, 'tma': tma,
                    'sampling': form.sampling.data,
                    'pos': pos.id,
                    'username': current_user.username}
            else:
                tma = json.dumps({str(form.jam.data): form.tma.data, 
                                  'cdate_'+str(form.jam.data): datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
                ret = {'ok': True, 'tma': tma,
                    'sampling': form.sampling.data,
                    'pos': pos.id,
                    'username': current_user.username}
                md = ManualDaily.create(**ret)
        else:
            print(form.errors)
            ret = {'ok': False, 'error': form.errors}
    if form.fetch.data == True:
        return jsonify(ret)
    else:
        return redirect('/')

@bp.route('/debit')
def lengkung_debit():
    '''Hitung DEBIT
    Q = c (H + a)^b
    Q = Debit
    H = TMA
    '''
    ctx = {
        'poses': LengkungDebit.select()
    }
    return render_template('pos/lengkung_debit.html', ctx=ctx)

@bp.route('/')
@login_required
def index():
    pm = dict([(p.pos.id, p) for p in PosMap.select()])
    op = dict([(p.pos.id, p) for p in OPos.select() if p.pos_id != None])
    poses = Pos.select().order_by(Pos.tipe, Pos.nama, Pos.elevasi.desc())
    for p in poses:
        if p.id in pm:
            p.source = pm[p.id].nama
        if p.id in op:
            p.vendor = op[p.id].source
    return render_template('pos/index.html', poses=poses)