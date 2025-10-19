# Unified Smart E-commerce API - Complete Guide

## 🎉 What's New?

The two separate APIs (`smart_ecommerce_api.py` and `display_api.py`) have been **merged into one powerful unified API** (`unified_ecommerce_api.py`) with all errors fixed!

## ✅ Fixed Errors

### 1. **smart_ecommerce_api.py Issues Fixed:**
   - ❌ `/search` endpoint was returning sample/dummy data instead of real scraping results
   - ❌ Scraper imports using relative paths causing import errors
   - ❌ Missing sys.path configuration for scrapers directory
   - ✅ **Fixed:** `/search` now uses `intelligent_search()` function
   - ✅ **Fixed:** Added proper scrapers directory to Python path
   - ✅ **Fixed:** All imports now work correctly

### 2. **display_api.py Issues Fixed:**
   - ❌ Running on separate port (5002) causing confusion
   - ❌ Duplicate functionality with smart_ecommerce_api.py
   - ❌ No actual scraping capability
   - ✅ **Fixed:** Merged into unified API on single port (5000)
   - ✅ **Fixed:** Combined display and search functionality
   - ✅ **Fixed:** Single source of truth for all operations

### 3. **General Issues Fixed:**
   - ❌ Two separate APIs causing workflow confusion
   - ❌ Import path issues with scrapers
   - ❌ Inconsistent error handling
   - ✅ **Fixed:** Single unified API with clear workflow
   - ✅ **Fixed:** Proper error handling throughout
   - ✅ **Fixed:** Better logging and status reporting

## 🚀 Quick Start

### Option 1: Using Batch File (Windows - Recommended)
```batch
start_unified_api.bat
```

### Option 2: Using Python Script
```bash
python start_unified_api.py
```

### Option 3: Direct Launch
```bash
python unified_ecommerce_api.py
```

## 🌐 Access the API

Once started, the API is available at:
- **Main URL:** http://127.0.0.1:5000
- **Documentation:** http://127.0.0.1:5000 (Beautiful web interface)

## 📍 Complete API Endpoints

### 1. **Search Products (Main Endpoint)**
```
GET /search?q=<query>&platforms=<platforms>&force_refresh=<bool>
POST /search (JSON body)
```

**Example:**
```bash
# Search all platforms
http://127.0.0.1:5000/search?q=laptop

# Search specific platforms
http://127.0.0.1:5000/search?q=smartphone&platforms=amazon,flipkart

# Force fresh scraping (bypass cache)
http://127.0.0.1:5000/search?q=shoes&force_refresh=true
```

**JSON POST Example:**
```json
{
  "query": "phones",
  "platforms": ["amazon", "flipkart"],
  "force_refresh": false
}
```

### 2. **Platform-Specific Search**
```
GET /search/<platform>?q=<query>&force_refresh=<bool>
```

**Example:**
```bash
http://127.0.0.1:5000/search/amazon?q=iphone
http://127.0.0.1:5000/search/flipkart?q=laptop
http://127.0.0.1:5000/search/myntra?q=shoes
http://127.0.0.1:5000/search/meesho?q=dress
```

### 3. **Status & Management**
```
GET  /status           # API and MongoDB status
GET  /cache/stats      # Cache statistics
POST /cache/clear      # Clear all cached data
GET  /products/all     # Get all cached products
```

## 🔄 Smart Workflow

```
User Search Request
        ↓
1. Check MongoDB Cache (24h validity)
        ↓
   ┌────┴────┐
   ↓         ↓
FOUND    NOT FOUND
   ↓         ↓
Return    Scrape from
Cached    E-commerce Sites
Results   (Amazon, Flipkart, etc.)
   ↓         ↓
   └────→  Save to MongoDB
            ↓
         Return Results
```

## 🎯 Key Features

### ✨ Unified Features
1. **Single API:** One port, one service, simplified architecture
2. **Intelligent Caching:** MongoDB Atlas with 24-hour expiry
3. **Cache-First Strategy:** Instant results for repeated searches
4. **Auto-Scraping:** Fresh data when cache misses
5. **Force Refresh:** Bypass cache when needed
6. **Multi-Platform:** Amazon, Flipkart, Myntra, Meesho
7. **Unified Format:** Consistent JSON across all sources
8. **Performance Tracking:** Cache hits, timing, source info

### 🔧 Technical Improvements
- Fixed scraper import paths
- Added proper sys.path configuration
- Merged duplicate functionalities
- Improved error handling
- Better logging system
- Single MongoDB connection
- Graceful shutdown handling

## 📊 Response Format

### Successful Search Response
```json
{
  "success": true,
  "query": "laptop",
  "total_results": 25,
  "source": "mixed (cache + web_scraping)",
  "cache_hits": 2,
  "fresh_searches": 2,
  "processing_time": "15.3s",
  "timestamp": "2025-10-19T12:30:00",
  "mongodb_status": "connected",
  "results": [
    {
      "site": "Amazon",
      "query": "laptop",
      "total_products": 10,
      "basic_products": [...],
      "detailed_products": [...]
    },
    {
      "site": "Flipkart",
      "query": "laptop",
      "total_products": 8,
      "basic_products": [...],
      "detailed_products": [...]
    }
  ]
}
```

### Source Types
- `"mongodb_cache"` - All results from cache (Fast!)
- `"web_scraping"` - All results freshly scraped
- `"mixed (cache + web_scraping)"` - Some cached, some fresh

## 🎨 Web Interface

Visit http://127.0.0.1:5000 in your browser for:
- Beautiful, modern UI
- Complete API documentation
- Live test links
- Status indicators
- Workflow visualization
- Quick test buttons

## 🧪 Testing Examples

### Test 1: Basic Search
```bash
curl "http://127.0.0.1:5000/search?q=smartphone"
```

### Test 2: Platform-Specific
```bash
curl "http://127.0.0.1:5000/search/amazon?q=iphone"
```

### Test 3: Force Refresh
```bash
curl "http://127.0.0.1:5000/search?q=laptop&force_refresh=true"
```

### Test 4: Check Status
```bash
curl "http://127.0.0.1:5000/status"
```

### Test 5: View Cache Stats
```bash
curl "http://127.0.0.1:5000/cache/stats"
```

### Test 6: Get All Products
```bash
curl "http://127.0.0.1:5000/products/all"
```

## 📦 Requirements

Make sure you have these installed:
```bash
pip install flask flask-cors pymongo certifi selenium
```

Or install from requirements file:
```bash
pip install -r scrapers/requirements.txt
```

## 🔐 MongoDB Configuration

The API uses MongoDB Atlas for caching. Configuration is in the code:
- **Connection:** Automatic on startup
- **Database:** `ecommerce_search_db`
- **Collection:** `search_results`
- **Cache Duration:** 24 hours
- **Fallback:** Works without MongoDB (NO-CACHE mode)

## 🐛 Troubleshooting

### Issue: API won't start
**Solution:** Check if port 5000 is available
```bash
# Windows
netstat -ano | findstr :5000

# Kill process if needed (replace PID)
taskkill /PID <PID> /F
```

### Issue: MongoDB connection failed
**Solution:** API works fine without MongoDB (NO-CACHE mode)
- All searches will be fresh (no caching)
- Check internet connection
- Verify MongoDB credentials

### Issue: Scraper import errors
**Solution:** 
- Ensure scrapers folder exists
- Check scrapers contain required search functions
- Verify Python path is correct

### Issue: Slow responses
**Solution:**
- First search is always slower (scraping)
- Subsequent searches use cache (much faster)
- Use `force_refresh=false` for cached results

## 📈 Performance

| Operation | First Request | Cached Request |
|-----------|--------------|----------------|
| Single Platform | 10-15 seconds | < 0.5 seconds |
| All Platforms | 30-60 seconds | < 1 second |
| Status Check | < 0.1 seconds | < 0.1 seconds |

## 🔒 Security Notes

- API runs on localhost (127.0.0.1) only
- CORS enabled for frontend integration
- MongoDB credentials in code (for development)
- For production: Use environment variables

## 🎓 Advanced Usage

### Custom Platform Selection
```bash
# Only specific platforms
curl "http://127.0.0.1:5000/search?q=phone&platforms=amazon,flipkart"
```

### Cache Management
```bash
# View cache statistics
curl "http://127.0.0.1:5000/cache/stats"

# Clear all cache
curl -X POST "http://127.0.0.1:5000/cache/clear"
```

### JSON POST Requests
```python
import requests

response = requests.post('http://127.0.0.1:5000/search', json={
    'query': 'laptop',
    'platforms': ['amazon', 'flipkart'],
    'force_refresh': False
})

print(response.json())
```

## 📝 Migration from Old APIs

### Before (2 APIs):
- **Port 5000:** smart_ecommerce_api.py (search & cache)
- **Port 5002:** display_api.py (display only)
- ❌ Confusing workflow
- ❌ Duplicate code
- ❌ Import errors

### After (1 API):
- **Port 5000:** unified_ecommerce_api.py (all-in-one)
- ✅ Single service
- ✅ Clear workflow
- ✅ Fixed imports
- ✅ Better performance

## 🤝 Support

If you encounter any issues:
1. Check the logs: `unified_ecommerce_api.log`
2. Verify MongoDB connection
3. Test with simple queries first
4. Check scraper functionality individually

## 🎉 Summary

The Unified Smart E-commerce API provides:
- ✅ **One API** instead of two
- ✅ **Fixed imports** for scrapers
- ✅ **Working search** with real data
- ✅ **Intelligent caching** with MongoDB
- ✅ **Beautiful documentation** interface
- ✅ **Complete error handling**
- ✅ **Performance tracking**

**Start using it now:**
```bash
python start_unified_api.py
# or
start_unified_api.bat
```

Visit: http://127.0.0.1:5000

Happy Searching! 🚀


