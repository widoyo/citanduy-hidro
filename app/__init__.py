from flask import Flask, render_template, flash, redirect, request, url_for
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from urllib.parse import urlparse, urljoin

import requests
import datetime
import json

from app.models import FetchLog, User, Pos, LuwesPos
from app.config import SOURCE_A, SOURCE_B, SOURCE_C

login_manager = LoginManager()
login_manager.login_view = 'login'

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

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

    
def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    
    @app.cli.command('fetch-sda')
    def fetch_sdatelemetry():
        '''Membaca data pada server SDATELEMETRY'''
        x = requests.get(SOURCE_A)
        fl = FetchLog.create(url=x.url, response=x.status_code, body=x.text, source='SA')
        fl.sa_to_daily()
            
    @app.cli.command('fetch-telemet')
    def fetch_telemet():
        '''Membaca data pada server Omtronik'''
        x = requests.get(SOURCE_B)
        body = ''
        inside = False
        for l in x.text.split('\n'):
            if l.startswith('<table'):
                inside = True
            if l.startswith('</table'):
                body += l
                inside = False
            if len(l) > 3 and inside:
                if l.startswith('<td>Date') or l.startswith('<td>RTU') or l.startswith('<td>Chann') or l.startswith('<td>Value') or l.startswith('<td>Satuan'):
                    pass
                else:
                    body += l
                    
        fl = FetchLog.create(url=x.url, response=x.status_code, body=body, source='SB')
        fl.sb_to_daily()

    @app.cli.command('fetch-luwes')
    def fetch_luwes():
        '''Membaca data dari luwes'''
        for l in LuwesPos.select():
            data = {'a': 'stat', 'imei': l.imei}
            x = requests.post(SOURCE_C, data=data)
            rst_body = json.loads(x.text)
            pch_fields = 'rec;submitted_at;imei;name;power_current;power_voltage;rain_rate;raindrop'.split(';')
            pda_fields = 'rec;submitted_at;imei;name;power_current;power_voltage;level_sensor'.split(';')
            if l.tipe == '1':
                body = dict([(f, rst_body[f])for f in pch_fields])
            elif l.tipe == '2':
                body = dict([(f, rst_body[f])for f in pda_fields])
            fl = FetchLog.create(url=x.url, response=x.status_code, body=json.dumps(body), source='SC')
            fl.sc_to_daily()
    
    
    register_bluprint(app)
    
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        print('load_user: ', user_id)
        try:
            return User.get(user_id)
        except User.DoesNotExist:
            return None
    
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
                flash('Invalid username or password')
                return redirect(url_for('login'))
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password')
                return redirect(url_for('login'))
            login_user(user, remember=True, force=True)
            user.last_login = datetime.datetime.now()
            user.save()
            return redirect_back('homepage')
        return render_template('login.html', title='Sign In', form=form, next=next)
    
    @app.route('/logout')
    def logout():
        logout_user()
        return redirect('/')    

    
    @app.route('/')
    def homepage():
        '''background: #2193b0;  /* fallback for old browsers */
        background: -webkit-linear-gradient(to right, #6dd5ed, #2193b0);  /* Chrome 10-25, Safari 5.1-6 */
        background: linear-gradient(to right, #6dd5ed, #2193b0); /* W3C, IE 10+/ Edge, Firefox 16+, Chrome 26+, Opera 12+, Safari 7+ */
        '''
        if current_user.is_authenticated:
            try:
                pos = current_user.pos
                s = request.args.get('s', None)
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
                ctx = {
                    'pos': pos,
                    'sampling': sampling,
                    '_sampling': _sampling,
                    'sampling_': sampling_
                }
                return render_template('home_petugas.html', ctx=ctx)
            except Pos.DoesNotExist:
                return render_template('index.html')
        else:
            return render_template('index.html')
                


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
    
    app.register_blueprint(bp_pch)
    app.register_blueprint(bp_pda)
    app.register_blueprint(bp_pos)
    app.register_blueprint(bp_fetchlog)
    app.register_blueprint(bp_rdaily)
    app.register_blueprint(bp_rpos)
    app.register_blueprint(bp_user)
    app.register_blueprint(bp_map)
    app.register_blueprint(bp_petugas)
