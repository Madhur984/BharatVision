
import os
import sys
import requests
import logging
import sqlite3
import json
import csv
import subprocess
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from backend.app.services.compliance import compliance_service
from backend.app.schemas.compliance import ComplianceRequest
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("EcommerceScraper")

class EcommerceScraper:
    """
    Advanced E-commerce Scraper with Surya OCR and Gemma 2 NLP Validation.
    """
    
    
    def __init__(self, db_path: str = "scraped_results.db", hf_token: Optional[str] = None, api_base_url: str = None):
        """
        Initialize the scraper.
        
        Args:
            db_path: Path to the SQLite database file.
            hf_token: Hugging Face API token (Optional, mainly for local debug if needed).
            api_base_url: Base URL of the API (e.g., https://...hf.space). 
                          Defaults to env var API_BASE_URL or localhost.
        """
        self.db_path = db_path
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        
        # Determine API Base URL
        # Priority: Constructor -> Env Var -> Hardcoded Cloud URL -> Localhost
        self.api_base_url = api_base_url or os.getenv("API_BASE_URL")
        
        # If running in cloud (on the space itself), localhost is fastest
        # But if user wants to force cloud usage from local, they should set API_BASE_URL
        if not self.api_base_url:
            self.api_base_url = "https://madhur984-bharatvision-ml-api.hf.space"
            
        logger.info(f"Initialized Scraper with API Endpoint: {self.api_base_url}")

        self.output_dir = "scraped_data"
        self.images_dir = os.path.join(self.output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        
        self._init_db()
        
        # Headers for scraping to mimic a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def _init_db(self):
        """Initialize the SQLite database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                price TEXT,
                description TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                image_url TEXT,
                local_path TEXT,
                ocr_text TEXT,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS validation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                manufacturer_compliant BOOLEAN,
                net_quantity_compliant BOOLEAN,
                mrp_compliant BOOLEAN,
                consumer_care_compliant BOOLEAN,
                date_of_manufacture_compliant BOOLEAN,
                country_of_origin_compliant BOOLEAN,
                compliance_score REAL,
                full_analysis TEXT,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def scrape_product(self, url: str) -> Optional[int]:
        """
        Main method to scrape a product page.
        """
        logger.info(f"Starting scrape for {url}")
        
        # 1. Fetch HTML
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            return None

        # 2. Extract Basic Details
        title = self._clean_text(self._extract_title(soup))
        price = self._clean_text(self._extract_price(soup))
        description = self._clean_text(self._extract_description(soup))
        
        logger.info(f"Extracted: {title[:50]}... | {price}")

        # 3. Extract & Download Images
        image_urls = self._extract_image_urls(soup, url)
        # Limit to top 5 images to save time/resources for demo
        image_urls = image_urls[:5] 
        logger.info(f"Found {len(image_urls)} images")

        downloaded_images = []
        for i, img_url in enumerate(image_urls):
            local_path = self._download_image(img_url, f"{int(time.time())}_{i}")
            if local_path:
                downloaded_images.append((img_url, local_path))

        # 4. Perform OCR
        ocr_results = [] # List of (local_path, text)
        full_ocr_text = ""
        
        for img_url, local_path in downloaded_images:
            text = self._run_surya_ocr(local_path)
            if text:
                ocr_results.append((local_path, text))
                full_ocr_text += text + "\n"
        
        logger.info(f"OCR completed. Total text length: {len(full_ocr_text)}")

        # Combine all text for validation (Title + Desc + OCR)
        combined_text = f"Title: {title}\nPrice: {price}\nDescription: {description}\n\nOCR Text From Images:\n{full_ocr_text}"

        # 5. Validate Compliance (Hybrid Service)
        # Pre-populate some data from scraping to help the validator
        initial_data = {
            "mrp": price, # We already extracted price!
            "product_name": title
        }
        validation_res = self._validate_with_gemma(combined_text, product_data=initial_data)
        
        # 6. Save to DB
        product_id = self._save_results(
            url, title, price, description, 
            downloaded_images, ocr_results, validation_res
        )
        
        logger.info("Scraping and validation complete.")
        return product_id

    def _clean_text(self, text: str) -> str:
        if not text: return ""
        return " ".join(text.split()).strip()

    def _extract_title(self, soup):
        # Common selectors for Amazon, Flipkart, generic
        selectors = ['#productTitle', 'h1', '.B_NuCI', '.product-title']
        for sel in selectors:
            el = soup.select_one(sel)
            if el: return el.get_text()
        return ""

    def _extract_price(self, soup):
        selectors = ['.a-price-whole', '.a-price .a-offscreen', '._30jeq3', '.price']
        for sel in selectors:
            el = soup.select_one(sel)
            if el: return el.get_text()
        return ""

    def _extract_description(self, soup):
        # Try to find a description block
        selectors = ['#feature-bullets', '#productDescription', '.job-description', 'meta[name="description"]']
        text = ""
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                if el.name == 'meta':
                    text += el.get('content', '') + "\n"
                else:
                    text += el.get_text() + "\n"
        return text

    def _extract_image_urls(self, soup, base_url) -> List[str]:
        """
        Extract only product listing images, filtering out UI elements, logos, and icons.
        Enhanced with Amazon-specific selectors from SwatiModi/e-commerce-web-scraper.
        """
        urls = set()
        
        # Amazon-specific: Use s-image class for product images (from external scraper)
        if 'amazon' in base_url.lower():
            amazon_imgs = soup.find_all('img', {'class': 's-image'})
            for img in amazon_imgs:
                src = img.get('src')
                if src and not src.startswith('data:'):
                    urls.add(src)
                    logger.info(f"Found Amazon product image: {src[:50]}...")
        
        # Generic extraction for all platforms (existing logic)
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-old-hires')
            if not src or src.startswith('data:'):
                continue
                
            full_url = urljoin(base_url, src)
            
            # Filter out common non-product images
            skip_patterns = [
                'sprite', 'icon', 'transparent', 'logo', 'banner', 
                'header', 'footer', 'nav', 'menu', 'button',
                'arrow', 'search', 'cart', 'user', 'profile',
                '1x1', 'pixel', 'blank', 'placeholder'
            ]
            
            # Check if URL contains any skip patterns
            if any(pattern in full_url.lower() for pattern in skip_patterns):
                continue
            
            # Check image dimensions from HTML attributes (filter tiny images)
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    w, h = int(width), int(height)
                    # Skip images smaller than 100x100 (likely UI elements)
                    if w < 100 or h < 100:
                        continue
                except:
                    pass
            
            # Only include images from product-related paths
            product_indicators = ['product', 'item', 'image', 'media', 'img', 'assets']
            if any(indicator in full_url.lower() for indicator in product_indicators):
                urls.add(full_url)
            elif 'amazon' in base_url and 'images-amazon' in full_url:
                # Amazon-specific: their product images are in images-amazon domain
                urls.add(full_url)
            elif 'flipkart' in base_url and ('.jpg' in full_url or '.jpeg' in full_url or '.webp' in full_url):
                # Flipkart: include all image formats from their CDN
                urls.add(full_url)
                
        logger.info(f"Total product images found: {len(urls)}")
        return list(urls)

    def _download_image(self, url: str, prefix: str) -> Optional[str]:
        try:
            ext = url.split('.')[-1].split('?')[0]
            if len(ext) > 4 or ext not in ['jpg', 'jpeg', 'png', 'webp']:
                ext = 'jpg'
            
            filename = f"{prefix}.{ext}"
            path = os.path.join(self.images_dir, filename)
            
            if os.path.exists(path):
                return path

            response = requests.get(url, stream=True, headers=self.headers, timeout=10)
            if response.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return os.path.abspath(path)
        except Exception as e:
            logger.warning(f"Failed to download {url}: {e}")
        return None

    def _run_surya_ocr(self, image_path: str) -> str:
        """
        Runs OCR using the Cloud API endpoint.
        """
        try:
            # Use dynamically configured API URL
            api_url = f"{self.api_base_url.rstrip('/')}/api/ocr/surya"
            
            if not os.path.exists(image_path):
                return ""

            with open(image_path, 'rb') as f:
                files = {'file': f}
                # 300s timeout for cold start models
                response = requests.post(api_url, files=files, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    text = result.get("text", "")
                    if text:
                        return text
                    else:
                        logger.warning(f"Surya OCR API returned empty text.")
                        return ""
                else:
                    logger.warning(f"Surya OCR API error: {result.get('error')}")
                    return ""
            else:
                logger.warning(f"Surya OCR API status {response.status_code}: {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to run Surya OCR via API: {e}")
            return ""

    def _validate_with_gemma(self, text: str, product_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validates text using the new Hybrid Compliance Service.
        """
        try:
            # Construct Request
            req = ComplianceRequest(
                text=text,
                product_data=product_data or {}
            )
            
            # Call Service
            res_obj = compliance_service.check_compliance(req)
            
            # Map Response to Legacy Format for DB Compatibility
            mapped_res = {
                "compliance_score": res_obj.score,
                "full_analysis": json.dumps(res_obj.full_report),
                "manufacturer": {"valid": True, "value": res_obj.data.get("manufacturer_details", "Found")},
                "net_quantity": {"valid": True, "value": res_obj.data.get("net_quantity", "Found")},
                "mrp": {"valid": True, "value": res_obj.data.get("mrp", "Found")},
                "consumer_care": {"valid": True, "value": res_obj.data.get("customer_care_details", "Found")},
                "date_of_manufacture": {"valid": True, "value": res_obj.data.get("date_of_manufacture", "Found")},
                "country_of_origin": {"valid": True, "value": res_obj.data.get("country_of_origin", "Found")},
            }
            
            # Mark fields as invalid if they appear in violations
            for v in res_obj.violations:
                field = v.field
                if field in mapped_res:
                     mapped_res[field]["valid"] = False
                     mapped_res[field]["value"] = "MISSING"
                
                # Handle mapped names
                if field == "manufacturer_details": mapped_res["manufacturer"]["valid"] = False
                if field == "customer_care_details": mapped_res["consumer_care"]["valid"] = False
            
            return mapped_res
            
        except Exception as e:
            logger.error(f"Hybrid validation failed: {e}")
            return {
                "error": str(e),
                "compliance_score": 0,
                "full_analysis": "Validation failed due to internal error."
            }

    def _save_results(self, url, title, price, description, downloaded_images, ocr_results, validation_res) -> int:
        """Save all data to SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert Product
            cursor.execute('''
                INSERT OR REPLACE INTO products (url, title, price, description)
                VALUES (?, ?, ?, ?)
            ''', (url, title, price, description))
            product_id = cursor.lastrowid
            
            # Insert Images & OCR
            # Map local path to ocr text
            ocr_map = {path: text for path, text in ocr_results}
            
            for img_url, local_path in downloaded_images:
                text = ocr_map.get(local_path, "")
                cursor.execute('''
                    INSERT INTO product_images (product_id, image_url, local_path, ocr_text)
                    VALUES (?, ?, ?, ?)
                ''', (product_id, img_url, local_path, text))
            
            # Insert Validation Results
            # Parsing the JSON from Gemma
            v = validation_res
            cursor.execute('''
                INSERT INTO validation_results (
                    product_id, 
                    manufacturer_compliant, net_quantity_compliant, mrp_compliant,
                    consumer_care_compliant, date_of_manufacture_compliant, country_of_origin_compliant,
                    compliance_score, full_analysis
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_id,
                v.get('manufacturer', {}).get('valid', False),
                v.get('net_quantity', {}).get('valid', False),
                v.get('mrp', {}).get('valid', False),
                v.get('consumer_care', {}).get('valid', False),
                v.get('date_of_manufacture', {}).get('valid', False),
                v.get('country_of_origin', {}).get('valid', False),
                v.get('compliance_score', 0.0),
                json.dumps(validation_res) # Store full JSON in analysis column for simplicity
            ))
            
            conn.commit()
            conn.close()
            return product_id
        except Exception as e:
            logger.error(f"Database save error: {e}")
            return -1

    def export_data(self, format="json"):
        """Export database content to JSON or CSV."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products")
        products = [dict(row) for row in cursor.fetchall()]
        
        final_data = []
        for p in products:
            pid = p['id']
            # Get images
            cursor.execute("SELECT * FROM product_images WHERE product_id=?", (pid,))
            p['images'] = [dict(row) for row in cursor.fetchall()]
            
            # Get validation
            cursor.execute("SELECT * FROM validation_results WHERE product_id=?", (pid,))
            val = cursor.fetchone()
            p['validation'] = dict(val) if val else {}
            
            final_data.append(p)
            
        conn.close()
        
        output_file = os.path.join(self.output_dir, f"export_{int(time.time())}.{format}")
        
        if format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
        elif format == 'csv':
            # Flatten for CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'URL', 'Title', 'Price', 'Score', 'Compliance Details'])
                for item in final_data:
                    writer.writerow([
                        item['id'], 
                        item['url'], 
                        item['title'], 
                        item['price'],
                        item.get('validation', {}).get('compliance_score', 0),
                        item.get('validation', {}).get('full_analysis', '')[:500]
                    ])
                    
        logger.info(f"Exported data to {output_file}")
        return output_file

if __name__ == "__main__":
    scraper = EcommerceScraper()
    # Example Usage
    if len(sys.argv) > 1:
        url = sys.argv[1]
        scraper.scrape_product(url)
        scraper.export_data()
    else:
        print("Usage: python ecommerce_scraper.py <url>")
