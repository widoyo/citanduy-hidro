from flask_wtf import FlaskForm

from wtforms import StringField, SelectField, HiddenField, FloatField
from wtforms.validators import DataRequired


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
    
class TmaForm(FlaskForm):
    pos = HiddenField('pos_id')
    sampling = HiddenField('sampling')
    jam = SelectField('jam', choices=['07', '12', '17'])
    tma = FloatField('tma')