import argparse
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.ecommerce_scraper import EcommerceScraper

def main():
    parser = argparse.ArgumentParser(description="BharatVision Web Scraper")
    parser.add_argument("url", help="URL of the product page to scrape")
    parser.add_argument("--db", default="scraped_data.db", help="Path to output database")
    args = parser.parse_args()

    print(f"Initializing Scraper for {args.url}...")
    scraper = EcommerceScraper(db_path=args.db)

    try:
        pid = scraper.scrape_product(args.url)
        if pid:
            print(f"✅ Scrape successful! Product ID: {pid}")
            # Export to JSON
            out_file = scraper.export_data('json')
            print(f"📄 Data exported to: {out_file}")
        else:
            print("❌ Scrape failed to retrieve product details.")
    except Exception as e:
        print(f"❌ Error scraping: {e}")

if __name__ == "__main__":
    main()
