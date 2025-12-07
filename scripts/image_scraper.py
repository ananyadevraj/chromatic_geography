"""
image scraper for Chromatic Geography.
downloads city photographs from Unsplash API.
"""

import os
import json
import time
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

if not ACCESS_KEY:
    print("No API key found. Check your .env file.")
    exit(1)

CITIES = {
    "tokyo": ["tokyo neon signs night", "tokyo temples"],
    "marrakech": ["marrakech", "morocco architecture tiles"],
    "copenhagen": ["copenhagen nyhavn colorful", "copenhagen architecture"],
    "santorini": ["santorini blue domes", "santorini white buildings greece"],
    "havana": ["havana cuba colorful buildings", "havana vintage cars streets"],
    "mexico city": ["mexico city colorful buildings", "coyoacan mexico streets"],
    "istanbul": ["istanbul grand bazaar", "istanbul"],
    "jaipur": ["jaipur pink city india", "jaipur palace"],
    "bangkok": ["bangkok", "bangkok street market"],
    "melbourne": ["melbourne", "melbourne architecture"],
    "singapore": ["singapore green city", "singapore skyline", "singapore"],
    "rio de janeiro": ["rio brazil carnival", "rio brazil iconic", "rio favellas"],
}

IMAGES_PER_QUERY = 25
PAGES_PER_QUERY = 1
DELAY_BETWEEN_REQUESTS = 2

DATA_DIR = Path("data")
IMAGES_DIR = DATA_DIR / "images" / "cities"
METADATA_DIR = DATA_DIR / "metadata"


def ensure_directories():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    for city in CITIES.keys():
        (IMAGES_DIR / city).mkdir(exist_ok=True)


def make_api_request(endpoint, params):
    url = f"https://api.unsplash.com{endpoint}"
    headers = {"Authorization": f"Client-ID {ACCESS_KEY}"}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("Rate limited. Waiting 60s...")
            time.sleep(60)
            return make_api_request(endpoint, params)
        else:
            print(f"Request failed: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None


def search_photos(query, page=1, per_page=30):
    params = {
        "query": query,
        "page": page,
        "per_page": per_page,
        "orientation": "landscape"
    }
    data = make_api_request("/search/photos", params)
    if data and 'results' in data:
        return data['results']
    return []


def extract_photo_data(photo):
    return {
        "id": photo["id"],
        "color": photo["color"],
        "description": photo.get("description") or photo.get("alt_description"),
        "urls": {
            "raw": photo["urls"]["raw"],
            "regular": photo["urls"]["regular"],
            "small": photo["urls"]["small"],
            "thumb": photo["urls"]["thumb"]
        },
        "photographer": {
            "name": photo["user"]["name"],
            "username": photo["user"]["username"],
            "profile": photo["user"]["links"]["html"]
        }
    }


def download_image(url, save_path):
    try:
        response = requests.get(url, timeout=30, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        return False
    except Exception:
        return False


def save_metadata(city, photos):
    filepath = METADATA_DIR / f"{city}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(photos, f, indent=2, ensure_ascii=False)


def scrape_city(city, queries):
    print(f"\n{city.upper()}")
    
    all_photos = []
    seen_ids = set()
    
    for query in queries:
        for page in range(1, PAGES_PER_QUERY + 1):
            photos = search_photos(query, page=page, per_page=IMAGES_PER_QUERY)
            
            if not photos:
                break
            
            for photo in photos:
                if photo['id'] in seen_ids:
                    continue
                seen_ids.add(photo['id'])
                all_photos.append(extract_photo_data(photo))
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    save_metadata(city, all_photos)
    
    for photo in all_photos:
        save_path = IMAGES_DIR / city / f"{photo['id']}.jpg"
        if save_path.exists():
            continue
        download_image(photo['urls']['small'], save_path)
        time.sleep(0.5)
    
    print(f"  {len(all_photos)} photos")
    return all_photos


def main():
    ensure_directories()
    
    for city, queries in CITIES.items():
        scrape_city(city, queries)
    
    print("\nDone.")


if __name__ == "__main__":
    main()