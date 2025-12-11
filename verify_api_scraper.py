
import requests
import json
import time

URL = "http://localhost:8000/api/scrape/ecommerce"
TARGET_PAGE = "https://en.wikipedia.org/wiki/Honey" # Safe test URL

payload = {
    "url": TARGET_PAGE,
    "save_images": True
}

print(f"Calling Scraper API at {URL}...")
print(f"Target: {TARGET_PAGE}")

try:
    start_time = time.time()
    response = requests.post(URL, json=payload, timeout=300) # Increased timeout for Meta Llama Vision
    duration = time.time() - start_time
    
    print(f"Request completed in {duration:.2f} seconds")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n--- API SUCCESSS ---")
        print(f"Product ID: {data.get('product_id')}")
        
        prod = data.get('data', {})
        print(f"Title: {prod.get('title')}")
        
        imgs = data.get('images', [])
        print(f"Images Extracted: {len(imgs)}")
        if imgs:
            print(f"Sample OCR: {imgs[0].get('ocr_text', '')[:100]}...")
            
        val = data.get('validation', {})
        print(f"\nCompliance Score: {val.get('compliance_score')}")
        print("Mandatory Fields Check:")
        print(f" - Manufacturer: {val.get('manufacturer_compliant')}")
        print(f" - Net Qty: {val.get('net_quantity_compliant')}")
        print(f" - MRP: {val.get('mrp_compliant')}")
        
    else:
        print(f"\nAPI FAILED: {response.text}")

except Exception as e:
    print(f"\nConnection Error: {e}")
    print("Ensure 'simple_api.py' is running on port 8000!")
