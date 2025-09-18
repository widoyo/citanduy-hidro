from flask_wtf import FlaskForm

from wtforms import StringField, SelectField, HiddenField, FloatField, DateField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed, FileRequired



class UserForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])
    pos = SelectField('pos', choices=[])
    
class PasswordForm(FlaskForm):
    username = HiddenField('username')
    password = StringField('password', validators=[DataRequired()])
    
class CurahHujanForm(FlaskForm):
    pos = HiddenField('pos_id')
    sampling = HiddenField('sampling')
    ch = FloatField('curahhujan')
    fetch = HiddenField('fetch')
    
class TmaForm(FlaskForm):
    pos = HiddenField('pos_id')
    sampling = HiddenField('sampling')
    jam = SelectField('jam', choices=['07', '12', '17'])
    tma = FloatField('tma')
    fetch = HiddenField('fetch')

class NoteForm(FlaskForm):
    obj_name = HiddenField('obj_name')
    obj_id = HiddenField('obj_id')
    msg = StringField('msg')
    
class KlimatForm(FlaskForm):
    pos = HiddenField('pos_id')
    sampling = HiddenField('sampling')
    jam = SelectField('jam', choices=['07', '12', '17'])
    thermometer_max = FloatField('tmax')
    thermometer_min = FloatField('tmin')
    bola_basah = FloatField('bb')
    bola_kering = FloatField('bk')
    thermometer_apung_max = FloatField('tamax')
    thermometer_apung_min = FloatField('tamin')
    penguapan = FloatField('p')
    anemometer = FloatField('a') # km/jam
    rh = FloatField('rh') # Relatif Humidity dalam %
    
class HasilUjiKAForm(FlaskForm):
    pos = HiddenField('pos_id')
    sampling = HiddenField('sampling')
    ll = StringField('ll')
    fname = StringField('fname')
    lembaga = StringField('lembaga')
    

class PublikasiForm(FlaskForm):
    title = StringField('title', validators=[DataRequired()])
    sampling = DateField('sampling', validators=[DataRequired()])
    content = StringField('content', validators=[DataRequired()])
    tags = StringField('tags', validators=[DataRequired()])
    filename = FileField('filename', validators=[FileRequired(), FileAllowed(['pdf'], 'PDF only!')])