"""
Enhanced Legal Metrology Validation Patterns
Based on Legal Metrology (Package Commodities) Rules, 2011
"""

import re
from typing import Dict, Any, Optional

class LegalMetrologyValidator:
    """
    Comprehensive validator with all keyword variations and OCR error patterns
    """
    
    def __init__(self):
        # MRP Patterns
        self.mrp_patterns = [
            # Primary
            r'mrp[:\s]*₹?\s*([0-9,]+\.?\d*)',
            r'maximum retail price[:\s]*₹?\s*([0-9,]+\.?\d*)',
            r'max retail price[:\s]*₹?\s*([0-9,]+\.?\d*)',
            r'retail price[:\s]*₹?\s*([0-9,]+\.?\d*)',
            # Variants
            r'm\.r\.p[:\s]*₹?\s*([0-9,]+\.?\d*)',
            r'mrp rs\.?\s*([0-9,]+\.?\d*)',
            r'price\s*\(incl\.?\s*taxes?\)[:\s]*₹?\s*([0-9,]+\.?\d*)',
            r'price inclusive of all taxes[:\s]*₹?\s*([0-9,]+\.?\d*)',
            # Symbols
            r'₹\s*([0-9,]+\.?\d*)',
            r'rs\.?\s*([0-9,]+\.?\d*)',
            r'inr\s*([0-9,]+\.?\d*)',
        ]
        
        # Net Quantity Patterns
        self.quantity_patterns = [
            # Primary with units
            r'net quantity[:\s]*([0-9.]+\s*(?:g|gm|gram|grams|kg|kilogram|ml|millilitre|l|litre|mg|units?|pcs?|pieces?|pack|strips?))',
            r'net qty[:\s]*([0-9.]+\s*(?:g|gm|gram|grams|kg|kilogram|ml|millilitre|l|litre|mg|units?|pcs?|pieces?|pack|strips?))',
            r'net wt\.?[:\s]*([0-9.]+\s*(?:g|gm|gram|grams|kg|kilogram|ml|millilitre|l|litre|mg))',
            r'net weight[:\s]*([0-9.]+\s*(?:g|gm|gram|grams|kg|kilogram|ml|millilitre|l|litre|mg))',
            r'net vol\.?[:\s]*([0-9.]+\s*(?:ml|millilitre|l|litre))',
            r'quantity[:\s]*([0-9.]+\s*(?:g|gm|gram|grams|kg|kilogram|ml|millilitre|l|litre|mg|units?|pcs?|pieces?))',
            r'contents?[:\s]*([0-9.]+\s*(?:g|gm|gram|grams|kg|kilogram|ml|millilitre|l|litre|mg|units?|pcs?|pieces?))',
            # Variants
            r'n\.w\.?[:\s]*([0-9.]+\s*(?:g|gm|kg|ml|l))',
            r'nt\.?\s*wt\.?[:\s]*([0-9.]+\s*(?:g|gm|kg|ml|l))',
            r'wt\.?[:\s]*([0-9.]+\s*(?:g|gm|kg|ml|l))',
            r'qty\.?[:\s]*([0-9.]+\s*(?:g|gm|kg|ml|l|units?|pcs?))',
            # Approximation
            r'approx\.?\s*([0-9.]+\s*(?:g|gm|kg|ml|l))',
            # Generic number + unit
            r'([0-9.]+\s*(?:g|gm|gram|grams|kg|kilogram|ml|millilitre|l|litre|mg))',
        ]
        
        # Manufacturer/Packer Patterns
        self.manufacturer_patterns = [
            # Primary
            r'manufactured by[:\s]+([^\n]{10,200})',
            r'mfg\.?\s*by[:\s]+([^\n]{10,200})',
            r'mfd\.?\s*by[:\s]+([^\n]{10,200})',
            r'manufacturer[:\s]+([^\n]{10,200})',
            r'packed by[:\s]+([^\n]{10,200})',
            r'pkd\.?\s*by[:\s]+([^\n]{10,200})',
            r'packer[:\s]+([^\n]{10,200})',
            r'marketed by[:\s]+([^\n]{10,200})',
            r'imported by[:\s]+([^\n]{10,200})',
            r'importer[:\s]+([^\n]{10,200})',
            # Variants
            r'mnf\.?\s*by[:\s]+([^\n]{10,200})',
            r'mfr\.?\s*by[:\s]+([^\n]{10,200})',
            r'mftd\.?\s*by[:\s]+([^\n]{10,200})',
            r'pkged\.?\s*by[:\s]+([^\n]{10,200})',
        ]
        
        # Date Patterns
        self.date_patterns = [
            # Primary
            r'mfd\.?\s*date?[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'mfg\.?\s*date?[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'manufacturing date[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'date of mfg[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'packed on[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'pkd\.?\s*on[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'pkd\.?\s*date?[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'packaging date[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'import date[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            # Month/Year formats
            r'mfd\.?\s*([a-z]{3,9}\s*[0-9]{2,4})',
            r'mfg\.?\s*([a-z]{3,9}\s*[0-9]{2,4})',
            r'pkd\.?\s*([a-z]{3,9}\s*[0-9]{2,4})',
            r'm[:/]y[:\s]*([0-9]{1,2}[/-][0-9]{2,4})',
            # Best before / Expiry
            r'best before[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'expiry[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'shelf life[:\s]*([0-9]+\s*(?:days?|months?|years?))',
        ]
        
        # Country of Origin Patterns
        self.country_patterns = [
            # Primary
            r'country of origin[:\s]+([^\n]{3,50})',
            r'made in[:\s]+([^\n]{3,50})',
            r'manufactured in[:\s]+([^\n]{3,50})',
            r'product of[:\s]+([^\n]{3,50})',
            r'origin[:\s]+([^\n]{3,50})',
            # Variants
            r'c[/]o[:\s]+([^\n]{3,50})',
            r'country[:\s]+([^\n]{3,50})',
            r'imported from[:\s]+([^\n]{3,50})',
            r'source country[:\s]+([^\n]{3,50})',
        ]
        
        # Customer Care Patterns
        self.customer_care_patterns = [
            # Primary
            r'consumer care[:\s]+([^\n]{10,150})',
            r'customer care[:\s]+([^\n]{10,150})',
            r'customer support[:\s]+([^\n]{10,150})',
            r'helpline[:\s]+([^\n]{10,150})',
            r'toll free[:\s]+([^\n]{10,150})',
            r'support[:\s]+([^\n]{10,150})',
            r'complaints?[:\s]+([^\n]{10,150})',
            r'grievance[:\s]+([^\n]{10,150})',
            r'contact[:\s]+([^\n]{10,150})',
            # Variants
            r'cust\.?\s*care[:\s]+([^\n]{10,150})',
            r'helpline no\.?[:\s]+([^\n]{10,150})',
            r'care no\.?[:\s]+([^\n]{10,150})',
            r'email[:\s]+([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})',
            r'call[:\s]+([0-9\s\-+()]{10,20})',
            r'write to[:\s]+([^\n]{10,150})',
            # Phone patterns
            r'(\d{10})',
            r'(\+\d{1,3}\s*\d{10})',
            r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
        ]
        
        # Non-compliance indicators
        self.non_compliant_indicators = [
            'na', 'n/a', 'not applicable', 'not mentioned', 
            'not available', '—', 'nil', 'none'
        ]
    
    def validate(self, text: str, product_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive validation using all patterns
        """
        text_lower = text.lower()
        product_data = product_data or {}
        
        results = {
            "manufacturer": {"valid": False, "value": "MISSING"},
            "net_quantity": {"valid": False, "value": "MISSING"},
            "mrp": {"valid": False, "value": "MISSING"},
            "consumer_care": {"valid": False, "value": "MISSING"},
            "date_of_manufacture": {"valid": False, "value": "MISSING"},
            "country_of_origin": {"valid": False, "value": "MISSING"}
        }
        
        # 1. MRP
        if product_data.get("mrp"):
            results["mrp"]["valid"] = True
            results["mrp"]["value"] = str(product_data["mrp"])
        else:
            for pattern in self.mrp_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    value = match.group(1).strip()
                    if not any(nc in value for nc in self.non_compliant_indicators):
                        results["mrp"]["valid"] = True
                        results["mrp"]["value"] = "₹" + value
                        break
        
        # 2. Net Quantity
        for pattern in self.quantity_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1).strip()
                if not any(nc in value for nc in self.non_compliant_indicators):
                    results["net_quantity"]["valid"] = True
                    results["net_quantity"]["value"] = value
                    break
        
        # 3. Manufacturer
        for pattern in self.manufacturer_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1).strip()
                if len(value) > 10 and not any(nc in value for nc in self.non_compliant_indicators):
                    results["manufacturer"]["valid"] = True
                    results["manufacturer"]["value"] = value[:150]
                    break
        
        # 4. Date
        for pattern in self.date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1).strip()
                if not any(nc in value for nc in self.non_compliant_indicators):
                    results["date_of_manufacture"]["valid"] = True
                    results["date_of_manufacture"]["value"] = value[:50]
                    break
        
        # 5. Country
        for pattern in self.country_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1).strip()
                if len(value) > 2 and not any(nc in value for nc in self.non_compliant_indicators):
                    results["country_of_origin"]["valid"] = True
                    results["country_of_origin"]["value"] = value[:50]
                    break
        
        # 6. Customer Care
        for pattern in self.customer_care_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1).strip() if match.lastindex else match.group(0)
                if len(value) > 5 and not any(nc in value for nc in self.non_compliant_indicators):
                    results["consumer_care"]["valid"] = True
                    results["consumer_care"]["value"] = value[:150]
                    break
        
        # Calculate score
        compliant_count = sum(1 for v in results.values() if v["valid"])
        score = (compliant_count / 6) * 100
        
        results["compliance_score"] = score
        results["full_analysis"] = f"Enhanced validation: {compliant_count}/6 fields found"
        
        return results
