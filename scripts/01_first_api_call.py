#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
LESSON 1: YOUR FIRST API CALL
=============================================================================

This script teaches you how to:
1. Load secrets safely from environment variables
2. Make an HTTP GET request to an API
3. Parse the JSON response
4. Extract the data you actually need

Run this with: python scripts/01_first_api_call.py
=============================================================================
"""

import os
import requests
from dotenv import load_dotenv

# =============================================================================
# STEP 1: LOAD YOUR API KEY SAFELY
# =============================================================================

# load_dotenv() reads the .env file and makes its contents available
# as environment variables. This keeps your secrets out of your code.

load_dotenv()

# os.getenv() retrieves an environment variable
# If it doesn't exist, it returns None (or a default you specify)

access_key = os.getenv("UNSPLASH_ACCESS_KEY")

# Always check that you actually have the key!
if not access_key:
    print("❌ ERROR: No API key found!")
    print("   Make sure you have a .env file with:")
    print("   UNSPLASH_ACCESS_KEY=your_key_here")
    exit(1)

print("✅ API key loaded successfully")
print(f"   Key preview: {access_key[:8]}...")  # Only show first 8 chars for safety


# =============================================================================
# STEP 2: UNDERSTAND THE REQUEST WE'RE MAKING
# =============================================================================

# The Unsplash API documentation tells us:
# - Base URL: https://api.unsplash.com
# - Endpoint for searching: /search/photos
# - Required parameter: query (what to search for)
# - Optional parameters: per_page (how many results), page (which page)

# Let's build our request piece by piece:

base_url = "https://api.unsplash.com"
endpoint = "/search/photos"
full_url = base_url + endpoint

# Parameters go in a dictionary - requests will format them properly
params = {
    "query": "tokyo street",   # What we're searching for
    "per_page": 5,             # Just 5 for this test (max is 30)
    "page": 1,                 # First page of results
    "orientation": "landscape" # Optional: only landscape photos
}

# Headers include our authentication
headers = {
    "Authorization": f"Client-ID {access_key}"
}

print("\n📤 REQUEST WE'RE ABOUT TO MAKE:")
print(f"   URL: {full_url}")
print(f"   Parameters: {params}")
print(f"   Headers: Authorization: Client-ID {access_key[:8]}...")


# =============================================================================
# STEP 3: MAKE THE REQUEST
# =============================================================================

print("\n⏳ Making request to Unsplash...")

# requests.get() makes an HTTP GET request
# - GET means "give me data" (as opposed to POST which means "take this data")
# - We pass the URL, parameters, and headers

response = requests.get(full_url, params=params, headers=headers)

# The response object contains everything the server sent back
print(f"\n📥 RESPONSE RECEIVED:")
print(f"   Status code: {response.status_code}")

# Status codes tell you what happened:
# - 200 = Success! Here's your data.
# - 400 = Bad request (you did something wrong)
# - 401 = Unauthorized (bad API key)
# - 403 = Forbidden (you're not allowed)
# - 404 = Not found (wrong endpoint)
# - 429 = Too many requests (rate limited!)
# - 500 = Server error (their problem, not yours)

if response.status_code != 200:
    print(f"❌ ERROR: Request failed!")
    print(f"   Response: {response.text}")
    exit(1)

print("   ✅ Success!")


# =============================================================================
# STEP 4: PARSE THE JSON RESPONSE
# =============================================================================

# APIs return data as JSON (JavaScript Object Notation)
# It looks like this: {"key": "value", "list": [1, 2, 3]}
# Python can convert this to dictionaries and lists with .json()

data = response.json()

# Let's explore what we got back
print(f"\n📦 RESPONSE STRUCTURE:")
print(f"   Top-level keys: {list(data.keys())}")
print(f"   Total results available: {data['total']}")
print(f"   Results on this page: {len(data['results'])}")


# =============================================================================
# STEP 5: EXTRACT WHAT WE NEED
# =============================================================================

# The 'results' key contains a list of photo objects
# Each photo has LOTS of data - let's see what one looks like

print(f"\n🖼️  FIRST PHOTO - ALL AVAILABLE FIELDS:")
first_photo = data['results'][0]
for key in first_photo.keys():
    print(f"   - {key}")

# That's a lot! For our project, we only need:
# - id: unique identifier
# - urls: different size versions of the image
# - color: dominant color (Unsplash extracts this for us!)
# - description/alt_description: what's in the photo
# - user: who took it (for attribution)

print(f"\n🎯 DATA WE ACTUALLY CARE ABOUT:")
print(f"   ID: {first_photo['id']}")
print(f"   Color: {first_photo['color']}")
print(f"   Description: {first_photo.get('description') or first_photo.get('alt_description', 'No description')}")
print(f"   Photographer: {first_photo['user']['name']}")
print(f"\n   Available image sizes:")
for size, url in first_photo['urls'].items():
    print(f"      {size}: {url[:60]}...")


# =============================================================================
# STEP 6: PROCESS ALL RESULTS
# =============================================================================

print(f"\n📋 ALL PHOTOS FROM THIS SEARCH:")
print("-" * 60)

for i, photo in enumerate(data['results'], 1):
    print(f"\n   Photo {i}:")
    print(f"   └── ID: {photo['id']}")
    print(f"   └── Color: {photo['color']}")
    print(f"   └── By: {photo['user']['name']}")
    
    # Get the description, falling back to alt_description if main is None
    desc = photo.get('description') or photo.get('alt_description') or 'No description'
    # Truncate if too long
    if len(desc) > 50:
        desc = desc[:50] + "..."
    print(f"   └── Desc: {desc}")


# =============================================================================
# WHAT'S NEXT?
# =============================================================================

print("\n" + "=" * 60)
print("🎉 CONGRATULATIONS! You just made your first API call!")
print("=" * 60)
print("""
What you learned:
1. How to load secrets from .env files
2. How to construct an API request (URL + params + headers)
3. How to make the request with the requests library
4. How to parse JSON responses
5. How to extract the specific data you need

Next lesson: We'll build a proper scraper that:
- Handles multiple cities
- Paginates through many pages of results
- Saves the data to JSON files
- Downloads the actual images
- Respects rate limits so we don't get banned
""")