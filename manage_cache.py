#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cache Management Tool
"""

from pymongo import MongoClient
from datetime import datetime
import json

client = MongoClient('mongodb+srv://bilmo5352_db_user:Y2ImhIbqLYYmp5db@cluster0.9skkolg.mongodb.net/ecommerce_search_db?retryWrites=true&w=majority&appName=Cluster0')
db = client['ecommerce_search_db']
collection = db['search_results']

def show_all_cache():
    """Show all cached queries"""
    print("="*70)
    print("ALL CACHED QUERIES")
    print("="*70)
    print()
    
    all_cached = list(collection.find({}).sort('timestamp', -1))
    
    for i, item in enumerate(all_cached, 1):
        try:
            cache_key = item.get('cache_key', 'unknown')
            timestamp = item.get('timestamp', datetime.now())
            
            data = item.get('data', {})
            
            # Handle both dict and list data
            if isinstance(data, dict):
                total_products = data.get('total_products', 0)
                site = data.get('site', 'Unknown')
            else:
                total_products = len(data) if isinstance(data, list) else 0
                site = 'Unknown'
            
            age_hours = (datetime.now() - timestamp).total_seconds() / 3600
            
            print(f"{i:2}. {cache_key:35} | {site:10} | {total_products:2} products | {age_hours:.1f}h old")
        except Exception as e:
            print(f"{i:2}. ERROR: {cache_key if 'cache_key' in locals() else 'unknown'} - {e}")
    
    print()
    print(f"Total: {len(all_cached)} cached queries")
    print()

def clear_cache(query=None, platform=None):
    """Clear cache"""
    if query and platform:
        cache_key = f"{platform}:{query}".lower()
        result = collection.delete_one({'cache_key': cache_key})
        print(f"Deleted: {cache_key} ({result.deleted_count} entries)")
    else:
        result = collection.delete_many({})
        print(f"Cleared all cache ({result.deleted_count} entries)")

def inspect_cache(query, platform):
    """Inspect a cached entry in detail"""
    cache_key = f"{platform}:{query}".lower()
    result = collection.find_one({'cache_key': cache_key})
    
    if not result:
        print(f"NOT FOUND: {cache_key}")
        return
    
    print("="*70)
    print(f"CACHED DATA: {cache_key}")
    print("="*70)
    print()
    
    print(f"Timestamp: {result.get('timestamp')}")
    
    data = result.get('data', {})
    print(f"Site: {data.get('site')}")
    print(f"Query: {data.get('query')}")
    print(f"Total Products: {data.get('total_products')}")
    print()
    
    basic_products = data.get('basic_products', [])
    print(f"Basic Products: {len(basic_products)}")
    
    if basic_products:
        print()
        print("First 3 Products:")
        for i, product in enumerate(basic_products[:3], 1):
            title = product.get('title', 'N/A')
            price = product.get('price', 'N/A')
            rating = product.get('rating', 'N/A')
            
            print(f"\n{i}. {title[:60]}")
            print(f"   Price: {price}")
            print(f"   Rating: {rating}")
            print(f"   Has Image: {'Yes' if product.get('image_url') else 'No'}")
            print(f"   Has Link: {'Yes' if product.get('link') else 'No'}")
    
    print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_cache.py show")
        print("  python manage_cache.py inspect amazon laptop")
        print("  python manage_cache.py clear amazon laptop")
        print("  python manage_cache.py clearall")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'show':
        show_all_cache()
    
    elif command == 'inspect' and len(sys.argv) >= 4:
        platform = sys.argv[2]
        query = ' '.join(sys.argv[3:])
        inspect_cache(query, platform)
    
    elif command == 'clear' and len(sys.argv) >= 4:
        platform = sys.argv[2]
        query = ' '.join(sys.argv[3:])
        clear_cache(query, platform)
    
    elif command == 'clearall':
        response = input("Are you sure you want to clear ALL cache? (yes/no): ")
        if response.lower() == 'yes':
            clear_cache()
        else:
            print("Cancelled")
    
    else:
        print("Invalid command!")

