import datetime
from flask import Blueprint, render_template, request, abort, jsonify
from flask_login import current_user
from peewee import DoesNotExist

from app import get_sampling
from app.models import Pos, Publikasi
bp = Blueprint('publikasi', __name__, url_prefix='/pub')

@bp.route('/')
def index():
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
    pos_pub = Pos.select().where(Pos.tipe=='5').order_by(Pos.sungai)
    if sampling.month < 7:
        sampling = sampling.replace(month=1)
        _sampling = _sampling.replace(month=7, year=sampling.year - 1)
        if sampling_:
            sampling_ = sampling_.replace(month=7)
    else:
        sampling = sampling.replace(month=7)
        _sampling = _sampling.replace(month=1)
        if sampling_:
            sampling_ = sampling_.replace(month=1, year=sampling.year + 1)
    sungai = set([p.sungai for p in pos_pub])
    months = [sampling.month + m for m in range(6)]
    publikasi = (Publikasi.select()
                 .where(Publikasi.sampling.year==sampling.year,
                        Publikasi.sampling.month.in_(months))
                 .order_by(Publikasi.sampling))
    hasil_publikasi = {}
    for pub in publikasi:
        hasil_publikasi.update({'{}_{}'.format(pub.pos_id, pub.sampling.month): pub})
    
    out = {}
    for s in sungai:
        out.update({s: [p for p in pos_pub if p.sungai==s]})
    
    ctx = {
        '_sampling': _sampling,
        'sampling': sampling,
        'sampling_': sampling_,
        'poses': pos_pub,
        'sungai': out,
        'hasil_publikasi': hasil_publikasi
    }
    return render_template('publikasi/index.html', ctx=ctx)


@bp.route('/adm', methods=['GET'])
def get_all_pub():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)
    pubs = Publikasi.select().order_by(Publikasi.sampling.desc(), Publikasi.cdate.desc())
    return render_template('publikasi/adm/index.html', ctx={'pubs': pubs})

@bp.route('/adm/<int:pub_id>', methods=['GET'])
def get_one_pub(pub_id):
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)
    try:
        pub = Publikasi.get(Publikasi.id==pub_id)
    except DoesNotExist:
        abort(404)
    return render_template('publikasi/adm_one.html', ctx={'pub': pub})

@bp.route('/adm', methods=['POST'])
def create_pub():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)
    title = request.form.get('title', None)
    filename = request.form.get('filename', None)
    body = request.form.get('body', None)
    tags = request.form.get('tags', None)
    sampling_str = request.form.get('sampling', None)
    thumbnail_base64 = request.form.get('thumbnail_base64', None)
    if not (title and filename and body and sampling_str):
        abort(400, 'title, filename, body, sampling are required')
    try:
        filename = int(filename)
    except ValueError:
        abort(400, 'pos_id must be integer')
    try:
        sampling = datetime.datetime.strptime(sampling_str, '%Y-%m-%d').date()
    except ValueError:
        abort(400, 'sampling must be in YYYY-MM-DD format')
    try:
        new_pub = Publikasi.create(
            title=title,
            pos=pos,
            body=body,
            tags=tags,
            sampling=sampling,
            thumbnail_base64=thumbnail_base64
        )
    except Exception as e:
        abort(500, 'Failed to create publikasi: {}'.format(str(e)))
    return render_template('publikasi/adm_one.html', ctx={'pub': new_pub})