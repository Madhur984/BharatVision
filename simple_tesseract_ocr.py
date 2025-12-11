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
        "Customer Care": False,
        "Date of Manufacture": False,
        "Country of Origin": False
    }
    
    text_lower = text.lower()
    
    # 1. Manufacturer (look for "mfd by", "manufactured by", "marketed by")
    if any(word in text_lower for word in ['mfd by', 'manufactured by', 'marketed by', 'manufacturer']):
        results["Manufacturer Name/Address"] = True
    
    # 2. Net Quantity (look for units: kg, g, ml, l, litre)
    if re.search(r'\d+\s*(kg|g|gm|ml|l|litre|ltr)', text_lower):
        results["Net Quantity"] = True
    
    # 3. MRP (look for "mrp", "price", "rs", "₹")
    if any(word in text_lower for word in ['mrp', 'price', 'rs.', '₹']):
        results["MRP"] = True
    
    # 4. Customer Care (look for phone, email, "customer care")
    if any(word in text_lower for word in ['customer care', 'care', 'contact', '@', 'phone']):
        results["Customer Care"] = True
    
    # 5. Date of Manufacture (look for "mfg", "date", "exp")
    if any(word in text_lower for word in ['mfg', 'date', 'exp', 'expiry', 'best before']):
        results["Date of Manufacture"] = True
    
    # 6. Country of Origin (look for "made in", "country", "india")
    if any(word in text_lower for word in ['made in', 'country of origin', 'product of', 'india']):
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
