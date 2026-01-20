"""
Semantic Field Extractor using RAG
Intelligently extracts fields from OCR text using semantic search
"""

import re
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SemanticFieldExtractor:
    """
    Extract fields from OCR text using RAG semantic search
    Combines regex patterns with semantic understanding
    """
    
    def __init__(self, patterns_db: Dict, vector_store=None):
        """
        Initialize field extractor
        
        Args:
            patterns_db: Field patterns database
            vector_store: Optional VectorStore for semantic search
        """
        self.patterns_db = patterns_db
        self.vector_store = vector_store
        
        logger.info("SemanticFieldExtractor initialized")
        
    def extract_all_fields(self, text: str) -> Dict[str, any]:
        """
        Extract all fields from text
        
        Args:
            text: OCR text to extract from
            
        Returns:
            Dictionary of extracted fields
        """
        fields = {}
        
        for field_name in self.patterns_db.keys():
            value, confidence = self.extract_field(text, field_name)
            fields[field_name] = {
                'value': value,
                'confidence': confidence,
                'found': value is not None
            }
        
        logger.info(f"Extracted {sum(1 for f in fields.values() if f['found'])} fields from text")
        
        return fields
    
    def extract_field(self, text: str, field_name: str) -> Tuple[Optional[str], float]:
        """
        Extract a specific field from text
        
        Args:
            text: OCR text
            field_name: Name of field to extract
            
        Returns:
            Tuple of (extracted_value, confidence_score)
        """
        if field_name not in self.patterns_db:
            logger.warning(f"Unknown field: {field_name}")
            return None, 0.0
        
        pattern_data = self.patterns_db[field_name]
        
        # Method 1: Try regex patterns first (fast, high precision)
        value, confidence = self._extract_with_regex(text, pattern_data)
        if value and confidence > 0.8:
            logger.debug(f"Extracted {field_name} with regex: {value}")
            return value, confidence
        
        # Method 2: Try keyword-based extraction
        if not value:
            value, confidence = self._extract_with_keywords(text, pattern_data)
            if value and confidence > 0.7:
                logger.debug(f"Extracted {field_name} with keywords: {value}")
                return value, confidence
        
        # Method 3: Use RAG semantic search (slower, better recall)
        if self.vector_store and not value:
            value, confidence = self._extract_with_rag(text, field_name, pattern_data)
            if value:
                logger.debug(f"Extracted {field_name} with RAG: {value}")
                return value, confidence
        
        logger.debug(f"Could not extract {field_name}")
        return None, 0.0
    
    def _extract_with_regex(self, text: str, pattern_data: Dict) -> Tuple[Optional[str], float]:
        """Extract using regex patterns"""
        regex_patterns = pattern_data.get('regex_patterns', [])
        
        for pattern in regex_patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    # Extract the captured group or full match
                    value = match.group(1) if match.groups() else match.group(0)
                    return value.strip(), 0.9
            except Exception as e:
                logger.error(f"Regex error: {e}")
        
        return None, 0.0
    
    def _extract_with_keywords(self, text: str, pattern_data: Dict) -> Tuple[Optional[str], float]:
        """Extract using keyword matching"""
        keywords = pattern_data.get('keywords', [])
        
        for keyword in keywords:
            # Find keyword in text
            pattern = f"{re.escape(keyword)}[:\\s]*([^\\n]{{5,100}})"
            match = re.search(pattern, text, re.IGNORECASE)
            
            if match:
                value = match.group(1).strip()
                # Clean up the value
                value = re.sub(r'[\\r\\n]+', ' ', value)
                return value, 0.75
        
        return None, 0.0
    
    def _extract_with_rag(self, text: str, field_name: str, pattern_data: Dict) -> Tuple[Optional[str], float]:
        """Extract using RAG semantic search"""
        try:
            # Use semantic queries
            semantic_queries = pattern_data.get('semantic_queries', [])
            
            if not semantic_queries:
                return None, 0.0
            
            # Try each semantic query
            for query in semantic_queries:
                # Search in vector store
                results = self.vector_store.search(query, top_k=5, min_score=2.0)
                
                if results:
                    # Check if any result matches the field
                    for doc, metadata, score in results:
                        if metadata.get('field') == field_name and score < 1.0:
                            # Found relevant example, try to extract similar pattern from text
                            value = self._extract_similar_pattern(text, doc, field_name)
                            if value:
                                confidence = 1.0 - min(score, 0.9)
                                return value, confidence
            
        except Exception as e:
            logger.error(f"RAG extraction failed: {e}")
        
        return None, 0.0
    
    def _extract_similar_pattern(self, text: str, example: str, field_name: str) -> Optional[str]:
        """Extract value using similar pattern from example"""
        # This is a simplified version - could be enhanced with NLP
        
        # For MRP: look for price patterns
        if field_name == 'mrp':
            price_pattern = r'[₹Rs.]+\s*[\d,]+\.?\d*'
            match = re.search(price_pattern, text)
            if match:
                return match.group(0)
        
        # For manufacturer: look for company names and addresses
        elif field_name == 'manufacturer_details':
            # Look for patterns like "by Company Name, Address"
            pattern = r'(?:by|By)[:\\s]+([^\\n]{20,200})'
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # For net quantity: look for quantity patterns
        elif field_name == 'net_quantity':
            qty_pattern = r'\\d+\\.?\\d*\\s*(?:kg|g|gm|ml|l|ltr)'
            match = re.search(qty_pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def validate_extracted_field(self, field_name: str, value: str) -> Tuple[bool, List[str]]:
        """
        Validate extracted field value
        
        Args:
            field_name: Name of the field
            value: Extracted value
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if field_name not in self.patterns_db:
            return False, [f"Unknown field: {field_name}"]
        
        pattern_data = self.patterns_db[field_name]
        validation = pattern_data.get('validation', {})
        errors = []
        
        # Check minimum length
        min_length = validation.get('min_length')
        if min_length and len(value) < min_length:
            errors.append(f"Value too short (min: {min_length})")
        
        # Check maximum length
        max_length = validation.get('max_length')
        if max_length and len(value) > max_length:
            errors.append(f"Value too long (max: {max_length})")
        
        # Check numeric value range
        if 'min_value' in validation or 'max_value' in validation:
            try:
                # Extract numeric value
                num_match = re.search(r'[\d,]+\.?\d*', value)
                if num_match:
                    num_value = float(num_match.group(0).replace(',', ''))
                    
                    if 'min_value' in validation and num_value < validation['min_value']:
                        errors.append(f"Value too low (min: {validation['min_value']})")
                    
                    if 'max_value' in validation and num_value > validation['max_value']:
                        errors.append(f"Value too high (max: {validation['max_value']})")
            except ValueError:
                errors.append("Invalid numeric value")
        
        # Check required patterns
        if validation.get('must_have_decimal') and '.' not in value:
            errors.append("Missing decimal point")
        
        if validation.get('must_mention_taxes') and 'incl' not in value.lower():
            errors.append("Missing tax information")
        
        is_valid = len(errors) == 0
        return is_valid, errors


# Example usage
if __name__ == "__main__":
    # Sample patterns database
    patterns_db = {
        'mrp': {
            'regex_patterns': [
                r'(?:MRP|M\\.R\\.P)[:\\s]*[₹Rs.]*\\s*([\\d,]+(?:\\.\\d{2})?)'
            ],
            'keywords': ['MRP', 'Price'],
            'semantic_queries': ['What is the price?'],
            'validation': {
                'min_value': 1.0,
                'must_have_decimal': True
            }
        }
    }
    
    # Create extractor
    extractor = SemanticFieldExtractor(patterns_db)
    
    # Test extraction
    text = "Product Label\\nMRP: ₹50.00 (Incl. of all taxes)"
    value, confidence = extractor.extract_field(text, 'mrp')
    
    print(f"Extracted MRP: {value}")
    print(f"Confidence: {confidence:.2f}")
    
    # Validate
    is_valid, errors = extractor.validate_extracted_field('mrp', value)
    print(f"Valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
