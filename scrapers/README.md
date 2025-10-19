# Bilmo Scrapers Collection

This folder contains all the working scrapers organized by platform and functionality. Each scraper is designed to extract product information, deals, and flight data from various e-commerce and travel websites.

## 📁 Folder Structure

```
scrapers/
├── amazon/           # Amazon scrapers
├── flipkart/         # Flipkart scrapers  
├── myntra/           # Myntra scrapers
├── meesho/           # Meesho scrapers
├── flights/          # Flight booking scrapers
├── unified/          # Unified search and API systems
└── README.md         # This file
```

## 🛒 E-commerce Scrapers

### Amazon Scrapers (`amazon/`)
- **`amazon_search.py`** - Search products on Amazon India
- **`amazon_homepage_deals.py`** - Scrape deals from Amazon homepage
- **`amazon_homepage_deals.json`** - Sample deals data

**Usage:**
```bash
python amazon_search.py "iphone 15"
python amazon_homepage_deals.py
```

### Flipkart Scrapers (`flipkart/`)
- **`flipkart_search.py`** - Search products on Flipkart
- **`flipkart_homepage_deals.py`** - Scrape deals from Flipkart homepage
- **`flipkart_homepage_deals.json`** - Sample deals data

**Usage:**
```bash
python flipkart_search.py "laptop"
python flipkart_homepage_deals.py
```

### Myntra Scrapers (`myntra/`)
- **`myntra_search.py`** - Search products on Myntra
- **`myntra_working_scraper.py`** - Advanced Myntra scraper with anti-detection
- **`myntra_homepage_deals.py`** - Scrape deals from Myntra homepage
- **`myntra_homepage_deals_new.py`** - Updated Myntra deals scraper

**Usage:**
```bash
python myntra_search.py "puma shoes"
python myntra_working_scraper.py
```

### Meesho Scrapers (`meesho/`)
- **`meesho_search.py`** - Search products on Meesho

**Usage:**
```bash
python meesho_search.py "saree"
```

## ✈️ Flight Scrapers (`flights/`)

### Flight Booking Scrapers
- **`indigo_scraper.py`** - Scrape IndiGo flight prices
- **`google_flights_scraper.py`** - Scrape Google Flights (all airlines)
- **`flightapi.py`** - Multi-airline flight price scraper

**Usage:**
```bash
python indigo_scraper.py
python google_flights_scraper.py
python flightapi.py
```

## 🔄 Unified Search System (`unified/`)

### Core Unified Scrapers
- **`unified_search.py`** - Search all platforms simultaneously
- **`unified_search_all_platforms.py`** - Enhanced unified search
- **`run_unified_search.py`** - Run unified search with CLI
- **`search_products.py`** - Product search interface
- **`real_search_products.py`** - Real-time product search

### Smart API System
- **`smart_api.py`** - Intelligent API with caching
- **`smart_mongodb.py`** - MongoDB integration for caching
- **`smart_api_mongodb_integration.py`** - Complete smart API system
- **`intelligent_search_system.py`** - AI-powered search system

**Usage:**
```bash
python unified_search.py "iphone 15"
python run_unified_search.py
python smart_api.py
```

## 🚀 Quick Start

### Individual Platform Search
```bash
# Search Amazon
cd scrapers/amazon
python amazon_search.py "your search query"

# Search Flipkart  
cd scrapers/flipkart
python flipkart_search.py "your search query"

# Search Myntra
cd scrapers/myntra
python myntra_search.py "your search query"

# Search Meesho
cd scrapers/meesho
python meesho_search.py "your search query"
```

### Unified Search (All Platforms)
```bash
cd scrapers/unified
python unified_search.py "your search query"
```

### Flight Search
```bash
cd scrapers/flights
python google_flights_scraper.py
```

## 📋 Features

### E-commerce Scrapers
- ✅ Product search across multiple platforms
- ✅ Price comparison
- ✅ Product details extraction
- ✅ Image URLs and ratings
- ✅ Deal detection
- ✅ Homepage deals scraping

### Flight Scrapers
- ✅ Multi-airline support
- ✅ Price comparison
- ✅ Route optimization
- ✅ Real-time pricing

### Unified System
- ✅ Cross-platform search
- ✅ Intelligent caching
- ✅ MongoDB integration
- ✅ API endpoints
- ✅ Concurrent processing

## 🛠️ Requirements

All scrapers require:
- Python 3.7+
- Selenium WebDriver
- Chrome/Chromium browser
- Required Python packages (see `requirements.txt`)

## 📊 Data Output

All scrapers output JSON format with:
- Product information
- Prices
- Ratings
- Images
- URLs
- Timestamps

## 🔧 Configuration

Each scraper can be configured for:
- Headless mode
- Custom delays
- User agents
- Proxy settings
- Output formats

## 📝 Notes

- All scrapers include anti-detection measures
- Rate limiting is implemented to avoid blocking
- Error handling and retry mechanisms included
- Logging for debugging and monitoring
- MongoDB caching for improved performance

## 🚨 Important

- Use scrapers responsibly and respect website terms of service
- Implement appropriate delays between requests
- Monitor for changes in website structure
- Keep scrapers updated for best results
