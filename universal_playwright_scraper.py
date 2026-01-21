"""
Universal E-commerce Scraper using Playwright
Works for ANY website including Meesho, Flipkart, Amazon, etc.
Bypasses anti-bot protection by using a real browser.
"""

import asyncio
from playwright.async_api import async_playwright
import json
from typing import Dict, Optional
import re


async def scrape_product(url: str) -> Dict:
    """
    Universal product scraper that works on ANY e-commerce site.
    
    Args:
        url: Product page URL
        
    Returns:
        Dictionary with product details
    """
    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        # Create context with realistic settings
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-IN',
            timezone_id='Asia/Kolkata'
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to product page
            print(f"🌐 Loading: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for page to fully load
            await page.wait_for_timeout(2000)
            
            # Extract all text content
            full_text = await page.inner_text('body')
            
            # Extract product details using smart patterns
            product_data = {
                'url': url,
                'title': None,
                'price': None,
                'mrp': None,
                'brand': None,
                'description': None,
                'images': [],
                'full_text': full_text[:5000]  # First 5000 chars
            }
            
            # Try to find title (common patterns)
            title_selectors = [
                'h1',
                '[class*="title"]',
                '[class*="product-name"]',
                '[class*="ProductTitle"]',
                '[data-testid*="title"]'
            ]
            
            for selector in title_selectors:
                try:
                    title = await page.locator(selector).first.inner_text(timeout=1000)
                    if title and len(title) > 5:
                        product_data['title'] = title.strip()
                        break
                except:
                    continue
            
            # Try to find price (common patterns)
            price_patterns = [
                r'₹\s*[\d,]+',
                r'Rs\.?\s*[\d,]+',
                r'INR\s*[\d,]+'
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, full_text)
                if matches:
                    # First match is usually the selling price
                    product_data['price'] = matches[0]
                    # Second match might be MRP
                    if len(matches) > 1:
                        product_data['mrp'] = matches[1]
                    break
            
            # Extract all images
            try:
                images = await page.locator('img').all()
                for img in images[:10]:  # Limit to first 10 images
                    src = await img.get_attribute('src')
                    if src and ('http' in src or src.startswith('//')):
                        if src.startswith('//'):
                            src = 'https:' + src
                        product_data['images'].append(src)
            except:
                pass
            
            # Get page HTML for further processing
            html = await page.content()
            product_data['html_length'] = len(html)
            
            print(f"✅ Scraped successfully!")
            print(f"   Title: {product_data['title']}")
            print(f"   Price: {product_data['price']}")
            print(f"   Images: {len(product_data['images'])}")
            
            return product_data
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'error': str(e), 'url': url}
            
        finally:
            await browser.close()


async def scrape_multiple(urls: list) -> list:
    """Scrape multiple product URLs"""
    results = []
    for url in urls:
        result = await scrape_product(url)
        results.append(result)
        # Small delay between requests
        await asyncio.sleep(2)
    return results


# Example usage
if __name__ == "__main__":
    # Test URLs
    test_urls = [
        "https://www.meesho.com/muuchstac-ocean-face-wash-for-men-fight-acne-pimples-brighten-skin-clears-dirt-oil-control-refreshing-feel-multi-action-formula-100-ml-pack-of-2/p/3b2nnr",
        "https://www.amazon.in/dp/B0EXAMPLE",
        "https://www.flipkart.com/product/example"
    ]
    
    # Run scraper
    print("🚀 Starting Universal Scraper...")
    results = asyncio.run(scrape_multiple([test_urls[0]]))  # Test with first URL
    
    # Save results
    with open('scraped_products.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved {len(results)} products to scraped_products.json")
