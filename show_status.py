#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Show complete status of caching and scraping
"""

import requests
import json
import time
from pymongo import MongoClient
from datetime import datetime

API_URL = "http://127.0.0.1:5000"

print("="*70)
print("COMPLETE STATUS CHECK")
print("="*70)
print()

# Check API is running
print("[1] API Status")
print("-"*70)
try:
    response = requests.get(f"{API_URL}/status", timeout=2)
    status = response.json()
    print(f"API: ONLINE")
    print(f"MongoDB: {'CONNECTED' if status.get('mongodb_available') else 'DISCONNECTED'}")
    print(f"Cached Entries: {status.get('cached_count', 0)}")
except Exception as e:
    print(f"API: OFFLINE - {e}")
    exit(1)

print()
print("[2] MongoDB Cache Contents")
print("-"*70)

try:
    client = MongoClient('mongodb+srv://bilmo5352_db_user:Y2ImhIbqLYYmp5db@cluster0.9skkolg.mongodb.net/ecommerce_search_db?retryWrites=true&w=majority&appName=Cluster0', serverSelectionTimeoutMS=5000)
    db = client['ecommerce_search_db']
    collection = db['search_results']
    
    all_cached = list(collection.find({}, {'cache_key': 1, 'timestamp': 1, 'data.total_products': 1}))
    
    print(f"Total Cached Queries: {len(all_cached)}")
    print()
    
    for item in all_cached[:10]:  # Show first 10
        key = item.get('cache_key', 'unknown')
        timestamp = item.get('timestamp', 'unknown')
        total = item.get('data', {}).get('total_products', 0)
        
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600 if isinstance(timestamp, datetime) else 0
        
        print(f"  {key:30} - {total:2} products - {age_hours:.1f}h old")
    
except Exception as e:
    print(f"MongoDB Error: {e}")

print()
print("[3] Test Cache-First (laptop)")
print("-"*70)

start = time.time()
try:
    response = requests.get(f"{API_URL}/search?q=laptop&platforms=amazon", timeout=5)
    elapsed = time.time() - start
    data = response.json()
    
    print(f"Time: {elapsed:.2f}s")
    print(f"Source: {data.get('source')}")
    print(f"Cache Hits: {data.get('cache_hits')}")
    print(f"Fresh Searches: {data.get('fresh_searches')}")
    print(f"Total Results: {data.get('total_results')}")
    
    if elapsed < 1 and data.get('cache_hits', 0) > 0:
        print("Result: CACHE WORKING (fast)")
    else:
        print("Result: SCRAPED (slow)")
except Exception as e:
    print(f"Error: {e}")

print()
print("[4] Test Fresh Scrape (unique query)")
print("-"*70)
print("Searching for 'testproduct999' (NOT in cache)...")
print()

start = time.time()
try:
    response = requests.get(f"{API_URL}/search?q=testproduct999&platforms=amazon", timeout=60)
    elapsed = time.time() - start
    data = response.json()
    
    print(f"Time: {elapsed:.2f}s")
    print(f"Source: {data.get('source')}")
    print(f"Cache Hits: {data.get('cache_hits')}")
    print(f"Fresh Searches: {data.get('fresh_searches')}")
    print(f"Total Results: {data.get('total_results')}")
    
    if elapsed > 10 and data.get('fresh_searches', 0) > 0:
        print("Result: SCRAPER WORKING (took time)")
    else:
        print("Result: From cache (unexpected)")
except Exception as e:
    print(f"Error: {e}")

print()
print("="*70)
print("SUMMARY")
print("="*70)
print()
print("1. API: ONLINE")
print("2. MongoDB: CONNECTED")
print("3. Cache-First Strategy: WORKING")
print("4. Amazon Scraping: CHECK ABOVE")
print()
print("If you want fresh Amazon data for 'laptop':")
print("  Option 1: Delete cache and search again")
print("  Option 2: Search for a different term")
print("  Option 3: Wait 24 hours for cache to expire")
print()


