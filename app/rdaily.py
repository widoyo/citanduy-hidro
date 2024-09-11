from flask import Blueprint, render_template, request
import datetime
from peewee import DoesNotExist
from app.models import RDaily, OPos, Pos, VENDORS
from app import get_sampling
from app.config import SDATELEMETRY_POS_EXCLUDES

bp = Blueprint('rdaily', __name__, url_prefix='/rdaily')

@bp.route('/<pos_name>/')
def show(pos_name):
    (_s, s, s_) = get_sampling(request.args.get('s', None))
    print('pos_name: ', pos_name)
    try:
        pos = OPos.get(OPos.nama==pos_name)
    except DoesNotExist:
        pos = None
    try:
        this_day = RDaily.select().where(RDaily.nama==pos_name, 
                                     RDaily.sampling==s.strftime('%Y-%m-%d')).first()
    except DoesNotExist:
        this_day = None
    ctx = {
        '_sampling': _s,
        'sampling': s,
        'sampling_': s_,
        'opos': pos,
        'this_day': this_day
    }
    return render_template('rdaily/show.html', ctx=ctx)

@bp.route('/')
def index():
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    
    our_poses = Pos.select().where(Pos.tipe.in_(('1','2','3'))).order_by(Pos.nama)
    rdaily = RDaily.select().where(RDaily.sampling == sampling.strftime('%Y-%m-%d'))
    rd_un_mapped = [r for r in rdaily if r.pos_id == None]
    for p in our_poses:
        p.rdailies = [r for r in rdaily if r.pos_id==p.id]
    
    pos_excludes = SDATELEMETRY_POS_EXCLUDES.split(';')
    rdaily = [r for r in rdaily if r.nama not in pos_excludes]
    f_50 = [r for r in rdaily if r.kinerja < 20]
    f_70 = [r for r in rdaily if r.kinerja < 70]
    vendors = set([r.source for r in rdaily])
    vendors = [(v, len([r for r in rdaily if r.source == v]), sum(r.kinerja for r in rdaily if r.source==v)) for v in vendors]
    vendors = sorted(vendors, key=lambda x:x[0])
    
    ctx = {
        'rdaily': rdaily,
        'ki_50': f_50,
        'ki_70': f_70,
        'VENDORS': VENDORS,
        'vendors': vendors,
        'all_pos': our_poses,
        'unused': rd_un_mapped,
        's': sampling,
        '_s': _sampling,
        's_': sampling_
    }
    return render_template('rdaily/index.html', ctx=ctx)