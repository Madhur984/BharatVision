# data_refiner/config.py
"""
Configuration for Data Refinement Module
Contains regex patterns, model settings, and constants for data extraction
"""

import re
from typing import Dict, List, Pattern

# Model Configuration
MODEL_NAME = "2"  # Ollama model name
MAX_NEW_TOKENS = 100
TEMPERATURE = 0.1  # Low temperature for consistent extraction

# Output Template - Matches ComplianceValidator schema exactly
COMPLIANCE_TEMPLATE = {
    "product_id": None,
    "category": None,
    "manufacturer_details": None,
    "importer_details": None,
    "net_quantity": None,
    "mrp": None,
    "unit_sale_price": None,
    "country_of_origin": None,
    "date_of_manufacture": None,
    "date_of_import": None,
    "best_before_date": None,
    "consumer_care": None,
    "dimensions": None,
    "contents": None
}

# Regex Patterns for High-Confidence Extraction
class RegexPatterns:
    """Pre-compiled regex patterns for data extraction"""
    
    # MRP Patterns - Various formats
    MRP_PATTERNS = [
        re.compile(r'(?:MRP|M\.R\.P\.?|MAXIMUM RETAIL PRICE|MAX\. RETAIL PRICE)\s*[:\-]?\s*(?:₹|RS\.?|INR)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
        re.compile(r'(?:₹|RS\.?|INR)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
        re.compile(r'PRICE[:\-]?\s*(?:₹|RS\.?|INR)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
        re.compile(r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:₹|RS\.?|RUPEES?)', re.IGNORECASE)
    ]
    
    # Net Quantity Patterns
    NET_QUANTITY_PATTERNS = [
        re.compile(r'(?:NET\s+(?:QTY|QUANTITY|WT|WEIGHT)|NET\.?\s*(?:QTY|QUANTITY|WT|WEIGHT))[:\-]?\s*(\d+(?:\.\d+)?\s*(?:G|KG|ML|L|LITERS?|GRAMS?|KILOS?|UNIT|UNITS?|PCS?|PIECES?|N|COUNT))', re.IGNORECASE),
        re.compile(r'(?:QTY|QUANTITY|WT|WEIGHT)[:\-]?\s*(\d+(?:\.\d+)?\s*(?:G|KG|ML|L|LITERS?|GRAMS?|KILOS?|UNIT|UNITS?|PCS?|PIECES?|N|COUNT))', re.IGNORECASE),
        re.compile(r'(\d+(?:\.\d+)?\s*(?:G|KG|ML|L|LITERS?|GRAMS?|KILOS?|UNIT|UNITS?|PCS?|PIECES?|N|COUNT))\s*(?:NET|NETT)', re.IGNORECASE),
        re.compile(r'(\d+\s*(?:G|KG|ML|L|UNIT|UNITS?|PCS?|PIECES?|N))\b', re.IGNORECASE)
    ]
    
    # Date Patterns - Manufacturing, Import, Best Before
    DATE_PATTERNS = [
        # MM/YYYY format
        re.compile(r'(?:MFD|MFG|MANUFACTURED|MANUFACTURING|DATE\s+OF\s+MFG)[:\-]?\s*(\d{1,2}\/\d{4})', re.IGNORECASE),
        re.compile(r'(?:MFD|MFG)[:\-]?\s*(\d{1,2}\/\d{4})', re.IGNORECASE),
        # DD/MM/YYYY format
        re.compile(r'(?:MFD|MFG|MANUFACTURED|MANUFACTURING|DATE\s+OF\s+MFG)[:\-]?\s*(\d{1,2}\/\d{1,2}\/\d{4})', re.IGNORECASE),
        # Best before patterns
        re.compile(r'(?:BEST\s+BEFORE|USE\s+BEFORE|EXPIRY|EXP)[:\-]?\s*(\d{1,2}\/\d{1,2}\/\d{4})', re.IGNORECASE),
        re.compile(r'(?:BEST\s+BEFORE|USE\s+BEFORE|EXPIRY|EXP)[:\-]?\s*(\d{1,2}\/\d{4})', re.IGNORECASE),
        # Import date patterns
        re.compile(r'(?:IMPORT|IMPORTED)[:\-]?\s*(\d{1,2}\/\d{1,2}\/\d{4})', re.IGNORECASE),
        re.compile(r'(?:IMPORT|IMPORTED)[:\-]?\s*(\d{1,2}\/\d{4})', re.IGNORECASE)
    ]
    
    # Country of Origin Patterns
    COUNTRY_PATTERNS = [
        re.compile(r'(?:MADE\s+IN|COUNTRY\s+OF\s+ORIGIN|ORIGIN)[:\-]?\s*([A-Z][A-Z\s]{2,20})', re.IGNORECASE),
        re.compile(r'(?:MANUFACTURED\s+IN)[:\-]?\s*([A-Z][A-Z\s]{2,20})', re.IGNORECASE)
    ]
    
    # Consumer Care Patterns - Phone numbers and emails
    CONSUMER_CARE_PATTERNS = [
        re.compile(r'(?:CUSTOMER\s+(?:CARE|SERVICE|SUPPORT)|CONSUMER\s+CARE|HELPLINE|CONTACT)[:\-]?\s*([0-9\s\-\+\(\)]{10,20})', re.IGNORECASE),
        re.compile(r'(\d{4}\s+\d{3}\s+\d{4})', re.IGNORECASE),  # 1800 123 4567 format
        re.compile(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', re.IGNORECASE),  # Email
        re.compile(r'(?:TOLL\s+FREE|FREE)[:\-]?\s*([0-9\s\-\+\(\)]{10,20})', re.IGNORECASE)
    ]
    
    # Manufacturer/Company Patterns
    MANUFACTURER_PATTERNS = [
        re.compile(r'(?:MANUFACTURED\s+BY|MFD\s+BY|COMPANY)[:\-]?\s*([A-Z][A-Za-z0-9\s\.,\-]{10,100})', re.IGNORECASE),
        re.compile(r'([A-Z][A-Za-z\s]+(?:LTD|LIMITED|PRIVATE|PVT|COMPANY|CO|CORP|CORPORATION|INC)[A-Za-z\s\.,\-]*)', re.IGNORECASE),
        re.compile(r'([A-Z][A-Za-z0-9\s\.,\-]+(?:700\d{3}|110\d{3}|400\d{3}|500\d{3}|560\d{3}|600\d{3}))', re.IGNORECASE)  # With PIN codes
    ]
    
    # Dimensions Patterns
    DIMENSION_PATTERNS = [
        re.compile(r'(?:SIZE|DIMENSIONS?|MEASUREMENTS?)[:\-]?\s*(\d+(?:\.\d+)?\s*[X×]\s*\d+(?:\.\d+)?(?:\s*[X×]\s*\d+(?:\.\d+)?)?\s*(?:CM|MM|M|INCHES?|IN)?)', re.IGNORECASE),
        re.compile(r'(\d+(?:\.\d+)?\s*[X×]\s*\d+(?:\.\d+)?(?:\s*[X×]\s*\d+(?:\.\d+)?)?\s*(?:CM|MM|M|INCHES?|IN))', re.IGNORECASE)
    ]

# Common Indian company suffixes for better manufacturer detection
COMPANY_SUFFIXES = [
    "LIMITED", "LTD", "PRIVATE LIMITED", "PVT LTD", "PVT. LTD.", 
    "COMPANY", "CO", "CORPORATION", "CORP", "INC", "INCORPORATED",
    "ENTERPRISES", "INDUSTRIES", "FOODS", "PRODUCTS"
]

# Common unit standardization
UNIT_STANDARDIZATION = {
    "G": "g", "GRAMS": "g", "GRAM": "g",
    "KG": "kg", "KILOS": "kg", "KILO": "kg",
    "ML": "ml", "MILLILITRES": "ml", "MILLILITERS": "ml",
    "L": "L", "LITRES": "L", "LITERS": "L",
    "UNIT": "UNIT", "UNITS": "UNIT",
    "PCS": "PCS", "PIECES": "PCS", "PIECE": "PCS",
    "N": "N", "COUNT": "COUNT"
}

# Currency standardization
CURRENCY_SYMBOLS = ["₹", "RS.", "RS", "INR", "RUPEES", "RUPEE"]

# NLP Prompts for Complex Extraction
NLP_PROMPTS = {
    "manufacturer": """From the following text, extract only the manufacturer's or company's full name and complete address including city, state, and PIN code. Return only the manufacturer details, nothing else: "{text}" """,
    
    "consumer_care": """From the following text, extract only customer care contact information including phone numbers and email addresses. Return only the contact details, nothing else: "{text}" """,
    
    "importer": """From the following text, extract only the importer's name and address if mentioned. Return only the importer details or return 'None' if not found: "{text}" """,
    
    "product_category": """From the following text, identify the product category or type. Return only the product category in 1-2 words: "{text}" """,
    
    "product_contents": """From the following text, extract only the product contents or ingredients list. Ignore manufacturing details, addresses, and contact information. Return only the product contents: "{text}" """
}

# Data Validation Rules
VALIDATION_RULES = {
    "mrp": {
        "min_value": 1,
        "max_value": 100000,
        "required_prefix": "₹"
    },
    "net_quantity": {
        "required_units": ["g", "kg", "ml", "L", "UNIT", "PCS", "N"],
        "min_numeric": 0.1
    },
    "phone": {
        "min_digits": 10,
        "max_digits": 15
    }
}