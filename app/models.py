import datetime
import json
import peewee as pw

sqlite_db = pw.SqliteDatabase('hidro_citanduy.db', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 64})


class BaseModel(pw.Model):
    class Meta:
        database = sqlite_db


class FetchLog(BaseModel):
    url = pw.CharField(max_length=250)
    response = pw.TextField(null=True)
    body = pw.TextField(null=True)
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    

class Pos(BaseModel):
    nama = pw.CharField(max_length=100)
    ll = pw.CharField(max_length=50, null=True)
    raw = pw.TextField(null=True)
    latest_sampling = pw.DateTimeField(null=True)
    cdate = pw.DateTimeField(default=datetime.datetime.now)




