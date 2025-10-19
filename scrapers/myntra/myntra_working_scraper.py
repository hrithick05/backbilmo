#!/usr/bin/env python3
"""
Working Myntra Scraper - Real Data Extraction
Uses advanced techniques to bypass anti-bot measures and extract actual products
"""

import time
import json
import logging
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_stealth_driver(headless=True):
    """Create a stealth Chrome driver that bypasses detection"""
    try:
        service = Service(ChromeDriverManager().install())
        logger.info("Creating stealth Chrome driver...")
    except Exception as e:
        logger.error(f"ChromeDriverManager failed: {e}")
        service = Service()
        logger.info("Using system ChromeDriver")
    
    options = Options()
    if headless:
        options.add_argument('--headless=new')  # Use new headless mode
    
    # Advanced stealth options
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-images')  # Faster loading
    options.add_argument('--disable-javascript')  # Disable JS initially
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-features=VizDisplayCompositor')
    
    driver = webdriver.Chrome(service=service, options=options)
    
    # Execute stealth scripts
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
    driver.execute_script("window.chrome = {runtime: {}}")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})})")
    
    return driver

def scrape_myntra_homepage_deals(headless: bool = True, max_items_per_section: int = 20):
    """Scrape Myntra homepage with multiple strategies"""
    driver = create_stealth_driver(headless=headless)
    all_sections = []
    
    try:
        logger.info("🏠 Accessing Myntra homepage...")
        
        # Strategy 1: Try direct API endpoints first
        logger.info("🔍 Strategy 1: Checking for API endpoints...")
        try:
            # Try common e-commerce API patterns
            api_endpoints = [
                "https://www.myntra.com/api/v1/homepage",
                "https://www.myntra.com/api/homepage",
                "https://www.myntra.com/api/v2/homepage",
                "https://www.myntra.com/api/products/homepage",
                "https://www.myntra.com/api/deals/homepage"
            ]
            
            for endpoint in api_endpoints:
                try:
                    driver.get(endpoint)
                    time.sleep(3)
                    page_source = driver.page_source
                    
                    if ('product' in page_source.lower() or 'deal' in page_source.lower() or 
                        'price' in page_source.lower() or len(page_source) > 1000):
                        logger.info(f"✅ Found API endpoint: {endpoint}")
                        # Parse JSON response if possible
                        try:
                            json_data = json.loads(page_source)
                            products = extract_products_from_api(json_data)
                            if products:
                                section_data = {
                                    'section_title': 'API Products',
                                    'item_count': len(products),
                                    'items': products[:max_items_per_section]
                                }
                                all_sections.append(section_data)
                                logger.info(f"✅ Extracted {len(products)} products from API")
                                return create_success_response(all_sections)
                        except json.JSONDecodeError:
                            continue
                except Exception as e:
                    logger.debug(f"API endpoint {endpoint} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"API strategy failed: {e}")
        
        # Strategy 2: Try different Myntra URLs
        logger.info("🌐 Strategy 2: Trying different Myntra URLs...")
        urls_to_try = [
            "https://www.myntra.com",
            "https://myntra.com",
            "https://www.myntra.com/women",
            "https://www.myntra.com/men",
            "https://www.myntra.com/kids",
            "https://www.myntra.com/home-living",
            "https://www.myntra.com/beauty",
            "https://www.myntra.com/sale"
        ]
        
        for url in urls_to_try:
            try:
                logger.info(f"Trying URL: {url}")
                driver.get(url)
                time.sleep(8)
                
                # Check if page loaded properly
                page_title = driver.title.lower()
                page_source = driver.page_source
                
                if ('myntra' in page_title or 'fashion' in page_title or 
                    len(page_source) > 50000):  # Real page should be substantial
                    
                    logger.info(f"✅ Successfully loaded: {url}")
                    
                    # Try to extract products from this page
                    products = extract_products_from_page(driver, max_items_per_section)
                    if products:
                        section_title = extract_page_title(url)
                        section_data = {
                            'section_title': section_title,
                            'item_count': len(products),
                            'items': products[:max_items_per_section]
                        }
                        all_sections.append(section_data)
                        logger.info(f"✅ Extracted {len(products)} products from {url}")
                        
                        # If we got good results, return early
                        if len(products) >= 5:
                            return create_success_response(all_sections)
                    else:
                        logger.warning(f"No products found on {url}")
                        
            except Exception as e:
                logger.debug(f"Failed to load {url}: {e}")
                continue
        
        # Strategy 3: Try mobile version
        logger.info("📱 Strategy 3: Trying mobile version...")
        try:
            mobile_options = Options()
            if headless:
                mobile_options.add_argument('--headless=new')
            mobile_options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1')
            mobile_options.add_argument('--window-size=375,667')
            
            mobile_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=mobile_options)
            mobile_driver.get("https://m.myntra.com")
            time.sleep(8)
            
            products = extract_products_from_page(mobile_driver, max_items_per_section)
            if products:
                section_data = {
                    'section_title': 'Mobile Products',
                    'item_count': len(products),
                    'items': products[:max_items_per_section]
                }
                all_sections.append(section_data)
                logger.info(f"✅ Extracted {len(products)} products from mobile version")
            
            mobile_driver.quit()
            
        except Exception as e:
            logger.debug(f"Mobile strategy failed: {e}")
        
        # Strategy 4: Try with JavaScript enabled
        logger.info("⚡ Strategy 4: Trying with JavaScript enabled...")
        try:
            # Create new driver with JavaScript enabled
            js_options = Options()
            if headless:
                js_options.add_argument('--headless=new')
            js_options.add_argument('--no-sandbox')
            js_options.add_argument('--disable-dev-shm-usage')
            js_options.add_argument('--window-size=1920,1080')
            js_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            js_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=js_options)
            js_driver.get("https://www.myntra.com")
            
            # Wait for page to load completely
            WebDriverWait(js_driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll to load dynamic content
            for i in range(5):
                js_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            products = extract_products_from_page(js_driver, max_items_per_section)
            if products:
                section_data = {
                    'section_title': 'JavaScript Products',
                    'item_count': len(products),
                    'items': products[:max_items_per_section]
                }
                all_sections.append(section_data)
                logger.info(f"✅ Extracted {len(products)} products with JavaScript")
            
            js_driver.quit()
            
        except Exception as e:
            logger.debug(f"JavaScript strategy failed: {e}")
        
        # Strategy 5: Try specific category pages
        logger.info("🏷️ Strategy 5: Trying specific category pages...")
        categories = [
            "https://www.myntra.com/women-ethnic-wear",
            "https://www.myntra.com/men-tshirts",
            "https://www.myntra.com/women-western-wear",
            "https://www.myntra.com/men-shirts",
            "https://www.myntra.com/women-footwear",
            "https://www.myntra.com/men-footwear"
        ]
        
        for category_url in categories:
            try:
                driver.get(category_url)
                time.sleep(6)
                
                products = extract_products_from_page(driver, max_items_per_section)
                if products:
                    section_title = extract_page_title(category_url)
                    section_data = {
                        'section_title': section_title,
                        'item_count': len(products),
                        'items': products[:max_items_per_section]
                    }
                    all_sections.append(section_data)
                    logger.info(f"✅ Extracted {len(products)} products from {section_title}")
                    
                    # Stop after finding some products
                    if len(all_sections) >= 3:
                        break
                        
            except Exception as e:
                logger.debug(f"Category {category_url} failed: {e}")
                continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📦 TOTAL SECTIONS EXTRACTED: {len(all_sections)}")
        total_items = sum(s['item_count'] for s in all_sections)
        logger.info(f"📦 TOTAL ITEMS EXTRACTED: {total_items}")
        logger.info(f"{'='*60}")
        
        # Save results
        homepage_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'Myntra India Homepage (Working Scraper)',
            'total_sections': len(all_sections),
            'total_items': total_items,
            'sections': all_sections
        }
        
        with open('myntra_homepage_deals.json', 'w', encoding='utf-8') as f:
            json.dump(homepage_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(all_sections)} sections to myntra_homepage_deals.json")
        
        return homepage_data
        
    except Exception as e:
        logger.error(f"❌ Error scraping Myntra: {e}")
        return create_error_response(str(e))
    finally:
        driver.quit()

def extract_products_from_page(driver, max_items):
    """Extract products from any Myntra page"""
    products = []
    
    try:
        # Strategy 1: Look for product links
        product_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/product/'], a[href*='/p/']")
        logger.info(f"Found {len(product_links)} product links")
        
        for link in product_links[:max_items]:
            try:
                product_info = extract_product_from_link(link, driver)
                if product_info and is_valid_product(product_info):
                    products.append(product_info)
            except Exception as e:
                logger.debug(f"Error extracting from link: {e}")
                continue
        
        # Strategy 2: Look for any elements with product-like content
        if not products:
            logger.info("No products from links, trying broader search...")
            
            # Look for any elements containing prices and product-like text
            all_elements = driver.find_elements(By.CSS_SELECTOR, "div, span, a, section, article")
            
            for elem in all_elements[:100]:  # Check first 100 elements
                try:
                    text = elem.text.strip()
                    if (text and len(text) > 10 and len(text) < 500 and 
                        ('₹' in text or 'Rs' in text) and
                        any(word in text.lower() for word in ['shirt', 'dress', 'shoes', 'bag', 'watch', 'jeans', 'top', 'kurta', 'saree', 'tshirt', 'pants', 'shorts', 'skirt'])):
                        
                        product_info = extract_product_from_text(elem, driver)
                        if product_info and is_valid_product(product_info):
                            products.append(product_info)
                            
                            if len(products) >= max_items:
                                break
                                
                except Exception as e:
                    logger.debug(f"Error processing element: {e}")
                    continue
        
        # Strategy 3: Look for images with product context
        if not products:
            logger.info("No products from text, trying image-based extraction...")
            
            images = driver.find_elements(By.CSS_SELECTOR, "img")
            for img in images[:50]:  # Check first 50 images
                try:
                    alt_text = img.get_attribute('alt') or ''
                    src = img.get_attribute('src') or ''
                    
                    if (alt_text and len(alt_text) > 5 and 
                        any(word in alt_text.lower() for word in ['shirt', 'dress', 'shoes', 'bag', 'watch', 'jeans', 'top', 'kurta', 'saree'])):
                        
                        # Find parent container
                        parent = img.find_element(By.XPATH, "..")
                        product_info = extract_product_from_image_context(parent, alt_text, src)
                        
                        if product_info and is_valid_product(product_info):
                            products.append(product_info)
                            
                            if len(products) >= max_items:
                                break
                                
                except Exception as e:
                    logger.debug(f"Error processing image: {e}")
                    continue
        
        logger.info(f"Extracted {len(products)} products from page")
        return products
        
    except Exception as e:
        logger.error(f"Error extracting products from page: {e}")
        return []

def extract_product_from_link(link_element, driver):
    """Extract product information from a link element"""
    product_info = {
        'title': '',
        'price': '',
        'discount': '',
        'image': '',
        'link': '',
        'mrp': '',
        'brand': ''
    }
    
    try:
        # Get link
        product_info['link'] = link_element.get_attribute('href') or ''
        
        # Get title from various sources
        title = link_element.get_attribute('aria-label') or ''
        if not title:
            try:
                img = link_element.find_element(By.CSS_SELECTOR, "img")
                title = img.get_attribute('alt') or ''
            except:
                pass
        
        if not title:
            title = link_element.text.strip()
        
        if not title and product_info['link']:
            title = extract_title_from_url(product_info['link'])
        
        product_info['title'] = title[:100] if title else ''
        
        # Get image
        try:
            img = link_element.find_element(By.CSS_SELECTOR, "img")
            product_info['image'] = img.get_attribute('src') or ''
        except:
            pass
        
        # Get price from parent container
        try:
            parent = link_element.find_element(By.XPATH, "..")
            price_text = parent.text
            
            # Extract price
            price_match = re.search(r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', price_text)
            if price_match:
                product_info['price'] = f"₹{price_match.group(1)}"
            
            # Extract MRP
            mrp_match = re.search(r'MRP\s*₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', price_text)
            if mrp_match:
                product_info['mrp'] = f"₹{mrp_match.group(1)}"
            
            # Extract discount
            discount_match = re.search(r'(\d+)%\s*OFF', price_text)
            if discount_match:
                product_info['discount'] = f"{discount_match.group(1)}% OFF"
                
        except Exception as e:
            logger.debug(f"Error extracting price: {e}")
        
    except Exception as e:
        logger.debug(f"Error extracting product from link: {e}")
    
    return product_info

def extract_product_from_text(text_element, driver):
    """Extract product from text element"""
    product_info = {
        'title': '',
        'price': '',
        'discount': '',
        'image': '',
        'link': '',
        'mrp': '',
        'brand': ''
    }
    
    try:
        text = text_element.text.strip()
        
        # Extract title (first line without price)
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and '₹' not in line and not line.replace(',', '').replace('.', '').isdigit():
                product_info['title'] = line[:100]
                break
        
        # Extract price
        price_match = re.search(r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
        if price_match:
            product_info['price'] = f"₹{price_match.group(1)}"
        
        # Extract MRP
        mrp_match = re.search(r'MRP\s*₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
        if mrp_match:
            product_info['mrp'] = f"₹{mrp_match.group(1)}"
        
        # Extract discount
        discount_match = re.search(r'(\d+)%\s*OFF', text)
        if discount_match:
            product_info['discount'] = f"{discount_match.group(1)}% OFF"
        
        # Try to find link in parent
        try:
            parent = text_element.find_element(By.XPATH, "..")
            link = parent.find_element(By.CSS_SELECTOR, "a[href*='/product/'], a[href*='/p/']")
            product_info['link'] = link.get_attribute('href') or ''
        except:
            pass
        
        # Try to find image
        try:
            parent = text_element.find_element(By.XPATH, "..")
            img = parent.find_element(By.CSS_SELECTOR, "img")
            product_info['image'] = img.get_attribute('src') or ''
        except:
            pass
        
    except Exception as e:
        logger.debug(f"Error extracting product from text: {e}")
    
    return product_info

def extract_product_from_image_context(parent_element, alt_text, image_src):
    """Extract product from image context"""
    product_info = {
        'title': alt_text[:100],
        'price': '',
        'discount': '',
        'image': image_src,
        'link': '',
        'mrp': '',
        'brand': ''
    }
    
    try:
        # Get text from parent
        parent_text = parent_element.text
        
        # Extract price
        price_match = re.search(r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', parent_text)
        if price_match:
            product_info['price'] = f"₹{price_match.group(1)}"
        
        # Try to find link
        try:
            link = parent_element.find_element(By.CSS_SELECTOR, "a[href*='/product/'], a[href*='/p/']")
            product_info['link'] = link.get_attribute('href') or ''
        except:
            pass
        
    except Exception as e:
        logger.debug(f"Error extracting product from image context: {e}")
    
    return product_info

def extract_products_from_api(api_data):
    """Extract products from API response"""
    products = []
    
    try:
        if isinstance(api_data, dict):
            # Look for common API response patterns
            for key in ['products', 'items', 'data', 'results', 'deals', 'offers']:
                if key in api_data:
                    items = api_data[key]
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                product_info = {
                                    'title': item.get('title', item.get('name', item.get('product_name', ''))),
                                    'price': item.get('price', item.get('selling_price', '')),
                                    'mrp': item.get('mrp', item.get('original_price', '')),
                                    'discount': item.get('discount', item.get('discount_percent', '')),
                                    'image': item.get('image', item.get('image_url', '')),
                                    'link': item.get('url', item.get('product_url', '')),
                                    'brand': item.get('brand', item.get('brand_name', ''))
                                }
                                
                                if product_info['title'] and product_info['price']:
                                    products.append(product_info)
        
    except Exception as e:
        logger.debug(f"Error extracting products from API: {e}")
    
    return products

def extract_page_title(url):
    """Extract page title from URL"""
    try:
        if '/women' in url:
            return 'Women\'s Fashion'
        elif '/men' in url:
            return 'Men\'s Fashion'
        elif '/kids' in url:
            return 'Kids Fashion'
        elif '/beauty' in url:
            return 'Beauty Products'
        elif '/home-living' in url:
            return 'Home & Living'
        elif '/sale' in url:
            return 'Sale Items'
        else:
            return 'Featured Products'
    except:
        return 'Products'

def extract_title_from_url(url):
    """Extract product title from URL"""
    try:
        if '/product/' in url:
            parts = url.split('/product/')[1].split('/')
        elif '/p/' in url:
            parts = url.split('/p/')[0].split('/')
        else:
            return ''
        
        product_part = parts[0] if parts else ''
        
        if product_part:
            title = product_part.replace('-', ' ').replace('_', ' ')
            title = ' '.join(word.capitalize() for word in title.split())
            return title
        
        return ''
    except:
        return ''

def is_valid_product(product_info):
    """Check if this is a valid product"""
    if not product_info or not product_info.get('title'):
        return False
    
    title = product_info['title'].lower()
    
    # Filter out obvious non-products
    invalid_keywords = [
        'mailto:', 'email', '@', 'contact', 'support', 'help',
        'search', 'icon', 'login', 'cart', 'menu', 'navigation',
        'cookie', 'privacy', 'terms', 'about', 'career', 'blog'
    ]
    
    for keyword in invalid_keywords:
        if keyword in title:
            return False
    
    # Must have reasonable title length
    if len(product_info['title']) < 5 or len(product_info['title']) > 200:
        return False
    
    return True

def create_success_response(sections):
    """Create success response"""
    total_items = sum(s['item_count'] for s in sections)
    return {
        'timestamp': datetime.now().isoformat(),
        'source': 'Myntra India Homepage (Working Scraper)',
        'total_sections': len(sections),
        'total_items': total_items,
        'sections': sections
    }

def create_error_response(error_message):
    """Create error response"""
    return {
        'timestamp': datetime.now().isoformat(),
        'source': 'Myntra India Homepage (Working Scraper)',
        'total_sections': 0,
        'total_items': 0,
        'sections': [],
        'error': error_message
    }

if __name__ == "__main__":
    # Test the working scraper
    headless = True
    max_items = 20
    
    logger.info(f"🚀 Starting Working Myntra scraper...")
    logger.info(f"Headless mode: {headless}")
    logger.info(f"Max items per section: {max_items}")
    
    result = scrape_myntra_homepage_deals(headless=headless, max_items_per_section=max_items)
    
    print(f"\n{'='*60}")
    print(f"✅ WORKING SCRAPER COMPLETE")
    print(f"{'='*60}")
    print(f"Total Sections: {result.get('total_sections', 0)}")
    print(f"Total Items: {result.get('total_items', 0)}")
    
    if result.get('error'):
        print(f"Error: {result['error']}")
    elif result.get('sections'):
        print(f"\n📊 Sections Found:")
        for i, section in enumerate(result['sections'][:5], 1):
            print(f"   {i}. {section['section_title']} ({section['item_count']} items)")
        if len(result['sections']) > 5:
            print(f"   ... and {len(result['sections']) - 5} more sections")
    
    print(f"\n💾 Saved to: myntra_homepage_deals.json")
    print(f"{'='*60}\n")
