from flask import abort, jsonify, request
from flask_login import login_required, current_user
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from app.api import bp
from app.models import Notes

'''
class Notes(BaseModel):
    #Komentar/Catatan terhadap
    username = pw.CharField(max_length=20)
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    msg = pw.TextField()
    obj_name = pw.CharField() # pos, petugas, manualdaily, rdaily
    obj_id = pw.IntegerField()
    parent_id = pw.IntegerField(null=True)
'''
OBJ_LIST = 'Pos_Petugas_ManualDaily_RDaily'.split('_')

@bp.route('/note/<int:id>', methods=['GET'])
def get_note():
    note = Notes.get(id)
    return jsonify(note.to_dict())

@bp.route('/note', methods=['GET'])
def get_notes():
    pass

@bp.route('/note', methods=['POST'])
@login_required
def create_note():
    ret = {'ok': False}
    data = request.get_json()
    username = current_user.username
    obj_name = data.get('obj_name')
    obj_id = data.get('obj_id')
    msg = data.get('msg')
    
    new_note = Notes.create()
