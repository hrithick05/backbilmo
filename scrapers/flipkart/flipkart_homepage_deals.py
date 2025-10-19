#!/usr/bin/env python3
"""
Flipkart Homepage Deals Scraper
Scrapes deals and offers from Flipkart India homepage
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
        logger.info("Flipkart Deals WebDriver initialized with ChromeDriverManager")
    except Exception as e:
        logger.error(f"ChromeDriverManager failed: {e}")
        try:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Flipkart Deals WebDriver initialized with system ChromeDriver")
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

def scrape_flipkart_homepage_deals(headless: bool = True, max_items_per_section: int = 10):
    """Scrape Flipkart homepage focusing on actual product deals with prices"""
    driver = create_driver(headless=headless)
    all_sections = []
    
    try:
        logger.info("🏠 Visiting Flipkart India homepage...")
        driver.get("https://www.flipkart.com")
        time.sleep(3)  # Reduced from 10 to 3 seconds
        
        # Smart scrolling like Amazon - scroll until no more content loads
        logger.info("📜 Scrolling to load deals...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 10  # Reduced from 20 to 10
        
        while scroll_attempts < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # Reduced from 2-3 to 1 second
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.info(f"✅ Reached end after {scroll_attempts + 1} scrolls")
                break
            
            last_height = new_height
            scroll_attempts += 1
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)  # Reduced from 5 to 1 second
        
        # Save HTML for debugging
        logger.info("📸 Saving Flipkart homepage HTML...")
        html_content = driver.page_source
        with open('flipkart_homepage.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info("🔍 Extracting sections and deals...")
        
        # Simplified Strategy: Find section containers efficiently
        section_selectors = [
            "div[data-id]",  # Flipkart specific
            "div._1AtVbE",   # Common Flipkart widget class
            "div._2MlkI1",   # Another widget class
            "div[class*='widget']",
            "div[class*='section']",
            "section[data-id]",
        ]
        
        processed_titles = set()
        
        for selector in section_selectors:
            try:
                sections = driver.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"🔍 Checking '{selector}': found {len(sections)} containers")
                
                for section in sections[:15]:  # Limit to first 15 per selector
                    try:
                        # Extract section title
                        section_title = extract_section_title(section)
                        
                        # Skip if no title or already processed
                        if not section_title or section_title in processed_titles:
                            continue
                        
                        # Extract items
                        section_items = extract_section_items(section, driver, max_items_per_section)
                        
                        # Only add section if it has valid products with titles
                        # Prefer items with images and prices
                        valid_items = [item for item in section_items if item.get('title') and len(item.get('title', '')) > 5]
                        
                        # Log items with missing data for debugging
                        items_with_images = sum(1 for item in valid_items if item.get('image'))
                        items_with_prices = sum(1 for item in valid_items if item.get('price'))
                        logger.info(f"  📊 Images: {items_with_images}/{len(valid_items)}, Prices: {items_with_prices}/{len(valid_items)}")
                        
                        for item in valid_items:
                            if not item.get('image'):
                                logger.warning(f"  ⚠️ Item missing image: {item.get('title', 'Unknown')[:40]}")
                            if not item.get('price'):
                                logger.warning(f"  ⚠️ Item missing price: {item.get('title', 'Unknown')[:40]}")
                        
                        if valid_items and len(valid_items) > 0:
                            section_data = {
                                'section_title': section_title,
                                'item_count': len(valid_items),
                                'items': valid_items
                            }
                            all_sections.append(section_data)
                            processed_titles.add(section_title)
                            logger.info(f"  ✅ '{section_title}': {len(valid_items)} items")
                        else:
                            logger.debug(f"  ⚠️ Skipping '{section_title}': no valid products")
                    except Exception as e:
                        logger.debug(f"  ⚠️ Error processing section: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        
        # Also extract from headings (like Amazon does)
        logger.info("🔄 Extracting from headings...")
        heading_sections = extract_sections_from_all_headings(driver, max_items_per_section, processed_titles)
        
        for section in heading_sections:
            # Only add if has valid items and not already processed
            if section['section_title'] not in processed_titles and section.get('item_count', 0) > 0:
                # Double check items are valid
                valid_items = [item for item in section.get('items', []) if item.get('title') and len(item.get('title', '')) > 5]
                if valid_items:
                    section['items'] = valid_items
                    section['item_count'] = len(valid_items)
                    all_sections.append(section)
                    processed_titles.add(section['section_title'])
                    logger.info(f"  ✅ '{section['section_title']}': {len(valid_items)} items")
                else:
                    logger.debug(f"  ⚠️ Skipping '{section['section_title']}': no valid products")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📦 TOTAL SECTIONS EXTRACTED: {len(all_sections)}")
        total_items = sum(s['item_count'] for s in all_sections)
        logger.info(f"📦 TOTAL ITEMS EXTRACTED: {total_items}")
        logger.info(f"{'='*60}")
        
        # Save to JSON file
        homepage_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'Flipkart India Homepage',
            'total_sections': len(all_sections),
            'total_items': total_items,
            'sections': all_sections
        }
        
        with open('flipkart_homepage_deals.json', 'w', encoding='utf-8') as f:
            json.dump(homepage_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(all_sections)} sections to flipkart_homepage_deals.json")
        
        return homepage_data
        
    except Exception as e:
        logger.error(f"❌ Error scraping Flipkart homepage: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'source': 'Flipkart India Homepage',
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
        title_selectors = ["h1", "h2", "h3", "h4", "h5", "h6", "span", "div"]
        
        for selector in title_selectors:
            try:
                title_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                title_text = title_elem.text.strip()
                if title_text and len(title_text) > 5 and len(title_text) < 100:
                    # Clean up the title
                    title_text = title_text.replace('\n', ' ').strip()
                    return title_text
            except:
                continue
        
        return None
    except:
        return None

def extract_product_info_improved(link_element, parent_element):
    """Extract detailed product information with better accuracy"""
    product_info = {
        'title': '',
        'price': '',
        'discount': '',
        'image': '',
        'link': ''
    }
    
    try:
        # Extract link
        link = link_element.get_attribute('href') or ''
        if link:
            if link.startswith('/'):
                link = 'https://www.flipkart.com' + link
            product_info['link'] = link
        
        # Extract title - try multiple methods
        title = ''
        
        # Method 1: aria-label
        title = link_element.get_attribute('aria-label') or ''
        
        # Method 2: image alt text
        if not title:
            try:
                img = link_element.find_element(By.TAG_NAME, 'img')
                title = img.get_attribute('alt') or ''
            except:
                pass
        
        # Method 3: text content
        if not title:
            title = link_element.text.strip()
        
        # Method 4: Look in parent for title
        if not title and parent_element:
            try:
                title_elem = parent_element.find_element(By.CSS_SELECTOR, "span, div, p")
                title = title_elem.text.strip()
            except:
                pass
        
        # Clean up title
        if title:
            title = title.split('\n')[0].strip()
            title = title.split('(')[0].strip()
            # Filter out invalid titles
            if len(title) > 5 and len(title) < 200 and not title.lower().startswith('mailto:'):
                product_info['title'] = title
        
        # Extract image
        try:
            img = link_element.find_element(By.TAG_NAME, 'img')
            img_src = img.get_attribute('src') or ''
            if img_src and ('flipkart' in img_src.lower() or 'img' in img_src.lower()):
                product_info['image'] = img_src
        except:
            pass
        
        # Extract price - look in parent element
        if parent_element:
            try:
                price_selectors = [
                    # Flipkart specific price selectors
                    "span[class*='_30jeq3']",
                    "div[class*='_30jeq3']",
                    "span[class*='_1vC4OE']",
                    "div[class*='_1vC4OE']",
                    "span[class*='_25b18c']",
                    "div[class*='_25b18c']",
                    "span[class*='_3tbKJd']",
                    "div[class*='_3tbKJd']",
                    "span[class*='_2tW1I0']",
                    "div[class*='_2tW1I0']",
                    # Generic price selectors
                    "span[class*='price']",
                    "div[class*='price']", 
                    "span[class*='rupee']",
                    "div[class*='rupee']",
                    "span[class*='amount']",
                    "div[class*='amount']",
                    "span[class*='cost']",
                    "div[class*='cost']",
                    # Look for any element with ₹ symbol
                    "span:contains('₹')",
                    "div:contains('₹')",
                    "p:contains('₹')"
                ]
                
                for selector in price_selectors:
                    try:
                        if ':contains(' in selector:
                            # Use XPath for contains
                            xpath_selector = f".//{selector.split(':')[0]}[contains(text(), '₹')]"
                            price_elem = parent_element.find_element(By.XPATH, xpath_selector)
                        else:
                            price_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
                        
                        price_text = price_elem.text.strip()
                        if price_text and ('₹' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                            if '₹' not in price_text:
                                price_text = f'₹{price_text}'
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
                link_parent = link_element.find_element(By.XPATH, './..')
                price_elements = link_parent.find_elements(By.CSS_SELECTOR, "span, div, p")
                
                for elem in price_elements:
                    text = elem.text.strip()
                    if text and ('₹' in text or text.replace(',', '').replace('.', '').isdigit()):
                        if '₹' not in text:
                            text = f'₹{text}'
                        product_info['price'] = text
                        break
            except:
                pass
        
        # Extract discount
        if parent_element:
            try:
                discount_selectors = [
                    "span[class*='discount']",
                    "div[class*='discount']",
                    "span[class*='off']",
                    "div[class*='off']",
                    "span[class*='save']",
                    "div[class*='save']",
                    "span[class*='deal']",
                    "div[class*='deal']",
                    "span[class*='_3Ay6Sb']",
                    "div[class*='_3Ay6Sb']"
                ]
                
                for selector in discount_selectors:
                    try:
                        discount_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
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

def is_valid_product(product_info):
    """Check if this is a valid product (not email, generic text, etc.)"""
    if not product_info or not product_info.get('title'):
        return False
    
    title = product_info['title'].lower()
    
    # Only filter out obvious non-products
    invalid_keywords = [
        'mailto:', 'email', '@', 'contact', 'support', 'help',
        'purchases.oni@flipkart.com'
    ]
    
    for keyword in invalid_keywords:
        if keyword in title:
            return False
    
    # Must have a reasonable title length
    if len(product_info['title']) < 5 or len(product_info['title']) > 200:
        return False
    
    return True

def extract_products_from_container(container, driver, max_items):
    """Extract products from a deal container"""
    products = []
    
    try:
        product_links = container.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
        
        for link in product_links[:max_items]:
            product_info = extract_product_info_improved(link, container)
            if product_info and is_valid_product(product_info):
                products.append(product_info)
        
        return products
    except Exception as e:
        logger.debug(f"Error extracting products from container: {e}")
        return []

def find_product_parent_section(link_element, driver):
    """Find the parent section for a product link"""
    try:
        # Try to find a parent div that looks like a section
        parent = link_element.find_element(By.XPATH, "./ancestor::div[contains(@class, '_') or contains(@class, 'css-') or contains(@class, 'card') or contains(@class, 'widget')][1]")
        return parent
    except:
        try:
            # Fallback to any div parent within 3 levels
            parent = link_element.find_element(By.XPATH, "./ancestor::div[3]")
            return parent
        except:
            return None

def find_parent_section(link_element, driver):
    """Find the parent section/container for a product link"""
    try:
        # Try to find a parent div that looks like a section
        parent = link_element.find_element(By.XPATH, "./ancestor::div[contains(@class, '_') or contains(@class, 'css-') or contains(@class, 'card') or contains(@class, 'widget')][1]")
        return parent
    except:
        try:
            # Fallback to any div parent within 3 levels
            parent = link_element.find_element(By.XPATH, "./ancestor::div[3]")
            return parent
        except:
            return None

def extract_section_title_from_parent(parent_element):
    """Extract section title from parent element"""
    try:
        # Look for headings in the parent
        title_selectors = ["h1", "h2", "h3", "h4", "h5", "h6", "span", "div"]
        
        for selector in title_selectors:
            try:
                title_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
                title_text = title_elem.text.strip()
                if title_text and len(title_text) > 5 and len(title_text) < 100:
                    # Clean up the title
                    title_text = title_text.replace('\n', ' ').strip()
                    return title_text
            except:
                continue
        
        return None
    except:
        return None

def extract_item_info_from_link(link_element, driver):
    """Extract detailed item information from a product link"""
    item_info = {
        'title': '',
        'price': '',
        'discount': '',
        'image': '',
        'link': ''
    }
    
    try:
        # Extract link
        link = link_element.get_attribute('href') or ''
        if link:
            if link.startswith('/'):
                link = 'https://www.flipkart.com' + link
            item_info['link'] = link
        
        # Extract title from various sources
        # 1. Try aria-label
        title = link_element.get_attribute('aria-label') or ''
        
        # 2. Try image alt text
        if not title:
            try:
                img = link_element.find_element(By.TAG_NAME, 'img')
                title = img.get_attribute('alt') or ''
            except:
                pass
        
        # 3. Try text content
        if not title:
            title = link_element.text.strip()
        
        # 4. Try to find title in parent elements
        if not title:
            try:
                parent = link_element.find_element(By.XPATH, './..')
                title_elem = parent.find_element(By.CSS_SELECTOR, "span, div, p")
                title = title_elem.text.strip()
            except:
                pass
        
        # Clean up title
        if title:
            title = title.split('\n')[0].strip()  # Take first line
            title = title.split('(')[0].strip()    # Remove parentheses content
            if len(title) > 5 and len(title) < 200:
                item_info['title'] = title
        
        # Extract image
        try:
            img = link_element.find_element(By.TAG_NAME, 'img')
            img_src = img.get_attribute('src') or ''
            if img_src and ('flipkart' in img_src.lower() or 'img' in img_src.lower()):
                item_info['image'] = img_src
        except:
            pass
        
        # Extract price (look in parent section)
        try:
            parent = link_element.find_element(By.XPATH, './..')
            price_selectors = [
                "span[class*='price']",
                "div[class*='price']",
                "span[class*='rupee']",
                "div[class*='rupee']",
                "span[class*='amount']",
                "div[class*='amount']",
                "span[class*='cost']",
                "div[class*='cost']"
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = parent.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.text.strip()
                    if price_text and ('₹' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                        if '₹' not in price_text:
                            price_text = f'₹{price_text}'
                        item_info['price'] = price_text
                        break
                except:
                    continue
        except:
            pass
        
        # Extract discount
        try:
            parent = link_element.find_element(By.XPATH, './..')
            discount_selectors = [
                "span[class*='discount']",
                "div[class*='discount']",
                "span[class*='off']",
                "div[class*='off']",
                "span[class*='save']",
                "div[class*='save']",
                "span[class*='deal']",
                "div[class*='deal']"
            ]
            
            for selector in discount_selectors:
                try:
                    discount_elem = parent.find_element(By.CSS_SELECTOR, selector)
                    discount_text = discount_elem.text.strip()
                    if discount_text and ('%' in discount_text or 'off' in discount_text.lower() or 'save' in discount_text.lower()):
                        item_info['discount'] = discount_text
                        break
                except:
                    continue
        except:
            pass
        
        return item_info
    except Exception as e:
        logger.debug(f"Error extracting item info from link: {e}")
        return item_info

def extract_sections_from_headings_improved(driver, max_items=10):
    """Extract sections from headings with improved product detection"""
    sections = []
    
    try:
        # Get ALL headings (h1, h2, h3, h4)
        all_headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4")
        logger.info(f"   Found {len(all_headings)} total headings")
        
        for heading in all_headings:
            try:
                title = heading.text.strip()
                
                # Skip if invalid
                if not title or len(title) < 3 or len(title) > 150:
                    continue
                
                # Find parent container
                parent = None
                try:
                    parent = heading.find_element(By.XPATH, "./ancestor::div[contains(@class, '_') or contains(@class, 'css-')][1]")
                except:
                    try:
                        parent = heading.find_element(By.XPATH, "./ancestor::div[5]")
                    except:
                        continue
                
                if not parent:
                    continue
                
                # Extract items from this parent
                items = extract_section_items_improved(parent, driver, max_items)
                
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

def extract_section_items_improved(section_element, driver, max_items=10):
    """Extract items from a section with improved detection"""
    items = []
    
    try:
        # Try to find product links within the section
        item_selectors = [
            "a[href*='/p/']",
            "a[href*='/product/']",
            "a[href*='/dp/']",
            "div[class*='product'] a",
            "div[class*='item'] a",
            "div[class*='card'] a",
            "div[class*='widget'] a",
            "li a",
            "div[class^='_'] a",
            "div[class*='css-'] a",
        ]
        
        seen_links = set()
        
        for selector in item_selectors:
            try:
                item_links = section_element.find_elements(By.CSS_SELECTOR, selector)
                
                for item_link in item_links:
                    try:
                        href = item_link.get_attribute('href') or ''
                        if href and href not in seen_links:
                            item_info = extract_item_info_from_link(item_link, driver)
                            if item_info and item_info.get('title') and len(item_info['title']) > 10:
                                items.append(item_info)
                                seen_links.add(href)
                                
                                if len(items) >= max_items:
                                    break
                    except:
                        continue
                
                if len(items) >= max_items:
                    break
            except:
                continue
        
        return items[:max_items]
    except Exception as e:
        logger.debug(f"Error extracting section items: {e}")
        return []

def extract_section_title(section_element):
    """Extract section title/heading from a container"""
    try:
        # Try multiple heading selectors
        title_selectors = [
            "h1", "h2", "h3", "h4", "h5", "h6",
            "div._1AtVbE h2",
            "div._2MlkI1 h2",
            "div._1YokD2 h2",
            "div._1HmYoV h2",
            "div._3e7xtJ h2",
            "div._2cLu-l h2",
            "div._1fQZEK h2",
            "div._3gijNv h2",
            "div._2d0qh9 h2",
            "div._3O0U0u h2",
            "div._2QfC02 h2",
            "div[class*='header'] h2",
            "div[class*='title'] span",
            "div[class*='title'] div",
            "div[class*='title'] p",
            "span[class*='headline']",
            "div._1AtVbE span",
            "div._2MlkI1 span",
            "div._1YokD2 span",
            "div._1HmYoV span",
            "div._3e7xtJ span",
            "div._2cLu-l span",
            "div._1fQZEK span",
            "div._3gijNv span",
            "div._2d0qh9 span",
            "div._3O0U0u span",
            "div._2QfC02 span",
            # Generic selectors
            "div[class*='title']",
            "div[class*='header']",
            "div[class*='heading']",
            "span[class*='title']",
            "span[class*='header']",
            "span[class*='heading']",
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
    """Extract items from a section - only valid products"""
    items = []
    
    try:
        # Try to find product cards within the section
        item_selectors = [
            # Direct product links (most reliable)
            "a[href*='/p/']",
            "a[href*='/product/']",
            # Current Flipkart selectors
            "div.q8WwEU a",
            "div._3zsGrb a", 
            "div._2-LWwB a",
            # Legacy Flipkart selectors
            "div._1AtVbE a",
            "div._2MlkI1 a",
            "div._1YokD2 a",
            # Generic selectors
            "li a",
            "div[class*='item'] a",
            "div[class*='product'] a",
            "div[class*='card'] a",
        ]
        
        for selector in item_selectors:
            try:
                item_links = section_element.find_elements(By.CSS_SELECTOR, selector)
                
                if item_links and len(item_links) > 0:
                    for item_link in item_links[:max_items * 3]:  # Check more to filter
                        item_info = extract_item_info(item_link, section_element)
                        # Only add if has valid title, link, and preferably image/price
                        if item_info and item_info.get('title') and item_info.get('link') and len(item_info.get('title', '')) > 5:
                            # Prefer items with price and image, but add anyway if we don't have enough
                            if item_info.get('image') or item_info.get('price') or len(items) < 3:
                                items.append(item_info)
                                
                                if len(items) >= max_items:
                                    break
                    
                    if len(items) > 0:
                        break
            except:
                continue
        
        return items[:max_items]
    except Exception as e:
        logger.debug(f"Error extracting section items: {e}")
        return []

def extract_item_info(item_element, section_element):
    """Extract information from a single item - Enhanced for Flipkart"""
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
                link = 'https://www.flipkart.com' + link
            # Validate that it's a Flipkart link only
            if 'flipkart.com' in link:
                item_info['link'] = link
            else:
                # Skip non-Flipkart links
                logger.debug(f"Skipping non-Flipkart link: {link}")
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
        
        # 4. Extract from URL if nothing else works
        if not title and link:
            try:
                # Extract product name from URL
                url_parts = link.split('/p/')[0].split('/')
                if url_parts:
                    product_slug = url_parts[-1]
                    title = product_slug.replace('-', ' ').title()
            except:
                pass
        
        # Clean up title
        if title:
            title = title.split('\n')[0].strip()  # Take first line
            title = title.split('(')[0].strip()    # Remove parentheses content
            if len(title) > 10 and len(title) < 200:
                item_info['title'] = title
        
        # ULTRA AGGRESSIVE IMAGE EXTRACTION - SEARCH EVERYWHERE
        try:
            img_src = None
            
            # Method 1: Find ALL images in a broader area and pick the best one
            search_elements = [item_element]
            
            # Add parent to search
            try:
                parent = item_element.find_element(By.XPATH, './..')
                search_elements.append(parent)
            except:
                pass
            
            # Add grandparent to search
            try:
                grandparent = item_element.find_element(By.XPATH, './../..')
                search_elements.append(grandparent)
            except:
                pass
            
            # Add section if available
            if section_element:
                search_elements.append(section_element)
            
            # Search all these elements for images
            all_found_images = []
            for elem in search_elements:
                try:
                    imgs = elem.find_elements(By.TAG_NAME, 'img')
                    for img in imgs:
                        # Get ALL attributes
                        src = img.get_attribute('src') or ''
                        data_src = img.get_attribute('data-src') or ''
                        
                        # Collect all possible sources
                        if src and src.strip() and not src.startswith('data:'):
                            all_found_images.append(src)
                        if data_src and data_src.strip() and not data_src.startswith('data:'):
                            all_found_images.append(data_src)
                except:
                    continue
            
            # Filter and pick the best product image (not logos/banners)
            product_images = []
            
            for img_url in all_found_images:
                img_url = img_url.strip()
                
                # Skip logos, headers, and UI elements
                skip_patterns = [
                    'fkheaderlogo', 'logo', 'header', 'banner', 'sprite',
                    'icon', 'arrow', 'cart', 'badge', 'footer', 'exploreplus',
                    'fk-p-flap/1620', 'fk-p-flap/530', 'fk-p-flap/520',  # Banner sizes
                    'batman-returns/batman-returns/p/images'  # UI images
                ]
                
                if any(pattern in img_url.lower() for pattern in skip_patterns):
                    continue
                
                # Clean up URL
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = 'https://www.flipkart.com' + img_url
                
                # Accept product images only
                if img_url.startswith('http') and len(img_url) > 10:
                    # Prefer product image domains
                    if any(x in img_url.lower() for x in ['rukminim', 'flixcart.com/image', '/image/']):
                        product_images.append(img_url)
            
            # Use first product image if found
            if product_images:
                img_src = product_images[0]
            elif all_found_images:
                # Fallback to any image if no product images
                for img_url in all_found_images:
                    img_url = img_url.strip()
                    if img_url.startswith('http') and 'logo' not in img_url.lower():
                        img_src = img_url
                        break
            
            # If found, save it
            if img_src:
                item_info['image'] = img_src
                logger.info(f"✅ IMAGE: {item_info.get('title', 'Unknown')[:25]} -> {img_src[:50]}")
            else:
                logger.warning(f"❌ NO IMG: {item_info.get('title', 'Unknown')[:40]} (searched {len(all_found_images)} images)")
                    
        except Exception as e:
            logger.error(f"Error extracting image: {e}")
        
        # ENHANCED PRICE EXTRACTION - Multiple strategies
        price_found = False
        
        # Strategy 1: Look in immediate parent
        if not price_found:
            try:
                parent = item_element.find_element(By.XPATH, './..')
                # Try multiple Flipkart price selectors
                price_selectors = [
                    "div._30jeq3", "span._30jeq3",  # Flipkart specific
                    "div._1vC4OE", "span._1vC4OE",  # Flipkart specific
                    "div._25b18c", "span._25b18c",  # Flipkart specific
                    "div[class*='_30jeq']", "span[class*='_30jeq']",
                    "div[class*='price']", "span[class*='price']",
                ]
                
                for selector in price_selectors:
                    try:
                        price_elem = parent.find_element(By.CSS_SELECTOR, selector)
                        price_text = price_elem.text.strip()
                        if price_text and ('₹' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                            if '₹' not in price_text and price_text.replace(',', '').replace('.', '').isdigit():
                                price_text = f'₹{price_text}'
                            item_info['price'] = price_text
                            price_found = True
                            break
                    except:
                        continue
            except:
                pass
        
        # Strategy 2: Look in section element
        if not price_found and section_element:
            try:
                # Get all text from section
                section_text = section_element.text
                if section_text and '₹' in section_text:
                    # Extract prices using regex
                    import re
                    price_pattern = r'₹[\d,]+(?:\.\d+)?'
                    prices = re.findall(price_pattern, section_text)
                    if prices:
                        item_info['price'] = prices[0]
                        price_found = True
            except:
                pass
        
        # Strategy 3: Look for any element with rupee symbol near the link
        if not price_found:
            try:
                # Expand search area
                ancestor = item_element.find_element(By.XPATH, './ancestor::div[3]')
                all_text_elems = ancestor.find_elements(By.CSS_SELECTOR, "div, span")
                
                for elem in all_text_elems:
                    try:
                        text = elem.text.strip()
                        if text and '₹' in text:
                            # Verify it looks like a price
                            import re
                            if re.search(r'₹\s*[\d,]+', text):
                                price_match = re.search(r'₹\s*[\d,]+', text)
                                if price_match:
                                    item_info['price'] = price_match.group(0).strip()
                                    price_found = True
                                    break
                    except:
                        continue
            except:
                pass
        
        # Extract discount
        try:
            parent = item_element.find_element(By.XPATH, './..')
            discount_selectors = [
                "div._3Ay6Sb", "span._3Ay6Sb",  # Flipkart specific
                "div[class*='discount']", "span[class*='discount']",
                "div[class*='off']", "span[class*='off']",
            ]
            
            for selector in discount_selectors:
                try:
                    discount_elem = parent.find_element(By.CSS_SELECTOR, selector)
                    discount_text = discount_elem.text.strip()
                    if discount_text and ('%' in discount_text or 'off' in discount_text.lower()):
                        item_info['discount'] = discount_text
                        break
                except:
                    continue
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
                    parent = heading.find_element(By.XPATH, "./ancestor::div[contains(@class, '_1AtVbE') or contains(@class, '_2MlkI1') or contains(@data-testid, '')]")
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
        all_product_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/'], a[href*='/product/']")
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
    print(f"FLIPKART HOMEPAGE - COMPLETE PAGE SCRAPER")
    print(f"{'='*60}")
    print(f"Mode: {'Headless' if headless else 'Visible Browser'}")
    print(f"Max Items Per Section: {max_items}")
    print(f"Strategy: Scroll entire page + Multi-level extraction")
    print(f"{'='*60}\n")
    
    result = scrape_flipkart_homepage_deals(headless=headless, max_items_per_section=max_items)
    
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total Sections: {result.get('total_sections', 0)}")
    print(f"Total Items: {result.get('total_items', 0)}")
    
    if result.get('sections'):
        print(f"\nSections Found:")
        for i, section in enumerate(result['sections'][:5], 1):
            print(f"   {i}. {section['section_title']} ({section['item_count']} items)")
        if len(result['sections']) > 5:
            print(f"   ... and {len(result['sections']) - 5} more sections")
    
    print(f"\nSaved to: flipkart_homepage_deals.json")
    print(f"{'='*60}\n")

def extract_product_info_with_price(link_element, parent_element):
    """Extract product information with enhanced price detection"""
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
        
        # Extract title - try multiple methods
        title_selectors = [
            # Aria label
            "aria-label",
            # Image alt text
            "img[alt]",
            # Text content
            "span", "div", "p", "h1", "h2", "h3", "h4", "h5", "h6"
        ]
        
        title_found = False
        for selector in title_selectors:
            try:
                if selector == "aria-label":
                    title = link_element.get_attribute('aria-label')
                    if title and len(title) > 5:
                        product_info['title'] = title.strip()
                        title_found = True
                        break
                elif selector.startswith("img"):
                    img_elem = link_element.find_element(By.CSS_SELECTOR, selector)
                    title = img_elem.get_attribute('alt')
                    if title and len(title) > 5:
                        product_info['title'] = title.strip()
                        title_found = True
                        break
                else:
                    text_elem = link_element.find_element(By.CSS_SELECTOR, selector)
                    title = text_elem.text.strip()
                    if title and len(title) > 5:
                        product_info['title'] = title
                        title_found = True
                        break
            except:
                continue
        
        # If no title found in link, try parent element
        if not title_found and parent_element:
            try:
                # Look for text in parent
                parent_text = parent_element.text.strip()
                if parent_text and len(parent_text) > 5:
                    # Take first line or first 50 chars
                    lines = parent_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 5 and len(line) < 100:
                            product_info['title'] = line
                            break
            except:
                pass
        
        # Extract image
        try:
            img_elem = link_element.find_element(By.CSS_SELECTOR, "img")
            product_info['image'] = img_elem.get_attribute('src') or ''
        except:
            pass
        
        # Enhanced price extraction - look in parent element first
        if parent_element:
            try:
                # Get all text elements in parent
                all_elements = parent_element.find_elements(By.CSS_SELECTOR, "*")
                price_candidates = []
                
                for elem in all_elements:
                    try:
                        text = elem.text.strip()
                        if text and ('₹' in text or 'Rs' in text or 'INR' in text):
                            # Check if it looks like a price
                            clean_text = text.replace('₹', '').replace('Rs', '').replace('INR', '').replace(',', '').replace('*', '').strip()
                            if clean_text and clean_text.replace('.', '').isdigit():
                                price_candidates.append(text)
                    except:
                        continue
                
                # Take the first valid price
                if price_candidates:
                    product_info['price'] = price_candidates[0]
                
                # Also try specific selectors
                if not product_info['price']:
                    price_selectors = [
                        "span[class*='_30jeq3']", "div[class*='_30jeq3']", # Flipkart specific
                        "span[class*='_1vC4OE']", "div[class*='_1vC4OE']", # Flipkart specific
                        "span[class*='_25b18c']", "div[class*='_25b18c']", # Flipkart specific
                        "span[class*='_3tbKJd']", "div[class*='_3tbKJd']", # Flipkart specific
                        "span[class*='_2tW1I0']", "div[class*='_2tW1I0']", # Flipkart specific
                        "span[class*='price']", "div[class*='price']", # Generic
                        "span[class*='amount']", "div[class*='amount']", # Generic
                        "span[class*='cost']", "div[class*='cost']" # Generic
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
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
        if parent_element:
            try:
                discount_selectors = [
                    "span[class*='_3Ay6Sb']", "div[class*='_3Ay6Sb']", # Flipkart specific
                    "span[class*='discount']", "div[class*='discount']", # Generic
                    "span[class*='off']", "div[class*='off']", # Generic
                    "span[class*='save']", "div[class*='save']" # Generic
                ]
                
                for selector in discount_selectors:
                    try:
                        discount_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
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

def extract_products_from_deal_container(container, driver, max_items):
    """Extract products from a deal container"""
    products = []
    try:
        # Look for product links in this container
        product_links = container.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
        
        for link in product_links[:max_items]:
            product_info = extract_product_info_with_price(link, container)
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
                            if numbers and any(len(num.replace(',', '')) >= 3 for num in numbers):
                                price_candidates.append(text)
                    except:
                        continue
                
                # Take the first valid price
                if price_candidates:
                    product_info['price'] = price_candidates[0]
                
                # Also try specific selectors
                if not product_info['price']:
                    price_selectors = [
                        "span[class*='_30jeq3']", "div[class*='_30jeq3']", # Flipkart specific
                        "span[class*='_1vC4OE']", "div[class*='_1vC4OE']", # Flipkart specific
                        "span[class*='_25b18c']", "div[class*='_25b18c']", # Flipkart specific
                        "span[class*='_3tbKJd']", "div[class*='_3tbKJd']", # Flipkart specific
                        "span[class*='_2tW1I0']", "div[class*='_2tW1I0']", # Flipkart specific
                        "span[class*='price']", "div[class*='price']", # Generic
                        "span[class*='amount']", "div[class*='amount']", # Generic
                        "span[class*='cost']", "div[class*='cost']" # Generic
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
                    "span[class*='_3Ay6Sb']", "div[class*='_3Ay6Sb']", # Flipkart specific
                    "span[class*='discount']", "div[class*='discount']", # Generic
                    "span[class*='off']", "div[class*='off']", # Generic
                    "span[class*='save']", "div[class*='save']" # Generic
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
    """Extract product title from Flipkart URL"""
    try:
        if not url or '/p/' not in url:
            return ''
        
        # Extract the product part from URL
        # Example: https://www.flipkart.com/samsung-galaxy-f36-5g-black-128-gb/p/itm...
        parts = url.split('/p/')[0].split('/')
        
        # Get the last part which should be the product name
        product_part = parts[-1] if parts else ''
        
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
