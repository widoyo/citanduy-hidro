import dateparser
import re

def classify_request(user_request):
    # Categories
    categories = {"chart": ["chart", "graph", "plot", "grafik"], 
                  "data": ["data", "list", "records"], 
                  "summary": ["summarize", "summary", "overview", "gambaran"],
                  "hujan": ["hujan", "curah hujan", "pch", "pos hujan"],
                  "max": ["tertinggi", "maksimum"],
                  "tma": ["pda", "duga air", "tinggi muka air"],
                  "petugas": ["siapa", "petugas"],
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
user_request = "Can you show me a chart of water levels from December 1st to December 10th?"

# Classify request
request_type = classify_request(user_request)
print(f"Request type: {request_type}")

# Extract date range
date_range = extract_date_range(user_request)
print(f"Date range: {date_range}")