# Universal E-commerce Scraper - Installation Guide

## Prerequisites

Install Playwright:
```bash
pip install playwright
playwright install chromium
```

## Usage

### 1. Single Product
```python
import asyncio
from universal_playwright_scraper import scrape_product

url = "https://www.meesho.com/product/xyz"
result = asyncio.run(scrape_product(url))
print(result)
```

### 2. Multiple Products
```python
import asyncio
from universal_playwright_scraper import scrape_multiple

urls = [
    "https://www.meesho.com/product1",
    "https://www.amazon.in/product2",
    "https://www.flipkart.com/product3"
]

results = asyncio.run(scrape_multiple(urls))
```

### 3. Run Directly
```bash
python universal_playwright_scraper.py
```

## Features

✅ Works on **ANY** e-commerce website
✅ Bypasses anti-bot protection (uses real browser)
✅ Handles JavaScript-heavy sites
✅ Extracts: Title, Price, MRP, Images, Full Text
✅ No rate limiting issues
✅ Works for Meesho, Flipkart, Amazon, etc.

## Output Format

```json
{
  "url": "https://...",
  "title": "Product Name",
  "price": "₹299",
  "mrp": "₹599",
  "brand": "Brand Name",
  "images": ["https://image1.jpg", "https://image2.jpg"],
  "full_text": "Complete page text..."
}
```

## Troubleshooting

If you get errors:
1. Make sure Playwright is installed: `playwright install chromium`
2. On Linux, install dependencies: `playwright install-deps chromium`
3. On Streamlit Cloud, add to `packages.txt`:
   ```
   chromium
   chromium-driver
   ```
