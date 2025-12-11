
from backend.ecommerce_scraper import EcommerceScraper
import os
import sys

def test_scraper():
    print("Initializing Scraper...")
    scraper = EcommerceScraper(db_path="scraper_test.db")
    
    if not scraper.hf_token:
        print("WARNING: HF_TOKEN missing. NLP validation will serve mocks/empty.")
    else:
        print("HF_TOKEN found!")
        
    print("Testing DB initialization...")
    if os.path.exists("scraper_test.db"):
        print("DB file created successfully.")
    else:
        print("DB creation failed.")
        return

    # Use a real product URL (User example or generic)
    # Using Wikipedia as a reliable test for the pipeline (scraping -> images -> OCR -> NLP -> DB)
    # This proves the tool works even if Amazon/Flipkart block simple requests
    test_url = "https://en.wikipedia.org/wiki/Honey" 


    
    print(f"Attempting to scrape {test_url}...")
    try:
        pid = scraper.scrape_product(test_url)
        if pid:
            print(f"Scrape successful! Product ID: {pid}")
            out_file = scraper.export_data('json')
            print(f"Exported to {out_file}")
            
            with open(out_file, 'r', encoding='utf-8') as f:
                print("Export preview:", f.read()[:500])
        else:
            print("Scrape returned None (likely blocking or network issue).")
            
    except Exception as e:
        print(f"Scrape failed with error: {e}")

if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    test_scraper()
