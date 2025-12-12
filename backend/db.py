
import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages SQLite database for storing crawled product data and local image references.
    """
    
    def __init__(self, db_path: str = "output/products.db"):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_db()

    def _ensure_db_dir(self):
        """Ensure the directory for the database exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _init_db(self):
        """Initialize the database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create products table
            # We store complex structures (lists, dicts) as JSON strings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_url TEXT PRIMARY KEY,
                    platform TEXT,
                    title TEXT,
                    brand TEXT,
                    price REAL,
                    mrp REAL,
                    net_quantity TEXT,
                    manufacturer TEXT,
                    country_of_origin TEXT,
                    description TEXT,
                    features JSON,           -- List[str]
                    specs JSON,              -- Dict[str, str]
                    legal_disclaimer TEXT,
                    seller TEXT,
                    image_urls JSON,         -- List[str]
                    local_image_paths JSON,  -- List[str] - Local file paths
                    aplus_content TEXT,
                    ocr_text TEXT,
                    full_page_text TEXT,
                    extracted_at TEXT,
                    compliance_status TEXT,
                    compliance_score REAL,
                    issues_found JSON        -- List[str]
                )
            """)
            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def upsert_product(self, product_data: Dict[str, Any]):
        """
        Insert or Update a product record.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prepare data: Convert list/dicts to JSON strings
            features_json = json.dumps(product_data.get('features', []))
            specs_json = json.dumps(product_data.get('specs', {}))
            image_urls_json = json.dumps(product_data.get('image_urls', []))
            # local_image_paths might be computed in crawler, defaulting to empty list
            local_paths = product_data.get('local_image_paths', [])
            local_paths_json = json.dumps(local_paths)
            issues_json = json.dumps(product_data.get('issues_found', []))
            
            # Handle timestamps
            extracted_at = product_data.get('extracted_at') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            sql = """
                INSERT INTO products (
                    product_url, platform, title, brand, price, mrp, 
                    net_quantity, manufacturer, country_of_origin, description,
                    features, specs, legal_disclaimer, seller, 
                    image_urls, local_image_paths, aplus_content, 
                    ocr_text, full_page_text, extracted_at, 
                    compliance_status, compliance_score, issues_found
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_url) DO UPDATE SET
                    platform=excluded.platform,
                    title=excluded.title,
                    brand=excluded.brand,
                    price=excluded.price,
                    mrp=excluded.mrp,
                    net_quantity=excluded.net_quantity,
                    manufacturer=excluded.manufacturer,
                    country_of_origin=excluded.country_of_origin,
                    description=excluded.description,
                    features=excluded.features,
                    specs=excluded.specs,
                    legal_disclaimer=excluded.legal_disclaimer,
                    seller=excluded.seller,
                    image_urls=excluded.image_urls,
                    local_image_paths=excluded.local_image_paths,
                    aplus_content=excluded.aplus_content,
                    ocr_text=excluded.ocr_text,
                    full_page_text=excluded.full_page_text,
                    extracted_at=excluded.extracted_at,
                    compliance_status=excluded.compliance_status,
                    compliance_score=excluded.compliance_score,
                    issues_found=excluded.issues_found
            """
            
            values = (
                product_data.get('product_url'),
                product_data.get('platform'),
                product_data.get('title'),
                product_data.get('brand'),
                product_data.get('price'),
                product_data.get('mrp'),
                product_data.get('net_quantity'),
                product_data.get('manufacturer'),
                product_data.get('country_of_origin'),
                product_data.get('description'),
                features_json,
                specs_json,
                product_data.get('legal_disclaimer'),
                product_data.get('seller'),
                image_urls_json,
                local_paths_json,
                product_data.get('aplus_content'),
                product_data.get('ocr_text'),
                product_data.get('full_page_text'),
                extracted_at,
                product_data.get('compliance_status'),
                product_data.get('compliance_score'),
                issues_json
            )
            
            cursor.execute(sql, values)
            conn.commit()
            conn.close()
            logger.info(f"Product saved to DB: {product_data.get('title')[:30]}...")
            
        except Exception as e:
            logger.error(f"Failed to upsert product {product_data.get('product_url')}: {e}")
            # Don't raise, just log error to allow crawler to continue
    
    def get_all_products(self):
        """Get all products from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY extracted_at DESC")
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to list of dicts
            products = []
            for row in rows:
                product = dict(row)
                # Parse JSON fields
                for json_field in ['features', 'specs', 'image_urls', 'local_image_paths', 'issues_found']:
                    if product.get(json_field):
                        try:
                            product[json_field] = json.loads(product[json_field])
                        except:
                            pass
                products.append(product)
            
            return products
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            return []
    
    def export_to_csv(self, output_path: str = "exported_products.csv"):
        """Export all products to a CSV file."""
        import csv
        
        try:
            products = self.get_all_products()
            if not products:
                logger.warning("No products to export")
                return None
            
            # Define CSV columns
            fieldnames = [
                'product_url', 'platform', 'title', 'brand', 'price', 'mrp',
                'net_quantity', 'manufacturer', 'country_of_origin', 
                'compliance_status', 'compliance_score', 'issues_found',
                'description', 'ocr_text', 'extracted_at'
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                
                for product in products:
                    # Convert lists to readable strings
                    if isinstance(product.get('issues_found'), list):
                        product['issues_found'] = '; '.join(product['issues_found'])
                    
                    writer.writerow(product)
            
            logger.info(f"Exported {len(products)} products to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return None
