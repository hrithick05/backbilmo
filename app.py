#!/usr/bin/env python3
"""
THE ONLY BACKEND YOU NEED
Simple, clean, and works perfectly with the frontend
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from datetime import datetime, timedelta
import logging

# Add scrapers to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapers'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# MongoDB setup
MONGODB_AVAILABLE = False
mongodb_client = None
mongodb_db = None

try:
    from pymongo import MongoClient
    mongodb_uri = "mongodb+srv://bilmo5352_db_user:Y2ImhIbqLYYmp5db@cluster0.9skkolg.mongodb.net/ecommerce_search_db?retryWrites=true&w=majority&appName=Cluster0"
    mongodb_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    mongodb_client.admin.command('ping')
    mongodb_db = mongodb_client['ecommerce_search_db']
    MONGODB_AVAILABLE = True
    logger.info("✅ MongoDB Connected")
except Exception as e:
    logger.warning(f"⚠️ MongoDB unavailable: {e}")

def get_from_db(query, platform):
    """Check MongoDB first"""
    if not MONGODB_AVAILABLE:
        return None
    
    try:
        cache_key = f"{platform}:{query}".lower()
        collection = mongodb_db['search_results']
        result = collection.find_one({
            "cache_key": cache_key,
            "timestamp": {"$gte": datetime.now() - timedelta(hours=24)}
        })
        
        if result:
            logger.info(f"✅ DB HIT: {platform}/{query}")
            return result.get('data')
        
        logger.info(f"❌ DB MISS: {platform}/{query}")
        return None
    except Exception as e:
        logger.error(f"DB error: {e}")
        return None

def save_to_db(query, platform, data):
    """Save to MongoDB"""
    if not MONGODB_AVAILABLE:
        return
    
    try:
        cache_key = f"{platform}:{query}".lower()
        collection = mongodb_db['search_results']
        collection.replace_one(
            {"cache_key": cache_key},
            {
                "cache_key": cache_key,
                "query": query,
                "platform": platform,
                "data": data,
                "timestamp": datetime.now()
            },
            upsert=True
        )
        logger.info(f"💾 SAVED: {platform}/{query}")
    except Exception as e:
        logger.error(f"Save error: {e}")

def scrape_platform(platform, query):
    """Scrape a platform"""
    logger.info(f"🌐 SCRAPING: {platform}/{query}")
    
    try:
        import io
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
        
        if platform == 'amazon':
            from amazon.amazon_search import search_amazon
            result = search_amazon(query, headless=True)
        elif platform == 'flipkart':
            from flipkart.flipkart_search import search_flipkart
            result = search_flipkart(query, headless=True)
        elif platform == 'myntra':
            from myntra.myntra_search import search_myntra
            result = search_myntra(query, headless=True, use_universal_approach=True)
        elif platform == 'meesho':
            from meesho.meesho_search import search_meesho
            result = search_meesho(query, headless=True)
        else:
            return None
        
        sys.stdout, sys.stderr = old_stdout, old_stderr
        return result
        
    except Exception as e:
        if 'old_stdout' in locals():
            sys.stdout, sys.stderr = old_stdout, old_stderr
        logger.error(f"Scrape error {platform}: {e}")
        return {
            "site": platform.title(),
            "query": query,
            "total_products": 0,
            "basic_products": [],
            "detailed_products": []
        }

def format_product(product):
    """Format one product"""
    return {
        "title": product.get('title') or product.get('name', 'Unknown'),
        "name": product.get('title') or product.get('name', 'Unknown'),
        "price": product.get('price', 'N/A'),
        "image": product.get('image_url') or product.get('image', 'https://via.placeholder.com/250x200'),
        "image_url": product.get('image_url') or product.get('image', 'https://via.placeholder.com/250x200'),
        "link": product.get('link') or product.get('url', '#'),
        "url": product.get('link') or product.get('url', '#'),
        "rating": product.get('rating', 'N/A'),
        "mrp": product.get('mrp'),
        "discount": product.get('discount')
    }

def format_result(raw_result, query):
    """Format platform result"""
    all_products = raw_result.get('basic_products', []) + raw_result.get('detailed_products', [])
    formatted = [format_product(p) for p in all_products]
    
    return {
        "site": raw_result.get('site', 'Unknown'),
        "query": query,
        "total_products": len(formatted),
        "basic_products": formatted
    }

@app.route('/search', methods=['GET', 'POST'])
def search():
    """
    THE MAIN ENDPOINT
    Flow: Check DB → Return if found → Else scrape → Save → Return
    """
    import time
    start = time.time()
    
    # Get parameters
    if request.method == 'POST':
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        platforms = data.get('platforms', None)
        force = data.get('force_refresh', False)
    else:
        query = request.args.get('q', '').strip()
        platforms_str = request.args.get('platforms', '').strip()
        platforms = [p.strip() for p in platforms_str.split(',')] if platforms_str else None
        force = request.args.get('force_refresh', 'false').lower() == 'true'
    
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    if not platforms:
        platforms = ['amazon', 'flipkart', 'myntra', 'meesho']
    
    logger.info(f"\n{'='*60}")
    logger.info(f"SEARCH: {query} | Platforms: {platforms}")
    logger.info(f"{'='*60}")
    
    results = []
    cache_hits = 0
    fresh = 0
    total = 0
    
    for platform in platforms:
        try:
            platform = platform.lower().strip()
            
            # STEP 1: Check DB first
            if not force:
                cached = get_from_db(query, platform)
                if cached:
                    formatted = format_result(cached, query)
                    results.append(formatted)
                    total += formatted['total_products']
                    cache_hits += 1
                    logger.info(f"⚡ {platform.upper()}: {formatted['total_products']} from DB")
                    continue
            
            # STEP 2: Not in DB - scrape
            fresh += 1
            raw = scrape_platform(platform, query)
            
            if raw and raw.get('total_products', 0) > 0:
                save_to_db(query, platform, raw)
                formatted = format_result(raw, query)
                results.append(formatted)
                total += formatted['total_products']
                logger.info(f"🌐 {platform.upper()}: {formatted['total_products']} scraped")
            else:
                logger.warning(f"⚠️ {platform.upper()}: No products found")
                
        except Exception as e:
            logger.error(f"❌ {platform.upper()} error: {e}")
            # Continue with other platforms even if one fails
            continue
    
    elapsed = round(time.time() - start, 2)
    
    if cache_hits > 0 and fresh == 0:
        source = "mongodb_cache"
    elif cache_hits > 0 and fresh > 0:
        source = f"mixed ({cache_hits} cache, {fresh} scraped)"
    else:
        source = "web_scraping"
    
    logger.info(f"✅ DONE: {total} products in {elapsed}s")
    logger.info(f"{'='*60}\n")
    
    return jsonify({
        "success": True,
        "query": query,
        "total_results": total,
        "source": source,
        "cache_hits": cache_hits,
        "fresh_searches": fresh,
        "processing_time": f"{elapsed}s",
        "timestamp": datetime.now().isoformat(),
        "mongodb_status": "connected" if MONGODB_AVAILABLE else "disconnected",
        "results": results
    })

@app.route('/status')
def status():
    """API status"""
    cache_count = 0
    if MONGODB_AVAILABLE:
        try:
            cache_count = mongodb_db['search_results'].count_documents({})
        except:
            pass
    
    return jsonify({
        "success": True,
        "api_status": "online",
        "mongodb_status": "connected" if MONGODB_AVAILABLE else "disconnected",
        "cache_entries": cache_count,
        "supported_platforms": ["amazon", "flipkart", "myntra", "meesho"]
    })

@app.route('/')
def home():
    """Home page"""
    return """
    <html>
    <head><title>E-commerce API</title></head>
    <body style="font-family: Arial; padding: 40px; background: #f5f5f5;">
        <div style="max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
            <h1>🚀 E-commerce Search API</h1>
            <p><strong>Status:</strong> Online</p>
            <h2>Endpoints:</h2>
            <ul>
                <li><code>/search?q=laptop</code></li>
                <li><code>/search?q=smartphone&platforms=amazon,flipkart</code></li>
                <li><code>/status</code></li>
            </ul>
            <h2>Test:</h2>
            <p><a href="/search?q=laptop">Search: laptop</a></p>
            <p><a href="/status">Check status</a></p>
        </div>
    </body>
    </html>
    """

# Error handlers to ensure JSON responses
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "success": False}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error", "success": False, "details": str(error)}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled exception: {error}")
    return jsonify({"error": "Internal server error", "success": False, "details": str(error)}), 500

if __name__ == '__main__':
    logger.info("\n" + "="*60)
    logger.info("🚀 E-COMMERCE API STARTING")
    logger.info("="*60)
    logger.info(f"MongoDB: {'✅ Connected' if MONGODB_AVAILABLE else '❌ Disconnected'}")
    logger.info(f"URL: http://127.0.0.1:5000")
    logger.info("="*60 + "\n")
    
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)

