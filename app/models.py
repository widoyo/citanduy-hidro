import datetime
from flask_login import UserMixin
from bcrypt import checkpw, hashpw, gensalt
import peewee as pw

import json

from app.html_table_parser import HTMLTableParser
from app import db_wrapper


SUNGAI_LIST = 'Citanduy_Ciseel_Cibeureum_Cijolang_Cileueur'.split('_')
PCH_MAP = dict([(44, 'PCH Ciamis'), (45, 'PCH Cibariwal')])

class BaseModel(db_wrapper.Model):
    pass

class Das(BaseModel):
    nama = pw.CharField(max_length=50)
    
class FetchLog(BaseModel):
    url = pw.CharField(max_length=250, index=True)
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
    
    def sc_to_daily(self):
        if self.source != 'SC':
            return
        data = json.loads(self.body)
        '''
        {"imei":"869467048458989",
        "level_sensor":0,"name":"PCH CIMANGGU",
        "power_current":95,"power_voltage":4.17,
        "rain_rate":0,"raindrop":0.029,
        "rec":106317428,
        "submitted_at":"2024-04-29T21:21:00Z"}
        '''
        sb = datetime.datetime.fromisoformat(data.get('submitted_at').replace('Z', '+00:00'))
        this_sampling = sb.astimezone(datetime.timezone(datetime.timedelta(hours=7))).replace(tzinfo=None)
        new_raw = {'sampling': this_sampling.isoformat()}
        if 'PCH' in data['name']:
            tipe = '1'
            new_raw.update({'rain': data.get('raindrop')})
        else:
            tipe = '2'
            new_raw.update({'wlevel': data.get('level_sensor')})
        
        pos, pos_created = OPos.get_or_create(
            nama=data['name'], source='SC', 
            defaults={'latest_sampling': this_sampling, 'tipe':tipe})
        
        rd, rdaily_created = RDaily.get_or_create(
            source='SC', nama=data.get('name'),
            sampling=this_sampling.date(), 
            defaults={'raw': json.dumps([new_raw])})

        if not pos_created:
            if pos.latest_sampling < this_sampling:
                pos.latest_sampling = this_sampling
                pos.save()
                
        if not rdaily_created:
            raw = json.loads(rd.raw)
            raw.append(new_raw)
            rd.raw = json.dumps(raw)
            rd.save()

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
                try:
                    rain = float(r['Rain'])
                except:
                    rain = 0.0
                new_raw = [{
                    "sampling": this_sampling.isoformat(),
                    "rain": rain,
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
    nama = pw.CharField(max_length=35, index=True)
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
    nama = pw.CharField(max_length=50, unique=True, index=True)
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
            sampling = datetime.datetime.fromisoformat(d['sampling'])
            jam = sampling.hour
            out[jam]['num'] += 1
            if d.get('rain'):
                try:
                    if self.source != 'SC':
                        out[jam]['rain'] += float(d['rain'])
                    else:
                        raise KeyError
                except KeyError:
                    out[jam]['rain'] = float(d['rain'])
            if d.get('wlevel'):
                out[jam]['wlevel'] = d['wlevel']
        return out
    
    def _rain(self):
        if not 'rain' in self.raw:
            return None
        rain24 = dict([(i, {'count': 0, 'rain': 0.0}) for i in range(7,24)] + [(i, {'count': 0, 'rain': 0.0}) for i in range(7)])
        data = json.loads(self.raw)
        data = [d for d in data if datetime.datetime.fromisoformat(d.get('sampling')).hour > 6]
        next_day = self.sampling + datetime.timedelta(days=1)
        next = RDaily.select().where(RDaily.nama==self.nama, 
                                   RDaily.sampling.year==next_day.year,
                                   RDaily.sampling.month == next_day.month,
                                   RDaily.sampling.day == next_day.day).first()
        data2 = []
        if next:
            data2 = json.loads(next.raw)
            data2 = [d for d in data2 if datetime.datetime.fromisoformat(d.get('sampling')).hour < 7]
        data += data2
        j, c, r = '', 0, 0.0
        for d in data:
            jam = d.get('sampling')[11:13]
            if j != jam:
                if j != '':
                    rain24[int(j)] = {'count': c, 'rain': r}
                j = jam
                c = 1
                r = 0.0
            else:
                c += 1
                r += float(d.get('rain'))
        
        return rain24
        
    class Meta:
        indexes = (
            ('nama'),
            (('nama', 'sampling'), True),
        )
    
class User(BaseModel, UserMixin):
    username = pw.CharField(max_length=20, unique=True, index=True)
    password = pw.CharField(max_length=100)
    pos = pw.ForeignKeyField(Pos, null=True)
    last_login = pw.DateTimeField(null=True)
    active = pw.BooleanField(default=True)
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    
    @property
    def is_admin(self):
        if self.pos:
            return False
        else:
            return True
    
    def check_password(self, password):
        return checkpw(password.encode(), self.password.encode())
    
    def set_password(self, password):
        self.password = hashpw(password.encode('utf-8'), gensalt())
        

class Petugas(BaseModel):
    nama = pw.CharField(max_length=50, index=True)
    nik = pw.CharField(max_length=20, null=True)
    hp = pw.CharField(max_length=20, null=True)
    dusun = pw.CharField(max_length=50, null=True)
    rt = pw.IntegerField(null=True)
    rw = pw.IntegerField(null=True)
    desa = pw.CharField(max_length=20, null=True)
    kecamatan = pw.CharField(max_length=20, null=True)
    kabupaten = pw.CharField(max_length=20, null=True)
    pendidikan = pw.CharField(max_length=5, null=True)
    pos = pw.ForeignKeyField(Pos, null=True)
    tipe = pw.CharField(max_length=2, null=True) # 1: PCH, 2: PDA, 3: Klimat
    username = pw.CharField(max_length=20, null=True)


class PosMap(BaseModel):
    pos = pw.ForeignKeyField(Pos, unique=True)
    source = pw.CharField(max_length=30)
    
    
class LuwesPos(BaseModel):
    nama = pw.CharField(max_length=35, unique=True)
    imei = pw.CharField(max_length=30, unique=True)
    pos = pw.ForeignKeyField(Pos, null=True)
    tipe = pw.CharField(max_length=2, default='1') # 1 PCH, 2 PDA, 3 Klimat
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    mdate = pw.DateTimeField(null=True)

class ManualDaily(BaseModel):
    '''Data Harian TMA & CH dari Petugas'''
    pos = pw.ForeignKeyField(Pos)
    username = pw.CharField(max_length=20)
    sampling = pw.DateField()
    ch = pw.FloatField(null=True)
    tma = pw.TextField(null=True) # JSON {'7': ?, '12': ? '17': ?}
    cdate = pw.DateTimeField(default=datetime.datetime.now)

    @property
    def _tma(self):
        if not self.tma:
            return None
        return json.loads(self.tma)
    
    class Meta:
        indexes = (
            (('pos', 'sampling'), True),
        )