#!/usr/bin/env python3
"""
flipkart_search.py
Usage:
  python flipkart_search.py "iphone 14"
or
  python flipkart_search.py   # then type query when prompted
"""

import sys
import time
import json
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def create_driver(headless: bool = False) -> webdriver.Chrome:
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        # Try with ChromeDriverManager first
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Flipkart WebDriver initialized with ChromeDriverManager")
    except Exception as e:
        print(f"ChromeDriverManager failed: {e}")
        try:
            # Fallback to system ChromeDriver
            driver = webdriver.Chrome(options=chrome_options)
            print("Flipkart WebDriver initialized with system ChromeDriver")
        except Exception as e2:
            print(f"All ChromeDriver methods failed: {e2}")
            raise e2
    
    # Execute JavaScript to remove webdriver properties
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("delete navigator.__proto__.webdriver")
    
    return driver

def extract_product_details(driver: webdriver.Chrome) -> dict:
    """Extract detailed product information from a product page"""
    product_details = {
        "name": "",
        "price": "",
        "mrp": "",
        "discount_percentage": "",
        "discount_amount": "",
        "brand": "",
        "category": "",
        "rating": "",
        "reviews_count": "",
        "availability": "",
        "link": driver.current_url,
        "images": [],
        "specifications": {}
    }
    
    try:
        # Wait for page to fully load
        time.sleep(2)
        
        # Extract product name - try multiple selectors
        name_selectors = [
            "span.B_NuCI",  # Main product title
            "h1[class*='B_NuCI']",
            "h1",
            "span[class*='B_NuCI']",
            "div[class*='B_NuCI']",
            "div[data-automation-id='product-title']",
            "h1[data-automation-id='product-title']",
            "span[data-automation-id='product-title']"
        ]
        
        for selector in name_selectors:
            try:
                name_elem = driver.find_element(By.CSS_SELECTOR, selector)
                name_text = name_elem.text.strip()
                if name_text and len(name_text) > 5:
                    product_details["name"] = name_text
                    print(f"    Found name: {name_text}")
                    break
            except:
                continue
        
        # Extract price - comprehensive selectors with MRP and discount handling
        price_selectors = [
            "div._30jeq3",  # Main price
            "div[class*='_30jeq3']",
            "span[class*='_30jeq3']",
            "div[class*='_25b18c']",
            "span[class*='_25b18c']",
            "div[class*='_16Jk6d']",  # Alternative price selector
            "span[class*='_16Jk6d']",
            "div[class*='_1vC4OE']",  # Another price selector
            "span[class*='_1vC4OE']",
            "div[data-automation-id='product-price']",
            "span[data-automation-id='product-price']",
            "div[class*='price']",
            "span[class*='price']"
        ]
        
        # Extract current price and MRP separately
        current_price = ""
        mrp_price = ""
        
        for selector in price_selectors:
            try:
                price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text):
                    # Check if this is likely the current price (not struck through)
                    try:
                        parent_elem = price_elem.find_element(By.XPATH, "./..")
                        parent_classes = parent_elem.get_attribute('class') or ''
                        
                        # If parent has strikethrough, it's likely MRP
                        if 'strike' in parent_classes.lower() or 'mrp' in parent_classes.lower():
                            if not mrp_price:
                                mrp_price = price_text
                                print(f"    Found MRP: {price_text}")
                        else:
                            if not current_price:
                                current_price = price_text
                                print(f"    Found current price: {price_text}")
                    except:
                        # If we can't determine, assume it's current price
                        if not current_price:
                            current_price = price_text
                            
            except:
                continue
        
        # Set the final price - prioritize current price over MRP
        if current_price:
            product_details["price"] = current_price
            if mrp_price:
                product_details["mrp"] = mrp_price
                # Calculate discount percentage
                try:
                    current_num = float(current_price.replace('₹', '').replace(',', '').replace('Rs', '').strip())
                    mrp_num = float(mrp_price.replace('₹', '').replace(',', '').replace('Rs', '').strip())
                    if mrp_num > current_num:
                        discount_percent = ((mrp_num - current_num) / mrp_num) * 100
                        product_details["discount_percentage"] = f"{discount_percent:.0f}% off"
                        product_details["discount_amount"] = f"₹{mrp_num - current_num:,.0f}"
                        print(f"    Calculated discount: {product_details['discount_percentage']} (₹{product_details['discount_amount']} off)")
                except:
                    pass
        elif mrp_price:
            product_details["price"] = mrp_price
            print(f"    Warning: Only MRP found, no current price detected")
        
        # Extract brand (from breadcrumbs or product name)
        try:
            breadcrumb_selectors = [
                "a._2whKao",  # Original breadcrumb selector
                "a[class*='_2whKao']",
                "nav a",  # Any nav link
                "div[class*='breadcrumb'] a",
                "ol[class*='breadcrumb'] a"
            ]
            
            breadcrumbs = []
            for selector in breadcrumb_selectors:
                try:
                    breadcrumbs = driver.find_elements(By.CSS_SELECTOR, selector)
                    if breadcrumbs:
                        break
                except:
                    continue
            
            if breadcrumbs:
                # Look for brand in breadcrumbs (usually second or third item)
                for crumb in breadcrumbs[1:3]:
                    crumb_text = crumb.text.strip()
                    if crumb_text and len(crumb_text) < 20:  # Brand names are usually short
                        product_details["brand"] = crumb_text
                        print(f"    Found brand from breadcrumb: {crumb_text}")
                        break
        except:
            pass
        
        # Extract category (from breadcrumbs)
        try:
            if breadcrumbs:
                # Category is usually the first breadcrumb
                category_text = breadcrumbs[0].text.strip()
                if category_text:
                    product_details["category"] = category_text
                    print(f"    Found category: {category_text}")
        except:
            pass
        
        # Extract reviews count
        try:
            review_count_selectors = [
                "span._2_R_DZ",  # Reviews count
                "span[class*='_2_R_DZ']",
                "div[class*='_2_R_DZ']",
                "span[class*='review']",
                "div[class*='review']",
                "span[class*='rating']",
                "div[class*='rating']"
            ]
            
            for selector in review_count_selectors:
                try:
                    review_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    review_text = review_elem.text.strip()
                    if review_text and ('rating' in review_text.lower() or 'review' in review_text.lower() or ',' in review_text):
                        product_details["reviews_count"] = review_text
                        print(f"    Found reviews count: {review_text}")
                        break
                except:
                    continue
        except:
            pass
        
        # Extract availability
        try:
            availability_selectors = [
                "span[class*='availability']",
                "div[class*='availability']",
                "span[class*='stock']",
                "div[class*='stock']",
                "span[class*='delivery']",
                "div[class*='delivery']"
            ]
            
            for selector in availability_selectors:
                try:
                    avail_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    avail_text = avail_elem.text.strip()
                    if avail_text and ('stock' in avail_text.lower() or 'available' in avail_text.lower() or 'delivery' in avail_text.lower()):
                        product_details["availability"] = avail_text
                        print(f"    Found availability: {avail_text}")
                        break
                except:
                    continue
        except:
            pass
        
        # Extract rating - enhanced selectors for better accuracy
        rating_selectors = [
            "div._3LWZlK",  # Main rating stars
            "span._3LWZlK",  # Rating text
            "div[class*='_3LWZlK']",
            "span[class*='_3LWZlK']",
            "div[class*='_2d4LTz']",  # Alternative rating selector
            "span[class*='_2d4LTz']",
            "div[class*='_3uSWvM']",  # Another rating selector
            "span[class*='_3uSWvM']",
            "div[class*='rating']",
            "span[class*='rating']",
            "div[data-automation-id='product-rating']",
            "span[data-automation-id='product-rating']",
            "div[class*='_1i0wkb']",  # New Flipkart rating selector
            "span[class*='_1i0wkb']"
        ]
        
        for selector in rating_selectors:
            try:
                rating_elem = driver.find_element(By.CSS_SELECTOR, selector)
                rating_text = rating_elem.text.strip()
                # More lenient validation for ratings
                if rating_text and len(rating_text) > 0:
                    # Check if it looks like a rating (number with optional decimal)
                    import re
                    if re.match(r'^\d+(\.\d+)?$', rating_text) and float(rating_text) <= 5.0:
                        product_details["rating"] = rating_text
                        print(f"    Found rating: {rating_text}")
                        break
            except:
                continue
        
        # If brand not found in breadcrumbs, try to extract from product name
        if not product_details["brand"] and product_details["name"]:
            name_parts = product_details["name"].split()
            if name_parts:
                # Enhanced brand extraction for clothing and general products
                common_brands = [
                    # International clothing brands
                    "Nike", "Adidas", "Puma", "Reebok", "Converse", "Vans", "New Balance", "Under Armour", "Skechers", "Fila", "Jordan", "Champion", 
                    "Levi's", "Tommy Hilfiger", "Calvin Klein", "H&M", "Zara", "Forever 21", "Uniqlo", "Gap", "American Eagle", "Hollister", "Abercrombie", 
                    "Ralph Lauren", "Lacoste", "Polo", "Gucci", "Prada", "Versace", "Armani", "Hugo Boss", "Diesel", "Guess", "Michael Kors", "Coach", 
                    "Kate Spade", "Tory Burch", "Ray-Ban", "Oakley", "Asics", "Mizuno", "Brooks", "Saucony",
                    # Indian clothing brands
                    "Allen Solly", "Van Heusen", "Peter England", "Louis Philippe", "Arrow", "Park Avenue", "Blackberrys", "Red Tape", "Campus Sutra",
                    "The Bear House", "The Indian Garage Co", "Hellcat", "Turtle", "Glitchez", "Vebnor", "Dhaduk", "Stoneberg", "STI", "Rare Rabbit",
                    # Tech brands
                    "Apple", "Samsung", "OnePlus", "Xiaomi", "Realme", "Vivo", "Oppo", "Motorola", "Nokia", "Sony", "LG", "HP", "Dell", "Lenovo", "Asus", "Acer", "MSI", "Google", "Nothing", "Honor", "POCO"
                ]
                for brand in common_brands:
                    if brand.lower() in product_details["name"].lower():
                        product_details["brand"] = brand
                        print(f"    Found brand from name: {brand}")
                        break
                
                # If still no brand found, try to extract from URL or first word
                if not product_details["brand"]:
                    # Try to extract brand from URL
                    url_parts = driver.current_url.split('/')
                    for part in url_parts:
                        if part and len(part) > 2 and not part.isdigit() and part not in ['www.flipkart.com', 'search', 'q', 'store', 'clo', 'ash', 'axc']:
                            # Check if it looks like a brand name
                            if not any(word in part.lower() for word in ['men', 'women', 'boys', 'girls', 'kids', 'unisex', 'shirt', 'shirts']):
                                product_details["brand"] = part.replace('-', ' ').replace('+', ' ').title()
                                print(f"    Extracted brand from URL: {product_details['brand']}")
                                break
                    
                    # If still no brand, try first word of product name
                    if not product_details["brand"] and name_parts:
                        first_word = name_parts[0]
                        if len(first_word) > 2 and not first_word.lower() in ['men', 'women', 'boys', 'girls', 'kids', 'unisex']:
                            product_details["brand"] = first_word.title()
                            print(f"    Extracted brand from first word: {product_details['brand']}")
        
        # Extract product images
        try:
            print(f"    Starting image extraction...")
            
            # Wait a bit more for images to load
            time.sleep(1)
            
            image_selectors = [
                "img._396cs4",  # Main product image
                "img[class*='_396cs4']",  # Alternative main image
                "img._2r_T1I",  # Product gallery images
                "img[class*='_2r_T1I']",  # Alternative gallery images
                "img[class*='product-image']",  # Generic product image
                "img[class*='_1BweB8']",  # Another image selector
                "img[class*='_2d1DkJ']",  # Another image selector
                "img[class*='_3exPp9']",  # Another image selector
                "img[class*='_2QcJZg']",  # Another image selector
                "img[class*='_3n6B0X']",  # Another image selector
            ]
            
            all_images = []
            found_images = set()  # To track unique images
            
            for selector in image_selectors:
                try:
                    images = driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"    Found {len(images)} images with selector: {selector}")
                    
                    for img in images:
                        try:
                            img_src = img.get_attribute('src')
                            img_alt = img.get_attribute('alt') or ''
                            
                            # Debug: print image source
                            if img_src:
                                print(f"      Image src: {img_src[:100]}...")
                            
                            # Filter out placeholder images and get only product images
                            if img_src and ('flipkart' in img_src.lower() or 'rukminim' in img_src.lower()) and 'placeholder' not in img_src.lower():
                                # Get high-resolution image URL
                                if 'image' in img_src and 'q=' in img_src:
                                    # Replace quality parameter to get higher resolution
                                    high_res_src = img_src.replace('q=70', 'q=100').replace('q=50', 'q=100')
                                else:
                                    high_res_src = img_src
                                
                                # Avoid duplicates
                                if high_res_src not in found_images:
                                    found_images.add(high_res_src)
                                    
                                    image_info = {
                                        "url": high_res_src,
                                        "alt": img_alt,
                                        "thumbnail": img_src
                                    }
                                    
                                    all_images.append(image_info)
                                    print(f"      Added image: {img_alt[:50]}...")
                                    
                        except Exception as img_error:
                            print(f"      Error processing image: {img_error}")
                            continue
                                
                except Exception as e:
                    print(f"    Error with selector {selector}: {e}")
                    continue
            
            # Also try to find images using XPath
            try:
                print(f"    Trying XPath image extraction...")
                xpath_images = driver.find_elements(By.XPATH, "//img[contains(@src, 'flipkart') or contains(@src, 'rukminim')]")
                print(f"    Found {len(xpath_images)} images via XPath")
                
                for img in xpath_images:
                    try:
                        img_src = img.get_attribute('src')
                        img_alt = img.get_attribute('alt') or ''
                        
                        if img_src and 'placeholder' not in img_src.lower():
                            high_res_src = img_src.replace('q=70', 'q=100').replace('q=50', 'q=100')
                            
                            if high_res_src not in found_images:
                                found_images.add(high_res_src)
                                
                                image_info = {
                                    "url": high_res_src,
                                    "alt": img_alt,
                                    "thumbnail": img_src
                                }
                                
                                all_images.append(image_info)
                                print(f"      Added XPath image: {img_alt[:50]}...")
                    except:
                        continue
            except Exception as xpath_error:
                print(f"    XPath image extraction error: {xpath_error}")
            
            # Limit to first 8 images to avoid too much data
            product_details["images"] = all_images[:8]
            print(f"    Final result: Found {len(product_details['images'])} product images")
            
            # Debug: print first image URL if available
            if product_details["images"]:
                print(f"    First image URL: {product_details['images'][0]['url']}")
            
        except Exception as e:
            print(f"    Error extracting images: {e}")
            product_details["images"] = []
        
        # Extract specifications
        try:
            print(f"    Extracting specifications...")
            
            spec_selectors = [
                "div[class*='specification'] table tr",  # Specification table rows
                "div[class*='specification'] div",  # Specification divs
                "div[class*='details'] table tr",  # Details table rows
                "div[class*='details'] div",  # Details divs
                "div[class*='features'] div",  # Features divs
                "div[class*='product-features'] div"  # Product features divs
            ]
            
            specifications = {}
            
            for selector in spec_selectors:
                try:
                    spec_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in spec_elements:
                        text = elem.text.strip()
                        if text and len(text) > 10 and ':' in text:
                            # Try to parse key-value pairs
                            parts = text.split(':', 1)
                            if len(parts) == 2:
                                key = parts[0].strip()
                                value = parts[1].strip()
                                if key and value:
                                    specifications[key] = value
                    if specifications:
                        break
                except:
                    continue
            
            product_details["specifications"] = specifications
            print(f"    Found {len(specifications)} specifications")
            
        except Exception as e:
            print(f"    Error extracting specifications: {e}")
            product_details["specifications"] = {}
        
        # Debug: Print what we found
        print(f"    Final extracted data: {product_details}")
        
    except Exception as e:
        print(f"    Error extracting product details: {e}")
    
    return product_details

def close_flipkart_login_popup(driver: webdriver.Chrome, timeout: int = 5):
    """Flipkart usually shows a login modal. This attempts to close it."""
    try:
        wait = WebDriverWait(driver, timeout)
        # The close button '✕' is usually a button or span near a modal; try a few common selectors:
        selectors = [
            "button._2KpZ6l._2doB4z",          # class-based close (common)
            "button._2KpZ6l._2doB4z",         # same fallback
            "button._2KpZ6l._2doB4z",         # repeated intentionally
            "button[aria-label='Close']",
            "button[title='Close']",
            "button:contains('✕')",           # not supported by selenium, kept for reference
        ]
        # A more robust approach: try to find any button inside modal container and click the first visible one.
        # We'll attempt some targeted selectors used on Flipkart:
        try:
            close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button._2KpZ6l._2doB4z")))
            close_btn.click()
            return
        except Exception:
            # fallback: try to click the overlay close if present
            try:
                # a generic attempt: find close icon element by xpath for '✕' symbol
                el = driver.find_element(By.XPATH, "//button[contains(., '✕') or contains(., 'Close')]")
                el.click()
                return
            except Exception:
                # nothing to do; maybe popup not present
                return
    except TimeoutException:
        return

def search_flipkart(query: str, headless: bool = False, max_results: int = 20):
    """
    Search Flipkart and return structured product data (like Meesho approach)
    Returns: dict with products in the format expected by intelligent search system
    """
    driver = create_driver(headless=headless)
    try:
        print(f"Searching Flipkart for: {query}")
        
        # Navigate directly to search URL (like Meesho approach)
        search_url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
        driver.get(search_url)
        time.sleep(5)

        # Close login popup if present
        close_flipkart_login_popup(driver)

        # Wait for search results to load
        print("Waiting for search results to load...")
        time.sleep(5)
        
        # Save the HTML content of the search results page
        html_content = driver.page_source
        filename = f"flipkart_search_{query.replace(' ', '_')}.html"
        
        # Write HTML to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nSearch results saved as: {filename}")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Extract product information from search results page (like Meesho)
        products_info = []
        
        # Try different selectors for product cards (updated for new Flipkart structure)
        product_selectors = [
            "a.CGtC98",  # Main product link containers (NEW)
            "div[data-id]",  # Product containers with data-id
            "div.tUxRFH",  # Product card containers (NEW)
            "a[href*='/p/']",  # Product links (NEW)
        ]
        
        product_cards = []
        for selector in product_selectors:
            try:
                cards = driver.find_elements(By.CSS_SELECTOR, selector)
                if cards and len(cards) > 1:  # More than 1 to avoid header/footer elements
                    product_cards = cards
                    print(f"Found {len(cards)} product cards using selector: {selector}")
                    break
            except Exception:
                continue
        
        if not product_cards:
            print("No product cards found with standard selectors.")
            return
        
        # Debug: Let's see what's actually in the first card
        if product_cards:
            print(f"\nDebugging first product card:")
            first_card = product_cards[0]
            print(f"Card HTML snippet: {first_card.get_attribute('outerHTML')[:500]}...")
            
            # Try to find any text content in the card
            all_text = first_card.text.strip()
            print(f"All text in first card: {all_text[:200]}...")
        
        # Extract information from each product card (simplified like Meesho)
        for i, card in enumerate(product_cards[:max_results]):
            try:
                product_info = {}
                
                # Extract title from card text - the product name is on line 2
                card_text = card.text.strip()
                lines = card_text.split('\n')
                
                # Line 1: "Add to Compare" (skip)
                # Line 2: Product name (this is what we want)
                # Line 3: Ratings
                # Line 4+: Specifications
                
                if len(lines) >= 2:
                    potential_title = lines[1].strip()
                    if (potential_title and len(potential_title) > 10 and 
                        not potential_title.startswith('₹') and 
                        not potential_title.endswith('%') and
                        'rating' not in potential_title.lower() and
                        'review' not in potential_title.lower()):
                        product_info['title'] = potential_title
                
                # Extract brand from title if we have one
                if product_info.get('title'):
                    title = product_info['title']
                    # Enhanced brand list including common laptop/electronics brands
                    common_brands = [
                        # Electronics/Laptop brands
                        "HP", "Dell", "Lenovo", "Asus", "ASUS", "Acer", "MSI", "Apple", "Samsung", "Sony", "LG", 
                        "Toshiba", "Fujitsu", "Alienware", "Razer", "Microsoft", "Surface", "Huawei", "Honor",
                        "Xiaomi", "Realme", "OnePlus", "Oppo", "Vivo", "Motorola", "Nokia", "Google", "Nothing",
                        "JBL", "Boat", "Sennheiser", "Philips", "Panasonic", "Canon", "Nikon", "Flipkart",
                        # Clothing brands  
                        "Arrow", "Van Heusen", "Peter England", "Louis Philippe", "Allen Solly", "Park Avenue",
                        "Nike", "Adidas", "Puma", "Reebok", "Converse", "Levi's", "Tommy Hilfiger", "Calvin Klein"
                    ]
                    for brand in common_brands:
                        if brand.lower() in title.lower():
                            product_info['brand'] = brand
                            break
                    
                    # If no brand found, try first word
                    if not product_info.get('brand'):
                        title_words = title.split()
                        if title_words and len(title_words[0]) > 2:
                            product_info['brand'] = title_words[0]
                
                # If title is "Add to Compare" or similar, try to get from image alt text
                if (not product_info.get('title') or 
                    product_info.get('title') in ['Add to Compare', 'View Product', 'Bestseller', 'Compare']):
                    try:
                        img_elem = card.find_element(By.TAG_NAME, "img")
                        img_alt = img_elem.get_attribute('alt') or ''
                        if img_alt and len(img_alt) > 10:
                            # Clean up the alt text to get just the product name
                            product_name = img_alt.split(' - ')[0].strip()  # Take first part before dash
                            if product_name and len(product_name) > 5:
                                product_info['title'] = product_name
                                # Re-extract brand from new title
                                title = product_info['title']
                                common_brands = [
                                    "HP", "Dell", "Lenovo", "Asus", "ASUS", "Acer", "MSI", "Apple", "Samsung", "Sony", "LG", 
                                    "Toshiba", "Fujitsu", "Alienware", "Razer", "Microsoft", "Surface", "Huawei", "Honor",
                                    "Xiaomi", "Realme", "OnePlus", "Oppo", "Vivo", "Motorola", "Nokia", "Google", "Nothing"
                                ]
                                for brand in common_brands:
                                    if brand.lower() in title.lower():
                                        product_info['brand'] = brand
                                        break
                                
                                # If no brand found, try first word
                                if not product_info.get('brand') or product_info.get('brand') == 'Add':
                                    title_words = title.split()
                                    if title_words and len(title_words[0]) > 2:
                                        product_info['brand'] = title_words[0]
                    except:
                        pass
                
                # If still no title, try to extract from link URL (Flipkart URLs contain product names)
                if not product_info.get('title'):
                    try:
                        link = product_info.get('link', '')
                        if link and '/p/' in link:
                            # Extract product name from URL path
                            url_parts = link.split('/p/')
                            if len(url_parts) > 1:
                                product_slug = url_parts[1].split('/')[0]
                                # Convert slug to readable name
                                product_name = product_slug.replace('-', ' ').title()
                                if product_name and len(product_name) > 5:
                                    product_info['title'] = product_name
                    except:
                        pass
                
                # If still no title found, try to get it from the card's text content (like Meesho)
                if not product_info.get('title'):
                    try:
                        card_text = card.text.strip()
                        lines = card_text.split('\n')
                        # First pass: look for actual product names (longer, descriptive text)
                        for line in lines:
                            line = line.strip()
                            # Look for product names (longer text, not variants or prices)
                            if (line and len(line) > 15 and len(line) < 100 and 
                                not line.startswith('₹') and 
                                not line.startswith('%') and 
                                not line.endswith('%') and
                                not line.endswith('off') and
                                'off' not in line.lower() and 
                                'delivery' not in line.lower() and 
                                'reviews' not in line.lower() and
                                'rating' not in line.lower() and
                                'free' not in line.lower() and
                                ':' not in line and  # Skip time formats
                                not line.replace(':', '').replace('h', '').replace('m', '').replace('s', '').replace(' ', '').isdigit() and
                                not line.lower().startswith('pack of') and  # Skip variants
                                not line.lower().startswith('buy') and
                                not line.lower().startswith('top discount') and
                                not line.lower().startswith('sponsored') and
                                not line.lower().startswith('assured') and
                                line not in ['Bestseller', 'Add to Compare', 'View Product', 'Currently unavailable', 'Out of stock', 'Not available']):  # Skip common UI text
                                product_info['title'] = line
                                break
                        
                        # Fallback: if no product name found, use the first meaningful line
                        if not product_info.get('title'):
                            for line in lines:
                                line = line.strip()
                                if (line and len(line) > 5 and len(line) < 100 and 
                                    not line.startswith('₹') and 
                                    not line.startswith('%') and 
                                    not line.endswith('%') and
                                    not line.endswith('off') and
                                    'off' not in line.lower() and 
                                    'delivery' not in line.lower() and 
                                    'reviews' not in line.lower() and
                                    'rating' not in line.lower() and
                                    'free' not in line.lower() and
                                    ':' not in line and  # Skip time formats
                                    not line.replace(':', '').replace('h', '').replace('m', '').replace('s', '').replace(' ', '').isdigit() and
                                    not line.lower().startswith('buy') and
                                    not line.lower().startswith('top discount') and
                                    line not in ['Bestseller', 'Add to Compare', 'View Product', 'Currently unavailable', 'Out of stock', 'Not available']):  # Skip common UI text
                                    product_info['title'] = line
                                    break
                    except:
                        pass
                
                # Extract price information - Enhanced to get MRP and discounts
                try:
                    import re
                    
                    # Look for price patterns in each line
                    for line in lines:
                        line = line.strip()
                        
                        # Look for multiple prices in one line like "₹1,732₹2,54731% off"
                        # Enhanced approach to handle various price formats
                        if '₹' in line and line.count('₹') >= 2:
                            # Use regex to find all price patterns more accurately
                            price_pattern = r'₹[\d,]+'
                            all_prices = re.findall(price_pattern, line)
                            
                            if len(all_prices) >= 2:
                                # Clean up prices - be more careful about removing discount percentages
                                clean_prices = []
                                for i, price in enumerate(all_prices):
                                    # For the last price, check if it has discount percentage attached
                                    if i == len(all_prices) - 1:
                                        # Look for pattern like ₹54948 where 48 might be discount %
                                        # Only remove if the last 2 digits are reasonable discount percentage
                                        price_num = price.replace('₹', '').replace(',', '')
                                        if len(price_num) > 4:
                                            last_two = price_num[-2:]
                                            if last_two.isdigit() and 1 <= int(last_two) <= 95:
                                                # This looks like discount percentage, remove it
                                                clean_price_num = price_num[:-2]
                                                clean_prices.append('₹' + clean_price_num)
                                            else:
                                                clean_prices.append(price)
                                        else:
                                            clean_prices.append(price)
                                    else:
                                        clean_prices.append(price)
                                
                                if len(clean_prices) >= 2:
                                    product_info['price'] = clean_prices[0]
                                    product_info['mrp'] = clean_prices[1]
                                    print(f"    Found current price: {clean_prices[0]}")
                                    print(f"    Found MRP: {clean_prices[1]}")
                                    
                                    # Look for discount percentage in the same line
                                    discount_match = re.search(r'(\d{1,2})%', line)
                                    if discount_match:
                                        discount_val = int(discount_match.group(1))
                                        if 1 <= discount_val <= 95:
                                            product_info['discount_percentage'] = discount_match.group(1) + '%'
                                            print(f"    Found discount: {product_info['discount_percentage']}")
                                    
                                    # Calculate discount amount if we have both prices
                                    try:
                                        current_num = float(product_info['price'].replace('₹', '').replace(',', ''))
                                        mrp_num = float(product_info['mrp'].replace('₹', '').replace(',', ''))
                                        if mrp_num > current_num:
                                            discount_amount = mrp_num - current_num
                                            product_info['discount_amount'] = f"₹{discount_amount:,.0f}"
                                            print(f"    Calculated discount amount: {product_info['discount_amount']}")
                                    except Exception as e:
                                        print(f"    Error calculating discount: {e}")
                                    break
                        
                        # Fallback: look for single price
                        elif line.startswith('₹') and len(line) < 20 and not product_info.get('price'):
                            price_match = re.search(r'₹[\d,]+', line)
                            if price_match:
                                product_info['price'] = price_match.group(0)
                                print(f"    Found current price: {price_match.group(0)}")
                        
                        # Look for standalone discount percentage
                        elif ('%' in line and not product_info.get('discount_percentage')):
                            discount_match = re.search(r'(\d{1,2})%', line)
                            if discount_match:
                                discount_val = int(discount_match.group(1))
                                if 1 <= discount_val <= 95:
                                    product_info['discount_percentage'] = discount_match.group(1) + '%'
                                    print(f"    Found discount: {product_info['discount_percentage']}")
                except:
                    pass
                
                # Extract rating from card text - enhanced to catch more rating formats
                if not product_info.get('rating'):
                    try:
                        import re
                        for line in lines:
                            line = line.strip()
                            
                            # Look for patterns like "4.1(590)" or "4.1(21,214)" - most common format
                            rating_match = re.search(r'(\d+\.?\d*)\s*\(([\d,]+)\)', line)
                            if rating_match:
                                rating = rating_match.group(1)
                                review_count = rating_match.group(2)
                                if float(rating) <= 5.0:
                                    product_info['rating'] = rating
                                    product_info['reviews_count'] = f"{rating}({review_count})"
                                    print(f"    Found rating: {rating} with {review_count} reviews")
                                    break
                            
                            # Look for patterns like "4.1 Ratings & 3 Reviews"
                            elif 'rating' in line.lower() and 'review' in line.lower():
                                rating_match = re.search(r'(\d+\.?\d*)', line)
                                if rating_match:
                                    rating = rating_match.group(1)
                                    if float(rating) <= 5.0:
                                        product_info['rating'] = rating
                                        product_info['reviews_count'] = line
                                        print(f"    Found rating: {rating} with reviews")
                                        break
                            
                            # Look for standalone rating numbers (fallback)
                            elif re.match(r'^\d+\.?\d*$', line) and len(line) <= 4:
                                try:
                                    rating_val = float(line)
                                    if 1.0 <= rating_val <= 5.0:
                                        product_info['rating'] = line
                                        print(f"    Found standalone rating: {line}")
                                        break
                                except:
                                    pass
                    except:
                        pass
                
                # Extract image URL with better quality
                try:
                    img_elem = card.find_element(By.TAG_NAME, "img")
                    img_src = img_elem.get_attribute('src') or ''
                    img_alt = img_elem.get_attribute('alt') or ''
                    
                    # Improve image quality by replacing quality parameters
                    if img_src and 'q=' in img_src:
                        # Replace quality parameter to get higher resolution
                        high_quality_src = img_src.replace('q=70', 'q=100').replace('q=50', 'q=100').replace('q=80', 'q=100')
                        product_info['image_url'] = high_quality_src
                        product_info['image_thumbnail'] = img_src  # Keep original as thumbnail
                    else:
                        product_info['image_url'] = img_src
                        product_info['image_thumbnail'] = img_src
                    
                    product_info['image_alt'] = img_alt
                    
                    # Use image alt text as product title if we don't have a good title yet
                    if img_alt and (not product_info.get('title') or 
                                   product_info.get('title', '').lower().startswith('pack of') or
                                   len(product_info.get('title', '')) < 10):
                        product_info['title'] = img_alt
                        print(f"    Using image alt as title: {img_alt[:50]}...")
                    else:
                        print(f"    Found image: {img_alt[:50]}...")
                except:
                    product_info['image_url'] = ''
                    product_info['image_alt'] = ''
                    product_info['image_thumbnail'] = ''
                
                # Extract product link - the card itself might be the link
                if not product_info.get('link'):
                    try:
                        # Check if the card element itself is an anchor tag
                        if card.tag_name.lower() == 'a':
                            href = card.get_attribute('href')
                            if href and '/p/' in href:
                                # Make sure it's a full URL
                                if href.startswith('/'):
                                    href = 'https://www.flipkart.com' + href
                                product_info['link'] = href
                    except:
                        pass
                
                # If still no link found, try to find anchor tags within the card (like Meesho)
                if not product_info.get('link'):
                    try:
                        # Look for any anchor tags within the card
                        link_elements = card.find_elements(By.TAG_NAME, "a")
                        for link_elem in link_elements:
                            href = link_elem.get_attribute('href')
                            if href and ('/p/' in href or 'flipkart.com' in href):
                                # Make sure it's a full URL
                                if href.startswith('/'):
                                    href = 'https://www.flipkart.com' + href
                                product_info['link'] = href
                                break
                    except:
                        pass
                
                # Extract brand (try to get from title or other elements) (like Meesho)
                try:
                    if product_info.get('title'):
                        # Enhanced brand list including clothing brands
                        common_brands = [
                            # Clothing brands
                            "SOPANI", "Arrow", "The Bear House", "STI", "Solstice", "Metronaut", "Rare Rabbit", "Park Avenue", "Allen Solly", 
                            "Van Heusen", "Peter England", "Louis Philippe", "Blackberrys", "Red Tape", "Campus Sutra", "The Indian Garage Co", 
                            "Hellcat", "Turtle", "Glitchez", "Vebnor", "Dhaduk", "Stoneberg", "Nike", "Adidas", "Puma", "Reebok", "Converse", 
                            "Vans", "New Balance", "Under Armour", "Skechers", "Fila", "Jordan", "Champion", "Levi's", "Tommy Hilfiger", 
                            "Calvin Klein", "H&M", "Zara", "Forever 21", "Uniqlo", "Gap", "American Eagle", "Hollister", "Abercrombie", 
                            "Ralph Lauren", "Lacoste", "Polo", "Gucci", "Prada", "Versace", "Armani", "Hugo Boss", "Diesel", "Guess", 
                            "Michael Kors", "Coach", "Kate Spade", "Tory Burch", "Ray-Ban", "Oakley", "Asics", "Mizuno", "Brooks", "Saucony",
                            # Tech brands
                            "Apple", "Samsung", "OnePlus", "Xiaomi", "Realme", "Vivo", "Oppo", "Motorola", "Nokia", "Sony", "LG", "HP", 
                            "Dell", "Lenovo", "Asus", "Acer", "MSI", "Google", "Nothing", "Honor", "POCO", "Redmi", "Mi", "JBL", "Boat", 
                            "Sennheiser", "Philips", "Panasonic", "Canon", "Nikon", "Flipkart"
                        ]
                        for brand in common_brands:
                            if brand.lower() in product_info['title'].lower():
                                product_info['brand'] = brand
                                break
                        
                        # If no brand found in common list, try to extract first word as brand
                        if not product_info.get('brand'):
                            title_words = product_info['title'].split()
                            if title_words:
                                # Take first word if it's not a common word or discount percentage
                                first_word = title_words[0].strip()
                                common_words = ["Modern", "Latest", "New", "Best", "Top", "Great", "Super", "Ultra", "Premium", "Quality", "Good", "Nice", "Cool", "Hot", "Trendy", "Stylish", "Fashionable", "Elegant", "Beautiful", "Amazing", "Wonderful", "Excellent", "Perfect", "Special", "Unique", "Exclusive", "Limited", "Classic", "Vintage", "Retro", "Contemporary", "Traditional", "Casual", "Formal", "Party", "Wedding", "Office", "Work", "Daily", "Everyday", "Weekend", "Holiday", "Summer", "Winter", "Spring", "Fall", "Seasonal", "Year", "Round", "MSI", "Acer", "Asus", "HP", "Dell", "Lenovo"]
                                
                                # Skip discount percentages and numbers
                                if (first_word not in common_words and 
                                    len(first_word) > 2 and 
                                    not first_word.replace('%', '').replace('off', '').isdigit() and
                                    not first_word.endswith('%') and
                                    not first_word.endswith('off')):
                                    product_info['brand'] = first_word
                                elif first_word in ["MSI", "Acer", "Asus"]:
                                    # These are valid laptop brands
                                    product_info['brand'] = first_word
                except:
                    pass
                
                # Extract category (try to infer from title) - Enhanced classification
                try:
                    if product_info.get('title'):
                        title_lower = product_info['title'].lower()
                        
                        # Electronics categories (prioritize specific terms)
                        if any(term in title_lower for term in ['laptop', 'notebook', 'ultrabook', 'gaming laptop', 'thin laptop', 'aspire', 'prestige', 'studio']):
                            product_info['category'] = 'Laptop'
                        elif any(term in title_lower for term in ['book4', 'galaxy book', 'motobook']):
                            # Specific laptop models
                            product_info['category'] = 'Laptop'
                        elif any(term in title_lower for term in ['mobile', 'smartphone', 'phone', 'iphone', 'android phone']):
                            product_info['category'] = 'Mobile'
                        elif any(term in title_lower for term in ['tablet', 'ipad']):
                            product_info['category'] = 'Tablet'
                        elif any(term in title_lower for term in ['headphone', 'earphone', 'speaker', 'audio', 'bluetooth']):
                            product_info['category'] = 'Audio'
                        elif any(term in title_lower for term in ['watch', 'smartwatch', 'fitness band']):
                            product_info['category'] = 'Watch'
                        elif any(term in title_lower for term in ['camera', 'dslr', 'lens']):
                            product_info['category'] = 'Camera'
                        elif any(term in title_lower for term in ['tv', 'television', 'smart tv']):
                            product_info['category'] = 'TV'
                        elif any(term in title_lower for term in ['refrigerator', 'fridge', 'washing machine', 'ac', 'air conditioner']):
                            product_info['category'] = 'Appliances'
                        elif any(term in title_lower for term in ['furniture', 'sofa', 'bed', 'table', 'chair']):
                            product_info['category'] = 'Furniture'
                        # Clothing categories
                        elif any(term in title_lower for term in ['saree', 'sari']):
                            product_info['category'] = 'Saree'
                        elif any(term in title_lower for term in ['shirt', 'formal shirt', 'casual shirt']):
                            product_info['category'] = 'Shirt'
                        elif any(term in title_lower for term in ['pant', 'trouser', 'formal pant']):
                            product_info['category'] = 'Pant'
                        elif any(term in title_lower for term in ['shoe', 'sneaker', 'boot', 'sandal', 'heel']):
                            product_info['category'] = 'Shoes'
                        elif any(term in title_lower for term in ['dress', 'gown', 'frock']):
                            product_info['category'] = 'Dress'
                        elif any(term in title_lower for term in ['kurta', 'kurti', 'ethnic wear']):
                            product_info['category'] = 'Kurta'
                        elif any(term in title_lower for term in ['jean', 'denim', 'jeans']):
                            product_info['category'] = 'Jeans'
                        elif any(term in title_lower for term in ['top', 'tshirt', 't-shirt', 'blouse']):
                            product_info['category'] = 'Top'
                        elif any(term in title_lower for term in ['bottom', 'legging', 'palazzo']):
                            product_info['category'] = 'Bottom'
                        elif any(term in title_lower for term in ['bag', 'purse', 'handbag', 'backpack']):
                            product_info['category'] = 'Bags'
                        elif any(term in title_lower for term in ['jewelry', 'necklace', 'ring', 'bracelet', 'earring']):
                            product_info['category'] = 'Jewelry'
                        else:
                            product_info['category'] = 'General'
                except:
                    pass
                
                # Extract reviews count (like Meesho)
                try:
                    card_text = card.text.strip()
                    lines = card_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if ('rating' in line.lower() or 'review' in line.lower()) and ',' in line:
                            product_info['reviews_count'] = line
                            break
                except:
                    pass
                
                # Extract availability and delivery information - Enhanced
                try:
                    card_text = card.text.strip()
                    lines = card_text.split('\n')
                    availability_found = False
                    delivery_found = False
                    
                    for line in lines:
                        line = line.strip()
                        
                        # Look for availability status
                        if not availability_found and any(term in line.lower() for term in ['delivery', 'stock', 'available', 'in stock', 'out of stock', 'currently unavailable', 'not available', 'bestseller', 'top discount']):
                            product_info['availability'] = line
                            availability_found = True
                            print(f"    Found availability: {line}")
                        
                        # Look for delivery information
                        elif not delivery_found and any(term in line.lower() for term in ['free delivery', 'express delivery', 'same day delivery', 'next day delivery', 'delivery by', 'shipping']):
                            product_info['delivery'] = line
                            delivery_found = True
                            print(f"    Found delivery: {line}")
                        
                        # Look for special offers or tags
                        elif any(term in line.lower() for term in ['top discount', 'bestseller', 'trending', 'new', 'launch', 'offer', 'deal']):
                            if not product_info.get('special_offers'):
                                product_info['special_offers'] = []
                            product_info['special_offers'].append(line)
                            print(f"    Found special offer: {line}")
                        
                        # If we found both, we can break
                        if availability_found and delivery_found:
                            break
                except:
                    pass
                
                # Extract product description and additional details
                try:
                    card_text = card.text.strip()
                    lines = card_text.split('\n')
                    
                    # Look for product descriptions (longer text that's not price/rating)
                    for line in lines:
                        line = line.strip()
                        if (len(line) > 20 and len(line) < 200 and 
                            not line.startswith('₹') and 
                            not re.match(r'^\d+\.?\d*\(\d+,\d+\)$', line) and  # Not rating format
                            not re.match(r'^\d+\.?\d*$', line) and  # Not standalone number
                            not line.lower().startswith('pack of') and
                            'channel' not in line.lower() and
                            'ml' not in line.lower() and
                            'glass' not in line.lower() and
                            'aluminium' not in line.lower()):
                            
                            if not product_info.get('description'):
                                product_info['description'] = line
                                print(f"    Found description: {line[:50]}...")
                                break
                except:
                    pass
                
                # Extract specifications from card text
                try:
                    specifications = []
                    card_text = card.text.strip()
                    lines = card_text.split('\n')
                    
                    # Look for specification-like lines (usually contain technical terms)
                    spec_keywords = ['gb', 'ram', 'storage', 'processor', 'intel', 'amd', 'windows', 'android', 'ios', 
                                   'display', 'screen', 'battery', 'camera', 'bluetooth', 'wifi', 'usb', 'hdmi']
                    
                    for line in lines:
                        line = line.strip()
                        # Skip prices, ratings, and UI text
                        if (line and len(line) > 10 and len(line) < 100 and
                            not line.startswith('₹') and 
                            not line.startswith('%') and 
                            not line.endswith('%') and
                            'rating' not in line.lower() and
                            'review' not in line.lower() and
                            'delivery' not in line.lower() and
                            'stock' not in line.lower() and
                            'available' not in line.lower() and
                            any(keyword in line.lower() for keyword in spec_keywords)):
                            specifications.append(line)
                    
                    if specifications:
                        product_info['specifications'] = specifications[:5]  # Limit to first 5 specs
                        print(f"    Found specifications: {len(specifications)} items")
                except:
                    pass
                
                # If we found any meaningful information, add it (like Meesho)
                if product_info.get('title') or product_info.get('price'):
                    products_info.append(product_info)
                    
            except Exception as e:
                print(f"Error extracting info from product {i+1}: {e}")
                continue
        
        # Display extracted information (like Meesho)
        if products_info:
            print(f"\n{'='*60}")
            print(f"EXTRACTED PRODUCT INFORMATION")
            print(f"{'='*60}")
            
            for i, product in enumerate(products_info, 1):
                print(f"\n{i}. {product.get('title', 'Title not found')}")
                print(f"   Price: {product.get('price', 'Price not found')}")
                if product.get('mrp'):
                    print(f"   MRP: {product['mrp']}")
                if product.get('discount_percentage'):
                    print(f"   Discount: {product['discount_percentage']}")
                if product.get('discount_amount'):
                    print(f"   You Save: {product['discount_amount']}")
                if product.get('rating'):
                    print(f"   Rating: {product['rating']}")
                if product.get('reviews_count'):
                    print(f"   Reviews: {product['reviews_count']}")
                if product.get('brand'):
                    print(f"   Brand: {product['brand']}")
                if product.get('category'):
                    print(f"   Category: {product['category']}")
                if product.get('availability'):
                    print(f"   Availability: {product['availability']}")
                if product.get('delivery'):
                    print(f"   Delivery: {product['delivery']}")
                if product.get('specifications'):
                    print(f"   Key Specs: {', '.join(product['specifications'][:3])}")
                if product.get('link'):
                    print(f"   Link: {product['link']}")
                if product.get('image_url'):
                    print(f"   Image: {product['image_url']}")
                print("-" * 50)
        else:
            print("No product information could be extracted.")

        # Display JSON data without saving to file (like Meesho)
        if products_info:
            json_data = {
                'query': query,
                'search_url': driver.current_url,
                'total_products': len(products_info),
                'products': products_info
            }
            print(f"\n{'='*60}")
            print(f"PRODUCT DATA (JSON FORMAT)")
            print(f"{'='*60}")
            print(json.dumps(json_data, indent=2, ensure_ascii=False))
            
            # Create detailed products from search results data (like Meesho)
            detailed_products = []
            
            print(f"\n{'='*60}")
            print(f"CREATING DETAILED PRODUCTS FROM SEARCH RESULTS")
            print(f"{'='*60}")
            
            # Take the first 3 products with the most complete information
            best_products = []
            for product in products_info:
                if product.get('title') and product.get('price'):
                    best_products.append(product)
                    if len(best_products) >= 3:
                        break
            
            for i, product in enumerate(best_products, 1):
                try:
                    print(f"\nProcessing product {i}: {product.get('title', 'Unknown')}")
                    
                    detailed_product = {
                        "name": product.get('title', ''),
                        "price": product.get('price', ''),
                        "mrp": product.get('mrp', ''),
                        "discount_percentage": product.get('discount_percentage', ''),
                        "discount_amount": product.get('discount_amount', ''),
                        "brand": product.get('brand', ''),
                        "category": product.get('category', ''),
                        "rating": product.get('rating', ''),
                        "reviews_count": product.get('reviews_count', ''),
                        "description": product.get('description', ''),
                        "availability": product.get('availability', ''),
                        "delivery": product.get('delivery', ''),
                        "special_offers": product.get('special_offers', []),
                        "specifications": product.get('specifications', []),
                        "link": product.get('link', ''),
                        "images": [{"url": product.get('image_url', ''), "alt": product.get('image_alt', ''), "thumbnail": product.get('image_thumbnail', '')}] if product.get('image_url') else []
                    }
                    
                    detailed_products.append(detailed_product)
                    print(f"✅ Successfully processed product {i}")
                    
                except Exception as e:
                    print(f"❌ Error processing product {i}: {e}")
                    continue
            
            # Display detailed product information
            if detailed_products:
                print(f"\n{'='*80}")
                print(f"FINAL RESULTS - {len(detailed_products)} PRODUCTS")
                print(f"{'='*80}")
                
                for i, product in enumerate(detailed_products, 1):
                    print(f"\n{i}. {product.get('name', 'Name not found')}")
                    print(f"   Price: {product.get('price', 'Price not found')}")
                    if product.get('mrp'):
                        print(f"   MRP: {product['mrp']}")
                    if product.get('discount_percentage'):
                        print(f"   Discount: {product['discount_percentage']}")
                    if product.get('discount_amount'):
                        print(f"   You Save: {product['discount_amount']}")
                    print(f"   Brand: {product.get('brand', 'Brand not found')}")
                    print(f"   Category: {product.get('category', 'Category not found')}")
                    print(f"   Rating: {product.get('rating', 'Rating not found')}")
                    if product.get('reviews_count'):
                        print(f"   Reviews: {product['reviews_count']}")
                    if product.get('description'):
                        print(f"   Description: {product['description'][:100]}...")
                    if product.get('availability'):
                        print(f"   Availability: {product['availability']}")
                    if product.get('delivery'):
                        print(f"   Delivery: {product['delivery']}")
                    if product.get('special_offers'):
                        print(f"   Special Offers: {', '.join(product['special_offers'])}")
                    if product.get('specifications'):
                        print(f"   Key Specs: {', '.join(product['specifications'][:3])}")
                    print(f"   Images: {len(product.get('images', []))} images found")
                    if product.get('images'):
                        print(f"   Main Image: {product['images'][0]['url']}")
                    print(f"   Link: {product.get('link', 'Link not found')}")
                    print("-" * 80)
                
                # Display detailed products JSON without saving to file (like Meesho)
                detailed_json_data = {
                    'query': query,
                    'search_url': driver.current_url,
                    'total_products': len(detailed_products),
                    'products': detailed_products
                }
                print(f"\n{'='*60}")
                print(f"DETAILED PRODUCT DATA (JSON FORMAT)")
                print(f"{'='*60}")
                print(json.dumps(detailed_json_data, indent=2, ensure_ascii=False))
            else:
                print("\nNo detailed product information could be extracted.")

        print(f"\nFiles created:")
        print(f"- {filename} (Search results HTML)")
        print("JSON data displayed in console (no files saved)")
        
        print("Closing browser automatically...")
        
        # Return structured data for intelligent search system (like Meesho)
        if products_info:
            result = {
                "site": "Flipkart",
                "query": query,
                "total_products": len(products_info),
                "basic_products": products_info,
                "detailed_products": detailed_products if detailed_products else []
            }
            
            print(f"✅ Flipkart search completed: Found {len(products_info)} products")
            return result
        else:
            print("⚠️ No products found on Flipkart")
            return {
                "site": "Flipkart", 
                "query": query,
                "total_products": 0,
                "basic_products": [],
                "detailed_products": []
            }

    except Exception as e:
        print(f"❌ Flipkart search error: {e}")
        return {
            "site": "Flipkart",
            "query": query, 
            "total_products": 0,
            "products": [],
            "error": str(e)
        }
    finally:
        driver.quit()

if __name__ == "__main__":
    # get query from CLI arg or input
    query: Optional[str] = None
    headless_flag = False

    if len(sys.argv) >= 2:
        # allow e.g. python flipkart_search.py "iphone 14"
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter product to search on Flipkart: ").strip()

    # If user included --headless keyword, detect it (optional)
    if query and "--headless" in query:
        headless_flag = True
        query = query.replace("--headless", "").strip()

    if not query:
        print("No query provided. Exiting.")
        sys.exit(1)

    search_flipkart(query, headless=headless_flag)
