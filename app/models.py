import datetime
from flask_login import UserMixin
from flask import url_for
from bcrypt import checkpw, hashpw, gensalt
import peewee as pw
from playhouse.flask_utils import PaginatedQuery

import shortuuid
import json

from app.html_table_parser import HTMLTableParser
from app import db_wrapper

NUM_DAYS = (31,28,31,30,31,30,31,31,30,31,30,31)

SUNGAI_LIST = 'Citanduy_Ciseel_Cibeureum_Cijolang_Cileueur'.split('_')
#PCH_MAP = dict([(44, 'PCH Ciamis'), (45, 'PCH Cibariwal')])
VENDORS = {
    'SA': {
        'nama': 'Arindo'
    },
    'SB': {
        'nama': 'Komtronik'
    },
    'SC': {
        'nama': 'Luwes'
    }
}

class PaginatedApiMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = PaginatedQuery(query, per_page, page)
        
        data = {
            'items': resources,
            '_meta': {
                'page': page,
                'per_page': per_page,
                
            }
        }
        
        return data
    
class BaseModel(db_wrapper.Model):
    pass

class Notes(BaseModel):
    '''Komentar/Catatan terhadap'''
    username = pw.CharField(max_length=20)
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    msg = pw.TextField()
    obj_name = pw.CharField() # pos, petugas, manualdaily, rdaily
    obj_id = pw.IntegerField()
    parent_id = pw.IntegerField(null=True)
    
    def obj_url(self):
        ret = None
        if self.obj_name.lower() == 'pos':
            try:
                pos = Pos.get(self.obj_id)
                if pos.tipe in ('1', '3'):
                    ret = '/pch/{}'.format(pos.id)
                elif pos.tipe == '2':
                    ret = '/pda/{}'.format(pos.id)
            except pw.DoesNotExist:
                pass
        return ret
             
    def __str__(self):
        ret = self.obj_name
        if self.obj_name.lower() == 'pos':
            try:
                pos = Pos.get(self.obj_id)
                ret = pos.nama
            except pw.DoesNotExist:
                pass
        return ret
        
    def to_dict(self):
        data = {
            'id': self.id,
            'username': self.username,
            'msg': self.msg,
            'cdate': self.cdate.isoformat(),
            '_links': {
                'self': url_for('api.get_note', id=self.id)
            }
        }
    
    def from_dict(self, data):
        pass

class Foto(BaseModel):
    '''Foto-foto object'''
    id = pw.CharField(primary_key=True, max_length=22, default=shortuuid.uuid)
    username = pw.CharField(max_length=20)
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    fname = pw.CharField(max_length=25)
    msg = pw.TextField(null=True)
    obj_name = pw.CharField() # pos, petugas, manualdaily, rdaily
    obj_id = pw.IntegerField()


class Das(BaseModel):
    nama = pw.CharField(max_length=50)

class Incoming(BaseModel):
    id = pw.CharField(primary_key=True, max_length=22, default=shortuuid.uuid)
    user_agent = pw.CharField(max_length=35)
    body = pw.TextField()
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    
    def sb_to_daily(self):
        if self.user_agent != 'Komtronik-Gateway 1.0':
            return
        chann_no = {'1': 'rain', '2': 'battery', '3': 'wlevel'}
        chann_name = {'Rain Fall': 'rain', 'Battery': 'battery', 'Water Level': 'wlevel'}

        all_rec = {}
        lines = json.loads(self.body)
        for r in lines:
            try:
                field = chann_name[r['channel']]
            except KeyError:
                field = chann_no[r['channel_no']]
            
            rec_sampling = r['date_time'].replace(' ', 'T')
            this_key = r['name'] + '_' + rec_sampling[0:10]
            new_rec = {rec_sampling: {field: round(float(r['value']), 1)}}
            if this_key in all_rec:
                existing_rec = all_rec[this_key]
                if rec_sampling in existing_rec:
                    existing_rec[rec_sampling].update(new_rec[rec_sampling])
                else:
                    all_rec[this_key].update(new_rec)
            else:
                all_rec[this_key] = new_rec

        # INSERT or UPDATE Database (RDaily)
        posmaps = dict([(p.nama, p.pos_id) for p in PosMap.select()])
        for k, v in all_rec.items():
            (nama, this_sampling) = k.rsplit('_', 1)
            pos_id = posmaps.get(nama, None)
            
            tipe = '1' if 'rain' in str(list(v.items())[0]) else '2'
            opos, created = OPos.get_or_create(nama=nama, source='SB', 
                                               defaults={'tipe':tipe, 
                                                         'latest_sampling': datetime.datetime.now()})
            
            new_raw = []
            for sam, vv in v.items():
                vv.update({'sampling': sam})
                new_raw.append(vv)
            # update 'latest_sampling'
            opos.latest_sampling = new_raw[-1].get('sampling')
            opos.save()
            
            rd, created = RDaily.get_or_create(source='SB',
                                        nama=nama,
                                        sampling=this_sampling,
                                        defaults={'pos_id': pos_id,
                                                  'raw': json.dumps(new_raw)})
            # KHUSUS PDA&PCH Manganti id=
            if not created:
                existing_data = json.loads(rd.raw)
                existing_sampling = [data['sampling'] for data in existing_data]
                for row in new_raw:
                    if row.get('sampling') not in existing_sampling:
                        existing_data.append(row)
                rd.raw = json.dumps(existing_data)
                rd.save()

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
        new_raw = {'sampling': this_sampling.isoformat(), 'battery': data.get('power_voltage')}
        if 'PCH' in data['name']:
            tipe = '1'
            new_raw.update({'rain': data.get('raindrop')})
        else:
            tipe = '2'
            new_raw.update({'wlevel': data.get('level_sensor')})
        
        pos, pos_created = OPos.get_or_create(
            nama=data['name'], source='SC', 
            defaults={'latest_sampling': this_sampling, 'tipe':tipe})
        if this_sampling <= pos.latest_sampling:
            return
        luwespos = LuwesPos.get(LuwesPos.imei==data['imei'])
        mypos = luwespos.pos
        rd, rdaily_created = RDaily.get_or_create(
            source='SC', nama=data.get('name'),
            sampling=this_sampling.date(), 
            defaults={'raw': json.dumps([new_raw]),
                      'pos': mypos})

        if not pos_created:
            if pos.latest_sampling < this_sampling:
                pos.latest_sampling = this_sampling
                pos.save()
                
        if not rdaily_created:
            raw = json.loads(rd.raw)
            raw.append(new_raw)
            rd.raw = json.dumps(raw)
            rd.pos = mypos
            rd.save()

    def sb_to_daily(self):
        # Tidak digunakan sejak Okt 2024, 
        # ganti dengan /api/sensor, model Incoming
        if self.source != 'SB':
            return None
        parser = HTMLTableParser()
        parser.feed(self.body)
        rows = parser.tables[0]
        poses = dict([(p.nama, p.latest_sampling) for p in OPos.select() if p.source == 'SB'])
        for r in rows:
            if r[2] in ('Rain Fall', 'Water Level', 'Battery'):
                this_sampling = datetime.datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S')
                
                sampling = poses.get(r[1], None)
                battery = r[3]
                try:
                    posmap = PosMap.get(PosMap.nama==r[1])
                    pos_id = posmap.pos_id
                except:
                    pos_id = None
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
                                                    defaults={'raw': json.dumps(new_raw),
                                                              'pos_id': pos_id})
                    if not created:
                        raw = json.loads(rd.raw)
                        raw.append(new_raw[0])
                        rd.raw = json.dumps(raw)
                        rd.pos_id = pos_id
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
                                                        defaults={'raw': json.dumps(new_raw),
                                                                  'pos_id': pos_id})
                        if not created:
                            raw = json.loads(rd.raw)
                            raw.append(new_raw[0])
                            rd.raw = json.dumps(raw)
                            rd.pos_id = pos_id
                            rd.save()
                    
    
    def sa_to_daily(self):
        kick_off = 'kaso_sidareja_gunungcupu_pitulasi_kadipaten_subang_surusunda_ciputrahaji_pchpataruman_danasari_bendmanganti_janggala_karangbawang'.split('_')
        data = json.loads(self.body)
        rows = data['telemetryjakarta']
        poses = dict([(p.nama, p.latest_sampling) for p in OPos.select() if p.source == 'SA'])
        for r in rows:
            if r['nama_lokasi'] in kick_off:
                continue
            try:
                this_sampling = datetime.datetime.strptime(r['ReceivedDate'] + ' ' + r['ReceivedTime'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
            
            sampling = poses.get(r['nama_lokasi'], None)
            try:
                posmap = PosMap.get(PosMap.nama == r['nama_lokasi'])
                pos_id = posmap.pos_id
            except:
                pos_id = None
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
                                                defaults={'raw': json.dumps(new_raw),
                                                          'pos_id': pos_id})
                if not created:
                    raw = json.loads(rd.raw)
                    raw.append(new_raw[0])
                    rd.raw = json.dumps(raw)
                    rd.pos_id = pos_id
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
                                                    defaults={'raw': json.dumps(new_raw),
                                                              'pos_id': pos_id})
                    if not created:
                        raw = json.loads(rd.raw)
                        raw.append(new_raw[0])
                        rd.raw = json.dumps(raw)
                        rd.pos_id = pos_id
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
    register = pw.CharField(max_length=20, null=True)
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    mdate = pw.DateTimeField(null=True)
    orde = pw.IntegerField(null=True)
            
    @property
    def url(self):
        if self.tipe in ('1', '3'):
            pos = 'pch'
        elif self.tipe == '2':
            pos = 'pda'
        else:
            return None
        return '/' + pos + '/' + self.id
    
    @property
    def s_nama(self):
        return self.nama
    
    @property
    def dasarian(self, month: str = datetime.date.today().strftime('%Y')) -> dict:
        if self.tipe not in ('1', '3'):
            return {}
        

class OPos(BaseModel):
    pos = pw.ForeignKeyField(Pos, null=True)
    nama = pw.CharField(max_length=50, unique=True, index=True)
    tipe = pw.CharField(max_length=10, null=True)
    latest_sampling = pw.DateTimeField(index=True)
    source = pw.CharField(max_length=3)
    aktif = pw.BooleanField(default=True) # aktif = dioperasikan
    
    
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
    pos = pw.ForeignKeyField(Pos, null=True)
    source = pw.CharField(max_length=3) # sumber data
    nama = pw.CharField(max_length=50, index=True)
    sampling = pw.DateField(index=True)
    raw = pw.TextField(default='') # json string
    data_count = pw.IntegerField(default=0)
    m_rain = pw.FloatField(null=True)
    m_wlevel_7 = pw.FloatField(null=True)
    m_wlevel_12 = pw.FloatField(null=True)
    m_wlevel_17 = pw.FloatField(null=True)
    
    @property
    def vendor(self):
        return VENDORS[self.source]
    
    @property
    def nums(self):
        return len(json.loads(self.raw))
    
    @property
    def kinerja(self):
        ref = self.source == 'SB' and 15 or 5 # periode data (menit)
        if self.sampling == datetime.date.today():
            menits = datetime.datetime.now().hour * 60
            menits += datetime.datetime.now().minute
            target = int(menits / ref)
        else:
            target = (self.source == 'SB') and 96 or 288
        return int((self.nums / target) * 100)
    
    def _24jam(self):
        end_of_hour = 24
        out = dict([(i, {'num': 0, 'rain': 0, 'wlevel': 0}) for i in range(end_of_hour)])
        
        data_raw = json.loads(self.raw)
        for d in data_raw:
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
                out[jam]['wlevel'] = (self.source in ('SC', 'SB')) and d['wlevel'] * 100 or d['wlevel']
        return out
    
    def _tma(self):
        jams = (6, 11, 16)
        data = dict([(k+1, v) for k, v in self._24jam().items() if k in jams])
        return data            
    
    def _rain(self):
        if not 'rain' in self.raw:
            return None
        data = [(k, v) for k, v in self._24jam().items() if k > 6]
        next_day = RDaily.select().where(
            RDaily.sampling==self.sampling + datetime.timedelta(days=1),
            RDaily.pos_id==self.pos_id).first()
        if next_day:
            data += [(k, v) for k, v in next_day._24jam().items() if k < 7]
        
        rain24 = 0
        count24 = 0
        hourly = {}
        now = datetime.datetime.now()
        if self.source == 'SC':
            hujan_jam_sebelum = 0
            for k, v in data:
                sampling_date = self.sampling if k > 6 else \
                    self.sampling + datetime.timedelta(days=1)
                sampling_ = datetime.datetime.fromisoformat(sampling_date.isoformat())
                sampling_ = sampling_.replace(hour=k)
                if sampling_ > now:
                    continue
                hujan_jam_ini = v.get('rain') - hujan_jam_sebelum if v.get('num') > 0 else 0
                hourly[k] = {'count': v.get('num'), 'rain': hujan_jam_ini}
                hujan_jam_sebelum = v.get('rain')
                rain24 += hujan_jam_ini
                count24 += v.get('num')
        else:
            for k, v in data:
                hourly[k] = {'count': v.get('num'), 'rain': v.get('rain')}
                rain24 += v.get('rain')
                count24 += v.get('num')
        ret = {'count24': count24, 'rain24': rain24, 'hourly': hourly, 'raw': self.raw}
        return ret
        
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
        self.save()
        

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
    nama = pw.CharField(max_length=60)
    
    
class LuwesPos(BaseModel):
    nama = pw.CharField(max_length=35, unique=True)
    imei = pw.CharField(max_length=30, unique=True)
    pos = pw.ForeignKeyField(Pos, null=True)
    tipe = pw.CharField(max_length=2, default='1') # 1 PCH, 2 PDA, 3 Klimat
    no_telepon = pw.CharField(max_length=25, null=True)
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
    def is_by_petugas(self):
        return self.username == self.pos.user_set[0].username
    
    @property
    def _tma(self):
        if not self.tma:
            return None
        return json.loads(self.tma)
    
    class Meta:
        indexes = (
            (('pos', 'sampling'), True),
        )
        
class LengkungDebit(BaseModel):
    pos = pw.ForeignKeyField(Pos)
    versi = pw.DateField()
    c_ = pw.FloatField()
    a_ = pw.FloatField()
    b_ = pw.FloatField()
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    

class UserQuery(BaseModel):
    cdate = pw.DateTimeField(default=datetime.datetime.now)
    q = pw.TextField() # user query / asking
    intent = pw.TextField() # json
    entity = pw.TextField() # json
    
