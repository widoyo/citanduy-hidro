import functools
from flask import Flask, render_template, flash, redirect
from flask import jsonify, abort, request, url_for, Response
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from urllib.parse import urlparse, urljoin
from playhouse.flask_utils import FlaskDB
from dotenv import load_dotenv
from peewee import fn
import dateparser
from bs4 import BeautifulSoup
from gtts import gTTS

import requests
import datetime
import json

load_dotenv()

db_wrapper = FlaskDB()
csrf = CSRFProtect()

from app.models import FetchLog, User, RDaily, UserQuery, ManualDaily, Pos, OPos
from app.forms import CurahHujanForm, TmaForm
from app.utils import request_handler


def get_hard_rainfall(now: datetime.datetime = datetime.datetime.now()) -> list:
    rd = RDaily.select().where(RDaily.sampling==now.date())
    rain_list = []
    for r in rd:
        raw = json.loads(r.raw)
        if 'rain' not in raw[0]:
            continue
        pos = r.nama
        pos_id = None
        pos_ll = ''
        pos_source = r.source
        if r.pos != None:
            pos = r.pos.nama
            pos_id = r.pos.id
            pos_ll = r.pos.ll
        if 'PDA' in pos:
            continue
        minute_start = datetime.datetime.fromisoformat(raw[-1]['sampling'])
        durasi = datetime.timedelta()
        hujan = 0
        if r.source in ('SA', 'SB'):
            for ra in reversed(raw):
                sampling = datetime.datetime.fromisoformat(ra['sampling'])
                if sampling < now - datetime.timedelta(minutes=60):
                    continue
                if float(ra['rain']) > 0.0:
                    durasi += minute_start - sampling
                    minute_start = sampling
                hujan += float(ra['rain'])
        else:
            l = raw[-1]['rain']
            for ra in reversed(raw):
                sampling = datetime.datetime.fromisoformat(ra['sampling'])
                if sampling < now - datetime.timedelta(minutes=60):
                    continue
                rain_now = l - ra['rain']
                if rain_now > 0.0:
                    durasi += minute_start - sampling
                    minute_start = sampling
                hujan += rain_now
                l = ra['rain']
                #click.echo('{} {}'.format(sampling.strftime('%H:%M'), ra['rain']))
        if hujan > 10.0:
            rain_list.append(
                {
                    'pos': pos, 
                    'pos_id': pos_id,
                    'pos_ll': pos_ll,
                    'pos_source': pos_source,
                    'start_sampling': minute_start, 
                    'rain': hujan, 
                    'duration': durasi.total_seconds()
                })
    return rain_list

def get_delayed_device() -> list:
    '''Mengambil daftar perangkat yang tidak mengirimkan data dalam 24 jam terakhir'''
    now = datetime.datetime.now()
    device_list = []
    for r in OPos.select().where(OPos.aktif==True, OPos.latest_sampling <= (now - datetime.timedelta(hours=2))):
        device_list.append({
            'id': r.id,
            'logger_id': r.nama,
            'source': r.source,
            'latest_sampling': r.latest_sampling.strftime('%Y-%m-%d %H:%M:%S'),
            'tipe': r.tipe,
            'll': r.pos.ll if r.pos else None,
            'nama': r.pos.nama if r.pos else None,
        })
    
    return device_list

def get_sampling(s: str = None) -> list:
    try:
        sampling = datetime.datetime.strptime(s, '%Y-%m-%d')
        _sampling = sampling - datetime.timedelta(days=1)
        sampling_ = sampling + datetime.timedelta(days=1)
    except:
        sampling = datetime.datetime.now()
        _sampling = sampling - datetime.timedelta(days=1)
        sampling_ = None
    if sampling.date() >= datetime.date.today():
        sampling_ = None
    
    return (_sampling, sampling, sampling_)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login untuk mengakses...'

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc
        
def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target
        
def redirect_back(endpoint, **values):
    target = request.form['next']
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)

def admin_required(func):
    @functools.wraps(func)
    def myinner(*args, **kwargs):
        if current_user.pos:
            abort(404)
        return func(*args, **kwargs)
    return myinner
        
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
    
def create_app():
    app = Flask(__name__)
    #app.config['DATABASE'] = 'postgresql://citauser:thispass@localhost:5432/citadb'
    app.config.from_pyfile('config.py')
    db_wrapper.init_app(app)
    csrf.init_app(app)
    
    from app.cli import register as register_cli
    
    register_cli(app)
        
    register_bluprint(app)
    
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.get(user_id)
        except User.DoesNotExist:
            return None
    
    @app.route('/ews')
    def ews():
        '''Endpoint untuk EWS, hanya untuk testing'''
        if request.args.get('format', 'html') == 'json':
            poses = Pos.select().order_by(Pos.nama)
            data = []
            for p in poses:
                data.append({
                    'id': p.id,
                    'nama': p.nama,
                    'kabupaten': p.kabupaten,
                    'sungai': p.sungai,
                    'elevasi': p.elevasi,
                    'tipe': p.tipe,
                    'll': p.ll
                })
            return jsonify(data)
        if request.args.get('rain'):
            rain_list = get_hard_rainfall()
            return jsonify(rain_list)
        if request.args.get('device'):
            device_list = get_delayed_device()
            return jsonify(device_list)
        return render_template('ews.html')
    
    
    @app.route('/ai', methods=['GET', 'POST'])
    def chat():
        if request.method == 'POST':
            data = request.json
            user_text = data.get('text', '')
            q = request_handler(user_text)
            uq = UserQuery.create(q=user_text, intent=q.get('intent'))
            try:
                soup = BeautifulSoup(q.get('result').get('msg'), 'html.parser')
                to_voice = soup.get_text()
                speech = gTTS(text=to_voice, lang='id', slow=False)
                speech.save('app/static/audio/output.mp3')
            except:
                pass
            return jsonify(q)
        return render_template('ai.html')

    @app.route('/c', methods=['GET', 'POST'])
    def ch():
        if request.method == 'POST':
            data = request.json
            user_text = data.get('text', '')
            response = request_handler(user_text)
            #uq = UserQuery.create(q=user_text, intent=response)
            return jsonify(response)
        return render_template('chat.html')
        
    from flask import send_from_directory
    import os
    @app.route('/google91b0d3511e72c1af.html')
    def google_verify():
        try:
            return send_from_directory(os.path.join(os.getcwd(), 'app/static'), 'google91b0d3511e72c1af.html')
        except:
            abort(404)

    @app.route('/sitemap.xml')
    def sitemap():
        try:
            return send_from_directory(os.path.join(os.getcwd(), 'app/static'), 'sitemap.xml')
        except:
            abort(404)
            
    @app.route('/download', methods=['GET', 'POST'])
    @login_required
    def download():
        if request.method == 'POST':
            if request.form.get('sumber') == 'telemetri':
                # Download data telemetri per tipe pos, untuk Laporan Siaga
                sampling = request.form.get('sampling')
                tipe = request.form.get('tipe')
                if tipe == '1':
                    fname = 'CurahHujan_' + sampling + '.csv'
                    pos_ids = [p.id for p in Pos.select().where(Pos.tipe.in_(['1', '3'])).order_by(Pos.nama)]
                else:
                    fname = 'TinggiMukaAir_' + sampling + '.csv'
                    pos_ids = [p.id for p in Pos.select().where(Pos.tipe==tipe)]
                rd = RDaily.select().where(RDaily.sampling==sampling, RDaily.pos_id.in_(pos_ids))
                csv_data = tipe == '1' and 'Curah Hujan ' or 'Tinggi Muka Air'
                csv_data += ' ' + sampling + '\n'
                csv_data += 'Diunduh: {}\n'.format(datetime.datetime.now().strftime('%d %b %Y jam %H:%M:%S'))
                jam = ','.join([str(i) for i in range(0, 24)]) + '\n'
                if tipe == '1':
                    jam = ','.join([str(d) for d in list(rd[0]._rain().get('hourly').keys())])
                csv_data += 'Pos, Kabupaten,' + jam + '\n'

                for r in rd:
                    if tipe == '1':
                        data = ''
                        if r._rain() != None:
                            data = ['{:.1f}'.format(d.get('rain')) for d in list(r._rain().get('hourly').values())]
                    else:
                        data = [str(d.get('wlevel')) for d in r._24jam().values()]
                    csv_data += r.pos.nama + ',' + (r.pos.kabupaten or '-') + ',' + ','.join(data) + '\n'
                response = Response(csv_data, content_type="text/csv")
                response.headers["Content-Disposition"] = "attachment; filename={}".format(fname)
                return response
            
            try:
                data = request.form
                
                pos = Pos.get(int(data.get('pos_id')))
            except:
                return abort(404)
            csv_data = pos.nama + '\n'
            csv_data += 'Tanggal Download: ' + datetime.date.today().strftime('%d-%m-%Y') + '\n'
            if pos.tipe in ('1', '3'):
                csv_data += 'Tanggal, Curah hujan\n'
                mds = ManualDaily.select(ManualDaily.sampling, 
                                         ManualDaily.ch).where(
                                             ManualDaily.pos_id==pos.id).order_by(
                                                 ManualDaily.sampling)
                for m in mds:
                    csv_data += '{}, {}\n'.format(m.sampling, m.ch)
            elif pos.tipe == '2':
                csv_data += 'Tanggal, TMA7, TMA12, TMA17, TMARata-rata\n'
                mds = ManualDaily.select(ManualDaily.sampling, 
                                         ManualDaily.tma).where(
                                             ManualDaily.pos_id==pos.id).order_by(
                                                 ManualDaily.sampling)
                for m in mds:
                    tmas = json.loads(m.tma)
                    tma = {'07': None, '12': None, '17': None}
                    for j in ('07', '12', '17'):
                        try:
                            tma[j] = tmas[j]
                        except KeyError:
                            pass
                    filled_tma = [t for t in tma.values() if t]
                    tmarerata = sum(filled_tma)/ len(filled_tma)
                    csv_data += '{}, {}, {}, {}, {:.1f}\n'.format(m.sampling, 
                                                              tma['07'], 
                                                              tma['12'],
                                                              tma['17'],
                                                              tmarerata)

            response = Response(csv_data, content_type="text/csv")
            return response
 
        poses = Pos.select().order_by(Pos.nama)
        pdas = [p for p in poses if p.tipe == '2']
        pchs = [p for p in poses if p.tipe in ('1', '3')]
        for p in pchs:
            p.yearly = [(y.year, y.count) for y in p.manualdaily_set.select(ManualDaily.sampling.year.alias('year'), 
                                              fn.Count(ManualDaily.id).alias('count'))
                .group_by(ManualDaily.sampling.year)
                .order_by(ManualDaily.sampling.year)]
            p.count = p.manualdaily_set.count()
        for p in pdas:
            p.count = p.manualdaily_set.count()
        ctx = {
            'pdas': pdas,
            'pchs': pchs,
            'today': datetime.date.today()
        }
        return render_template('download/index.html', ctx=ctx)
    
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('homepage'))
        form = LoginForm()
        next = get_redirect_target()
        if form.validate_on_submit():
            try:
                user = User.get(User.username==form.username.data)
            except User.DoesNotExist:
                flash('username atau password keliru')
                return redirect(url_for('login'))
            if user is None or not user.check_password(form.password.data):
                flash('username atau password keliru')
                return redirect(url_for('login'))
            login_user(user)
            user.last_login = datetime.datetime.now()
            user.save()
            return redirect_back('homepage')
        return render_template('login.html', title='Sign In', form=form, next=next)
    
    @app.route('/logout')
    def logout():
        logout_user()
        return redirect('/')    

    @app.route('/me')
    def profile():
        user = User.get(User.username==current_user.username)
        ctx = {
            'me': user
        }
        return render_template('profile.html', ctx=ctx)
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.route('/')
    def homepage():
        '''background: #2193b0;  /* fallback for old browsers */
        background: -webkit-linear-gradient(to right, #6dd5ed, #2193b0);  /* Chrome 10-25, Safari 5.1-6 */
        background: linear-gradient(to right, #6dd5ed, #2193b0); /* W3C, IE 10+/ Edge, Firefox 16+, Chrome 26+, Opera 12+, Safari 7+ */
        '''
        if current_user.is_authenticated and current_user.pos is not None:
            formhujan = CurahHujanForm()
            formtma = TmaForm()
            pos = current_user.pos
                
            (_sampling, sampling, sampling_) = get_sampling(request.args.get('s', None))
            today = datetime.date.today()
            if current_user.pos.tipe == '1' and sampling.strftime('%Y%m') == today.strftime('%Y%m') and today.day == 1:
                sampling -= datetime.timedelta(days=1)
            sampling = sampling.replace(day=1)
            _sampling = (sampling - datetime.timedelta(days=1)).replace(day=1)
            list_data = {}
            if sampling.strftime('%Y%m') == today.strftime('%Y%m'):
                list_data = dict([(i+1, {'tgl': sampling + datetime.timedelta(days=i+1)}) for i in range(today.day)])
                sampling_ = None
            elif sampling.strftime('%Y%m') < today.strftime('%Y%m'):
                sampling_ = (sampling.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
                list_data = dict([(i+1, {'tgl': sampling + datetime.timedelta(days=i+1)}) for i in range((sampling_ - datetime.timedelta(days=1)).day)])
            if current_user.pos.tipe in ('1', '3'):
                list_data = dict([(k, v) for k, v in list_data.items() if v['tgl'].date() <= today])    
            
            formhujan.sampling.data = sampling
            formtma.sampling.data = sampling
            data_manual = dict([(md.sampling.day, {'ch': md.ch, 'tma': md._tma}) for md in ManualDaily.select().where(ManualDaily.sampling.year==sampling.year,
                                                    ManualDaily.sampling.month==sampling.month,
                                                    ManualDaily.pos==pos)])
            for i, d in list_data.items():
                if i in data_manual:
                    list_data[i].update(data_manual.get(i))
            num_day = (sampling_ and (sampling_ - datetime.timedelta(days=1)).day or today.day)
            ctx = {
                'pos': pos,
                'list_data': list_data,
                'sampling': sampling,
                '_sampling': _sampling,
                'sampling_': sampling_,
                'formhujan': formhujan,
                'formtma': formtma,
                'num_day': num_day,
                'num_ch': len(data_manual),
                'num_tma': sum([len(v['tma']) for v in data_manual.values() if v['tma']])
            }
            template = 'home_petugas.html'
            return render_template(template, ctx=ctx)
        else:
            today = datetime.date.today()
            hujans = [r for r in RDaily.select().where(
                RDaily.sampling==today.strftime('%Y-%m-%d'), RDaily.pos!=None)]
            hujans = [r for r in hujans if r.pos.tipe in ('1', '3')]
            ctx = {
                'hujans': hujans
            }
            return render_template('index.html', ctx=ctx, canonical_url=url_for('homepage', _external=True))
                
    return app


def register_bluprint(app):
    from app.pch import bp as bp_pch
    from app.pda import bp as bp_pda
    from app.pos import bp as bp_pos
    from app.fetchlog import bp as bp_fetchlog
    from app.rdaily import bp as bp_rdaily
    from app.rpos import bp as bp_rpos
    from app.user import bp as bp_user
    from app.map import bp as bp_map
    from app.petugas import bp as bp_petugas
    from app.pklimat import bp as bp_klimat
    from app.pka import bp as bp_ka
    from app.kinerja import bp as bp_kinerja
    from app.api import bp as bp_api
    from app.note import bp as bp_note
    
    app.register_blueprint(bp_pch)
    app.register_blueprint(bp_pda)
    app.register_blueprint(bp_pos)
    app.register_blueprint(bp_fetchlog)
    app.register_blueprint(bp_rdaily)
    app.register_blueprint(bp_rpos)
    app.register_blueprint(bp_user)
    app.register_blueprint(bp_map)
    app.register_blueprint(bp_petugas)
    app.register_blueprint(bp_klimat)
    app.register_blueprint(bp_ka)
    app.register_blueprint(bp_kinerja)
    app.register_blueprint(bp_api)
    app.register_blueprint(bp_note)
