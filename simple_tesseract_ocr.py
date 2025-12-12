import os
import pytesseract
from PIL import Image
import re
from pathlib import Path

# Configure Tesseract path (update if needed)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path):
    """Extract text from image using Tesseract OCR"""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"Error: {str(e)}"

def validate_legal_metrology(text):
    """
    Validate text against Legal Metrology (Package Commodities) Rules, 2011
    Checks for 6 mandatory declarations
    """
    results = {
        "Manufacturer Name/Address": False,
        "Net Quantity": False,
        "MRP": False,
        "Customer Care": False,  # Will be set to True if found in text
        "Date of Manufacture": False,
        "Country of Origin": False
    }
    
    text_lower = text.lower()
    
    # 1. Manufacturer / Packer / Importer
manufacturer_keywords = [
    'mfd by', 'mfg by', 'manufactured by', 'manufacturer',
    'marketed by', 'packed by', 'pkd by', 'packer', 'imported by',
    'importer', 'mnf by', 'mfg.', 'mfd.', 'mfr.', 'pkd', 'pkgd by',
    'address', 'addr', 'office', 'factory', 'works', 'company',
    'marketed', 'distributed by'
]

if any(word in text_lower for word in manufacturer_keywords):
    results["Manufacturer Name/Address"] = True


# 2. Net Quantity (units & quantity indicators)
net_quantity_keywords = [
    'net quantity', 'net qty', 'net qtty', 'net wt', 'net weight', 
    'weight', 'wt.', 'quantity', 'qty', 'net vol', 'content', 'contents',
    'g', 'gm', 'gram', 'grams', 'kg', 'kilogram',
    'ml', 'millilitre', 'l', 'ltr', 'litre',
    'mg', 'units', 'pcs', 'pieces', 'pack', 'packs',
    'approx', '~', '±'
]

if any(word in text_lower for word in net_quantity_keywords) or \
   re.search(r'\d+\s*(kg|g|gm|ml|l|ltr|litre|mg)', text_lower):
    results["Net Quantity"] = True


# 3. MRP (Maximum Retail Price)
mrp_keywords = [
    'mrp', 'm.r.p', 'maximum retail price', 'max retail price',
    'price', 'retail price', 'mrp:', 'mrp rs', 'mrp ₹',
    'price inclusive of all taxes', 'incl. of all taxes', 'incl taxes',
    'rs.', 'rs', '₹', 'inr', 'rupees', 'mrp-', 'm r p'
]

if any(word in text_lower for word in mrp_keywords):
    results["MRP"] = True


# 4. Customer Care / Consumer Support
customer_care_keywords = [
    'customer care', 'consumer care', 'customer support',
    'helpline', 'toll free', 'support', 'complaints', 'grievance',
    'contact', 'contact us', 'phone', 'call', 'email', '@',
    'care no', 'support no', 'helpline no', 'cust. care', 'write to'
]

if any(word in text_lower for word in customer_care_keywords):
    results["Customer Care"] = True


# 5. Date of Manufacture / Packing / Expiry
date_keywords = [
    'mfg', 'mfd', 'manufactured on', 'manufacturing date',
    'mfg date', 'mfd date', 'date of mfg', 'packaged on',
    'packed on', 'pkd', 'pkd on', 'pkd date',
    'best before', 'expiry', 'exp', 'exp date', 'exp.', 'use before',
    'm/y', 'm:y', 'month year'
]

if any(word in text_lower for word in date_keywords) or \
   re.search(r'\b(0[1-9]|1[0-2])/[0-9]{2,4}\b', text_lower):  # date patterns
    results["Date of Manufacture"] = True


# 6. Country of Origin
origin_keywords = [
    'country of origin', 'origin:', 'origin -', 'origin –',
    'made in', 'manufactured in', 'product of',
    'imported from', 'source country', 'country:',
    'india', 'china', 'japan', 'usa', 'germany', 'korea',
    'thailand', 'vietnam', 'indonesia'
]

if any(word in text_lower for word in origin_keywords):
    results["Country of Origin"] = True

    
    # Calculate compliance score
    compliant_count = sum(results.values())
    score = (compliant_count / 6) * 100
    
    return results, score

def process_directory(directory_path):
    """Process all images in directory"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    results_list = []
    
    print(f"\n{'='*80}")
    print(f"Processing images from: {directory_path}")
    print(f"{'='*80}\n")
    
    for file_path in Path(directory_path).glob('*'):
        if file_path.suffix.lower() in image_extensions:
            print(f"\n📸 Processing: {file_path.name}")
            print("-" * 80)
            
            # Extract text
            ocr_text = extract_text_from_image(file_path)
            
            # Validate
            validation_results, score = validate_legal_metrology(ocr_text)
            
            # Display results
            print(f"\n📝 OCR Text:\n{ocr_text[:300]}...\n")
            
            print(f"✅ Compliance Check:")
            for field, is_present in validation_results.items():
                status = "✓ Found" if is_present else "✗ Missing"
                print(f"  {status:12} - {field}")
            
            print(f"\n📊 Compliance Score: {score:.1f}%")
            
            if score >= 100:
                print("🟢 Status: COMPLIANT")
            elif score >= 50:
                print("🟡 Status: PARTIAL COMPLIANCE")
            else:
                print("🔴 Status: NON-COMPLIANT")
            
            results_list.append({
                'file': file_path.name,
                'score': score,
                'results': validation_results,
                'text': ocr_text
            })
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY: Processed {len(results_list)} images")
    avg_score = sum(r['score'] for r in results_list) / len(results_list) if results_list else 0
    print(f"Average Compliance Score: {avg_score:.1f}%")
    print(f"{'='*80}\n")
    
    return results_list

if __name__ == "__main__":
    # Get directory from user
    directory = input("Enter directory path with images: ").strip()
    
    if not os.path.exists(directory):
        print(f"❌ Directory not found: {directory}")
    else:
        results = process_directory(directory)
