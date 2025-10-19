#!/usr/bin/env python3
"""
Myntra Homepage Deals Scraper
Scrapes deals and products from Myntra India homepage
"""

import time
import json
import logging
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
    """Create and configure Chrome WebDriver"""
    try:
        # Try ChromeDriverManager first
        service = Service(ChromeDriverManager().install())
        logger.info("Myntra Deals WebDriver initialized with ChromeDriverManager")
    except Exception as e:
        logger.error(f"ChromeDriverManager failed: {e}")
        # Fallback to system ChromeDriver
        service = Service()
        logger.info("Myntra Deals WebDriver initialized with system ChromeDriver")
    
    options = Options()
    if headless:
        options.add_argument('--headless')
    
    # Additional options for better compatibility
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=service, options=options)
    
    # Execute scripts to avoid detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
    driver.execute_script("window.chrome = {runtime: {}}")
    
    return driver

def scrape_myntra_homepage_deals(headless: bool = True, max_items_per_section: int = 10):
    """Scrape Myntra homepage focusing on actual product deals with prices"""
    driver = create_driver(headless=headless)
    all_sections = []
    
    try:
        logger.info("🏠 Visiting Myntra India homepage...")
        driver.get("https://www.myntra.com")
        time.sleep(10)  # Wait longer for page to load
        
        # Scroll down to load content
        logger.info("📜 Scrolling to load deals...")
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(5)
        
        logger.info("🔍 Extracting product deals with prices...")
        
        # Strategy 1: Look for actual product cards with images and prices
        logger.info("🛍️ Looking for product cards with images and prices...")
        
        # Find all elements that contain both product links and price text
        all_elements = driver.find_elements(By.CSS_SELECTOR, "div, section, article")
        product_containers = []
        
        for elem in all_elements:
            try:
                # Check if this element has product links
                product_links = elem.find_elements(By.CSS_SELECTOR, "a[href*='/product/'], a[href*='/p/']")
                if not product_links:
                    continue
                
                # Check if this element has price text
                elem_text = elem.text
                has_price = False
                if elem_text and ('₹' in elem_text or 'Rs' in elem_text):
                    # Check if it's a valid price (not just text containing rupee symbol)
                    lines = elem_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and ('₹' in line or 'Rs' in line):
                            # Extract numbers from the line
                            import re
                            numbers = re.findall(r'[\d,]+', line)
                            if numbers and any(len(num.replace(',', '')) >= 2 for num in numbers):
                                has_price = True
                                break
                
                if has_price:
                    product_containers.append(elem)
                    
            except Exception as e:
                logger.debug(f"Error checking element: {e}")
                continue
        
        logger.info(f"   Found {len(product_containers)} containers with products and prices")
        
        sections_found = {}
        
        for container in product_containers[:20]:  # Check first 20 containers
            try:
                # Extract section title
                section_title = extract_section_title_from_card(container)
                if not section_title:
                    section_title = "Featured Products"
                
                # Extract products from this container
                products = []
                product_links = container.find_elements(By.CSS_SELECTOR, "a[href*='/product/'], a[href*='/p/']")
                
                for link in product_links[:max_items_per_section]:
                    product_info = extract_product_info_from_container(link, container)
                    if product_info and is_valid_product(product_info) and product_info.get('price'):
                        products.append(product_info)
                
                if products:
                    if section_title not in sections_found:
                        sections_found[section_title] = []
                    sections_found[section_title].extend(products)
                    logger.info(f"  ✅ Found {len(products)} products with prices in '{section_title}'")
                    
            except Exception as e:
                logger.debug(f"Error processing container: {e}")
                continue
        
        # Strategy 2: Look for specific deal banners and sections
        logger.info("🎯 Looking for deal banners...")
        deal_selectors = [
            "div[class*='banner']",
            "div[class*='promo']",
            "div[class*='offer']",
            "div[class*='deal']",
            "div[class*='flash']",
            "div[class*='sale']"
        ]
        
        for selector in deal_selectors:
            try:
                deal_containers = driver.find_elements(By.CSS_SELECTOR, selector)
                for container in deal_containers[:5]:  # Check first 5
                    products = extract_products_from_deal_container(container, driver, max_items_per_section)
                    if products:
                        section_title = extract_section_title_from_card(container) or "Special Deals"
                        if section_title not in sections_found:
                            sections_found[section_title] = []
                        sections_found[section_title].extend(products)
                        logger.info(f"  ✅ Found {len(products)} products in deal banner '{section_title}'")
            except Exception as e:
                logger.debug(f"Error with deal selector {selector}: {e}")
                continue
        
        # Strategy 3: Direct product link extraction with better price detection
        logger.info("🔗 Extracting direct product links with prices...")
        all_product_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/product/'], a[href*='/p/']")
        logger.info(f"   Found {len(all_product_links)} total product links")
        
        direct_products = {}
        for link in all_product_links[:max_items_per_section * 3]:
            try:
                # Find parent container
                parent_section = find_product_parent_section(link, driver)
                section_title = extract_section_title_from_parent(parent_section) if parent_section else "Direct Products"
                
                product_info = extract_product_info_from_container(link, parent_section)
                if product_info and is_valid_product(product_info) and product_info.get('price'):
                    if section_title not in direct_products:
                        direct_products[section_title] = []
                    direct_products[section_title].append(product_info)
            except Exception as e:
                logger.debug(f"Error processing direct link: {e}")
                continue
        
        # Merge all sections
        for section_title, products in sections_found.items():
            if products:
                section_data = {
                    'section_title': section_title,
                    'item_count': len(products),
                    'items': products[:max_items_per_section]
                }
                all_sections.append(section_data)
        
        for section_title, products in direct_products.items():
            if products and not any(s['section_title'] == section_title for s in all_sections):
                section_data = {
                    'section_title': section_title,
                    'item_count': len(products),
                    'items': products[:max_items_per_section]
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
            'source': 'Myntra India Homepage',
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
        return {
            'timestamp': datetime.now().isoformat(),
            'source': 'Myntra India Homepage',
            'total_deals': 0,
            'deals': [],
            'error': str(e)
        }
    finally:
        driver.quit()

def extract_section_title_from_card(card_element):
    """Extract section title from a product card"""
    try:
        # Look for headings in the card
        heading_selectors = ["h1", "h2", "h3", "h4", "h5", "h6", "span", "div"]
        
        for selector in heading_selectors:
            try:
                headings = card_element.find_elements(By.CSS_SELECTOR, selector)
                for heading in headings:
                    text = heading.text.strip()
                    if text and len(text) > 3 and len(text) < 100:
                        # Skip if it looks like a price
                        if '₹' not in text and not text.replace(',', '').replace('.', '').isdigit():
                            return text
            except:
                continue
        
        return "Featured Products"
    except:
        return "Featured Products"

def find_product_parent_section(link_element, driver):
    """Find the parent section containing the product link"""
    try:
        # Walk up the DOM tree to find a suitable parent
        current = link_element
        for _ in range(10):  # Max 10 levels up
            try:
                current = current.find_element(By.XPATH, "..")
                # Check if this parent has multiple product links
                product_links = current.find_elements(By.CSS_SELECTOR, "a[href*='/product/'], a[href*='/p/']")
                if len(product_links) > 1:
                    return current
            except:
                break
        return None
    except:
        return None

def extract_products_from_deal_container(container, driver, max_items):
    """Extract products from a deal container"""
    products = []
    try:
        # Look for product links in this container
        product_links = container.find_elements(By.CSS_SELECTOR, "a[href*='/product/'], a[href*='/p/']")
        
        for link in product_links[:max_items]:
            product_info = extract_product_info_from_container(link, container)
            if product_info and is_valid_product(product_info):
                products.append(product_info)
                
    except Exception as e:
        logger.debug(f"Error extracting from deal container: {e}")
    
    return products

def extract_section_title_from_parent(parent_element):
    """Extract section title from parent element"""
    if not parent_element:
        return "Products"
    
    try:
        # Look for headings
        heading_selectors = ["h1", "h2", "h3", "h4", "h5", "h6", "span", "div"]
        
        for selector in heading_selectors:
            try:
                headings = parent_element.find_elements(By.CSS_SELECTOR, selector)
                for heading in headings:
                    text = heading.text.strip()
                    if text and len(text) > 3 and len(text) < 100:
                        # Skip if it looks like a price
                        if '₹' not in text and not text.replace(',', '').replace('.', '').isdigit():
                            return text
            except:
                continue
        
        return "Featured Products"
    except:
        return "Featured Products"

def extract_product_info_from_container(link_element, container):
    """Extract product information from a container with enhanced price detection"""
    product_info = {
        'title': '',
        'price': '',
        'discount': '',
        'image': '',
        'link': ''
    }
    
    try:
        # Extract link
        product_info['link'] = link_element.get_attribute('href') or ''
        
        # Extract title from URL first (most reliable)
        if product_info['link']:
            product_info['title'] = extract_title_from_url(product_info['link'])
        
        # If no title from URL, try other methods
        if not product_info['title']:
            title_selectors = [
                # Aria label
                "aria-label",
                # Image alt text
                "img[alt]",
                # Text content
                "span", "div", "p", "h1", "h2", "h3", "h4", "h5", "h6"
            ]
            
            for selector in title_selectors:
                try:
                    if selector == "aria-label":
                        title = link_element.get_attribute('aria-label')
                        if title and len(title) > 5:
                            product_info['title'] = title.strip()
                            break
                    elif selector.startswith("img"):
                        img_elem = link_element.find_element(By.CSS_SELECTOR, selector)
                        title = img_elem.get_attribute('alt')
                        if title and len(title) > 5:
                            product_info['title'] = title.strip()
                            break
                    else:
                        text_elem = link_element.find_element(By.CSS_SELECTOR, selector)
                        title = text_elem.text.strip()
                        if title and len(title) > 5:
                            product_info['title'] = title
                            break
                except:
                    continue
        
        # Extract image
        try:
            img_elem = link_element.find_element(By.CSS_SELECTOR, "img")
            product_info['image'] = img_elem.get_attribute('src') or ''
        except:
            pass
        
        # Enhanced price extraction - look in container
        if container:
            try:
                # Get all text elements in container
                all_elements = container.find_elements(By.CSS_SELECTOR, "*")
                price_candidates = []
                
                for elem in all_elements:
                    try:
                        text = elem.text.strip()
                        if text and ('₹' in text or 'Rs' in text or 'INR' in text):
                            # Check if it looks like a price
                            import re
                            numbers = re.findall(r'[\d,]+', text)
                            if numbers and any(len(num.replace(',', '')) >= 2 for num in numbers):
                                price_candidates.append(text)
                    except:
                        continue
                
                # Take the first valid price
                if price_candidates:
                    product_info['price'] = price_candidates[0]
                
                # Also try specific selectors
                if not product_info['price']:
                    price_selectors = [
                        "span[class*='price']", "div[class*='price']", # Generic
                        "span[class*='amount']", "div[class*='amount']", # Generic
                        "span[class*='cost']", "div[class*='cost']", # Generic
                        "span[class*='rupee']", "div[class*='rupee']", # Generic
                        "span[class*='rs']", "div[class*='rs']" # Generic
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = container.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text and ('₹' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                                product_info['price'] = price_text
                                break
                        except:
                            continue
            except:
                pass
        
        # Also try to find price in the link element itself
        if not product_info['price']:
            try:
                # Look for price elements near the link
                link_text = link_element.text.strip()
                if link_text and ('₹' in link_text or link_text.replace(',', '').replace('.', '').isdigit()):
                    product_info['price'] = link_text
            except:
                pass
        
        # Extract discount
        if container:
            try:
                discount_selectors = [
                    "span[class*='discount']", "div[class*='discount']", # Generic
                    "span[class*='off']", "div[class*='off']", # Generic
                    "span[class*='save']", "div[class*='save']", # Generic
                    "span[class*='deal']", "div[class*='deal']" # Generic
                ]
                
                for selector in discount_selectors:
                    try:
                        discount_elem = container.find_element(By.CSS_SELECTOR, selector)
                        discount_text = discount_elem.text.strip()
                        if discount_text and ('%' in discount_text or 'off' in discount_text.lower() or 'save' in discount_text.lower()):
                            product_info['discount'] = discount_text
                            break
                    except:
                        continue
            except:
                pass
        
        return product_info
        
    except Exception as e:
        logger.debug(f"Error extracting product info: {e}")
        return product_info

def extract_title_from_url(url):
    """Extract product title from Myntra URL"""
    try:
        if not url or ('/product/' not in url and '/p/' not in url):
            return ''
        
        # Extract the product part from URL
        # Example: https://www.myntra.com/product-name/p/123456
        if '/product/' in url:
            parts = url.split('/product/')[1].split('/')
        else:
            parts = url.split('/p/')[0].split('/')
        
        # Get the product name part
        product_part = parts[0] if parts else ''
        
        if product_part:
            # Replace hyphens with spaces and clean up
            title = product_part.replace('-', ' ').replace('_', ' ')
            
            # Capitalize words
            title = ' '.join(word.capitalize() for word in title.split())
            
            # Clean up common patterns
            title = title.replace('Gb', 'GB').replace('Mb', 'MB')
            
            return title
        
        return ''
    except Exception as e:
        logger.debug(f"Error extracting title from URL: {e}")
        return ''

def is_valid_product(product_info):
    """Check if this is a valid product (not email, generic text, etc.)"""
    if not product_info or not product_info.get('title'):
        return False
    
    title = product_info['title'].lower()
    
    # Only filter out obvious non-products
    invalid_keywords = [
        'mailto:', 'email', '@', 'contact', 'support', 'help',
        'search', 'icon', 'login', 'cart', 'menu', 'navigation'
    ]
    
    for keyword in invalid_keywords:
        if keyword in title:
            return False
    
    # Must have a reasonable title length
    if len(product_info['title']) < 5 or len(product_info['title']) > 200:
        return False
    
    return True

if __name__ == "__main__":
    # Test the scraper
    headless = True
    max_items = 10
    
    logger.info(f"🚀 Starting Myntra homepage deals scraper...")
    logger.info(f"Headless mode: {headless}")
    logger.info(f"Max items per section: {max_items}")
    
    result = scrape_myntra_homepage_deals(headless=headless, max_items_per_section=max_items)
    
    print(f"\n{'='*60}")
    print(f"✅ SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total Sections: {result.get('total_sections', 0)}")
    print(f"Total Items: {result.get('total_items', 0)}")
    
    if result.get('sections'):
        print(f"\n📊 Sections Found:")
        for i, section in enumerate(result['sections'][:5], 1):
            print(f"   {i}. {section['section_title']} ({section['item_count']} items)")
        if len(result['sections']) > 5:
            print(f"   ... and {len(result['sections']) - 5} more sections")
    
    print(f"\n💾 Saved to: myntra_homepage_deals.json")
    print(f"{'='*60}\n")
