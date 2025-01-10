import dateparser
import re
import json
import datetime
import random
from peewee import DoesNotExist, fn
from flask import jsonify

from app.models import Pos, RDaily, ManualDaily

def classify_intent(text):
    return 'pic_pos'

def extract_entity(text):
    return []

def extract_date_month(text):
    return datetime.date.today()

def get_info_pos(pos_id):
    try:
        pos_data = Pos.get(Pos.id == int(pos_id))
        petugas = pos_data.petugas_set.first()
        result = {
            'LOC': pos_data.nama,
            'LATLON': pos_data.ll,
            'ELEV': pos_data.elevasi,
            'KAB': pos_data.kabupaten,
            'PIC': {'nama': petugas.nama,
                    'hp': petugas.hp} if petugas else None
        }
    except DoesNotExist:
        result = {'error': 'Pos not found'}
    return result

def get_info_hujan_pos_hari(pos, waktu):
    '''Return dictionary of hujan info for a specific pos and day'''
    result = {'LOC': pos, 'TIME': waktu}
    return result

def get_info_hujan_pos_bulan(pos, waktu):
    '''Return dictionary of hujan info for a specific pos and month'''
    result = {'LOC': pos, 'TIME': waktu}
    return result

def get_info_hujan_pos_tahun(pos, waktu):
    '''Return dictionary of hujan info for a specific pos and year'''
    result = {'LOC': pos, 'TIME': waktu}
    return result

def get_info_hujan_wilayah_hari(pos, waktu):
    '''Return dictionary of hujan info for a specific region (kabupaten) 
    and day'''
    result = {'LOC': pos, 'TIME': waktu}
    return result

def get_info_hujan_wilayah_bulan(pos, waktu):
    '''Return dictionary of hujan info for a specific region (kabupaten)
    and month'''
    result = {'LOC': pos, 'TIME': waktu}
    return result

def get_info_hujan_wilayah_tahun(pos, waktu):
    '''Return dictionary of hujan info for a specific region (kabupaten)
    and year'''
    result = {'LOC': pos, 'TIME': waktu}
    return result

def request_clues():
    reqs = [
        'Siapa petugas pos Majalengka?', # "petugas_pos" LOC: Majalengka
        'hujan bulan november', # "hujan_range" TIME: November
        'hujan kemarin', # "hujan_range" TIME: kemarin
        'Hari ini hujan terjadi di mana saja?', # "hujan_range" TIME: hari ini
        'Pos mana saja yang saat ini tidak aktif?', # "missing_telemetri"
        'hujan pos PCH Ciamis kemarin', # "hujan_range" LOC: Ciamis TIME: kemarin
        'grafik hujan bulan ini seluruh pos', # "hujan_range" TIME: bulan ini
        'Hujan tertinggi bulan November?', # "hujan_tertinggi" TIME: November
        'Tolong ke halaman peta hujan!', # "goto" PAGE: peta hujan
        'Pos debit di mana saja?', # "pos_debit"
        'Siapa penjaga pos Majalengka', # "petugas_pos" LOC: Majalengka
        'Petugas mana saja yang belum kirim data hari ini', # "missing_manual" ATTRIBUTE: petugas TIME: hari ini
    ]
    return reqs

def extract_loc(user_request):
    id_names = [(p.id, p.nama.replace('PCH', '').replace('PDA', '').lower().strip()) for p in Pos.select()]
    locs = []
    katas = user_request.split(' ')
    for i, n in id_names:
        n = n.replace('-', '')
        if any(m in n for m in katas):
            locs.append(i)
    return locs
    
def extract_time_phrases(text):
    # Daftar pola waktu (regex patterns)
    time_patterns = [
        r'\b\d+\s+(hari|bulan|tahun)\s+(lalu|ke depan)\b',   # Contoh: "5 hari lalu", "3 bulan ke depan"
        r'\b(sekarang|hari ini|kemarin|besok|bulan ini|tahun ini)\b',  # Contoh: "hari ini", "kemarin"
        r'\b(tanggal\s+\d+\s+\w+(\s+\d{4})?)\b',            # Contoh: "tanggal 15 Desember", "tanggal 1 Januari 2023"
        r'\b\d+\s+\w+\s+\d{4}\b',                           # Contoh: "12 Mei 1973"
        r'\b\d+\s+\w+\b',                                   # Contoh: "12 Mei"
    ]
    
    # Gabungkan semua pola ke dalam satu regex
    combined_pattern = "|".join(time_patterns)
    #print(combined_pattern)
    # Cari semua kecocokan dalam teks
    matches = re.findall(combined_pattern, text, re.IGNORECASE)
    print(matches)
    
    # Kembalikan daftar hasil
    return [match[0] if isinstance(match, tuple) else match for match in matches]

def request_handler(user_text):
    return classify_request(user_text)

def classify_request(user_request):
    pattern = (
        r"(?P<hujan>hujan ).*?"
        r"(?P<hari>(kemarin|hari ini|\d+ hari lalu))?"
        r"(?P<bulan>(bulan ini|(\d+ )?bulan lalu))?"
        r"(?: di (?:pos )?(?P<lokasi>\w+))?|"
        r"(?P<petugas>petugas\s+(?:(di|pada)\s+)?(?:pos\s+)?)(?P<nama>\w+)|"
        r"(?:\w+\s+)(?P<status>status\s+((?:(di|pada)\s+)?)pos\s+(?P<status_pos>\w+))|"
        r"(?P<daftar_pch>daftar\s+pos\s+hujan)|"
        r"(?P<daftar_pda>daftar\s+pos\s+duga\s+air)|"
        r"(?P<daftar>daftar\s+pos)"
    )
    match = re.match(pattern, user_request, re.IGNORECASE)
    ret = {'intent': None, 'entities': None, 'result': {'msg': ''}}
    default_msgs = [
        'Kami belum paham maksud anda',
        'Mohon maaf, kami masih perlu belajar, permintaan anda telah kami simpan.',
        'Saat ini kami baru menangani permintaan \'status pos\''
    ]
    ret['result']['msg'] = '?'
    if not match:
        return ret
    req_dict = match.groupdict()
    if req_dict.get('status'):
        pos = req_dict.get('status_pos')
        ret['intent'] = 'status_logger'
        ret['entities'] = {'LOC': pos}
        q = status_telemetri(pos)
        ret['result'] = q
    elif req_dict.get('daftar'):
        ret['result']['msg'] = 'Daftar **Pos Hidrologi** \n\n1. ' + '1. '.join([p.nama + '\n' for p in Pos.select().order_by(Pos.tipe, Pos.nama)])
    elif req_dict.get('daftar_pch'):
        ret['result']['msg'] = 'Daftar **Pos Curah Hujan** \n\n1. ' + '1. '.join([p.nama + '\n' for p in Pos.select().order_by(Pos.tipe, Pos.nama) if p.tipe == '1'])
    elif req_dict.get('daftar_pda'):
        ret['result']['msg'] = 'Daftar **Pos Duga Air** \n\n1. ' + '1. '.join(['**{}** (+{} M) di sungai {}\n'.format(p.nama, p.elevasi, p.sungai) for p in Pos.select().order_by(Pos.sungai, Pos.nama, Pos.elevasi) if p.tipe == '2'])
    elif req_dict.get('petugas'):
        nama_pos = req_dict.get('nama')
        q = Pos.select().where(Pos.nama.ilike('%{}%'.format(nama_pos)))
        if q.count() > 1:
            ret['result']['msg'] = 'Ada beberapa pos: ' + ','.join([p.nama for p in q])
        elif q is not None:
            p = petugas_pos(q.first().id)
            msg = 'Petugas pos **{}** adalah **{}** hp: {}'.format(p['pos'].get('nama'), p['petugas'].get('nama'), p['petugas'].get('hp'))
            msg += '\n\n**Kontribusi Data:**\n\n 1. ' + '1. '.join(['{}-{}: {}\n'.format(*r) for r in p['kontribusi']])
            ret['result']['msg'] = msg
    elif req_dict.get('hujan'):
        pos = req_dict.get('namapos') or ''
        hari = req_dict.get('hari')
        bulan = req_dict.get('bulan')
        pchs_id = [p.id for p in Pos.select().where(Pos.tipe.in_(('1', '3')))]
        msg = '?'
        if bulan:
            sampling = dateparser.parse(bulan)
            start = sampling.replace(day=1)
            end = (start + datetime.timedelta(days=32)).replace(day=1)
            if datetime.date.today().month == sampling.month:
                end = datetime.date.today()
            q = RDaily.select().where(RDaily.pos_id.in_(pchs_id), RDaily.sampling >= start, RDaily.sampling < end)
            if not q:
                msg = 'Bulan {} tidak ada data hujan'.format(sampling.strftime('%B %Y'))
            else:
                rain = sum([r._rain().get('rain24') for r in q if r._rain()])
                if rain == 0:
                    msg = 'Bulan {} tidak ada hujan'.format(sampling.strftime('%B %Y'))
                else:
                    msg = 'Bulan {} hujan terjadi {:.1f} mm di {} pos pada {} kabupaten.\n\n'.format(sampling.strftime('%B %Y'), rain, len(set(list([p.pos_id for p in q]))), len(set([r.pos.kabupaten for r in q])))
                    msg += 'Rata-rata tergolong hujan **{}**.\n\n'.format('ringan' if rain < 50 else 'sedang' if rain < 100 else 'lebat')
            '''
            Bulan (ini|Agustus 2024) hujan terjadi az mm di x pos pada y kabupaten.
            Rata-rata tergolong hujan ringan|sedang|lebat.
            
            Daftar Pos yang terjadi hujan pada waktu tersebut:
            1. Pos A (hujan: az mm)
            '''
        elif hari:
            sampling = dateparser.parse(hari)
            string_hari = sampling.date() == datetime.date.today() and 'Hari ini' or sampling.strftime('Tanggal %d %B %Y')
            q = RDaily.select().where(RDaily.pos_id.in_(pchs_id), RDaily.sampling == sampling)
            if not q:
                msg = '{} tidak ada data hujan'.format(string_hari)
            else:
                rain = sum([r._rain().get('rain24') for r in q if r._rain()])
                if rain == 0:
                    msg = '{} tidak ada hujan'.format(string_hari)
                else:
                    msg = '{} hujan terjadi {:.1f} mm di {} pos pada {} kabupaten.\n\n'.format(string_hari, rain, len(list(set([p.pos_id for p in q]))), len(set([r.pos.kabupaten if r.pos else '' for r in q])))
                    msg += 'Rata-rata tergolong hujan **{}**.\n\n'.format('ringan' if rain < 50 else 'sedang' if rain < 100 else 'lebat')
        ret['result']['msg'] = msg
    else:
        pass
    return ret  # Default category if none matches

def status_telemetri(q_pos_name):
    pos_ids = dict([(p.id, p.nama.lower()) for p in Pos.select()])
    pids = []
    msgs = '<b>{}</b> tidak ditemukan'.format(q_pos_name)
    for k, v in pos_ids.items():
        if q_pos_name.lower() in v:
            pids.append(k)
    subquery = (RDaily.select(RDaily.pos_id, fn.MAX(RDaily.sampling).alias('latest'))
             .where(RDaily.pos_id.in_(pids))
             .group_by(RDaily.pos_id))
    query = (RDaily.select(RDaily.pos, RDaily.raw, RDaily.sampling)
             .join(
                 subquery,
                 on=(
                     (RDaily.pos_id == subquery.c.pos_id) &
                     (RDaily.sampling == subquery.c.latest)
                 )
             ))
    if query:
        msgs = '<ol>'
        now = datetime.datetime.now()
        for rd in query:
            data = json.loads(rd.raw)
            nama_pos = rd.pos.nama
            data_terakhir = 'tidak ditemukan'
            if data:
                status = '<b>tidak sehat</b>'
                data_terakhir = datetime.datetime.fromisoformat(data[-1].get('sampling'))
                if now - data_terakhir <= datetime.timedelta(hours=1):
                    status = '<b>sehat</b>'
            msgs += '<li>{} status {}, data terakhir {}</li>\n'.format(nama_pos, status, data_terakhir)
        msgs += '</ol>'
    return {'msg': msgs}

def petugas_pos(pos_id):
    try:
        pos = Pos.get(pos_id)
        petugas = pos.petugas_set.first()
    except DoesNotExist:
        return None
    pos_fields = 'nama_kecamatan_kabupaten'.split('_')
    petugas_dict = {}
    kontribusi = None
    if petugas:
        petugas_fields = 'nama_hp_nik_dusun_desa_kecamatan_kabupaten'.split('_')
        petugas_dict = {f: getattr(petugas, f) for f in petugas_fields}
        kontribusi = (ManualDaily
                      .select(ManualDaily.sampling.year.alias('year'), ManualDaily.sampling.month.alias('month'), fn.COUNT(ManualDaily.id).alias('count'))
                      .where(ManualDaily.username==petugas.username)
                      .group_by(ManualDaily.sampling.year, ManualDaily.sampling.month)
                      .order_by(ManualDaily.sampling.year.desc(), ManualDaily.sampling.month.desc())
                      )
    return {'pos': {f: getattr(pos, f) for f in pos_fields}, 
            'petugas': petugas_dict,
            'kontribusi': [(r.year, r.month, r.count) for r in kontribusi] if kontribusi else []}
        
    
def is_hujan_request(req):
    ret = None
    pos = None
        
def extract_date_range(user_request):
    # Regular expression to capture date phrases
    date_phrases = re.findall(r"\b(dari|antara|hingga|sampai|dan|ke)\b\s*[\w\s,]+", user_request)
    
    # Parse dates using dateparser
    dates = []
    for phrase in date_phrases:
        parsed_date = dateparser.parse(phrase)
        if parsed_date:
            dates.append(parsed_date.strftime("%Y-%m-%d"))
    
    if len(dates) == 2:
        return {"start_date": dates[0], "end_date": dates[1]}
    elif len(dates) == 1:
        return {"start_date": dates[0], "end_date": None}
    else:
        return None

# Example user request
user_requests = [
    'Siapa petuugas pos Majalengka?',
    'hujan bulan november',
    'Pos mana saja yang saat ini tidak aktif?',
    'Berapa total hujan bulan ini?',
    'Hujan tertinggi bulan November?',
    'Hari ini hujan terjadi di mana saja?',
    'Tolong ke halaman peta hujan!',
    'Pos debit di mana saja?',
    'Siapa penjaga pos Majalengka',
    'Petugas mana saja yang belum kirim data hari ini',
    'Hari ini pos mana yang belum kirim data',
]
intents = [
    'pic_pos',
    'logger_status_gagal_semua',
    'total_hujan_waktu_rentang',
    'hujan_tertinggi_waktu_rentang',
    'hujan_terjadi_dimana_hari',
    'goto',
    'pos_debit',
    'missing_manual_data'
]

data = {
    "text": user_requests,
    "label": [0, 1, 2, 3, 4, 5, 6, 0, 7, 7]
}

if __name__ == '__main__':
    # Classify request
    for i in range(len(user_requests)):
        req = request_handler(user_requests[i])
        print(f"Request: {req} {user_requests[i]}")

    # Extract date range
    #date_range = extract_date_range(user_request)
    #print(f"Date range: {date_range}")