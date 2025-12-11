import json
import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path so `backend` package imports resolve
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.crawler import EcommerceCrawler

logging.basicConfig(level=logging.INFO)

# Single product URL to test
product_url = 'https://www.amazon.in/dp/B01JCFDX4S'

crawler = EcommerceCrawler()
print('Fetching:', product_url)
product = crawler.get_product_details(product_url, 'amazon')
if product is None:
    print('No product data returned')
else:
    # Convert dataclass to dict if needed
    try:
        d = product.__dict__
    except Exception:
        from dataclasses import asdict
        d = asdict(product)
    print(json.dumps(d, indent=2, ensure_ascii=False))
