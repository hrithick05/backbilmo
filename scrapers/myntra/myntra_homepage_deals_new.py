#!/usr/bin/env python3
"""
Enhanced Myntra Homepage Deals Scraper
Uses modern selectors and comprehensive extraction strategies
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
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_driver(headless=True):
    """Create and configure Chrome WebDriver with enhanced options"""
    try:
        service = Service(ChromeDriverManager().install())
        logger.info("Myntra Enhanced WebDriver initialized with ChromeDriverManager")
    except Exception as e:
        logger.error(f"ChromeDriverManager failed: {e}")
        service = Service()
        logger.info("Myntra Enhanced WebDriver initialized with system ChromeDriver")
    
    options = Options()
    if headless:
        options.add_argument('--headless')
    
    # Enhanced options for better compatibility and stealth
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=service, options=options)
    
    # Enhanced stealth scripts
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
    driver.execute_script("window.chrome = {runtime: {}}")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    
    return driver

def scrape_myntra_homepage_deals(headless: bool = True, max_items_per_section: int = 20):
    """Enhanced Myntra homepage scraper with multiple extraction strategies"""
    driver = create_driver(headless=headless)
    all_sections = []
    
    try:
        logger.info("🏠 Visiting Myntra India homepage...")
        
        # Try multiple URLs in case of redirects
        urls_to_try = [
            "https://www.myntra.com",
            "https://www.myntra.com/",
            "https://myntra.com",
            "https://myntra.com/"
        ]
        
        page_loaded = False
        for url in urls_to_try:
            try:
                logger.info(f"Trying URL: {url}")
                driver.get(url)
                time.sleep(8)
                
                # Check if we got the actual Myntra page
                page_title = driver.title.lower()
                page_source = driver.page_source.lower()
                
                if ('myntra' in page_title or 'fashion' in page_title or 
                    'myntra' in page_source or 'product' in page_source or
                    len(page_source) > 10000):  # Real page should be large
                    logger.info(f"✅ Successfully loaded Myntra page from {url}")
                    page_loaded = True
                    break
                else:
                    logger.warning(f"❌ Got error page from {url}: {page_title}")
                    
            except Exception as e:
                logger.warning(f"❌ Failed to load {url}: {e}")
                continue
        
        if not page_loaded:
            logger.error("❌ Failed to load Myntra homepage from any URL")
            return create_error_response("Failed to load Myntra homepage")
        
        # Enhanced page loading strategy
        logger.info("📜 Enhanced scrolling and loading...")
        
        # Wait for initial content
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Progressive scrolling to load content
        scroll_heights = [500, 1000, 1500, 2000, 2500, 3000]
        for height in scroll_heights:
            driver.execute_script(f"window.scrollTo(0, {height});")
            time.sleep(2)
        
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)
        
        logger.info("🔍 Starting comprehensive product extraction...")
        
        # Strategy 1: Modern React/Vue component selectors
        logger.info("🎯 Strategy 1: Modern component selectors...")
        modern_selectors = [
            # React component patterns
            "div[class*='ProductCard']",
            "div[class*='ProductCardBase']", 
            "div[class*='ProductTile']",
            "div[class*='ProductTileBase']",
            "div[class*='ProductBase']",
            "div[class*='Product']",
            
            # Generic product containers
            "div[class*='product']",
            "div[class*='item']",
            "div[class*='card']",
            "div[class*='tile']",
            "div[class*='deal']",
            "div[class*='offer']",
            
            # Data attributes
            "[data-testid*='product']",
            "[data-testid*='Product']",
            "[data-testid*='item']",
            "[data-testid*='card']",
            
            # Link-based selectors
            "a[href*='/product/']",
            "a[href*='/p/']",
            "a[href*='/dp/']",
            
            # Generic containers that might hold products
            "div[class*='container']",
            "div[class*='section']",
            "div[class*='grid']",
            "div[class*='list']"
        ]
        
        products_found = 0
        sections_found = {}
        
        for selector in modern_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"   Found {len(elements)} elements with selector: {selector}")
                
                if elements:
                    for elem in elements[:10]:  # Check first 10 elements
                        try:
                            products = extract_products_from_element(elem, driver)
                            if products:
                                section_title = extract_section_title(elem) or "Featured Products"
                                
                                if section_title not in sections_found:
                                    sections_found[section_title] = []
                                
                                for product in products:
                                    if is_valid_product(product) and product.get('price'):
                                        sections_found[section_title].append(product)
                                        products_found += 1
                                        
                                        if products_found >= max_items_per_section * 5:  # Limit total
                                            break
                                
                                logger.info(f"   ✅ Extracted {len(products)} products from {selector}")
                                
                        except Exception as e:
                            logger.debug(f"Error processing element: {e}")
                            continue
                            
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        # Strategy 2: Price-based extraction
        logger.info("💰 Strategy 2: Price-based extraction...")
        price_selectors = [
            "span[class*='price']",
            "div[class*='price']",
            "span[class*='Price']", 
            "div[class*='Price']",
            "span[class*='amount']",
            "div[class*='amount']",
            "span[class*='cost']",
            "div[class*='cost']",
            "span[class*='rupee']",
            "div[class*='rupee']",
            "span[class*='rs']",
            "div[class*='rs']",
            "[data-testid*='price']",
            "[data-testid*='Price']"
        ]
        
        for selector in price_selectors:
            try:
                price_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"   Found {len(price_elements)} price elements with selector: {selector}")
                
                for price_elem in price_elements[:20]:  # Check first 20
                    try:
                        price_text = price_elem.text.strip()
                        if is_valid_price(price_text):
                            # Find parent container with product info
                            product_info = extract_product_from_price_element(price_elem, driver)
                            if product_info and is_valid_product(product_info):
                                section_title = extract_section_title(price_elem) or "Price-Based Products"
                                
                                if section_title not in sections_found:
                                    sections_found[section_title] = []
                                
                                sections_found[section_title].append(product_info)
                                products_found += 1
                                
                    except Exception as e:
                        logger.debug(f"Error processing price element: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Error with price selector {selector}: {e}")
                continue
        
        # Strategy 3: Image-based extraction
        logger.info("🖼️ Strategy 3: Image-based extraction...")
        try:
            img_elements = driver.find_elements(By.CSS_SELECTOR, "img[src*='myntra'], img[alt*='product'], img[alt*='Product']")
            logger.info(f"   Found {len(img_elements)} product images")
            
            for img_elem in img_elements[:30]:  # Check first 30
                try:
                    product_info = extract_product_from_image_element(img_elem, driver)
                    if product_info and is_valid_product(product_info) and product_info.get('price'):
                        section_title = extract_section_title(img_elem) or "Image-Based Products"
                        
                        if section_title not in sections_found:
                            sections_found[section_title] = []
                        
                        sections_found[section_title].append(product_info)
                        products_found += 1
                        
                except Exception as e:
                    logger.debug(f"Error processing image element: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error with image extraction: {e}")
        
        # Strategy 4: Text-based extraction (fallback)
        logger.info("📝 Strategy 4: Text-based extraction (fallback)...")
        try:
            # Look for elements containing both product-like text and prices
            all_divs = driver.find_elements(By.CSS_SELECTOR, "div, section, article")
            
            for div in all_divs[:50]:  # Check first 50
                try:
                    text = div.text.strip()
                    if (len(text) > 20 and len(text) < 500 and 
                        ('₹' in text or 'Rs' in text or 'INR' in text) and
                        any(word in text.lower() for word in ['shirt', 'dress', 'shoes', 'bag', 'watch', 'jeans', 'top', 'kurta', 'saree'])):
                        
                        product_info = extract_product_from_text_element(div, driver)
                        if product_info and is_valid_product(product_info):
                            section_title = extract_section_title(div) or "Text-Based Products"
                            
                            if section_title not in sections_found:
                                sections_found[section_title] = []
                            
                            sections_found[section_title].append(product_info)
                            products_found += 1
                            
                except Exception as e:
                    logger.debug(f"Error processing text element: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error with text extraction: {e}")
        
        # Convert sections to final format
        for section_title, products in sections_found.items():
            if products:
                # Remove duplicates based on title and price
                unique_products = []
                seen = set()
                for product in products:
                    key = (product.get('title', ''), product.get('price', ''))
                    if key not in seen and key[0] and key[1]:
                        seen.add(key)
                        unique_products.append(product)
                
                if unique_products:
                    section_data = {
                        'section_title': section_title,
                        'item_count': len(unique_products),
                        'items': unique_products[:max_items_per_section]
                    }
                    all_sections.append(section_data)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📦 TOTAL SECTIONS EXTRACTED: {len(all_sections)}")
        total_items = sum(s['item_count'] for s in all_sections)
        logger.info(f"📦 TOTAL ITEMS EXTRACTED: {total_items}")
        logger.info(f"{'='*60}")
        
        # Save to JSON file
        homepage_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'Myntra India Homepage (Enhanced)',
            'total_sections': len(all_sections),
            'total_items': total_items,
            'sections': all_sections
        }
        
        with open('myntra_homepage_deals.json', 'w', encoding='utf-8') as f:
            json.dump(homepage_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(all_sections)} sections to myntra_homepage_deals.json")
        
        return homepage_data
        
    except Exception as e:
        logger.error(f"❌ Error scraping Myntra homepage: {e}")
        return create_error_response(str(e))
    finally:
        driver.quit()

def extract_products_from_element(element, driver):
    """Extract products from a given element"""
    products = []
    try:
        # Look for product links within this element
        product_links = element.find_elements(By.CSS_SELECTOR, "a[href*='/product/'], a[href*='/p/']")
        
        for link in product_links[:5]:  # Limit to 5 per element
            try:
                product_info = extract_product_info_from_link(link, element)
                if product_info and is_valid_product(product_info):
                    products.append(product_info)
            except:
                continue
                
    except Exception as e:
        logger.debug(f"Error extracting products from element: {e}")
    
    return products

def extract_product_info_from_link(link_element, container):
    """Extract comprehensive product information from a link"""
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
        # Extract link
        product_info['link'] = link_element.get_attribute('href') or ''
        
        # Extract title
        product_info['title'] = extract_title_from_link(link_element, container)
        
        # Extract image
        product_info['image'] = extract_image_from_link(link_element)
        
        # Extract price information
        price_info = extract_price_info_from_container(container)
        product_info.update(price_info)
        
        # Extract brand
        product_info['brand'] = extract_brand_from_container(container)
        
    except Exception as e:
        logger.debug(f"Error extracting product info: {e}")
    
    return product_info

def extract_title_from_link(link_element, container):
    """Extract product title from link and container"""
    title = ''
    
    try:
        # Try aria-label first
        title = link_element.get_attribute('aria-label') or ''
        
        # Try image alt text
        if not title:
            img = link_element.find_element(By.CSS_SELECTOR, "img")
            title = img.get_attribute('alt') or ''
        
        # Try text content
        if not title:
            title = link_element.text.strip()
        
        # Try to find title in nearby elements
        if not title:
            try:
                # Look for title in parent container
                title_elements = container.find_elements(By.CSS_SELECTOR, "span, div, p, h1, h2, h3, h4, h5, h6")
                for elem in title_elements:
                    text = elem.text.strip()
                    if (text and len(text) > 5 and len(text) < 100 and 
                        '₹' not in text and not text.replace(',', '').replace('.', '').isdigit()):
                        title = text
                        break
            except:
                pass
        
        # Extract from URL if still no title
        if not title and product_info.get('link'):
            title = extract_title_from_url(product_info['link'])
        
        # Clean up title
        if title:
            title = re.sub(r'\s+', ' ', title).strip()
            title = title[:100]  # Limit length
        
    except Exception as e:
        logger.debug(f"Error extracting title: {e}")
    
    return title

def extract_image_from_link(link_element):
    """Extract product image from link"""
    try:
        img = link_element.find_element(By.CSS_SELECTOR, "img")
        return img.get_attribute('src') or ''
    except:
        return ''

def extract_price_info_from_container(container):
    """Extract price information from container"""
    price_info = {'price': '', 'mrp': '', 'discount': ''}
    
    try:
        # Get all text from container
        container_text = container.text
        
        # Find price patterns
        price_patterns = [
            r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # ₹1,299.00
            r'Rs\.?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Rs. 1299
            r'INR\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # INR 1299
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*₹'  # 1299 ₹
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, container_text)
            prices.extend(matches)
        
        if prices:
            # Clean and sort prices
            clean_prices = []
            for price in prices:
                try:
                    clean_price = price.replace(',', '').replace('.', '')
                    if clean_price.isdigit() and len(clean_price) >= 3:
                        clean_prices.append(int(clean_price))
                except:
                    continue
            
            if clean_prices:
                clean_prices.sort()
                price_info['price'] = f"₹{clean_prices[-1]:,}"  # Highest price as current price
                
                if len(clean_prices) > 1:
                    price_info['mrp'] = f"₹{clean_prices[0]:,}"  # Lowest as MRP
                    
                    # Calculate discount
                    if clean_prices[0] > clean_prices[-1]:
                        discount = int(((clean_prices[0] - clean_prices[-1]) / clean_prices[0]) * 100)
                        price_info['discount'] = f"{discount}% OFF"
        
        # Look for discount text
        discount_patterns = [
            r'(\d+)%\s*OFF',
            r'(\d+)%\s*off',
            r'(\d+)%\s*OFF',
            r'OFF\s*(\d+)%',
            r'Save\s*(\d+)%'
        ]
        
        for pattern in discount_patterns:
            match = re.search(pattern, container_text, re.IGNORECASE)
            if match:
                price_info['discount'] = f"{match.group(1)}% OFF"
                break
        
    except Exception as e:
        logger.debug(f"Error extracting price info: {e}")
    
    return price_info

def extract_brand_from_container(container):
    """Extract brand from container"""
    try:
        # Look for brand in text
        text = container.text
        brand_patterns = [
            r'Brand:\s*([^\n\r]+)',
            r'by\s+([A-Za-z\s]+)',
            r'([A-Z][a-z]+)\s+[A-Z][a-z]+'  # Simple brand pattern
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, text)
            if match:
                brand = match.group(1).strip()
                if len(brand) > 2 and len(brand) < 50:
                    return brand
        
    except:
        pass
    
    return ''

def extract_product_from_price_element(price_elem, driver):
    """Extract product from price element"""
    try:
        # Find parent container
        current = price_elem
        for _ in range(5):
            try:
                current = current.find_element(By.XPATH, "..")
                # Look for product link in this container
                product_link = current.find_element(By.CSS_SELECTOR, "a[href*='/product/'], a[href*='/p/']")
                return extract_product_info_from_link(product_link, current)
            except:
                continue
    except:
        pass
    
    return None

def extract_product_from_image_element(img_elem, driver):
    """Extract product from image element"""
    try:
        # Find parent container with product link
        current = img_elem
        for _ in range(5):
            try:
                current = current.find_element(By.XPATH, "..")
                # Look for product link in this container
                product_link = current.find_element(By.CSS_SELECTOR, "a[href*='/product/'], a[href*='/p/']")
                return extract_product_info_from_link(product_link, current)
            except:
                continue
    except:
        pass
    
    return None

def extract_product_from_text_element(text_elem, driver):
    """Extract product from text element"""
    try:
        # Look for product link in this element
        product_link = text_elem.find_element(By.CSS_SELECTOR, "a[href*='/product/'], a[href*='/p/']")
        return extract_product_info_from_link(product_link, text_elem)
    except:
        pass
    
    return None

def extract_section_title(element):
    """Extract section title from element"""
    try:
        # Walk up DOM to find section title
        current = element
        for _ in range(10):
            try:
                # Look for headings in current element
                headings = current.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, span, div")
                for heading in headings:
                    text = heading.text.strip()
                    if (text and len(text) > 3 and len(text) < 100 and
                        '₹' not in text and not text.replace(',', '').replace('.', '').isdigit()):
                        return text
                
                current = current.find_element(By.XPATH, "..")
            except:
                break
        
        return "Featured Products"
    except:
        return "Featured Products"

def extract_title_from_url(url):
    """Extract product title from Myntra URL"""
    try:
        if not url or ('/product/' not in url and '/p/' not in url):
            return ''
        
        # Extract product name from URL
        if '/product/' in url:
            parts = url.split('/product/')[1].split('/')
        else:
            parts = url.split('/p/')[0].split('/')
        
        product_part = parts[0] if parts else ''
        
        if product_part:
            # Clean up the product name
            title = product_part.replace('-', ' ').replace('_', ' ')
            title = ' '.join(word.capitalize() for word in title.split())
            return title
        
        return ''
    except:
        return ''

def is_valid_price(price_text):
    """Check if text represents a valid price"""
    if not price_text:
        return False
    
    # Must contain currency symbol or be a number
    if not any(symbol in price_text for symbol in ['₹', 'Rs', 'INR']):
        # Check if it's just a number
        clean_text = price_text.replace(',', '').replace('.', '').strip()
        if not clean_text.isdigit():
            return False
    
    # Must have reasonable length
    if len(price_text) < 3 or len(price_text) > 20:
        return False
    
    # Extract numbers
    numbers = re.findall(r'\d+', price_text)
    if not numbers:
        return False
    
    # Check if any number is reasonable price (between 100 and 100000)
    for num in numbers:
        try:
            price_num = int(num.replace(',', ''))
            if 100 <= price_num <= 100000:
                return True
        except:
            continue
    
    return False

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

def create_error_response(error_message):
    """Create error response"""
    return {
        'timestamp': datetime.now().isoformat(),
        'source': 'Myntra India Homepage (Enhanced)',
        'total_sections': 0,
        'total_items': 0,
        'sections': [],
        'error': error_message
    }

if __name__ == "__main__":
    # Test the enhanced scraper
    headless = True
    max_items = 20
    
    logger.info(f"🚀 Starting Enhanced Myntra homepage deals scraper...")
    logger.info(f"Headless mode: {headless}")
    logger.info(f"Max items per section: {max_items}")
    
    result = scrape_myntra_homepage_deals(headless=headless, max_items_per_section=max_items)
    
    print(f"\n{'='*60}")
    print(f"✅ ENHANCED SCRAPING COMPLETE")
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
