from flask import Flask, render_template, flash, redirect, request, url_for
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from urllib.parse import urlparse, urljoin

import requests

from app.models import FetchLog, User, Pos

SDATELEMETRY = 'https://sdatelemetry.com/API_ap_telemetry/datatelemetry2.php?idbbws=8'
TELEMET = 'https://elektronikapolban.duckdns.org:8081/telemet/telemet/tabel10?p=0'

SECRET_KEY = '3jkowi920ujwp9803-2yu-2jd'

login_manager = LoginManager()

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

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get(User.username==user_id)
    except User.DoesNotExists:
        return None
    
def create_app():
    app = Flask(__name__)
    
    @app.cli.command('fetch-sda')
    def fetch_sdatelemetry():
        '''Membaca data pada server SDATELEMETRY'''
        x = requests.get(SDATELEMETRY)
        fl = FetchLog.create(url=x.url, response=x.status_code, body=x.text, source='SA')
        fl.sa_to_daily()
            
    @app.cli.command('fetch-telemet')
    def fetch_telemet():
        '''Membaca data pada server Omtronik'''
        x = requests.get(TELEMET)
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

    register_bluprint(app)
    
    login_manager.init_app(app)
    
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
            login_user(user, remember=form.remember_me.data)
            
            return redirect_back('homepage')
        return render_template('login.html', title='Sign In', form=form, next=next)
    
    @app.route('/logout')
    def logout():
        current_user.revoke_token()
        logout_user()
        return redirect('/')    

    
    @app.route('/')
    def homepage():
        '''background: #2193b0;  /* fallback for old browsers */
        background: -webkit-linear-gradient(to right, #6dd5ed, #2193b0);  /* Chrome 10-25, Safari 5.1-6 */
        background: linear-gradient(to right, #6dd5ed, #2193b0); /* W3C, IE 10+/ Edge, Firefox 16+, Chrome 26+, Opera 12+, Safari 7+ */
        '''
        return render_template('index.html')


    return app


def register_bluprint(app):
    from app.pch import bp as bp_pch
    from app.fetchlog import bp as bp_fetchlog
    from app.rdaily import bp as bp_rdaily
    from app.rpos import bp as bp_rpos
    
    app.register_blueprint(bp_pch)
    app.register_blueprint(bp_fetchlog)
    app.register_blueprint(bp_rdaily)
    app.register_blueprint(bp_rpos)
