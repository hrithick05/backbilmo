#!/usr/bin/env python3
"""
Amazon Homepage Deals Scraper
Scrapes deals and offers from Amazon India homepage
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_driver(headless: bool = True) -> webdriver.Chrome:
    """Create a Chrome WebDriver with stable settings"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
    
    # Enhanced anti-detection measures
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("detach", True)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Amazon Deals WebDriver initialized with ChromeDriverManager")
    except Exception as e:
        logger.error(f"ChromeDriverManager failed: {e}")
        try:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Amazon Deals WebDriver initialized with system ChromeDriver")
        except Exception as e2:
            logger.error(f"All ChromeDriver methods failed: {e2}")
            raise e2
    
    # Execute JavaScript to remove webdriver properties
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("delete navigator.__proto__.webdriver")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
    driver.execute_script("window.chrome = {runtime: {}}")
    
    return driver

def scrape_amazon_homepage_deals(headless: bool = True, max_items_per_section: int = 10):
    """Scrape ENTIRE Amazon India homepage by scrolling and capturing all sections"""
    driver = create_driver(headless=headless)
    all_sections = []
    
    try:
        logger.info("🏠 Visiting Amazon India homepage...")
        driver.get("https://www.amazon.in")
        time.sleep(5)  # Wait for initial page to load
        
        # Scroll down to load ALL content dynamically
        logger.info("📜 Scrolling to load entire page...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 20  # Limit scrolls to prevent infinite loop
        
        while scroll_attempts < max_scrolls:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for content to load
            
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                # No more content to load
                logger.info(f"✅ Reached end of page after {scroll_attempts + 1} scrolls")
                break
            
            last_height = new_height
            scroll_attempts += 1
            logger.info(f"   Scroll {scroll_attempts}/{max_scrolls}...")
        
        # Scroll back to top to ensure all content is visible
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        logger.info("📸 Saving complete homepage HTML...")
        html_content = driver.page_source
        with open('amazon_homepage.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info("🔍 Extracting ALL sections from entire homepage...")
        
        # Strategy 1: Find ALL section containers with headings
        section_selectors = [
            # Main content sections
            "div[data-card-identifier]",
            "div.feed-carousel",
            "div[class*='CardInstance']",
            "div.a-cardui",
            "div[data-csa-c-type='widget']",
            "div.fresh-shoveler",
            "div[class*='desktop-grid-column-container']",
            "div[class*='Desktop-module']",
            "div[class*='CardInstanceq']",
            "div.octopus-widget-v2",
            "div[data-cel-widget]",
            "section[data-csa-c-type='widget']",
        ]
        
        processed_titles = set()  # Track processed sections
        
        for selector in section_selectors:
            try:
                sections = driver.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"🔍 Checking selector '{selector}': found {len(sections)} containers")
                
                for section in sections:
                    try:
                        # Extract section title/heading
                        section_title = extract_section_title(section)
                        
                        # Skip if no title or already processed
                        if not section_title or section_title in processed_titles:
                            continue
                        
                        # Extract items in this section
                        section_items = extract_section_items(section, driver, max_items_per_section)
                        
                        # Only add section if it has valid products with titles
                        valid_items = [item for item in section_items if item.get('title') and len(item.get('title', '')) > 5]
                        
                        if valid_items and len(valid_items) > 0:
                            section_data = {
                                'section_title': section_title,
                                'item_count': len(valid_items),
                                'items': valid_items
                            }
                            
                            all_sections.append(section_data)
                            processed_titles.add(section_title)
                            logger.info(f"  ✅ Section '{section_title}': {len(valid_items)} items")
                        else:
                            logger.debug(f"  ⚠️ Skipping '{section_title}': no valid products")
                    except Exception as e:
                        logger.debug(f"  ⚠️ Error processing section: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        
        # Strategy 2: Extract ALL headings (h1, h2, h3) and their content
        logger.info("🔄 Extracting sections from all headings...")
        alternative_sections = extract_sections_from_all_headings(driver, max_items_per_section, processed_titles)
        
        for section in alternative_sections:
            # Only add if has valid items and not already processed
            if section['section_title'] not in processed_titles and section.get('item_count', 0) > 0:
                # Double check items are valid
                valid_items = [item for item in section.get('items', []) if item.get('title') and len(item.get('title', '')) > 5]
                if valid_items:
                    section['items'] = valid_items
                    section['item_count'] = len(valid_items)
                    all_sections.append(section)
                    processed_titles.add(section['section_title'])
                    logger.info(f"  ✅ Heading section '{section['section_title']}': {len(valid_items)} items")
                else:
                    logger.debug(f"  ⚠️ Skipping '{section['section_title']}': no valid products")
        
        # Strategy 3: Capture any remaining visible products not in sections
        logger.info("🔄 Capturing any remaining products...")
        remaining_products = extract_remaining_products(driver, processed_titles, max_items_per_section)
        if remaining_products:
            all_sections.append(remaining_products)
            logger.info(f"  ✅ Other Products: {remaining_products['item_count']} items")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📦 TOTAL SECTIONS EXTRACTED: {len(all_sections)}")
        total_items = sum(s['item_count'] for s in all_sections)
        logger.info(f"📦 TOTAL ITEMS EXTRACTED: {total_items}")
        logger.info(f"{'='*60}")
        
        # Save to JSON file
        homepage_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'Amazon India Homepage',
            'total_sections': len(all_sections),
            'total_items': total_items,
            'sections': all_sections
        }
        
        with open('amazon_homepage_deals.json', 'w', encoding='utf-8') as f:
            json.dump(homepage_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(all_sections)} sections to amazon_homepage_deals.json")
        
        return homepage_data
        
    except Exception as e:
        logger.error(f"❌ Error scraping Amazon homepage: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'source': 'Amazon India Homepage',
            'total_deals': 0,
            'deals': [],
            'error': str(e)
        }
    finally:
        driver.quit()

def extract_section_title(section_element):
    """Extract section title/heading from a container"""
    try:
        # Try multiple heading selectors
        title_selectors = [
            "h2",
            "h3",
            "div.a-cardui-header h2",
            "div[class*='header'] h2",
            "div[class*='title'] span",
            "span[class*='headline']",
            "div.feed-carousel-header",
            "div[data-csa-c-content-id] h2",
        ]
        
        for selector in title_selectors:
            try:
                title_elem = section_element.find_element(By.CSS_SELECTOR, selector)
                title_text = title_elem.text.strip()
                if title_text and len(title_text) > 2 and len(title_text) < 100:
                    # Clean up the title
                    title_text = title_text.replace('\n', ' ').strip()
                    return title_text
            except:
                continue
        
        return None
    except Exception as e:
        logger.debug(f"Error extracting section title: {e}")
        return None

def extract_section_items(section_element, driver, max_items=10):
    """Extract items from a section"""
    items = []
    
    try:
        # Try to find product cards within the section
        item_selectors = [
            "div.a-cardui-body a",
            "div[class*='grid'] a",
            "li a",
            "div[class*='item'] a",
            "div[class*='product'] a",
        ]
        
        for selector in item_selectors:
            try:
                item_links = section_element.find_elements(By.CSS_SELECTOR, selector)
                
                if item_links and len(item_links) > 0:
                    for item_link in item_links[:max_items]:
                        item_info = extract_item_info(item_link, section_element)
                        if item_info and item_info.get('title'):
                            items.append(item_info)
                    
                    if len(items) > 0:
                        break
            except:
                continue
        
        return items[:max_items]
    except Exception as e:
        logger.debug(f"Error extracting section items: {e}")
        return []

def extract_item_info(item_element, section_element):
    """Extract information from a single item"""
    item_info = {
        'title': '',
        'price': '',
        'discount': '',
        'image': '',
        'link': ''
    }
    
    try:
        # Extract link
        link = item_element.get_attribute('href') or ''
        if link:
            if link.startswith('/'):
                link = 'https://www.amazon.in' + link
            # Validate that it's an Amazon link only
            if 'amazon.in' in link or 'amazon.com' in link:
                item_info['link'] = link
            else:
                # Skip non-Amazon links
                logger.debug(f"Skipping non-Amazon link: {link}")
                return None
        
        # Extract title from various sources
        # 1. Try aria-label
        title = item_element.get_attribute('aria-label') or ''
        
        # 2. Try image alt text
        if not title:
            try:
                img = item_element.find_element(By.TAG_NAME, 'img')
                title = img.get_attribute('alt') or ''
            except:
                pass
        
        # 3. Try text content
        if not title:
            title = item_element.text.strip()
        
        # Clean up title
        if title:
            title = title.split('\n')[0].strip()  # Take first line
            title = title.split('(')[0].strip()    # Remove parentheses content
            if len(title) > 10 and len(title) < 200:
                item_info['title'] = title
        
        # Extract image - only accept Amazon images
        try:
            img = item_element.find_element(By.TAG_NAME, 'img')
            img_src = img.get_attribute('src') or ''
            # Validate Amazon images only (prevent other platform images)
            if img_src and ('amazon' in img_src.lower() or 'ssl-images-amazon' in img_src.lower()):
                item_info['image'] = img_src
            else:
                logger.debug(f"Skipping non-Amazon image: {img_src}")
        except:
            pass
        
        # Extract price (look in parent section)
        try:
            # Try to find price near the link
            parent = item_element.find_element(By.XPATH, './..')
            price_elem = parent.find_element(By.CSS_SELECTOR, "span[class*='price'], span.a-price-whole")
            price_text = price_elem.text.strip()
            if price_text and ('₹' in price_text or price_text.replace(',', '').isdigit()):
                if '₹' not in price_text:
                    price_text = f'₹{price_text}'
                item_info['price'] = price_text
        except:
            pass
        
        # Extract discount
        try:
            parent = item_element.find_element(By.XPATH, './..')
            discount_elem = parent.find_element(By.CSS_SELECTOR, "span[class*='badge'], span[class*='discount']")
            discount_text = discount_elem.text.strip()
            if discount_text and ('%' in discount_text or 'off' in discount_text.lower()):
                item_info['discount'] = discount_text
        except:
            pass
        
        return item_info
    except Exception as e:
        logger.debug(f"Error extracting item info: {e}")
        return item_info

def extract_sections_from_all_headings(driver, max_items=10, processed_titles=set()):
    """Extract sections from ALL headings on page"""
    sections = []
    
    try:
        # Get ALL headings (h1, h2, h3, h4)
        all_headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4")
        logger.info(f"   Found {len(all_headings)} total headings")
        
        for heading in all_headings:
            try:
                title = heading.text.strip()
                
                # Skip if invalid or already processed
                if not title or len(title) < 3 or len(title) > 150 or title in processed_titles:
                    continue
                
                # Find parent container (try multiple levels)
                parent = None
                try:
                    # Try to find a card/widget parent
                    parent = heading.find_element(By.XPATH, "./ancestor::div[contains(@class, 'card') or contains(@class, 'widget') or contains(@data-card-identifier, '') or contains(@data-cel-widget, '')]")
                except:
                    try:
                        # Fallback to any div parent within 5 levels
                        parent = heading.find_element(By.XPATH, "./ancestor::div[5]")
                    except:
                        continue
                
                if not parent:
                    continue
                
                # Extract items from this parent
                items = extract_section_items(parent, driver, max_items)
                
                if items and len(items) > 0:
                    section_data = {
                        'section_title': title,
                        'item_count': len(items),
                        'items': items
                    }
                    sections.append(section_data)
            except:
                continue
        
        return sections
    except Exception as e:
        logger.error(f"Heading extraction error: {e}")
        return []

def extract_remaining_products(driver, processed_titles, max_items=20):
    """Capture any products not yet categorized into sections"""
    try:
        # Find all links with images that look like products
        all_product_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/dp/'], a[href*='/gp/product/']")
        logger.info(f"   Found {len(all_product_links)} potential product links")
        
        remaining_items = []
        seen_links = set()
        
        for link in all_product_links[:max_items * 2]:  # Check more to filter
            try:
                href = link.get_attribute('href') or ''
                
                # Skip if already seen or invalid
                if not href or href in seen_links:
                    continue
                
                # Try to find an image within the link
                try:
                    img = link.find_element(By.TAG_NAME, 'img')
                except:
                    continue
                
                # Extract item info
                item_info = extract_item_info(link, link)
                
                if item_info and item_info.get('title') and len(item_info['title']) > 10:
                    remaining_items.append(item_info)
                    seen_links.add(href)
                    
                    if len(remaining_items) >= max_items:
                        break
            except:
                continue
        
        if remaining_items:
            return {
                'section_title': 'More Products',
                'item_count': len(remaining_items),
                'items': remaining_items
            }
        
        return None
    except Exception as e:
        logger.error(f"Remaining products extraction error: {e}")
        return None

def extract_deal_info(card_element, driver):
    """Extract deal information from a card element"""
    deal_info = {
        'title': '',
        'price': '',
        'original_price': '',
        'discount': '',
        'image': '',
        'link': '',
        'deal_type': '',
        'badge': ''
    }
    
    try:
        # Extract title
        title_selectors = [
            "h2 span",
            "h3 span",
            "div.a-text-bold",
            "div[class*='title']",
            "span.a-size-base-plus",
            "span.a-size-medium",
            "a span",
        ]
        
        for selector in title_selectors:
            try:
                title_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                title_text = title_elem.text.strip()
                if title_text and len(title_text) > 5 and len(title_text) < 200:
                    deal_info['title'] = title_text
                    break
            except:
                continue
        
        # Extract from image alt if no title found
        if not deal_info['title']:
            try:
                img = card_element.find_element(By.TAG_NAME, "img")
                img_alt = img.get_attribute('alt') or ''
                if img_alt and len(img_alt) > 10:
                    deal_info['title'] = img_alt.split(',')[0].strip()
            except:
                pass
        
        # Extract price
        price_selectors = [
            "span.a-price-whole",
            "span.a-offscreen",
            "span[class*='price']",
            "div[class*='price'] span",
        ]
        
        for selector in price_selectors:
            try:
                price_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                if price_text and '₹' in price_text:
                    deal_info['price'] = price_text
                    break
            except:
                continue
        
        # Extract discount/offer
        discount_selectors = [
            "span[class*='badge']",
            "div[class*='badge']",
            "span[class*='discount']",
            "div[class*='discount']",
            "span.a-color-price",
        ]
        
        for selector in discount_selectors:
            try:
                discount_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                discount_text = discount_elem.text.strip()
                if discount_text and ('%' in discount_text or 'off' in discount_text.lower()):
                    deal_info['discount'] = discount_text
                    break
            except:
                continue
        
        # Extract image - only accept Amazon images
        try:
            img = card_element.find_element(By.TAG_NAME, "img")
            img_src = img.get_attribute('src') or ''
            # Validate Amazon images only
            if img_src and ('amazon' in img_src.lower() or 'ssl-images-amazon' in img_src.lower()):
                deal_info['image'] = img_src
            else:
                logger.debug(f"Skipping non-Amazon deal image: {img_src}")
        except:
            pass
        
        # Extract link
        try:
            link_elem = card_element.find_element(By.TAG_NAME, "a")
            link = link_elem.get_attribute('href') or ''
            if link:
                if link.startswith('/'):
                    link = 'https://www.amazon.in' + link
                # Validate Amazon link only
                if 'amazon.in' in link or 'amazon.com' in link:
                    deal_info['link'] = link
                else:
                    logger.debug(f"Skipping non-Amazon deal link: {link}")
        except:
            pass
        
        # Extract deal type/badge
        try:
            badge_selectors = [
                "span[class*='Deal']",
                "div[class*='Deal']",
                "span.a-badge",
            ]
            
            for selector in badge_selectors:
                try:
                    badge_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                    badge_text = badge_elem.text.strip()
                    if badge_text:
                        deal_info['deal_type'] = badge_text
                        break
                except:
                    continue
        except:
            pass
        
        # Set default deal type if not found
        if not deal_info['deal_type']:
            deal_info['deal_type'] = 'Homepage Deal'
        
        return deal_info
        
    except Exception as e:
        logger.debug(f"Error extracting deal info: {e}")
        return deal_info

if __name__ == "__main__":
    import sys
    
    headless = '--headless' in sys.argv or '-h' in sys.argv
    max_items = 10
    
    # Check for max items argument
    for arg in sys.argv:
        if arg.startswith('--max='):
            try:
                max_items = int(arg.split('=')[1])
            except:
                pass
    
    print(f"\n{'='*60}")
    print(f"🛒 AMAZON HOMEPAGE - COMPLETE PAGE SCRAPER")
    print(f"{'='*60}")
    print(f"Mode: {'Headless' if headless else 'Visible Browser'}")
    print(f"Max Items Per Section: {max_items}")
    print(f"Strategy: Scroll entire page + Multi-level extraction")
    print(f"{'='*60}\n")
    
    result = scrape_amazon_homepage_deals(headless=headless, max_items_per_section=max_items)
    
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
    
    print(f"\n💾 Saved to: amazon_homepage_deals.json")
    print(f"{'='*60}\n")
