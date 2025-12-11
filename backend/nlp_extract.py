"""NLP-based field extraction from product text"""

import re
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

def extract_fields(text: str) -> Dict[str, Any]:
    """Extract legal metrology fields from product text"""
    
    text_lower = text.lower()
    fields = {}
    
    # Extract MRP
    mrp_patterns = [
        r'mrp[:\s]*(?:rs\.?)?[\s]*(\d+(?:\.\d{2})?)',
        r'₹\s*(\d+(?:\.\d{2})?)',
        r'price[:\s]*(?:rs\.?)?[\s]*(\d+(?:\.\d{2})?)',
    ]
    for pattern in mrp_patterns:
        match = re.search(pattern, text_lower)
        if match:
            fields['mrp_value'] = float(match.group(1))
            fields['mrp_raw'] = match.group(0)
            break
    
    # Extract Quantity
    qty_pattern = r'(\d+(?:\.\d{2})?)\s*(ml|l|litre|liter|g|kg|gm|mg|pcs|pieces)'
    match = re.search(qty_pattern, text_lower)
    if match:
        fields['net_quantity_value'] = float(match.group(1))
        fields['unit'] = match.group(2)
        fields['net_quantity_raw'] = match.group(0)
    
    # Extract Dates
    date_pattern = r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})'
    dates = re.findall(date_pattern, text)
    if dates:
        fields['mfg_date'] = f"{dates[0][0]}/{dates[0][1]}/{dates[0][2]}"
        if len(dates) > 1:
            fields['expiry_date'] = f"{dates[1][0]}/{dates[1][1]}/{dates[1][2]}"
    
    # Extract Brand/Manufacturer names (simple heuristic)
    brand_keywords = ['brand:', 'made by:', 'mfg by:', 'manufacturer:']
    for keyword in brand_keywords:
        if keyword in text_lower:
            start = text_lower.find(keyword) + len(keyword)
            end = text_lower.find('\n', start) if '\n' in text[start:] else start + 50
            fields['manufacturer_name'] = text[start:end].strip()[:50]
            break
    
    # Extract Country of Origin
    if 'made in' in text_lower or 'country of origin' in text_lower:
        countries = ['india', 'usa', 'china', 'japan', 'germany', 'uk']
        for country in countries:
            if country in text_lower:
                fields['country_of_origin'] = country.upper()
                break
    
    # Extract FSSAI/License numbers
    fssai_pattern = r'fssai[:\s]*([a-z0-9]+)'
    match = re.search(fssai_pattern, text_lower)
    if match:
        fields['fssai_number'] = match.group(1)
    
    # Extract phone numbers
    phone_pattern = r'(?:\+91|0)?[6-9]\d{9,10}'
    match = re.search(phone_pattern, text)
    if match:
        fields['contact_number'] = match.group(0)
    
    # Set confidence
    core_fields_found = sum(1 for k in ['mrp_value', 'net_quantity_value', 'manufacturer_name', 'country_of_origin'] if k in fields)
    fields['extraction_confidence'] = min(100, (core_fields_found / 4) * 100)
    
    return fields

def extract_and_validate(text: str) -> Dict[str, Any]:
    """Extract fields and return structured data"""
    fields = extract_fields(text)
    
    # Basic validation
    validation = {
        'has_mrp': 'mrp_value' in fields,
        'has_quantity': 'net_quantity_value' in fields,
        'has_manufacturer': 'manufacturer_name' in fields,
        'has_country': 'country_of_origin' in fields,
        'has_dates': 'mfg_date' in fields or 'expiry_date' in fields
    }
    
    return {
        'extracted_fields': fields,
        'validation': validation,
        'extraction_confidence': fields.get('extraction_confidence', 0)
    }
