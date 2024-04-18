import datetime
from flask_login import UserMixin
import peewee as pw
import json

from app.html_table_parser import HTMLTableParser

sqlite_db = pw.SqliteDatabase('hidro_citanduy.db', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 64})

SUNGAI_LIST = 'Citanduy_Ciseel_Cibeureum_Cijolang_Cileueur'.split('_')

class BaseModel(pw.Model):
    class Meta:
        database = sqlite_db

class Das(BaseModel):
    nama = pw.CharField(max_length=50)
    
class FetchLog(BaseModel):
    url = pw.CharField(max_length=250)
    response = pw.TextField(null=True)
    body = pw.TextField(null=True)
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    source = pw.CharField(max_length=3, null=True)

    def __repr__(self):
        return '<FetchLog {}>'.format(self.id)
    
    def to_daily(self):
        if self.source == 'SA':
            self.sa_to_daily()
        else:
            self.sb_to_daily()
    
    def sb_to_daily(self):
        if self.source != 'SB':
            return None
        parser = HTMLTableParser()
        parser.feed(self.body)
        rows = parser.tables[0]
        poses = dict([(p.nama, p.latest_sampling) for p in OPos.select() if p.source == 'SB'])
        for r in rows:
            if r[2] in ('Rain Fall', 'Water Level'):
                this_sampling = datetime.datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S')
                
                sampling = poses.get(r[1], None)
                if not sampling:
                    try:
                        OPos.create(source='SB', 
                                    nama=r[1], 
                                    latest_sampling=this_sampling,
                                    tipe=r[2])
                    except:
                        pass
                    if r[2] == 'Rain Fall':
                        new_raw = [{
                            'sampling': this_sampling.isoformat(),
                            'rain': r[3],
                        }]
                    else:
                        new_raw = [{
                            'sampling': this_sampling.isoformat(),
                            'wlevel': r[3]
                        }]

                    rd, created = RDaily.get_or_create(source='SB', 
                                                    nama=r[1], 
                                                    sampling=this_sampling.date(), 
                                                    defaults={'raw': json.dumps(new_raw)})
                    if not created:
                        raw = json.loads(rd.raw)
                        raw.append(new_raw[0])
                        rd.raw = json.dumps(raw)
                        rd.save()
                else:
                    if sampling < this_sampling:
                        op = OPos.get(OPos.nama==r[1])
                        op.latest_sampling = this_sampling
                        op.save()
                        if r[2] == 'Rain Fall':
                            new_raw = [{
                                "sampling": this_sampling.isoformat(),
                                "rain": r[3],
                                }]
                        else:
                            new_raw = [{
                                "sampling": this_sampling.isoformat(),
                                "wlevel": r[3]
                                }]

                        rd, created = RDaily.get_or_create(source='SB', 
                                                        nama=r[1], 
                                                        sampling=this_sampling.date(), 
                                                        defaults={'raw': json.dumps(new_raw)})
                        if not created:
                            raw = json.loads(rd.raw)
                            raw.append(new_raw[0])
                            rd.raw = json.dumps(raw)
                            rd.save()
                    
    
    def sa_to_daily(self):
        data = json.loads(self.body)
        rows = data['telemetryjakarta']
        poses = dict([(p.nama, p.latest_sampling) for p in OPos.select() if p.source == 'SA'])
        for r in rows:
            try:
                this_sampling = datetime.datetime.strptime(r['ReceivedDate'] + ' ' + r['ReceivedTime'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
            
            sampling = poses.get(r['nama_lokasi'], None)
            if not sampling:
                try:
                    OPos.create(source='SA', 
                                nama=r['nama_lokasi'], 
                                latest_sampling=this_sampling,
                                tipe=r['id_tipe'])
                except:
                    pass
                new_raw = [{
                    "sampling": this_sampling.isoformat(),
                    "rain": r['Rain'],
                    "wlevel": r['WLevel']
                    }]
                rd, created = RDaily.get_or_create(source='SA', 
                                                nama=r['nama_lokasi'], 
                                                sampling=this_sampling.date(), 
                                                defaults={'raw': json.dumps(new_raw)})
                if not created:
                    raw = json.loads(rd.raw)
                    raw.append(new_raw[0])
                    rd.raw = json.dumps(raw)
                    rd.save()
            else:
                if sampling < this_sampling:
                    op = OPos.get(OPos.nama==r['nama_lokasi'])
                    op.latest_sampling = this_sampling
                    op.save()
                    new_raw = [{
                        "sampling": this_sampling.isoformat(),
                        "rain": r['Rain'],
                        "wlevel": r['WLevel']
                        }]
                    rd, created = RDaily.get_or_create(source='SA', 
                                                    nama=r['nama_lokasi'], 
                                                    sampling=this_sampling.date(), 
                                                    defaults={'raw': json.dumps(new_raw)})
                    if not created:
                        raw = json.loads(rd.raw)
                        raw.append(new_raw[0])
                        rd.raw = json.dumps(raw)
                        rd.save()
                

class Pos(BaseModel):
    nama = pw.CharField(max_length=35)
    ll = pw.CharField(max_length=60, null=True)
    tipe = pw.CharField(max_length=3, null=True)
    elevasi = pw.IntegerField(null=True)
    latest_sampling = pw.DateTimeField(null=True)
    latest_up = pw.DateTimeField(null=True)
    das = pw.ForeignKeyField(Das, null=True)
    sungai = pw.CharField(max_length=30, null=True)
    sh = pw.FloatField(null=True) # batas siaga Hijau dalam meter
    sk = pw.FloatField(null=True) # batas siaga Kuning dalam meter
    sm = pw.FloatField(null=True) # batas siaga Merah dalam meter
    desa = pw.CharField(max_length=30, null=True)
    kecamatan = pw.CharField(max_length=30, null=True)
    kabupaten = pw.CharField(max_length=30, null=True)
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    mdate = pw.DateTimeField(null=True)
    

class OPos(BaseModel):
    nama = pw.CharField(max_length=50, unique=True)
    tipe = pw.CharField(max_length=10, null=True)
    latest_sampling = pw.DateTimeField(index=True)
    source = pw.CharField(max_length=3)
    
    
class Daily(BaseModel):
    pos = pw.ForeignKeyField(Pos)
    nama = pw.CharField(max_length=50, default='')
    sampling = pw.DateField()
    raw = pw.TextField(default='') # json string
    data_count = pw.IntegerField(default=0)
    m_rain = pw.FloatField(null=True)
    m_wlevel_7 = pw.FloatField(null=True)
    m_wlevel_12 = pw.FloatField(null=True)
    m_wlevel_17 = pw.FloatField(null=True)
    
    class Meta:
        indexes = (
            (('pos', 'sampling'), True),
        )

    
class RDaily(BaseModel):
    source = pw.CharField(max_length=3) # sumber data
    nama = pw.CharField(max_length=50, index=True)
    sampling = pw.DateField(index=True)
    raw = pw.TextField(default='') # json string
    data_count = pw.IntegerField(default=0)
    m_rain = pw.FloatField(null=True)
    m_wlevel_7 = pw.FloatField(null=True)
    m_wlevel_12 = pw.FloatField(null=True)
    m_wlevel_17 = pw.FloatField(null=True)
    
    def _24jam(self):
        out = dict([(i, {'num': 0, 'rain': 0, 'wlevel': 0}) for i in range(24)])
        for d in json.loads(self.raw):
            jam = int(d['sampling'][12:13])
            out[jam]['num'] += 1
            if d.get('rain'):
                out[jam]['rain'] = d['rain']
            if d.get('wlevel'):
                out[jam]['wlevel'] = d['wlevel']
        return out
    
    class Meta:
        indexes = (
            ('nama'),
            (('nama', 'sampling'), True),
        )
    
class User(BaseModel, UserMixin):
    username = pw.CharField(max_length=20, unique=True)
    password = pw.CharField(max_length=100)
    pos_id = pw.IntegerField(null=True)
    last_login = pw.DateTimeField()
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    
    
class PosMap(BaseModel):
    source = pw.CharField(max_length=3)
    dari = pw.CharField(max_length=50)
    ke = pw.CharField(max_length=50)
    ke_id = pw.IntegerField(null=True)