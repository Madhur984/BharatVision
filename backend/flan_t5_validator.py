"""
Flan-T5 based Legal Metrology Validator
Uses Google Flan-T5 to intelligently extract mandatory fields from text
"""

import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class FlanT5Validator:
    """
    Uses Flan-T5 LLM to extract Legal Metrology fields from product text
    """
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load Flan-T5 model - DISABLED, using regex fallback"""
        # Transformers removed - not using Flan-T5 anymore
        # try:
        #     from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        #     model_name = "google/flan-t5-base"
        #     logger.info(f"Loading {model_name}...")
        #     self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        #     self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        #     logger.info("Flan-T5 model loaded successfully")
        # except Exception as e:
        #     logger.error(f"Failed to load Flan-T5: {e}")
        self.model = None
        self.tokenizer = None
    
    def _ask_model(self, question: str, context: str) -> str:
        """Ask Flan-T5 a question about the text"""
        if not self.model or not self.tokenizer:
            return ""
        
        try:
            # Limit context to avoid token limits
            context = context[:2000]
            
            prompt = f"Question: {question}\nContext: {context}\nAnswer:"
            
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
            outputs = self.model.generate(**inputs, max_length=100)
            answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return answer.strip()
        except Exception as e:
            logger.error(f"Flan-T5 query failed: {e}")
            return ""
    
    def validate(self, text: str, product_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Use Flan-T5 to extract all 6 mandatory fields
        """
        product_data = product_data or {}
        
        results = {
            "manufacturer": {"valid": False, "value": "MISSING"},
            "net_quantity": {"valid": False, "value": "MISSING"},
            "mrp": {"valid": False, "value": "MISSING"},
            "consumer_care": {"valid": False, "value": "MISSING"},
            "date_of_manufacture": {"valid": False, "value": "MISSING"},
            "country_of_origin": {"valid": False, "value": "MISSING"}
        }
        
        # If model not loaded, fall back to regex
        if not self.model:
            logger.warning("Flan-T5 not available, using regex fallback")
            return self._regex_fallback(text, product_data)
        
        # Ask Flan-T5 to extract each field
        logger.info("Using Flan-T5 to extract fields...")
        
        # 1. Manufacturer
        manufacturer = self._ask_model(
            "What is the manufacturer or packer name and address?",
            text
        )
        if manufacturer and len(manufacturer) > 5:
            results["manufacturer"]["valid"] = True
            results["manufacturer"]["value"] = manufacturer[:150]
        
        # 2. Net Quantity
        quantity = self._ask_model(
            "What is the net quantity or weight of the product?",
            text
        )
        if quantity and any(unit in quantity.lower() for unit in ['g', 'kg', 'ml', 'l', 'gram', 'liter']):
            results["net_quantity"]["valid"] = True
            results["net_quantity"]["value"] = quantity[:50]
        
        # 3. MRP
        if product_data.get("mrp"):
            results["mrp"]["valid"] = True
            results["mrp"]["value"] = str(product_data["mrp"])
        else:
            mrp = self._ask_model(
                "What is the MRP or maximum retail price?",
                text
            )
            if mrp and (any(c.isdigit() for c in mrp)):
                results["mrp"]["valid"] = True
                results["mrp"]["value"] = mrp[:50]
        
        # 4. Customer Care
        contact = self._ask_model(
            "What is the customer care or contact information?",
            text
        )
        if contact and len(contact) > 5:
            results["consumer_care"]["valid"] = True
            results["consumer_care"]["value"] = contact[:150]
        
        # 5. Date
        date = self._ask_model(
            "What is the manufacturing date or best before date?",
            text
        )
        if date and len(date) > 2:
            results["date_of_manufacture"]["valid"] = True
            results["date_of_manufacture"]["value"] = date[:50]
        
        # 6. Country
        country = self._ask_model(
            "What is the country of origin?",
            text
        )
        if country and len(country) > 2:
            results["country_of_origin"]["valid"] = True
            results["country_of_origin"]["value"] = country[:50]
        
        # Calculate score
        compliant_count = sum(1 for v in results.values() if v["valid"])
        score = (compliant_count / 6) * 100
        
        results["compliance_score"] = score
        results["full_analysis"] = f"Flan-T5 validation: {compliant_count}/6 fields found"
        
        logger.info(f"Flan-T5 validation: {score:.1f}% ({compliant_count}/6 fields)")
        
        return results
    
    def _regex_fallback(self, text: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simple regex fallback if Flan-T5 not available"""
        from backend.enhanced_validator import LegalMetrologyValidator
        validator = LegalMetrologyValidator()
        return validator.validate(text, product_data)
