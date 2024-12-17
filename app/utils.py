import dateparser
import re
import json
import datetime
import random
from peewee import DoesNotExist, fn
from flask import jsonify

from app.models import Pos, RDaily

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
    pattern = r"(?P<hujan>hujan(?:\s+)?(?P<status_hujan>tertinggi\s+)?(?P<waktu>(kemarin|(((hari ini|\d+\s+hari lalu|bulan ini|(\d+\s+)?(bulan lalu|tahun lalu))|((?:bulan\s+)?\w+(\s+\d+)?)))))?((?:\s+di\s+)(?P<namapos>\w+))?)|(?P<petugas>petugas\s+(?:(di|pada)\s+)?(?:pos\s+)?)(?P<nama>\w+)|(?:\w+\s+)(?P<status>status\s+((?:(di|pada)\s+)?)pos\s+(?P<status_pos>\w+))"
    match = re.match(pattern, user_request, re.IGNORECASE)
    ret = {'intent': None, 'entities': None, 'result': {'msg': ''}}
    default_msgs = [
        'Kami belum paham maksud anda',
        'Mohon maaf, kami masih perlu belajar, permintaan anda telah kami simpan.',
        'Saat ini kami baru menangani permintaan \'status pos\''
    ]
    ret['result']['msg'] = default_msgs[random.randint(0, len(default_msgs))]
    if not match:
        return ret
    req_dict = match.groupdict()
    if req_dict.get('status'):
        pos = req_dict.get('status_pos')
        ret['intent'] = 'status_logger'
        ret['entities'] = {'LOC': pos}
        q = status_telemetri(pos)
        ret['result'] = q
    elif req_dict.get('petugas'):
        pos = req_dict.get('nama')
        ret = petugas_pos(pos)
    elif req_dict.get('hujan'):
        pos = req_dict.get('namapos') or ''
        waktu = req_dict.get('waktu')
        ret = 'hujan' + pos +' waktu: ' + waktu
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

def petugas_pos(nama_pos):
    try:
        poses = Pos.select().where(Pos.nama.like==nama_pos)
    except DoesNotExist:
        pos = None
    return ','.join([p.nama for p in poses])
        
    
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