#!/usr/bin/env python3
"""
meesho_search.py - Working Meesho scraper (extracts from search results only)
Usage:
  python meesho_search.py "saree"
"""

import sys
import time
import json
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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
    
    # Realistic user agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Additional stealth options
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Use system ChromeDriver instead of ChromeDriverManager
    try:
        # Try to use system ChromeDriver first
        driver = webdriver.Chrome(options=chrome_options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Meesho WebDriver initialized with system ChromeDriver")
        return driver
    except Exception as e:
        print(f"❌ Error creating Chrome driver: {e}")
        print("Make sure Chrome browser is installed and up to date.")
        raise e

def search_meesho(query: str, headless: bool = False):
    driver = None
    try:
        driver = create_driver(headless=headless)
        wait = WebDriverWait(driver, 15)

        print(f"Searching Meesho for: {query}")
        
        # Navigate directly to search URL (this approach worked before)
        search_url = f"https://www.meesho.com/search?q={query.replace(' ', '+')}"
        driver.get(search_url)
        time.sleep(5)

        # Wait for search results to load
        print("Waiting for search results to load...")
        time.sleep(5)
        
        # Save the HTML content of the search results page
        html_content = driver.page_source
        filename = f"meesho_search_{query.replace(' ', '_')}.html"
        
        # Write HTML to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nSearch results saved as: {filename}")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Extract product information from search results page
        products_info = []
        
        # Try different selectors for product cards
        product_selectors = [
            "div[class*='product']",  # Main product card container
            "div[class*='card']",  # Alternative card selector
            "div[class*='item']",  # Another card selector
            "div[class*='grid']",  # Grid item selector
            "a[href*='/p/']"  # Product link selector
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
            if driver:
                driver.quit()
            return {
                "site": "Meesho",
                "query": query,
                "total_products": 0,
                "basic_products": [],
                "detailed_products": []
            }
        
        # Debug: Let's see what's actually in the first card
        if product_cards:
            print(f"\nDebugging first product card:")
            first_card = product_cards[0]
            print(f"Card HTML snippet: {first_card.get_attribute('outerHTML')[:500]}...")
            
            # Try to find any text content in the card
            all_text = first_card.text.strip()
            print(f"All text in first card: {all_text[:200]}...")
            
            # Try to find any links
            links = first_card.find_elements(By.TAG_NAME, "a")
            print(f"Found {len(links)} links in first card")
            for i, link in enumerate(links[:3]):
                print(f"  Link {i+1}: {link.get_attribute('href')} - Text: {link.text.strip()[:50]}")
        
        # Extract information from each product card
        for i, card in enumerate(product_cards[:20]):  # Process up to 20 products
            try:
                product_info = {}
                
                # Extract title from various possible elements
                title_selectors = [
                    "h3", "h4", "h2", "h1",  # Heading tags
                    "a[title]",  # Title attribute
                    "div[class*='title']",
                    "span[class*='title']",
                    "a",  # Any link
                    "div[class*='name']",
                    "span[class*='name']",
                    "div[class*='product-name']",
                    "span[class*='product-name']",
                    "p"  # Paragraph tags
                ]
                
                for selector in title_selectors:
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, selector)
                        title_text = title_elem.text.strip()
                        # Skip discount percentages and other non-product names
                        if (title_text and len(title_text) > 3 and len(title_text) < 200 and
                            not title_text.endswith('%') and
                            not title_text.endswith('off') and
                            not title_text.startswith('%') and
                            'off' not in title_text.lower() and
                            not title_text.replace('%', '').replace('off', '').strip().isdigit()):
                            product_info['title'] = title_text
                            # Try to get link from title element
                            try:
                                product_info['link'] = title_elem.get_attribute('href') or ''
                            except:
                                pass
                            break
                    except:
                        continue
                
                # If no title found, try to get it from the card's text content
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
                                ':' not in line and  # Skip time formats like "01h : 03m : 26s"
                                not line.replace(':', '').replace('h', '').replace('m', '').replace('s', '').replace(' ', '').isdigit()):
                                product_info['title'] = line
                                break
                    except:
                        pass
                
                # Extract price from various possible elements
                price_selectors = [
                    "span[class*='price']",
                    "div[class*='price']",
                    "span[class*='selling']",
                    "div[class*='selling']",
                    "span[class*='mrp']",
                    "div[class*='mrp']",
                    "span[class*='cost']",
                    "div[class*='cost']",
                    "span[class*='amount']",
                    "div[class*='amount']"
                ]
                
                for selector in price_selectors:
                    try:
                        price_elem = card.find_element(By.CSS_SELECTOR, selector)
                        price_text = price_elem.text.strip()
                        if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text):
                            product_info['price'] = price_text
                            break
                    except:
                        continue
                
                # Extract price information from card text - Enhanced to get MRP and discounts
                if not product_info.get('price'):
                    try:
                        card_text = card.text.strip()
                        lines = card_text.split('\n')
                        import re
                        
                        for line in lines:
                            line = line.strip()
                            
                            # Look for multiple prices in one line like "₹233₹2579% off"
                            if '₹' in line and line.count('₹') >= 2:
                                price_pattern = r'₹[\d,]+'
                                all_prices = re.findall(price_pattern, line)
                                
                                if len(all_prices) >= 2:
                                    product_info['price'] = all_prices[0]
                                    product_info['mrp'] = all_prices[1]
                                    print(f"    Found current price: {all_prices[0]}")
                                    print(f"    Found MRP: {all_prices[1]}")
                                    
                                    # Look for discount percentage
                                    discount_match = re.search(r'(\d{1,2})%', line)
                                    if discount_match:
                                        discount_val = int(discount_match.group(1))
                                        if 1 <= discount_val <= 95:
                                            product_info['discount_percentage'] = discount_match.group(1) + '%'
                                            print(f"    Found discount: {product_info['discount_percentage']}")
                                    
                                    # Calculate discount amount
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
                            
                            # Fallback: single price
                            elif line.startswith('₹') and len(line) < 20:
                                product_info['price'] = line
                                print(f"    Found price: {line}")
                                break
                    except:
                        pass
                
                # Extract rating from various possible elements
                rating_selectors = [
                    "div[class*='rating']",
                    "span[class*='rating']",
                    "div[class*='star']",
                    "span[class*='star']",
                    "div[class*='review']",
                    "span[class*='review']",
                    "div[class*='score']",
                    "span[class*='score']"
                ]
                
                for selector in rating_selectors:
                    try:
                        rating_elem = card.find_element(By.CSS_SELECTOR, selector)
                        rating_text = rating_elem.text.strip()
                        if rating_text and rating_text.replace('.', '').replace(',', '').isdigit():
                            product_info['rating'] = rating_text
                            break
                    except:
                        continue
                
                # If no rating found, try to extract from card text
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
                
                # Extract image URL and alt text
                try:
                    img_elem = card.find_element(By.TAG_NAME, "img")
                    product_info['image_url'] = img_elem.get_attribute('src') or ''
                    product_info['image_alt'] = img_elem.get_attribute('alt') or ''
                    
                    # Use image alt text as product title if we don't have a good title yet
                    if product_info.get('image_alt') and (not product_info.get('title') or 
                                       product_info.get('title', '').lower().startswith('pack of') or
                                       len(product_info.get('title', '')) < 10):
                        product_info['title'] = product_info['image_alt']
                        print(f"    Using image alt as title: {product_info['image_alt'][:50]}...")
                    else:
                        print(f"    Found image: {product_info['image_alt'][:50]}...")
                except:
                    product_info['image_url'] = ''
                    product_info['image_alt'] = ''
                
                # Extract product link - the card itself might be the link
                if not product_info.get('link'):
                    try:
                        # Check if the card element itself is an anchor tag
                        if card.tag_name.lower() == 'a':
                            href = card.get_attribute('href')
                            if href and '/p/' in href:
                                # Make sure it's a full URL
                                if href.startswith('/'):
                                    href = 'https://www.meesho.com' + href
                                product_info['link'] = href
                                print(f"    Found product link from card element: {href}")
                    except:
                        pass
                
                # If still no link found, try to find anchor tags within the card
                if not product_info.get('link'):
                    try:
                        # Look for any anchor tags within the card
                        link_elements = card.find_elements(By.TAG_NAME, "a")
                        for link_elem in link_elements:
                            href = link_elem.get_attribute('href')
                            if href and ('/p/' in href or 'meesho.com' in href):
                                # Make sure it's a full URL
                                if href.startswith('/'):
                                    href = 'https://www.meesho.com' + href
                                product_info['link'] = href
                                print(f"    Found product link within card: {href}")
                                break
                    except:
                        pass
                
                # Extract brand (try to get from title or other elements)
                try:
                    if product_info.get('title'):
                        # Common brand names that might be at the start
                        common_brands = ["Nike", "Adidas", "Puma", "Reebok", "Converse", "Vans", "New Balance", "Under Armour", "Skechers", "Fila", "Jordan", "Champion", "Levi's", "Tommy Hilfiger", "Calvin Klein", "H&M", "Zara", "Forever 21", "Uniqlo", "Gap", "American Eagle", "Hollister", "Abercrombie", "Ralph Lauren", "Lacoste", "Polo", "Gucci", "Prada", "Versace", "Armani", "Hugo Boss", "Diesel", "Guess", "Michael Kors", "Coach", "Kate Spade", "Tory Burch", "Ray-Ban", "Oakley", "Puma", "Reebok", "Asics", "Mizuno", "Brooks", "Saucony", "Fashionate", "Meesho", "Style", "Trendy", "Fashion", "PU ONLINE", "KEESOR", "Modern", "Agile", "Classy", "Versatile", "Relaxed", "Trendy", "Fashionable", "Unique", "Latest", "Casual", "Sports", "Running", "Sneakers", "Elegant", "Funky", "Boys", "Women", "Men", "Samsung", "Apple", "OnePlus", "Xiaomi", "Realme", "Vivo", "Oppo", "Motorola", "LG", "Sony", "Huawei", "Honor", "Redmi", "POCO", "Nothing", "Google", "Pixel", "iPhone", "Galaxy", "Mi", "Redmi", "POCO", "Nothing", "Google", "Pixel", "iPhone", "Galaxy", "Mi"]
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
                
                # Extract category (try to infer from title)
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
                            product_info['category'] = 'Fashion'
                except:
                    pass
                
                # Extract reviews count
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
                
                # Extract availability
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
                
                # If we found any meaningful information, add it
                if product_info.get('title') or product_info.get('price'):
                    products_info.append(product_info)
                    
            except Exception as e:
                print(f"Error extracting info from product {i+1}: {e}")
                continue
        
        # Display extracted information
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

        # Display JSON data without saving to file
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
            
            # Create detailed products from search results data (since individual pages are blocked)
            detailed_products = []
            
            print(f"\n{'='*60}")
            print(f"CREATING DETAILED PRODUCTS FROM SEARCH RESULTS")
            print(f"{'='*60}")
            
            # Take the first 10 products with the most complete information
            best_products = []
            for product in products_info:
                if product.get('title') and product.get('price'):
                    best_products.append(product)
                    if len(best_products) >= 10:
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
                        "availability": product.get('availability', ''),
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
                    if product.get('mrp'):
                        print(f"   MRP: {product['mrp']}")
                    if product.get('discount_percentage'):
                        print(f"   Discount: {product['discount_percentage']}")
                    if product.get('discount_amount'):
                        print(f"   You Save: {product['discount_amount']}")
                    print(f"   Brand: {product.get('brand', 'Brand not found')}")
                    print(f"   Category: {product.get('category', 'Category not found')}")
                    if product.get('rating'):
                        print(f"   Rating: {product['rating']}")
                    if product.get('reviews_count'):
                        print(f"   Reviews: {product['reviews_count']}")
                    if product.get('availability'):
                        print(f"   Availability: {product['availability']}")
                    print(f"   Images: {len(product.get('images', []))} images found")
                    if product.get('images'):
                        print(f"   Main Image: {product['images'][0]['url']}")
                    print(f"   Link: {product.get('link', 'Link not found')}")
                    print("-" * 80)
                
                # Display detailed products JSON without saving to file
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
        
        # Return structured data for intelligent search system
        if products_info:
            result = {
                "site": "Meesho",
                "query": query,
                "total_products": len(products_info),
                "basic_products": products_info,
                "detailed_products": detailed_products if detailed_products else []
            }
            
            print(f"✅ Meesho search completed: Found {len(products_info)} products")
            return result
        else:
            print("⚠️ No products found on Meesho")
            return {
                "site": "Meesho", 
                "query": query,
                "total_products": 0,
                "basic_products": [],
                "detailed_products": []
            }

    except Exception as e:
        print(f"❌ Meesho search error: {e}")
        return {
            "site": "Meesho",
            "query": query, 
            "total_products": 0,
            "basic_products": [],
            "detailed_products": [],
            "error": str(e)
        }
    finally:
        if driver:
            driver.quit()

def extract_product_details(driver: webdriver.Chrome) -> dict:
    """Extract detailed product information from a Meesho product page"""
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
        
        # Extract product name - Meesho-specific selectors
        name_selectors = [
            "h1[class*='title']",  # Main product title
            "h1[class*='product']",  # Product title
            "h1[class*='name']",  # Product name
            "h1",  # Generic h1
            "h2",  # Generic h2
            "div[class*='title']",  # Title div
            "span[class*='title']",  # Title span
            "div[class*='product-name']",  # Product name div
            "span[class*='product-name']",  # Product name span
            "div[class*='product-title']",  # Product title div
            "span[class*='product-title']"  # Product title span
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
        
        # Extract price - Meesho-specific selectors
        price_selectors = [
            "span[class*='price']",  # Price span
            "div[class*='price']",  # Price div
            "span[class*='selling']",  # Selling price
            "div[class*='selling']",  # Selling price div
            "span[class*='mrp']",  # MRP
            "div[class*='mrp']",  # MRP div
            "span[class*='cost']",  # Cost
            "div[class*='cost']",  # Cost div
            "span[class*='amount']",  # Amount
            "div[class*='amount']"  # Amount div
        ]
        
        for selector in price_selectors:
            try:
                price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text):
                    product_details["price"] = price_text
                    print(f"    Found price: {price_text}")
                    break
            except:
                continue
        
        # Extract brand (from breadcrumbs or product name)
        try:
            breadcrumb_selectors = [
                "nav[class*='breadcrumb'] a",  # Breadcrumb nav
                "div[class*='breadcrumb'] a",  # Breadcrumb div
                "nav a",  # Any nav link
                "div[class*='nav'] a",  # Nav div
                "div[class*='category'] a",  # Category links
                "span[class*='brand']",  # Brand span
                "div[class*='brand']"  # Brand div
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
        
        # Extract rating - Meesho-specific selectors
        rating_selectors = [
            "div[class*='rating']",  # Rating div
            "span[class*='rating']",  # Rating span
            "div[class*='star']",  # Star rating div
            "span[class*='star']",  # Star rating span
            "div[class*='review']",  # Review div
            "span[class*='review']",  # Review span
            "div[class*='score']",  # Score div
            "span[class*='score']"  # Score span
        ]
        
        for selector in rating_selectors:
            try:
                rating_elem = driver.find_element(By.CSS_SELECTOR, selector)
                rating_text = rating_elem.text.strip()
                if rating_text and ('out of' in rating_text.lower() or 'star' in rating_text.lower() or rating_text.replace('.', '').replace(',', '').isdigit()):
                    product_details["rating"] = rating_text
                    print(f"    Found rating: {rating_text}")
                    break
            except:
                continue
        
        # If brand not found in breadcrumbs, try to extract from product name
        if not product_details["brand"] and product_details["name"]:
            name_parts = product_details["name"].split()
            if name_parts:
                # Common brand names that might be at the start
                common_brands = ["Nike", "Adidas", "Puma", "Reebok", "Converse", "Vans", "New Balance", "Under Armour", "Skechers", "Fila", "Jordan", "Champion", "Levi's", "Tommy Hilfiger", "Calvin Klein", "H&M", "Zara", "Forever 21", "Uniqlo", "Gap", "American Eagle", "Hollister", "Abercrombie", "Ralph Lauren", "Lacoste", "Polo", "Gucci", "Prada", "Versace", "Armani", "Hugo Boss", "Diesel", "Guess", "Michael Kors", "Coach", "Kate Spade", "Tory Burch", "Ray-Ban", "Oakley", "Puma", "Reebok", "Asics", "Mizuno", "Brooks", "Saucony", "Fashionate", "Meesho", "Style", "Trendy", "Fashion"]
                for brand in common_brands:
                    if brand.lower() in product_details["name"].lower():
                        product_details["brand"] = brand
                        print(f"    Found brand from name: {brand}")
                        break
        
        # Extract product images
        try:
            print(f"    Starting image extraction...")
            
            # Wait a bit more for images to load
            time.sleep(1)
            
            # Meesho-specific image selectors
            image_selectors = [
                "img[class*='product']",  # Product image
                "img[class*='main']",  # Main image
                "img[class*='hero']",  # Hero image
                "img[class*='primary']",  # Primary image
                "img[class*='zoom']",  # Zoom image
                "img[class*='gallery']",  # Gallery image
                "img[class*='carousel']",  # Carousel image
                "div[class*='image'] img",  # Image in div
                "div[class*='gallery'] img",  # Gallery image
                "div[class*='carousel'] img",  # Carousel image
                "div[class*='product'] img",  # Product div image
                "img[src*='meesho']",  # Any image with meesho in src
                "img[src*='images']",  # Any image with images in src
                "img[src*='cdn']"  # Any image with cdn in src
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
                            
                            # Filter out placeholder images and get only product images
                            if img_src and ('meesho' in img_src.lower() or 'images' in img_src.lower() or 'cdn' in img_src.lower()) and 'placeholder' not in img_src.lower():
                                # Get high-resolution image URL
                                if 'width=' in img_src:
                                    # Try to get higher resolution
                                    high_res_src = img_src.replace('width=360', 'width=800').replace('width=150', 'width=800')
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
            
            # Limit to first 5 images to avoid too much data
            product_details["images"] = all_images[:5]
            print(f"    Final result: Found {len(product_details['images'])} product images")
            
            # Debug: print first image URL if available
            if product_details["images"]:
                print(f"    First image URL: {product_details['images'][0]['url']}")
            
        except Exception as e:
            print(f"    Error extracting images: {e}")
            product_details["images"] = []
        
        # Debug: Print what we found
        print(f"    Final extracted data: {product_details}")
        
    except Exception as e:
        print(f"    Error extracting product details: {e}")
    
    return product_details

if __name__ == "__main__":
    # get query from CLI arg or input
    query: Optional[str] = None
    headless_flag = False

    if len(sys.argv) >= 2:
        # allow e.g. python meesho_search.py "nike shoes"
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter product to search on Meesho: ").strip()

    # If user included --headless keyword, detect it (optional)
    if query and "--headless" in query:
        headless_flag = True
        query = query.replace("--headless", "").strip()

    if not query:
        print("No query provided. Exiting.")
        sys.exit(1)

    search_meesho(query, headless=headless_flag)
