import sys
import pathlib
import json
import pprint

# Ensure project root in path
project_root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.crawler import EcommerceCrawler

def main():
    url = 'https://www.amazon.in/TATA-Product-Essential-Nutrition-Superfood/dp/B01JCFDX4S/'
    # Enable image extraction so YOLO + OCR is attempted.
    crawler = EcommerceCrawler(image_extractor=True)

    # Ensure crawler will try YOLO + OCR. Use Surya if available; otherwise fall back to Tesseract.
    try:
        from pathlib import Path
        repo_root = Path(__file__).resolve().parent.parent
        # point to bundled YOLO model if present
        crawler.yolo_model_path = str(repo_root / 'best.pt')
    except Exception:
        pass
    # prefer Surya if installed; otherwise rely on pytesseract (Tesseract must be installed on system)
    crawler.use_surya = False
    print('Fetching product details for:', url)
    prod = crawler.get_product_details(url, 'amazon')
    if not prod:
        print('Failed to extract product details')
        return

    out = {
        'title': prod.title,
        'brand': prod.brand,
        'price': prod.price,
        'mrp': prod.mrp,
        'description': (prod.description or '')[:1000],
        'page_text_snippet': (prod.full_page_text or '')[:1500],
        'ocr_snippet': (prod.ocr_text or '')[:800],
        'compliance_score': prod.compliance_score,
        'issues_found': prod.issues_found,
        'extracted_fields': (prod.compliance_details or {}).get('extracted_fields')
    }

    pprint.pprint(out)

if __name__ == '__main__':
    main()
