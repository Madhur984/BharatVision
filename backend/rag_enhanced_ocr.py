"""
RAG-Enhanced Surya OCR
Combines Surya OCR with RAG for government-grade accuracy
"""

import logging
from typing import Dict, Optional
from PIL import Image

logger = logging.getLogger(__name__)

class RAGEnhancedOCR:
    """
    Surya OCR enhanced with RAG for maximum accuracy
    Government-grade Legal Metrology compliance
    """
    
    def __init__(self):
        """Initialize RAG-enhanced OCR"""
        self.surya_ocr = None
        self.rag_manager = None
        self.initialized = False
        
        logger.info("RAGEnhancedOCR initialized")
    
    def _lazy_init(self):
        """Lazy initialization of components"""
        if self.initialized:
            return
        
        try:
            # Import Surya OCR
            from backend.surya_ocr import get_surya_ocr
            self.surya_ocr = get_surya_ocr()
            logger.info("✅ Surya OCR loaded")
            
            # Import RAG Manager
            from backend.rag import RAGManager
            self.rag_manager = RAGManager()
            
            # Try to load existing index
            try:
                self.rag_manager.initialize(force_rebuild=False)
                logger.info("✅ RAG system loaded from existing index")
            except:
                logger.warning("RAG index not found, running without RAG enhancement")
                self.rag_manager = None
            
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG-enhanced OCR: {e}")
            self.initialized = True  # Mark as initialized to avoid retry
    
    def process_image(
        self, 
        image: Image.Image,
        use_rag: bool = True
    ) -> Dict:
        """
        Process image with RAG-enhanced OCR
        
        Args:
            image: PIL Image
            use_rag: Whether to use RAG enhancement
            
        Returns:
            Dictionary with OCR results and RAG enhancements
        """
        self._lazy_init()
        
        result = {
            'success': False,
            'text': '',
            'confidence': 0.0,
            'rag_enhanced': False,
            'corrections': [],
            'extracted_fields': {},
            'error': None
        }
        
        try:
            # Step 1: Run Surya OCR
            logger.info("Running Surya OCR...")
            ocr_result = self.surya_ocr.extract_text_from_image(image)
            
            if not ocr_result.get('success'):
                result['error'] = ocr_result.get('error', 'OCR failed')
                return result
            
            raw_text = ocr_result.get('text', '')
            result['text'] = raw_text
            result['confidence'] = ocr_result.get('confidence', 0.0)
            result['success'] = True
            
            # Step 2: Apply RAG enhancement if available and enabled
            if use_rag and self.rag_manager:
                logger.info("Applying RAG enhancement...")
                try:
                    rag_result = self.rag_manager.process_ocr_text(
                        raw_text,
                        context="product label"
                    )
                    
                    # Update result with RAG enhancements
                    result['rag_enhanced'] = True
                    result['text'] = rag_result['corrected_text']
                    result['corrections'] = rag_result['corrections']['applied']
                    result['extracted_fields'] = rag_result['extracted_fields']
                    result['rag_summary'] = rag_result['summary']
                    
                    logger.info(f"✅ RAG applied: {rag_result['summary']['total_corrections']} corrections")
                    
                except Exception as e:
                    logger.error(f"RAG enhancement failed: {e}")
                    # Continue with raw OCR text
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG-enhanced OCR: {e}")
            result['error'] = str(e)
            return result
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        self._lazy_init()
        
        stats = {
            'surya_ocr_available': self.surya_ocr is not None,
            'rag_available': self.rag_manager is not None
        }
        
        if self.rag_manager:
            stats['rag_stats'] = self.rag_manager.get_stats()
        
        return stats


# Singleton instance
_rag_ocr_instance = None

def get_rag_enhanced_ocr() -> RAGEnhancedOCR:
    """Get singleton RAG-enhanced OCR instance"""
    global _rag_ocr_instance
    
    if _rag_ocr_instance is None:
        _rag_ocr_instance = RAGEnhancedOCR()
    
    return _rag_ocr_instance


# Example usage
if __name__ == "__main__":
    from PIL import Image
    
    # Initialize
    ocr = get_rag_enhanced_ocr()
    
    # Process image
    image = Image.new('RGB', (100, 100), color='white')
    result = ocr.process_image(image, use_rag=True)
    
    print(f"Success: {result['success']}")
    print(f"RAG Enhanced: {result['rag_enhanced']}")
    print(f"Text: {result['text']}")
    print(f"Corrections: {len(result['corrections'])}")
