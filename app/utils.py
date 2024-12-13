import dateparser
import re

def classify_request(user_request):
    # Categories
    categories = {"petugas": ["siapa", "petugas", "pos", "penjaga"], 
                  "goto": ["halaman", "ke", "tolong"], 
                  "total_hujan": ["total", "berapa", "hujan"],
                  "status_logger": ["mana", "tidak aktif"],
                  "hujan_tertinggi": ["hujan tertinggi", "mana", "berapa"],
                  "dimana_hujan": ["mana", "hujan", "terjadi"],
                  "pos": ["pos hidrologi", "pos duga air", "pos hujan"]}
    
    # Check for keywords to classify the request
    cats = []
    for category, keywords in categories.items():
        if any(keyword in user_request.lower() for keyword in keywords):
            cats.append(category)
    
    return cats  # Default category if none matches

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
    'Siapa petuugas pos PDA Pataruman?',
    'Pos mana saja yang saat ini tidak aktif?',
    'Berapa total hujan bulan ini?',
    'Berapa total hujan bulan Desember?',
    'Hujan tertinggi bulan November?',
    'Hari ini hujan terjadi di mana saja?',
    'Tolong ke halaman peta hujan!</li>',
    'Tolong ke halaman peta hujan tanggal 4 Desember 2024!',
    'Tolong ke halaman hujan tanggal 4 desember 2024!',
    'Pos debit di mana saja?',
]

if __name__ == '__main__':
    # Classify request
    for i in range(len(user_requests)):
        request_type = classify_request(user_requests[i])
        print(f"Request type: {request_type} {user_requests[i]}")

    # Extract date range
    date_range = extract_date_range(user_request)
    print(f"Date range: {date_range}")