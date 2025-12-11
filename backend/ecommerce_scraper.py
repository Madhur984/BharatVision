
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
from huggingface_hub import InferenceClient
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
    
    def __init__(self, db_path: str = "scraped_results.db", hf_token: Optional[str] = None):
        """
        Initialize the scraper.
        
        Args:
            db_path: Path to the SQLite database file.
            hf_token: Hugging Face API token. If None, tries to load from environment.
        """
        self.db_path = db_path
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        
        if not self.hf_token:
            # Try loading from .env or .env.cloud
            try:
                from dotenv import load_dotenv
                load_dotenv()
                self.hf_token = os.getenv("HF_TOKEN")
                if not self.hf_token and os.path.exists(".env.cloud"):
                     with open(".env.cloud", "r") as f:
                        for line in f:
                            if line.startswith("HF_TOKEN="):
                                self.hf_token = line.strip().split("=", 1)[1]
            except Exception:
                pass

        if not self.hf_token:
            logger.warning("HF_TOKEN not found. NLP validation will yield empty results.")

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
        
        Steps:
        1. Fetch HTML
        2. Extract Basic Details
        3. Extract & Download Images
        4. Perform OCR (Surya)
        5. Validate Compliance (Gemma 2)
        6. Save to DB
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

        # 5. Validate Compliance (Gemma 2)
        validation_res = self._validate_with_gemma(combined_text)
        
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
        urls = set()
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-old-hires')
            if src and not src.startswith('data:'):
                full_url = urljoin(base_url, src)
                # Filter out tiny icons often < 50px dimensions logic skipped for speed, filtering by keywords
                if 'sprite' not in full_url and 'icon' not in full_url and 'transparent' not in full_url:
                    urls.add(full_url)
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
        Runs OCR using local Surya OCR via API.
        """
        try:
            api_url = "http://localhost:8000/api/ocr/surya"
            
            if not os.path.exists(image_path):
                return ""

            with open(image_path, 'rb') as f:
                files = {'file': f}
                # Local OCR should be faster but initial load is slow
                response = requests.post(api_url, files=files, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    text = result.get("text", "")
                    if text:
                        return text
                    else:
                        logger.warning(f"Surya OCR API returned empty text for {os.path.basename(image_path)}")
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

    def _validate_with_gemma(self, text: str) -> Dict[str, Any]:
        """
        Validates text against 6 strict criteria using Gemma 2.
        Returns a dictionary with validation results.
        """
        if not self.hf_token:
            return {"score": 0, "analysis": "No HF Token detected."}
            
        prompt = f"""
You are a Legal Metrology Compliance Officer. Analyze the following product text (extracted from an e-commerce page and images) and verify if it contains the following 6 MANDATORY declarations.

MANDATORY DECLARATIONS:
1. Manufacturer Name & Address (Must include name and full address)
2. Net Quantity (Must be standard units like kg, g, ml, L, pc)
3. MRP (Maximum Retail Price)
4. Consumer Care Details (Phone or Email)
5. Date of Manufacture (or Packing/Import date)
6. Country of Origin

TEXT TO ANALYZE:
{text[:4000]} 

Evaluate each point strictly. valid=true if present and clear, valid=false if missing or ambiguous.
Return ONLY a valid JSON object in the following format:
{{
  "manufacturer": {{ "valid": boolean, "value": "extracted text or MISSING" }},
  "net_quantity": {{ "valid": boolean, "value": "extracted text or MISSING" }},
  "mrp": {{ "valid": boolean, "value": "extracted text or MISSING" }},
  "consumer_care": {{ "valid": boolean, "value": "extracted text or MISSING" }},
  "date_of_manufacture": {{ "valid": boolean, "value": "extracted text or MISSING" }},
  "country_of_origin": {{ "valid": boolean, "value": "extracted text or MISSING" }},
  "compliance_score": number (0-100 based on how many valid)
}}
"""
        try:
            client = InferenceClient(token=self.hf_token)
            # Using chat completion for instruction following
            messages = [{"role": "user", "content": prompt}]
            
            model = "google/gemma-2-9b-it" 
            response = client.chat_completion(messages, model=model, max_tokens=1000)
            
            content = response.choices[0].message.content
            
            # Extract JSON from response
            json_str = content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
                
            data = json.loads(json_str.strip())
            data['full_analysis'] = content # Save raw mostly for debug
            return data
            
        except Exception as e:
            logger.error(f"Gemma validation failed: {e}")
            return {
                "error": str(e),
                "compliance_score": 0,
                "full_analysis": "Validation failed due to API error."
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
