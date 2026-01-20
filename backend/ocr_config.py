"""
OCR Configuration for BharatVision

This module configures OCR processing based on the data source:
- E-commerce platforms: Skip image OCR (use scraped data)
- Image uploads: Use Surya OCR
- Batch processing: Use Surya OCR
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class OCRConfig:
    """OCR configuration manager"""
    
    # E-commerce platforms that don't need image OCR
    ECOMMERCE_PLATFORMS = ['amazon', 'flipkart', 'jiomart', 'myntra', 'snapdeal']
    
    # OCR engine preferences
    PRIMARY_OCR = 'surya'  # Use Surya OCR for image uploads and batch processing
    FALLBACK_OCR = 'tesseract'  # Fallback if Surya fails
    
    @staticmethod
    def should_skip_ocr(source: str) -> bool:
        """
        Determine if OCR should be skipped based on data source
        
        Args:
            source: Data source (e.g., 'amazon', 'upload', 'batch')
        
        Returns:
            True if OCR should be skipped, False otherwise
        """
        source_lower = source.lower()
        
        # Skip OCR for e-commerce platforms (use scraped data)
        if any(platform in source_lower for platform in OCRConfig.ECOMMERCE_PLATFORMS):
            logger.info(f"Skipping OCR for e-commerce platform: {source}")
            return True
        
        return False
    
    @staticmethod
    def get_ocr_engine(source: str) -> str:
        """
        Get the appropriate OCR engine for the data source
        
        Args:
            source: Data source (e.g., 'upload', 'batch', 'camera')
        
        Returns:
            OCR engine name ('surya' or 'tesseract')
        """
        if OCRConfig.should_skip_ocr(source):
            return 'none'
        
        # Use Surya OCR for image uploads and batch processing
        source_lower = source.lower()
        if any(keyword in source_lower for keyword in ['upload', 'batch', 'image', 'camera']):
            logger.info(f"Using Surya OCR for: {source}")
            return OCRConfig.PRIMARY_OCR
        
        # Default to Surya
        return OCRConfig.PRIMARY_OCR
    
    @staticmethod
    def get_ocr_config(source: str) -> Dict[str, Any]:
        """
        Get complete OCR configuration for a data source
        
        Args:
            source: Data source
        
        Returns:
            Configuration dictionary
        """
        skip_ocr = OCRConfig.should_skip_ocr(source)
        engine = OCRConfig.get_ocr_engine(source)
        
        config = {
            'skip_ocr': skip_ocr,
            'engine': engine,
            'use_surya': engine == 'surya',
            'use_tesseract': engine == 'tesseract',
            'lang_codes': ['en', 'hi'],  # English and Hindi
            'device': os.getenv('DEVICE', 'auto'),
        }
        
        logger.info(f"OCR config for '{source}': {config}")
        return config


def process_with_ocr(image_path: str, source: str = 'upload') -> Optional[Dict[str, Any]]:
    """
    Process image with appropriate OCR configuration
    
    Args:
        image_path: Path to image file
        source: Data source (e.g., 'upload', 'batch', 'amazon')
    
    Returns:
        OCR results or None if OCR is skipped
    """
    config = OCRConfig.get_ocr_config(source)
    
    if config['skip_ocr']:
        logger.info(f"OCR skipped for source: {source}")
        return None
    
    # Import OCR integrator
    try:
        from backend.ocr_integration import OCRIntegrator
        
        ocr = OCRIntegrator()
        
        if config['use_surya']:
            logger.info(f"Processing {image_path} with Surya OCR")
            result = ocr.extract_text_from_image_url(image_path)
        else:
            logger.info(f"Processing {image_path} with Tesseract OCR")
            result = ocr.extract_text_from_image_url(image_path)
        
        return result
        
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        return None


# Example usage
if __name__ == "__main__":
    # E-commerce platform - skip OCR
    config1 = OCRConfig.get_ocr_config('amazon')
    print(f"Amazon config: {config1}")
    # Output: {'skip_ocr': True, 'engine': 'none', ...}
    
    # Image upload - use Surya OCR
    config2 = OCRConfig.get_ocr_config('upload')
    print(f"Upload config: {config2}")
    # Output: {'skip_ocr': False, 'engine': 'surya', 'use_surya': True, ...}
    
    # Batch processing - use Surya OCR
    config3 = OCRConfig.get_ocr_config('batch')
    print(f"Batch config: {config3}")
    # Output: {'skip_ocr': False, 'engine': 'surya', 'use_surya': True, ...}
