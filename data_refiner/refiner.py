# data_refiner/refiner.py
"""
DataRefiner Class - Main module for cleaning and structuring OCR output

This class takes messy OCR output and produces clean, structured JSON
ready for compliance validation using a hybrid approach of regex patterns
and targeted NLP extraction.

NOTE: Heavy imports (transformers) are done LAZILY inside __init__ 
to avoid model loading at module import time.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
import copy
import torch

# Lazy import flag - actual import happens in __init__
TRANSFORMERS_AVAILABLE = None  # Will be set in __init__

from .config import (
    COMPLIANCE_TEMPLATE, RegexPatterns, NLP_PROMPTS, UNIT_STANDARDIZATION,
    CURRENCY_SYMBOLS, COMPANY_SUFFIXES, VALIDATION_RULES, MODEL_NAME,
    MAX_NEW_TOKENS, TEMPERATURE
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataRefiner:
    """
    Main class for refining messy OCR output into clean compliance JSON
    
    Uses a hybrid approach:
    1. High-confidence regex extraction for structured data (MRP, dates, quantities)
    2. Targeted NLP extraction for complex multi-line fields (manufacturer, consumer care)
    3. Final cleanup and standardization
    """
    
    def __init__(self):
        """Initialize the DataRefiner with regex patterns and NLP model"""
        logger.info("Initializing DataRefiner...")
        
        # Initialize regex patterns
        self.patterns = RegexPatterns()
        
        # Initialize NLP model - DISABLED (using Ollama API instead)
        self.nlp_available = False
        self.nlp_pipeline = None
        logger.info("NLP extraction via Ollama API (not loading transformers)")
        
        # Track extracted data to avoid duplication
        self.extracted_substrings = set()
        
        logger.info("DataRefiner initialized successfully")
    
    def refine(self, messy_data: Dict[str, Any], use_nlp: bool = True) -> Dict[str, Optional[str]]:
        """
        Main refinement method that takes messy OCR data and returns clean structured JSON
        
        Args:
            messy_data: Dictionary with messy OCR output
            use_nlp: (Optional) Whether to use Gemma 2 AI for extraction (default: True)
            
        Returns:
            Dictionary matching ComplianceValidator schema with clean data
        """
        logger.info(f"Starting data refinement process (NLP enabled: {use_nlp})...")
        
        # Step 1: Initialize clean output template
        clean_output = copy.deepcopy(COMPLIANCE_TEMPLATE)
        
        # Step 2: Aggregate all text content for processing
        all_text = self._aggregate_text(messy_data)
        logger.info(f"Processing text content: {len(all_text)} characters")
        
        # Step 3: High-confidence regex extraction
        remaining_text = self._extract_with_regex(all_text, clean_output)
        
        # Step 4: Targeted NLP extraction for complex fields
        if self.nlp_available and use_nlp and remaining_text.strip():
            self._extract_with_nlp(remaining_text, clean_output)
        
        # Step 5: Final cleanup and standardization
        self._final_cleanup(clean_output)
        
        # Step 6: Copy over simple fields that don't need processing
        self._copy_simple_fields(messy_data, clean_output)
        
        logger.info("Data refinement completed")
        return clean_output
    
    def _aggregate_text(self, messy_data: Dict[str, Any]) -> str:
        """Aggregate all string values from messy data into one text block"""
        text_parts = []
        
        for key, value in messy_data.items():
            if isinstance(value, str) and value.strip():
                text_parts.append(value.strip())
        
        return " ".join(text_parts)
    
    def _extract_with_regex(self, text: str, clean_output: Dict) -> str:
        """
        Extract high-confidence data using regex patterns
        Returns remaining text after extraction
        """
        logger.info("Performing regex-based extraction...")
        remaining_text = text
        
        # Extract MRP
        mrp_value, remaining_text = self._extract_mrp(remaining_text)
        if mrp_value:
            clean_output["mrp"] = mrp_value
            logger.info(f"Extracted MRP: {mrp_value}")
        
        # Extract Net Quantity
        quantity_value, remaining_text = self._extract_net_quantity(remaining_text)
        if quantity_value:
            clean_output["net_quantity"] = quantity_value
            logger.info(f"Extracted Net Quantity: {quantity_value}")
        
        # Extract Dates
        mfg_date, remaining_text = self._extract_manufacturing_date(remaining_text)
        if mfg_date:
            clean_output["date_of_manufacture"] = mfg_date
            logger.info(f"Extracted Manufacturing Date: {mfg_date}")
        
        best_before_date, remaining_text = self._extract_best_before_date(remaining_text)
        if best_before_date:
            clean_output["best_before_date"] = best_before_date
            logger.info(f"Extracted Best Before Date: {best_before_date}")
        
        # Extract Country of Origin
        country, remaining_text = self._extract_country_of_origin(remaining_text)
        if country:
            clean_output["country_of_origin"] = country
            logger.info(f"Extracted Country: {country}")
        
        # Extract Consumer Care
        consumer_care, remaining_text = self._extract_consumer_care(remaining_text)
        if consumer_care:
            clean_output["consumer_care"] = consumer_care
            logger.info(f"Extracted Consumer Care: {consumer_care}")
        
        # Extract Dimensions
        dimensions, remaining_text = self._extract_dimensions(remaining_text)
        if dimensions:
            clean_output["dimensions"] = dimensions
            logger.info(f"Extracted Dimensions: {dimensions}")
        
        return remaining_text
    
    def _extract_mrp(self, text: str) -> Tuple[Optional[str], str]:
        """Extract MRP using regex patterns"""
        for pattern in self.patterns.MRP_PATTERNS:
            match = pattern.search(text)
            if match:
                price = match.group(1).replace(",", "")
                # Standardize currency format
                formatted_price = f"₹{price}"
                # Remove extracted text
                remaining_text = pattern.sub("", text, count=1)
                return formatted_price, remaining_text
        return None, text
    
    def _extract_net_quantity(self, text: str) -> Tuple[Optional[str], str]:
        """Extract net quantity using regex patterns"""
        for pattern in self.patterns.NET_QUANTITY_PATTERNS:
            match = pattern.search(text)
            if match:
                quantity = match.group(1).strip()
                # Standardize units
                quantity = self._standardize_units(quantity)
                # Remove extracted text
                remaining_text = pattern.sub("", text, count=1)
                return quantity, remaining_text
        return None, text
    
    def _extract_manufacturing_date(self, text: str) -> Tuple[Optional[str], str]:
        """Extract manufacturing date"""
        for pattern in self.patterns.DATE_PATTERNS[:3]:  # First 3 are MFG patterns
            match = pattern.search(text)
            if match:
                date = match.group(1)
                remaining_text = pattern.sub("", text, count=1)
                return date, remaining_text
        return None, text
    
    def _extract_best_before_date(self, text: str) -> Tuple[Optional[str], str]:
        """Extract best before date"""
        for pattern in self.patterns.DATE_PATTERNS[3:5]:  # Best before patterns
            match = pattern.search(text)
            if match:
                date = match.group(1)
                remaining_text = pattern.sub("", text, count=1)
                return date, remaining_text
        return None, text
    
    def _extract_country_of_origin(self, text: str) -> Tuple[Optional[str], str]:
        """Extract country of origin"""
        for pattern in self.patterns.COUNTRY_PATTERNS:
            match = pattern.search(text)
            if match:
                country = match.group(1).strip().title()
                remaining_text = pattern.sub("", text, count=1)
                return country, remaining_text
        return None, text
    
    def _extract_consumer_care(self, text: str) -> Tuple[Optional[str], str]:
        """Extract consumer care information"""
        extracted_parts = []
        remaining_text = text
        
        for pattern in self.patterns.CONSUMER_CARE_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                if match not in extracted_parts:
                    extracted_parts.append(match.strip())
                    remaining_text = pattern.sub("", remaining_text, count=1)
        
        if extracted_parts:
            consumer_care = ", ".join(extracted_parts)
            return consumer_care, remaining_text
        
        return None, text
    
    def _extract_dimensions(self, text: str) -> Tuple[Optional[str], str]:
        """Extract product dimensions"""
        for pattern in self.patterns.DIMENSION_PATTERNS:
            match = pattern.search(text)
            if match:
                dimensions = match.group(1).strip()
                remaining_text = pattern.sub("", text, count=1)
                return dimensions, remaining_text
        return None, text
    
    def _extract_with_nlp(self, remaining_text: str, clean_output: Dict):
        """Extract complex fields using NLP"""
        logger.info("Performing NLP-based extraction...")
        
        if not remaining_text.strip():
            return
        
        # Extract manufacturer details
        if not clean_output.get("manufacturer_details"):
            manufacturer = self._nlp_extract("manufacturer", remaining_text)
            if manufacturer and manufacturer.lower() != "none":
                clean_output["manufacturer_details"] = manufacturer
                logger.info(f"NLP extracted Manufacturer: {manufacturer}")
        
        # Extract importer details
        if not clean_output.get("importer_details"):
            importer = self._nlp_extract("importer", remaining_text)
            if importer and importer.lower() != "none":
                clean_output["importer_details"] = importer
                logger.info(f"NLP extracted Importer: {importer}")
        
        # Extract product category
        if not clean_output.get("category"):
            category = self._nlp_extract("product_category", remaining_text)
            if category and category.lower() != "none":
                clean_output["category"] = category
                logger.info(f"NLP extracted Category: {category}")
        
        # Extract product contents (if not already filled)
        if not clean_output.get("contents"):
            contents = self._nlp_extract("product_contents", remaining_text)
            if contents and contents.lower() != "none":
                clean_output["contents"] = contents
                logger.info(f"NLP extracted Contents: {contents}")
    
    def _nlp_extract(self, field_type: str, text: str) -> Optional[str]:
        """Extract specific field using NLP"""
        if not self.nlp_available:
            return None
        
        try:
            # Gemma chat template construction
            base_prompt = NLP_PROMPTS[field_type].format(text=text[:1500])  # Increased context window
            chat = [
                {"role": "user", "content": base_prompt}
            ]
            
            # Use tokenizer's chat template if available
            if hasattr(self.nlp_pipeline.tokenizer, "apply_chat_template"):
                prompt = self.nlp_pipeline.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
            else:
                # Fallback manual template
                prompt = f"<start_of_turn>user\n{base_prompt}<end_of_turn>\n<start_of_turn>model\n"

            result = self.nlp_pipeline(prompt)
            extracted = result[0]["generated_text"].strip()
            
            # Basic validation
            if len(extracted) > 3 and extracted.lower() not in ["none", "not found", "n/a"]:
                return extracted
            
        except Exception as e:
            logger.warning(f"NLP extraction failed for {field_type}: {e}")
        
        return None
    
    def _standardize_units(self, quantity: str) -> str:
        """Standardize quantity units"""
        for old_unit, new_unit in UNIT_STANDARDIZATION.items():
            quantity = re.sub(rf'\b{old_unit}\b', new_unit, quantity, flags=re.IGNORECASE)
        return quantity
    
    def _final_cleanup(self, clean_output: Dict):
        """Final cleanup and standardization of extracted data"""
        logger.info("Performing final cleanup...")
        
        for key, value in clean_output.items():
            if isinstance(value, str) and value:
                # Remove extra whitespace
                clean_output[key] = re.sub(r'\s+', ' ', value.strip())
                
                # Specific field cleanup
                if key == "mrp" and not value.startswith("₹"):
                    clean_output[key] = f"₹{value}"
                
                elif key in ["manufacturer_details", "importer_details"]:
                    # Ensure proper capitalization for company names
                    clean_output[key] = self._clean_company_name(value)
                
                elif key == "consumer_care":
                    # Clean phone numbers and emails
                    clean_output[key] = self._clean_contact_info(value)
    
    def _clean_company_name(self, company: str) -> str:
        """Clean and format company names"""
        # Remove extra punctuation and normalize spacing
        company = re.sub(r'[,;]{2,}', ',', company)
        company = re.sub(r'\s+', ' ', company)
        
        # Ensure company suffixes are properly formatted
        for suffix in COMPANY_SUFFIXES:
            company = re.sub(rf'\b{suffix.lower()}\b', suffix, company, flags=re.IGNORECASE)
        
        return company.strip()
    
    def _clean_contact_info(self, contact: str) -> str:
        """Clean contact information"""
        # Standardize phone number format
        contact = re.sub(r'(\d{4})\s*(\d{3})\s*(\d{4})', r'\1 \2 \3', contact)
        return contact.strip()
    
    def _copy_simple_fields(self, messy_data: Dict, clean_output: Dict):
        """Copy over simple fields that don't need complex processing"""
        simple_fields = ["country_of_origin", "product_id"]
        
        for field in simple_fields:
            if field in messy_data and messy_data[field] and not clean_output.get(field):
                clean_output[field] = str(messy_data[field]).strip()
    
    def validate_output(self, clean_output: Dict) -> bool:
        """Validate the cleaned output against business rules"""
        try:
            # Validate MRP
            if clean_output.get("mrp"):
                price_match = re.search(r'₹(\d+(?:\.\d{2})?)', clean_output["mrp"])
                if price_match:
                    price_value = float(price_match.group(1))
                    if not (VALIDATION_RULES["mrp"]["min_value"] <= price_value <= VALIDATION_RULES["mrp"]["max_value"]):
                        logger.warning(f"MRP validation failed: {price_value}")
                        return False
            
            # Add more validation rules as needed
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False


# Convenience function for quick usage
def refine_data(messy_data: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Convenience function to refine data without creating a DataRefiner instance
    
    Args:
        messy_data: Dictionary with messy OCR output
        
    Returns:
        Dictionary with clean, structured data
    """
    refiner = DataRefiner()
    return refiner.refine(messy_data)


if __name__ == "__main__":
    # Example usage and testing
    sample_messy_data = {
        "contents": "I TRIMER I LOS DIVISING DARE I PRUSH 3 COMES LISTER...KOLKATA - 700156, WEST BENGAL ₹ 985.00 (INCLUSIVE OF ALL TAXES) CUSTOMER SERVICE EXECUTIVE...1 UNIT 12/2024...",
        "country_of_origin": "India"
    }
    
    refiner = DataRefiner()
    clean_result = refiner.refine(sample_messy_data)
    
    print("--- Cleaned and Final JSON ---")
    for key, value in clean_result.items():
        print(f"{key}: {value}")