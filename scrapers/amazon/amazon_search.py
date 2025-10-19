#!/usr/bin/env python3
"""
amazon_search.py
Usage:
  python amazon_search.py "iphone 14"
or
  python amazon_search.py   # then type query when prompted
"""

import sys
import time
import json
import re
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
    
    # Enhanced anti-detection measures
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-domain-reliability")
    chrome_options.add_argument("--disable-component-extensions-with-background-pages")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("detach", True)
    
    try:
        # Try with ChromeDriverManager first
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Amazon WebDriver initialized with ChromeDriverManager")
    except Exception as e:
        print(f"ChromeDriverManager failed: {e}")
        try:
            # Fallback to system ChromeDriver
            driver = webdriver.Chrome(options=chrome_options)
            print("Amazon WebDriver initialized with system ChromeDriver")
        except Exception as e2:
            print(f"All ChromeDriver methods failed: {e2}")
            raise e2
    
    # Execute JavaScript to remove webdriver properties and enhance stealth
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("delete navigator.__proto__.webdriver")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
    driver.execute_script("Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})})")
    driver.execute_script("window.chrome = {runtime: {}}")
    driver.execute_script("Object.defineProperty(navigator, 'platform', {get: () => 'Win32'})")
    driver.execute_script("Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4})")
    driver.execute_script("Object.defineProperty(navigator, 'deviceMemory', {get: () => 8})")
    
    return driver

def extract_product_details(driver: webdriver.Chrome) -> dict:
    """Extract detailed product information from an Amazon product page"""
    product_details = {
        "name": "",
        "price": "",
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
        time.sleep(3)
        
        # Extract product name - try multiple selectors
        name_selectors = [
            "span#productTitle",  # Main product title
            "h1#title",  # Alternative title selector
            "h1.a-size-large",  # Another title selector
            "span[data-automation-id='product-title']",
            "h1[data-automation-id='product-title']",
            "div#titleSection h1",
            "div#titleSection span",
            "h1.a-size-large.product-title-word-break"
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
        
        # Extract price - prioritize current/discounted price over MRP
        price_selectors = [
            "span.a-price.a-text-price.a-size-medium.a-color-base span.a-offscreen",  # Current price in offscreen
            "span.a-price.a-text-price.a-size-medium span.a-offscreen",  # Alternative current price
            "span.a-price.a-size-medium span.a-offscreen",  # Current price without text-price class
            "div.a-section.a-spacing-none span.a-price.a-text-price span.a-offscreen",  # Current price in section
            "span.a-offscreen",  # Price in offscreen (current price)
            "span.a-price-whole",  # Main price whole part (current price)
            "div.a-section.a-spacing-none.aok-align-center span.a-price-whole",  # Current price in center
            "span[data-automation-id='product-price']",  # Automation price
            "div[data-automation-id='product-price']",  # Automation price div
            "span.a-price-range",  # Price range selector
            "div.a-section.a-spacing-none span.a-price-whole"  # Fallback price
        ]
        
        # Extract current price and MRP separately
        current_price = ""
        mrp_price = ""
        discount_info = ""
        
        for selector in price_selectors:
            try:
                price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                if price_text and ('₹' in price_text or 'Rs' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                    # Check if this is likely the current price (not struck through)
                    parent_elem = price_elem.find_element(By.XPATH, "./..")
                    parent_classes = parent_elem.get_attribute('class') or ''
                    
                    # If parent has strikethrough or text-decoration, it's likely MRP
                    if 'a-text-strike' in parent_classes or 'a-text-strikethrough' in parent_classes:
                        if not mrp_price:  # Only set if we haven't found MRP yet
                            mrp_price = price_text
                            print(f"    Found MRP: {price_text}")
                    else:
                        if not current_price:  # Only set if we haven't found current price yet
                            current_price = price_text
                            print(f"    Found current price: {price_text}")
                            
            except:
                continue
        
        # Try to find MRP (struck-through price) and discount information
        try:
            # Look for struck-through prices (MRP)
            mrp_selectors = [
                "span.a-price.a-text-price.a-text-strike",  # Struck-through price
                "span.a-text-strike",  # Struck-through text
                "span.a-price.a-text-price span.a-offscreen",  # MRP in offscreen
                "div.a-section span.a-price.a-text-price",  # MRP in section
                "span.a-price.a-text-price"  # Alternative MRP selector
            ]
            
            for selector in mrp_selectors:
                try:
                    mrp_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    mrp_text = mrp_elem.text.strip()
                    if mrp_text and ('₹' in mrp_text or 'Rs' in mrp_text or mrp_text.replace(',', '').replace('.', '').isdigit()):
                        if not mrp_price:  # Only set if we haven't found MRP yet
                            mrp_price = mrp_text
                            print(f"    Found MRP: {mrp_text}")
                            break
                except:
                    continue
            
            # Look for discount information
            discount_selectors = [
                "span.a-size-small.a-color-secondary",  # Discount percentage
                "span.a-size-base.a-color-secondary",  # Alternative discount
                "span.a-color-price",  # Price color elements
                "div.a-section.a-spacing-none span.a-size-small",  # Small text in price section
                "span.a-size-small.a-color-success",  # Success color discount
                "span.a-size-base.a-color-success",  # Alternative success color
                "div.a-section span.a-size-small",  # Small text in section
                "span.a-size-small"  # Any small text
            ]
            
            for selector in discount_selectors:
                try:
                    discount_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    discount_text = discount_elem.text.strip()
                    if discount_text and ('%' in discount_text or 'off' in discount_text.lower() or 'save' in discount_text.lower()):
                        discount_info = discount_text
                        print(f"    Found discount info: {discount_text}")
                        break
                except:
                    continue
        except:
            pass
        
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
            if discount_info:
                product_details["discount_info"] = discount_info
        elif mrp_price:
            product_details["price"] = mrp_price
            print(f"    Warning: Only MRP found, no current price detected")
        
        # Extract brand (from product name or brand section)
        try:
            brand_selectors = [
                "a#bylineInfo",  # Brand link
                "span#bylineInfo",  # Brand span
                "div#bylineInfo a",  # Brand in div
                "span[data-automation-id='product-brand']",
                "div[data-automation-id='product-brand']"
            ]
            
            for selector in brand_selectors:
                try:
                    brand_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    brand_text = brand_elem.text.strip()
                    if brand_text and len(brand_text) < 50:
                        product_details["brand"] = brand_text
                        print(f"    Found brand: {brand_text}")
                        break
                except:
                    continue
        except:
            pass
        
        # If brand not found, try to extract from product name
        if not product_details["brand"] and product_details["name"]:
            name_parts = product_details["name"].split()
            if name_parts:
                # Common brand names that might be at the start
                common_brands = ["Apple", "Samsung", "OnePlus", "Xiaomi", "Realme", "Vivo", "Oppo", "Motorola", "Nokia", "Sony", "LG", "HP", "Dell", "Lenovo", "Asus", "Acer", "MSI", "Google", "Nothing", "Honor", "POCO", "Redmi", "Mi", "JBL", "Boat", "Sennheiser", "Philips", "Panasonic", "Canon", "Nikon"]
                for brand in common_brands:
                    if brand.lower() in product_details["name"].lower():
                        product_details["brand"] = brand
                        print(f"    Found brand from name: {brand}")
                        break
        
        # Extract category (from breadcrumbs)
        try:
            breadcrumb_selectors = [
                "div#wayfinding-breadcrumbs_feature_div a",  # Breadcrumb links
                "nav[aria-label='Breadcrumb'] a",  # Breadcrumb nav
                "div[data-automation-id='breadcrumb'] a",  # Breadcrumb automation
                "ul[aria-label='Breadcrumb'] a"  # Breadcrumb ul
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
                # Category is usually the last breadcrumb
                category_text = breadcrumbs[-1].text.strip()
                if category_text:
                    product_details["category"] = category_text
                    print(f"    Found category: {category_text}")
        except:
            pass
        
        # Extract rating - comprehensive selectors
        rating_selectors = [
            "span.a-icon-alt",  # Rating stars with text
            "div[data-automation-id='product-rating'] span",
            "span[data-automation-id='product-rating']",
            "div.a-section.a-spacing-none span.a-icon-alt",
            "div#averageCustomerReviews span.a-icon-alt",
            "div#reviewsMedley span.a-icon-alt",
            "span.a-icon.a-icon-star",  # Star icon
            "div#averageCustomerReviews span.a-icon",  # Star icon in reviews
            "div#reviewsMedley span.a-icon",  # Star icon in reviews medley
            "span[aria-label*='star']",  # Star with aria-label
            "span[aria-label*='out of']",  # Rating with aria-label
            "div#averageCustomerReviews span[aria-label]",  # Reviews section aria-label
            "div#reviewsMedley span[aria-label]",  # Reviews medley aria-label
            "span.a-size-base.a-color-base",  # Base size color rating
            "div.a-row.a-spacing-small span.a-icon-alt",  # Row with spacing
            "span.a-icon.a-icon-star-mini",  # Mini star icon
            "div#averageCustomerReviews span.a-icon-star-mini",  # Mini star in reviews
            "div#reviewsMedley span.a-icon-star-mini",  # Mini star in reviews medley
            "span[class*='a-icon-star']",  # Any star icon class
            "div[class*='rating'] span",  # Rating div spans
            "span[class*='rating']",  # Rating spans
            "div#averageCustomerReviews",  # Reviews section
            "div#reviewsMedley",  # Reviews medley
            "span.a-size-base",  # Base size spans
            "div.a-section span.a-icon-alt"  # Section spans
        ]
        
        for selector in rating_selectors:
            try:
                rating_elem = driver.find_element(By.CSS_SELECTOR, selector)
                rating_text = rating_elem.text.strip()
                aria_label = rating_elem.get_attribute('aria-label') or ''
                title_attr = rating_elem.get_attribute('title') or ''
                
                # Check text content, aria-label, and title attribute
                if rating_text and ('out of' in rating_text.lower() or rating_text.replace('.', '').replace(',', '').isdigit()):
                    product_details["rating"] = rating_text
                    print(f"    Found rating: {rating_text}")
                    break
                elif aria_label and ('out of' in aria_label.lower() or 'star' in aria_label.lower()):
                    product_details["rating"] = aria_label
                    print(f"    Found rating from aria-label: {aria_label}")
                    break
                elif title_attr and ('out of' in title_attr.lower() or 'star' in title_attr.lower()):
                    product_details["rating"] = title_attr
                    print(f"    Found rating from title: {title_attr}")
                    break
            except:
                continue
        
        # If still no rating found, try XPath approach
        if not product_details["rating"]:
            try:
                print(f"    Trying XPath rating extraction...")
                xpath_selectors = [
                    "//span[contains(@class, 'a-icon-alt')]",
                    "//span[contains(@aria-label, 'out of')]",
                    "//span[contains(@aria-label, 'star')]",
                    "//span[contains(@title, 'out of')]",
                    "//span[contains(@title, 'star')]",
                    "//div[contains(@id, 'averageCustomerReviews')]//span",
                    "//div[contains(@id, 'reviewsMedley')]//span"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        rating_elem = driver.find_element(By.XPATH, xpath)
                        rating_text = rating_elem.text.strip()
                        aria_label = rating_elem.get_attribute('aria-label') or ''
                        title_attr = rating_elem.get_attribute('title') or ''
                        
                        if rating_text and ('out of' in rating_text.lower() or rating_text.replace('.', '').replace(',', '').isdigit()):
                            product_details["rating"] = rating_text
                            print(f"    Found rating via XPath: {rating_text}")
                            break
                        elif aria_label and ('out of' in aria_label.lower() or 'star' in aria_label.lower()):
                            product_details["rating"] = aria_label
                            print(f"    Found rating via XPath aria-label: {aria_label}")
                            break
                        elif title_attr and ('out of' in title_attr.lower() or 'star' in title_attr.lower()):
                            product_details["rating"] = title_attr
                            print(f"    Found rating via XPath title: {title_attr}")
                            break
                    except:
                        continue
            except Exception as xpath_error:
                print(f"    XPath rating extraction error: {xpath_error}")
        
        # Extract reviews count
        try:
            review_count_selectors = [
                "span#acrCustomerReviewText",  # Reviews count
                "a#acrCustomerReviewLink span",  # Reviews count in link
                "div[data-automation-id='product-reviews-count']",
                "span[data-automation-id='product-reviews-count']",
                "div#averageCustomerReviews a span"
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
                "span#availability span",  # Availability span
                "div#availability span",  # Availability div
                "span[data-automation-id='product-availability']",
                "div[data-automation-id='product-availability']",
                "span.a-size-medium.a-color-success",  # Success color availability
                "span.a-size-medium.a-color-price"  # Price color availability
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
        
        # Extract product images
        try:
            print(f"    Starting image extraction...")
            
            # Wait a bit more for images to load
            time.sleep(2)
            
            image_selectors = [
                "img#landingImage",  # Main product image
                "div#imgTagWrapperId img",  # Main image wrapper
                "div#altImages img",  # Alternative images
                "div#imageBlock img",  # Image block images
                "div[data-automation-id='product-image'] img",  # Automation images
                "div#imageBlockThumbs img",  # Thumbnail images
                "div#altImages ul li img"  # Alternative images list
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
                            if img_src and ('amazon' in img_src.lower() or 'ssl-images' in img_src.lower()) and 'placeholder' not in img_src.lower():
                                # Get high-resolution image URL
                                if '._' in img_src:
                                    # Replace size parameters to get higher resolution
                                    high_res_src = img_src.replace('._AC_SX679_', '._AC_SX2000_').replace('._AC_SX466_', '._AC_SX2000_').replace('._AC_SX522_', '._AC_SX2000_')
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
                xpath_images = driver.find_elements(By.XPATH, "//img[contains(@src, 'amazon') or contains(@src, 'ssl-images')]")
                print(f"    Found {len(xpath_images)} images via XPath")
                
                for img in xpath_images:
                    try:
                        img_src = img.get_attribute('src')
                        img_alt = img.get_attribute('alt') or ''
                        
                        if img_src and 'placeholder' not in img_src.lower():
                            high_res_src = img_src.replace('._AC_SX679_', '._AC_SX2000_').replace('._AC_SX466_', '._AC_SX2000_').replace('._AC_SX522_', '._AC_SX2000_')
                            
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
                "div#feature-bullets ul li span",  # Feature bullets
                "div#productDescription p",  # Product description
                "div#detailBullets_feature_div ul li span",  # Detail bullets
                "div#productDetails_feature_div table tr",  # Product details table
                "div#technicalSpecifications_feature_div table tr"  # Technical specs table
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

def search_amazon(query: str, headless: bool = False, max_results: int = 20):
    driver = create_driver(headless=headless)
    try:
        print(f"Searching Amazon for: {query}")
        
        # First visit Amazon homepage to establish session
        print("Visiting Amazon homepage first...")
        driver.get("https://www.amazon.in")
        time.sleep(3)
        
        # Navigate to search URL
        search_url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
        print(f"Navigating to search URL: {search_url}")
        driver.get(search_url)
        time.sleep(8)

        # Wait for search results to load
        print("Waiting for search results to load...")
        time.sleep(8)
        
        # Check if we got blocked
        if "503" in driver.title or "Service Unavailable" in driver.page_source:
            print("⚠️ Got 503 error, trying alternative approach...")
            # Try with different user agent and retry
            driver.execute_script("Object.defineProperty(navigator, 'userAgent', {get: () => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})")
            time.sleep(2)
            driver.get(search_url)
            time.sleep(8)
        
        # Save the HTML content of the search results page
        html_content = driver.page_source
        filename = f"amazon_search_{query.replace(' ', '_')}.html"
        
        # Write HTML to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nSearch results saved as: {filename}")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Extract product information from search results page (like Meesho)
        products_info = []
        
        # Try different selectors for product cards (simplified like Meesho)
        product_selectors = [
            "div[data-component-type='s-search-result']",  # Main product card container
            "div.s-result-item",  # Alternative card selector
            "div[data-asin]",  # Generic product containers with ASIN
            "div.s-card-container",  # Another card selector
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
                
                # Extract title from various possible elements (simplified like Meesho)
                title_selectors = [
                    "h2 a span",  # Main title in search results
                    "h2 a",  # Main title link in search results
                    "span.a-size-medium.a-color-base.a-text-normal",  # Title span
                    "h3 a span",  # Alternative heading
                    "h3 a",  # Alternative heading link
                ]
                
                for selector in title_selectors:
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, selector)
                        title_text = title_elem.text.strip()
                        # Skip discount percentages and other non-product names (like Meesho)
                        if (title_text and len(title_text) > 5 and len(title_text) < 200 and
                            not title_text.endswith('%') and
                            not title_text.endswith('off') and
                            not title_text.startswith('%') and
                            'off' not in title_text.lower() and
                            not title_text.replace('%', '').replace('off', '').strip().isdigit()):
                            product_info['title'] = title_text
                            # Try to get link from the element or its parent
                            try:
                                if title_elem.tag_name == 'a':
                                    product_info['link'] = title_elem.get_attribute('href') or ''
                                else:
                                    # Try to find a parent link
                                    parent_link = title_elem.find_element(By.XPATH, "./ancestor::a")
                                    if parent_link:
                                        product_info['link'] = parent_link.get_attribute('href') or ''
                            except:
                                pass
                            break
                    except:
                        continue
                
                # If no title found, try to get it from image alt text (Amazon stores product names there)
                if not product_info.get('title'):
                    try:
                        img_elem = card.find_element(By.CSS_SELECTOR, "img")
                        img_alt = img_elem.get_attribute('alt') or ''
                        if img_alt and len(img_alt) > 10:
                            # Clean up the alt text to get just the product name
                            product_name = img_alt.split(',')[0].strip()  # Take first part before comma
                            product_info['title'] = product_name
                    except:
                        pass
                
                # If no title found, try to get it from the card's text content (like Meesho)
                if not product_info.get('title'):
                    try:
                        card_text = card.text.strip()
                        lines = card_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            # Skip discount percentages, prices, delivery info, reviews, etc.
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
                                not line.replace(':', '').replace('h', '').replace('m', '').replace('s', '').replace(' ', '').isdigit()):
                                product_info['title'] = line
                                break
                    except:
                        pass
                
                # Extract price information (enhanced to get MRP and discount)
                price_selectors = [
                    "span.a-price.a-text-price.a-size-medium span.a-offscreen",  # Current price in offscreen
                    "span.a-price.a-size-medium span.a-offscreen",  # Current price without text-price
                    "span.a-offscreen",  # Price in offscreen (current price)
                    "span.a-price-whole",  # Main price whole part (current price)
                    "span.a-price-symbol",  # Price symbol
                    "span[data-automation-id='product-price']",  # Automation price
                    "div[data-automation-id='product-price']",  # Automation price div
                ]
                
                current_price = ""
                mrp_price = ""
                discount_info = ""
                
                for selector in price_selectors:
                    try:
                        price_elem = card.find_element(By.CSS_SELECTOR, selector)
                        price_text = price_elem.text.strip()
                        if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text):
                            # If we only got the symbol, try to get the parent element
                            if price_text == '₹':
                                try:
                                    parent = price_elem.find_element(By.XPATH, "./..")
                                    parent_text = parent.text.strip()
                                    if parent_text and '₹' in parent_text:
                                        price_text = parent_text
                                except:
                                    continue
                            
                            # Check if this is MRP (struck through) or current price
                            parent_elem = price_elem.find_element(By.XPATH, "./..")
                            parent_classes = parent_elem.get_attribute('class') or ''
                            
                            if 'a-text-strike' in parent_classes or 'a-text-strikethrough' in parent_classes:
                                if not mrp_price:
                                    mrp_price = price_text
                            else:
                                if not current_price:
                                    current_price = price_text
                    except:
                        continue
                
                # Set the main price (prefer current price over MRP)
                if current_price:
                    product_info['price'] = current_price
                elif mrp_price:
                    product_info['price'] = mrp_price
                
                # Set MRP if we found it
                if mrp_price:
                    product_info['mrp'] = mrp_price
                
                # Try to find discount information
                try:
                    card_text = card.text.strip()
                    lines = card_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if '%' in line and 'off' in line.lower():
                            discount_info = line
                            break
                        elif line.startswith('Save') and '₹' in line:
                            discount_info = line
                            break
                    
                    if discount_info:
                        product_info['discount_percentage'] = discount_info
                except:
                    pass
                
                # If no price found, try to extract from card text (like Meesho)
                if not product_info.get('price'):
                    try:
                        card_text = card.text.strip()
                        lines = card_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith('₹') and len(line) < 20:
                                product_info['price'] = line
                                break
                        # If still no price, try to find any line with ₹
                        if not product_info.get('price'):
                            for line in lines:
                                if '₹' in line and len(line) < 30:
                                    # Clean up the price line
                                    price_line = line.strip()
                                    if price_line.count('₹') == 1:  # Only one price symbol
                                        product_info['price'] = price_line
                                        break
                    except:
                        pass
                
                # Extract rating using a comprehensive approach
                # Amazon's rating structure is complex, so we'll try multiple methods
                
                # Method 1: Look for aria-label attributes that contain star ratings
                try:
                    rating_elements = card.find_elements(By.CSS_SELECTOR, "[aria-label*='out of 5'], [aria-label*='star']")
                    for elem in rating_elements:
                        aria_label = elem.get_attribute('aria-label') or ''
                        if aria_label:
                            # Extract rating from aria-label like "4.2 out of 5 stars"
                            star_match = re.search(r'(\d+\.?\d*)\s*out\s*of\s*5', aria_label.lower())
                            if star_match:
                                rating_val = float(star_match.group(1))
                                if 0 <= rating_val <= 5:
                                    product_info['rating'] = star_match.group(1)
                                    print(f"    Found star rating from aria-label: {product_info['rating']}")
                                    break
                except:
                    pass
                
                # Method 2: Look for specific rating elements
                if not product_info.get('rating'):
                    rating_selectors = [
                        "span.a-icon-alt",  # Rating stars with text
                        "span[class*='a-icon-star']",  # Star icon spans
                        "i[class*='a-icon-star']",  # Star icon elements
                        "div[class*='rating'] span",  # Rating div spans
                        "span[class*='rating']",  # Rating spans
                    ]
                    
                    for selector in rating_selectors:
                        try:
                            rating_elem = card.find_element(By.CSS_SELECTOR, selector)
                            rating_text = rating_elem.text.strip()
                            
                            if rating_text and ('out of' in rating_text.lower() or 'star' in rating_text.lower()):
                                # Extract star rating from text like "4.2 out of 5 stars"
                                star_match = re.search(r'(\d+\.?\d*)\s*out\s*of\s*5', rating_text.lower())
                                if star_match:
                                    rating_val = float(star_match.group(1))
                                    if 0 <= rating_val <= 5:
                                        product_info['rating'] = star_match.group(1)
                                        print(f"    Found star rating: {product_info['rating']}")
                                        break
                        except:
                            continue
                
                # Method 3: Extract from card text as fallback
                if not product_info.get('rating'):
                    try:
                        card_text = card.text.strip()
                        # Look for patterns like "4.2 out of 5 stars" in the card text
                        star_match = re.search(r'(\d+\.?\d*)\s*out\s*of\s*5\s*stars?', card_text.lower())
                        if star_match:
                            rating_val = float(star_match.group(1))
                            if 0 <= rating_val <= 5:
                                product_info['rating'] = star_match.group(1)
                                print(f"    Found star rating from card text: {product_info['rating']}")
                    except Exception as e:
                        print(f"    Error extracting rating from card text: {e}")
                
                # Extract review count (separate from star ratings)
                review_selectors = [
                    "a[href*='reviews'] span",  # Review link spans
                    "span.a-size-base",  # Base size spans (often contain review counts)
                    "div.a-row.a-spacing-small span",  # Row with spacing
                ]
                
                for selector in review_selectors:
                    try:
                        review_elem = card.find_element(By.CSS_SELECTOR, selector)
                        review_text = review_elem.text.strip()
                        
                        # Look for patterns like "1,234" or "1234" - these are review counts
                        if review_text and (',' in review_text or review_text.isdigit()):
                            if len(review_text) > 2 and len(review_text) < 10:  # Reasonable review count length
                                # Make sure it's not a star rating
                                if not ('out of' in review_text.lower() or 'star' in review_text.lower()):
                                    product_info['reviews_count'] = review_text
                                    break
                    except:
                        continue
                
                # If no rating found, try to extract from card text (like Meesho)
                if not product_info.get('rating'):
                    try:
                        card_text = card.text.strip()
                        lines = card_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.replace('.', '').isdigit() and len(line) <= 4 and float(line) <= 5.0:
                                product_info['rating'] = line
                                break
                    except:
                        pass
                
                # Extract image URL (like Meesho)
                try:
                    img_elem = card.find_element(By.TAG_NAME, "img")
                    product_info['image_url'] = img_elem.get_attribute('src') or ''
                    product_info['image_alt'] = img_elem.get_attribute('alt') or ''
                except:
                    product_info['image_url'] = ''
                    product_info['image_alt'] = ''
                
                # Extract product link - the card itself might be the link (like Meesho)
                if not product_info.get('link'):
                    try:
                        # Check if the card element itself is an anchor tag
                        if card.tag_name.lower() == 'a':
                            href = card.get_attribute('href')
                            if href and '/dp/' in href:
                                # Make sure it's a full URL
                                if href.startswith('/'):
                                    href = 'https://www.amazon.in' + href
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
                            if href and ('/dp/' in href or 'amazon.in' in href):
                                # Make sure it's a full URL
                                if href.startswith('/'):
                                    href = 'https://www.amazon.in' + href
                                product_info['link'] = href
                                break
                    except:
                        pass
                
                # Extract brand (try to get from title or other elements) (like Meesho)
                try:
                    if product_info.get('title'):
                        # Common brand names that might be at the start
                        common_brands = ["Apple", "Samsung", "OnePlus", "Xiaomi", "Realme", "Vivo", "Oppo", "Motorola", "Nokia", "Sony", "LG", "HP", "Dell", "Lenovo", "Asus", "Acer", "MSI", "Google", "Nothing", "Honor", "POCO", "Redmi", "Mi", "JBL", "Boat", "Sennheiser", "Philips", "Panasonic", "Canon", "Nikon", "Amazon"]
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
                                common_words = ["Modern", "Latest", "New", "Best", "Top", "Great", "Super", "Ultra", "Premium", "Quality", "Good", "Nice", "Cool", "Hot", "Trendy", "Stylish", "Fashionable", "Elegant", "Beautiful", "Amazing", "Wonderful", "Excellent", "Perfect", "Special", "Unique", "Exclusive", "Limited", "Classic", "Vintage", "Retro", "Contemporary", "Traditional", "Casual", "Formal", "Party", "Wedding", "Office", "Work", "Daily", "Everyday", "Weekend", "Holiday", "Summer", "Winter", "Spring", "Fall", "Seasonal", "Year", "Round"]
                                
                                # Skip discount percentages and numbers
                                if (first_word not in common_words and 
                                    len(first_word) > 2 and 
                                    not first_word.replace('%', '').replace('off', '').isdigit() and
                                    not first_word.endswith('%') and
                                    not first_word.endswith('off')):
                                    product_info['brand'] = first_word
                except:
                    pass
                
                # Extract category (try to infer from title) (like Meesho)
                try:
                    if product_info.get('title'):
                        title_lower = product_info['title'].lower()
                        if 'mobile' in title_lower or 'phone' in title_lower or 'smartphone' in title_lower or 'iphone' in title_lower or 'galaxy' in title_lower or 'android' in title_lower:
                            product_info['category'] = 'Mobile'
                        elif 'laptop' in title_lower or 'computer' in title_lower or 'notebook' in title_lower:
                            product_info['category'] = 'Laptop'
                        elif 'tablet' in title_lower or 'ipad' in title_lower:
                            product_info['category'] = 'Tablet'
                        elif 'headphone' in title_lower or 'earphone' in title_lower or 'speaker' in title_lower:
                            product_info['category'] = 'Audio'
                        elif 'watch' in title_lower or 'smartwatch' in title_lower:
                            product_info['category'] = 'Watch'
                        elif 'camera' in title_lower or 'dslr' in title_lower:
                            product_info['category'] = 'Camera'
                        elif 'saree' in title_lower:
                            product_info['category'] = 'Saree'
                        elif 'shirt' in title_lower:
                            product_info['category'] = 'Shirt'
                        elif 'pant' in title_lower:
                            product_info['category'] = 'Pant'
                        elif 'shoe' in title_lower:
                            product_info['category'] = 'Shoe'
                        elif 'dress' in title_lower:
                            product_info['category'] = 'Dress'
                        elif 'kurta' in title_lower:
                            product_info['category'] = 'Kurta'
                        elif 'jean' in title_lower:
                            product_info['category'] = 'Jeans'
                        elif 'top' in title_lower:
                            product_info['category'] = 'Top'
                        elif 'bottom' in title_lower:
                            product_info['category'] = 'Bottom'
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
                
                # Extract availability (like Meesho)
                try:
                    card_text = card.text.strip()
                    lines = card_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if 'delivery' in line.lower() or 'stock' in line.lower() or 'available' in line.lower():
                            product_info['availability'] = line
                            break
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
                if product.get('rating'):
                    print(f"   Rating: {product['rating']}")
                if product.get('brand'):
                    print(f"   Brand: {product['brand']}")
                if product.get('category'):
                    print(f"   Category: {product['category']}")
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
                        "brand": product.get('brand', ''),
                        "category": product.get('category', ''),
                        "rating": product.get('rating', ''),
                        "link": product.get('link', ''),
                        "images": [{"url": product.get('image_url', ''), "alt": product.get('image_alt', ''), "thumbnail": product.get('image_url', '')}] if product.get('image_url') else []
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
                    print(f"   Brand: {product.get('brand', 'Brand not found')}")
                    print(f"   Category: {product.get('category', 'Category not found')}")
                    print(f"   Rating: {product.get('rating', 'Rating not found')}")
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
                "site": "Amazon",
                "query": query,
                "total_products": len(products_info),
                "basic_products": products_info,
                "detailed_products": detailed_products if detailed_products else []
            }
            
            print(f"✅ Amazon search completed: Found {len(products_info)} products")
            return result
        else:
            print("⚠️ No products found on Amazon")
            return {
                "site": "Amazon", 
                "query": query,
                "total_products": 0,
                "basic_products": [],
                "detailed_products": []
            }

    except Exception as e:
        print(f"❌ Amazon search error: {e}")
        return {
            "site": "Amazon",
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
        # allow e.g. python amazon_search.py "iphone 14"
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter product to search on Amazon.in: ").strip()

    # If user included --headless keyword, detect it (optional)
    if query and "--headless" in query:
        headless_flag = True
        query = query.replace("--headless", "").strip()

    if not query:
        print("No query provided. Exiting.")
        sys.exit(1)

    search_amazon(query, headless=headless_flag)
