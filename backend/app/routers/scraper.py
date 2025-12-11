from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging
import json
import sqlite3

router = APIRouter()
logger = logging.getLogger("bharatvision.scraper")

class ScrapeRequest(BaseModel):
    url: str = Field(..., description="E-commerce URL to scrape")
    save_images: bool = Field(default=True, description="Whether to download and save images")

@router.post("/ecommerce")
async def scrape_ecommerce(request: ScrapeRequest):
    """
    Scrape an e-commerce page using the existing EcommerceScraper backend.
    """
    logger.info(f"Received scrape request for: {request.url}")
    
    try:
        from backend.ecommerce_scraper import EcommerceScraper
        
        # Initialize scraper with DB path relative to execution root
        # Ideally this path should be in config
        scraper = EcommerceScraper(db_path="scraped_results.db")
        
        product_id = scraper.scrape_product(request.url)
        
        if product_id and product_id > 0:
            # Fetch result from DB
            conn = sqlite3.connect("scraped_results.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
            product = dict(cursor.fetchone())
            
            cursor.execute("SELECT * FROM product_images WHERE product_id=?", (product_id,))
            images = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM validation_results WHERE product_id=?", (product_id,))
            validation_row = cursor.fetchone()
            validation = dict(validation_row) if validation_row else {}
            
            if validation.get('full_analysis'):
                try:
                    validation['full_analysis'] = json.loads(validation['full_analysis'])
                except:
                    pass
            
            conn.close()
            
            return {
                "success": True,
                "product_id": product_id,
                "data": product,
                "images": images,
                "validation": validation
            }
        else:
             return {"success": False, "error": "Scraping failed or returned no content."}
             
    except Exception as e:
        logger.error(f"Scrape API error: {e}")
        return {"success": False, "error": str(e)}
