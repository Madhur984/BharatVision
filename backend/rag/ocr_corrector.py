"""
OCR Error Corrector using RAG
Corrects OCR errors using knowledge base and context
"""

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class OCRCorrector:
    """
    Correct OCR errors using RAG and knowledge base
    Government-grade accuracy with context-aware corrections
    """
    
    def __init__(self, corrections_db: Dict, vector_store=None):
        """
        Initialize OCR corrector
        
        Args:
            corrections_db: OCR corrections database
            vector_store: Optional VectorStore for semantic verification
        """
        self.corrections_db = corrections_db
        self.vector_store = vector_store
        
        # Extract correction mappings
        self.field_corrections = corrections_db.get('common_ocr_errors', {}).get('field_names', {})
        self.number_corrections = corrections_db.get('common_ocr_errors', {}).get('numbers', {})
        self.currency_corrections = corrections_db.get('common_ocr_errors', {}).get('currency', {})
        self.unit_corrections = corrections_db.get('common_ocr_errors', {}).get('units', {})
        self.context_corrections = corrections_db.get('context_corrections', [])
        
        logger.info("OCRCorrector initialized with correction database")
        
    def correct_text(self, ocr_text: str, context: Optional[str] = None) -> Tuple[str, List[Dict]]:
        """
        Correct OCR errors in extracted text
        
        Args:
            ocr_text: Raw OCR text
            context: Optional context for better corrections
            
        Returns:
            Tuple of (corrected_text, corrections_applied)
        """
        corrected = ocr_text
        corrections_applied = []
        
        # Step 1: Apply direct field name corrections
        corrected, field_corrections = self._apply_field_corrections(corrected)
        corrections_applied.extend(field_corrections)
        
        # Step 2: Apply context-based corrections
        if context:
            corrected, context_corrections = self._apply_context_corrections(corrected, context)
            corrections_applied.extend(context_corrections)
        
        # Step 3: Apply number corrections
        corrected, num_corrections = self._apply_number_corrections(corrected)
        corrections_applied.extend(num_corrections)
        
        # Step 4: Apply currency corrections
        corrected, curr_corrections = self._apply_currency_corrections(corrected)
        corrections_applied.extend(curr_corrections)
        
        # Step 5: Apply unit corrections
        corrected, unit_corrections = self._apply_unit_corrections(corrected)
        corrections_applied.extend(unit_corrections)
        
        # Step 6: Semantic verification with RAG (if available)
        if self.vector_store:
            corrected, rag_corrections = self._verify_with_rag(corrected, ocr_text)
            corrections_applied.extend(rag_corrections)
        
        logger.info(f"Applied {len(corrections_applied)} corrections to OCR text")
        
        return corrected, corrections_applied
    
    def _apply_field_corrections(self, text: str) -> Tuple[str, List[Dict]]:
        """Apply direct field name corrections"""
        corrections = []
        corrected = text
        
        for wrong, correct in self.field_corrections.items():
            if wrong in corrected:
                corrected = corrected.replace(wrong, correct)
                corrections.append({
                    'type': 'field_name',
                    'wrong': wrong,
                    'correct': correct,
                    'confidence': 0.95
                })
        
        return corrected, corrections
    
    def _apply_context_corrections(self, text: str, context: str) -> Tuple[str, List[Dict]]:
        """Apply context-aware corrections"""
        corrections = []
        corrected = text
        
        for correction in self.context_corrections:
            pattern = correction['pattern']
            context_keywords = correction['context'].split('|')
            replacement = correction['correction']
            confidence = correction.get('confidence', 0.9)
            
            # Check if any context keyword exists in the text
            has_context = any(keyword.lower() in text.lower() for keyword in context_keywords)
            
            if has_context:
                # Apply correction
                matches = re.finditer(pattern, corrected, re.IGNORECASE)
                for match in matches:
                    original = match.group(0)
                    corrected = corrected.replace(original, replacement)
                    corrections.append({
                        'type': 'context_based',
                        'wrong': original,
                        'correct': replacement,
                        'context': correction['context'],
                        'confidence': confidence
                    })
        
        return corrected, corrections
    
    def _apply_number_corrections(self, text: str) -> Tuple[str, List[Dict]]:
        """Apply number corrections (O->0, l->1, etc.)"""
        corrections = []
        corrected = text
        
        # Only correct numbers in numeric contexts (near digits or currency)
        for wrong, correct in self.number_corrections.items():
            # Pattern: wrong character surrounded by digits or currency
            pattern = f'([₹Rs.\\d])({re.escape(wrong)})([\\d])'
            matches = re.finditer(pattern, corrected)
            
            for match in matches:
                original = match.group(2)
                corrected = corrected.replace(match.group(0), f"{match.group(1)}{correct}{match.group(3)}")
                corrections.append({
                    'type': 'number',
                    'wrong': original,
                    'correct': correct,
                    'confidence': 0.85
                })
        
        return corrected, corrections
    
    def _apply_currency_corrections(self, text: str) -> Tuple[str, List[Dict]]:
        """Apply currency symbol corrections"""
        corrections = []
        corrected = text
        
        for wrong, correct in self.currency_corrections.items():
            if wrong in corrected:
                corrected = corrected.replace(wrong, correct)
                corrections.append({
                    'type': 'currency',
                    'wrong': wrong,
                    'correct': correct,
                    'confidence': 0.9
                })
        
        return corrected, corrections
    
    def _apply_unit_corrections(self, text: str) -> Tuple[str, List[Dict]]:
        """Apply unit standardization"""
        corrections = []
        corrected = text
        
        for wrong, correct in self.unit_corrections.items():
            # Match unit after numbers
            pattern = f'(\\d+\\.?\\d*)\\s*{re.escape(wrong)}\\b'
            matches = re.finditer(pattern, corrected, re.IGNORECASE)
            
            for match in matches:
                original = match.group(0)
                replacement = f"{match.group(1)} {correct}"
                corrected = corrected.replace(original, replacement)
                corrections.append({
                    'type': 'unit',
                    'wrong': wrong,
                    'correct': correct,
                    'confidence': 0.9
                })
        
        return corrected, corrections
    
    def _verify_with_rag(self, corrected_text: str, original_text: str) -> Tuple[str, List[Dict]]:
        """Verify corrections using RAG semantic search"""
        corrections = []
        
        try:
            # Query: "Verify if this text is correct for Legal Metrology label"
            query = f"Is this correct for product label: {corrected_text[:100]}"
            results = self.vector_store.search(query, top_k=3, min_score=1.0)
            
            if results and results[0][2] < 0.5:  # High similarity (low distance)
                # High confidence - text is likely correct
                corrections.append({
                    'type': 'rag_verification',
                    'status': 'verified',
                    'confidence': 1.0 - results[0][2],
                    'matched_example': results[0][0][:50]
                })
            elif not results or results[0][2] > 2.0:  # Low similarity
                # Low confidence - might need manual review
                logger.warning(f"Low RAG confidence for: {corrected_text[:50]}...")
                corrections.append({
                    'type': 'rag_verification',
                    'status': 'low_confidence',
                    'confidence': 0.5,
                    'note': 'Manual review recommended'
                })
        
        except Exception as e:
            logger.error(f"RAG verification failed: {e}")
        
        return corrected_text, corrections
    
    def get_correction_stats(self, corrections: List[Dict]) -> Dict:
        """Get statistics about applied corrections"""
        stats = {
            'total_corrections': len(corrections),
            'by_type': {},
            'avg_confidence': 0.0
        }
        
        for correction in corrections:
            corr_type = correction['type']
            stats['by_type'][corr_type] = stats['by_type'].get(corr_type, 0) + 1
        
        if corrections:
            stats['avg_confidence'] = sum(c.get('confidence', 0) for c in corrections) / len(corrections)
        
        return stats


# Example usage
if __name__ == "__main__":
    # Sample corrections database
    corrections_db = {
        'common_ocr_errors': {
            'field_names': {
                'M8P': 'MRP',
                'MBP': 'MRP'
            },
            'numbers': {
                'O': '0',
                'l': '1'
            }
        },
        'context_corrections': [
            {
                'pattern': 'M[8B]P',
                'context': 'price|retail',
                'correction': 'MRP',
                'confidence': 0.95
            }
        ]
    }
    
    # Create corrector
    corrector = OCRCorrector(corrections_db)
    
    # Test correction
    ocr_text = "M8P: Rs. 5O.OO"
    corrected, corrections = corrector.correct_text(ocr_text, context="price")
    
    print(f"Original: {ocr_text}")
    print(f"Corrected: {corrected}")
    print(f"Corrections: {corrections}")
