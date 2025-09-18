import datetime
from flask import Blueprint, render_template, request, abort, url_for, redirect
from flask_login import current_user
from peewee import DoesNotExist
from werkzeug.utils import secure_filename

import fitz
from PIL import Image
from io import BytesIO
import base64

from app import get_sampling
from app.models import Pos, Publikasi
from app.forms import PublikasiForm
bp = Blueprint('publikasi', __name__, url_prefix='/pub')


def create_thumbnail_base64(pdf_file_object):
    """
    Creates a PNG thumbnail from the first page of a PDF file object
    and returns it as a Base64-encoded string.
    """
    try:
        # Open the PDF directly from the file object
        doc = fitz.open(stream=pdf_file_object.read(), filetype="pdf")
        page = doc[0]
        
        width = page.rect.width
        height = page.rect.height
        
        is_landscape = width > height
        
        if is_landscape:
            crop_rect = fitz.Rect(0, 0, height, height)  # Square crop
        else:
            crop_rect = fitz.Rect(0, 0, width, width)  # Square crop
        
        # Render the page to a pixmap
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=crop_rect)
        
        # Create a Pillow Image object from the pixmap
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Resize the image to a thumbnail size
        thumbnail_size = (128, 128)
        img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
        
        # Save the image to a BytesIO object in memory
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        
        # Get the bytes from the BytesIO object
        img_bytes = img_byte_arr.getvalue()
        
        # Encode the bytes to Base64
        base64_string = 'data:image/png;base64,' + base64.b64encode(img_bytes).decode('utf-8')
        
        doc.close()
        return base64_string
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@bp.route('/')
def index():
    (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
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
    months = [sampling.month + m for m in range(6)]
    publikasi = (Publikasi.select()
                 .where(Publikasi.sampling.year==sampling.year,
                        Publikasi.sampling.month.in_(months))
                 .order_by(Publikasi.sampling))
    
    ctx = {
        '_sampling': _sampling,
        'sampling': sampling,
        'sampling_': sampling_,
        'publikasi': publikasi
    }
    return render_template('publikasi/index.html', ctx=ctx)


@bp.route('/adm', methods=['GET'])
def get_all_pub():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)
    pubs = Publikasi.select().order_by(Publikasi.sampling.desc(), Publikasi.cdate.desc())
    return render_template('publikasi/adm/index.html', ctx={'pubs': pubs})


@bp.route('/adm/<int:pub_id>', methods=['PATCH'])
def update_pub(pub_id):
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)
    try:
        pub = Publikasi.get(Publikasi.id==pub_id)
    except DoesNotExist:
        abort(404)
    title = request.form.get('title', None)
    filename = request.form.get('filename', None)
    body = request.form.get('body', None)
    tags = request.form.get('tags', None)
    sampling_str = request.form.get('sampling', None)
    thumbnail_base64 = request.form.get('thumbnail_base64', None)
    if title:
        pub.title = title
    if filename:
        try:
            filename = int(filename)
            pos = Pos.get(Pos.id==filename, Pos.tipe=='5')
            pub.pos = pos
        except ValueError:
            abort(400, 'pos_id must be integer')
        except DoesNotExist:
            abort(400, 'pos_id not found or not tipe 5')
    if body:
        pub.body = body
    if tags is not None:
        pub.tags = tags
    if sampling_str:
        try:
            sampling = datetime.datetime.strptime(sampling_str, '%Y-%m-%d').date()
            pub.sampling = sampling
        except ValueError:
            abort(400, 'sampling must be in YYYY-MM-DD format')
    if thumbnail_base64 is not None:
        pub.thumbnail_base64 = thumbnail_base64
    try:
        pub.save()
    except Exception as e:
        abort(500, 'Failed to update publikasi: {}'.format(str(e)))
    return render_template('publikasi/adm_one.html', ctx={'pub': pub})


@bp.route('/adm/<int:pub_id>', methods=['GET', 'POST'])
def delete_pub(pub_id):
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)
    try:
        pub = Publikasi.get(Publikasi.id==pub_id)
    except DoesNotExist:
        abort(404)
    if request.method == 'POST':
        try:
            pub.delete_instance()
        except Exception as e:
            abort(500, 'Failed to delete publikasi: {}'.format(str(e)))
        return redirect(url_for('publikasi.get_all_pub'))
    return render_template('publikasi/adm/confirm_del.html', ctx={'pub': pub})


@bp.route('/adm/add', methods=['GET', 'POST'])
def add_pub():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)
    form = PublikasiForm()
    if form.validate_on_submit():
        f = form.filename.data
        thumbnail_base64 = create_thumbnail_base64(f)
        if thumbnail_base64 is None:
            abort(500, 'Failed to create thumbnail from PDF')
        filename = secure_filename(f.filename)
        new_pub = Publikasi.create(
            title=form.title.data,
            content=form.content.data,
            tags=form.tags.data,
            sampling=form.sampling.data,
            thumbnail_base64=thumbnail_base64,
            filename=filename
        )
        f.save(f'./app/static/pub/{filename}')
        return redirect(url_for('publikasi.get_all_pub'))
    else:
        return render_template('publikasi/adm/add.html', ctx={'form': form, 'errors': form.errors})
