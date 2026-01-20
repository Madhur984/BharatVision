"""
Surya OCR Integration - Dedicated module for Surya OCR
Ensures Surya OCR is used for all image uploads
"""

import logging
from typing import Optional, Dict, List, Any, Tuple
from PIL import Image
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class SuryaOCR:
    """Dedicated Surya OCR implementation"""
    
    def __init__(self, device: str = "auto"):
        """
        Initialize Surya OCR
        
        Args:
            device: Device to use ('cuda', 'cpu', or 'auto')
        """
        self.device = self._get_device(device)
        self.models_loaded = False
        self.det_model = None
        self.det_processor = None
        self.rec_model = None
        self.rec_processor = None
        
        logger.info(f"Initializing Surya OCR on device: {self.device}")
        self._load_models()
    
    def _get_device(self, device: str) -> str:
        """Determine the device to use"""
        if device == "auto":
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return device
    
    def _load_models(self):
        """Load Surya OCR models"""
        try:
            from surya.ocr import run_ocr
            from surya.model.detection.model import load_model as load_det_model
            from surya.model.detection.processor import load_processor as load_det_processor
            from surya.model.recognition.model import load_model as load_rec_model
            from surya.model.recognition.processor import load_processor as load_rec_processor
            
            # Load detection model
            logger.info("Loading Surya detection model...")
            self.det_model = load_det_model()
            self.det_processor = load_det_processor()
            
            # Load recognition model
            logger.info("Loading Surya recognition model...")
            self.rec_model = load_rec_model()
            self.rec_processor = load_rec_processor()
            
            self.models_loaded = True
            logger.info("✅ Surya OCR models loaded successfully")
            
        except ImportError as e:
            logger.error(f"❌ Surya OCR not installed. Install with: pip install surya-ocr")
            logger.error(f"Error: {e}")
            self.models_loaded = False
        except Exception as e:
            logger.error(f"❌ Failed to load Surya OCR models: {e}")
            self.models_loaded = False
    
    def extract_text_from_image(self, image_path: str, languages: List[str] = None) -> Dict[str, Any]:
        """
        Extract text from image using Surya OCR
        
        Args:
            image_path: Path to image file or URL
            languages: List of language codes (default: ['en', 'hi'])
        
        Returns:
            Dictionary with extracted text and metadata
        """
        if not self.models_loaded:
            logger.error("Surya OCR models not loaded")
            return {"success": False, "error": "Models not loaded"}
        
        if languages is None:
            languages = ['en', 'hi']  # English and Hindi
        
        try:
            # Load image
            image = self._load_image(image_path)
            if image is None:
                return {"success": False, "error": "Failed to load image"}
            
            # Run OCR
            from surya.ocr import run_ocr
            
            logger.info(f"Running Surya OCR on image (languages: {languages})...")
            predictions = run_ocr(
                [image],
                [languages],
                self.det_model,
                self.det_processor,
                self.rec_model,
                self.rec_processor
            )
            
            if not predictions or len(predictions) == 0:
                return {"success": False, "error": "No text detected"}
            
            # Extract text from predictions
            result = predictions[0]
            extracted_text = []
            bboxes = []
            confidences = []
            
            for text_line in result.text_lines:
                extracted_text.append(text_line.text)
                bboxes.append(text_line.bbox)
                if hasattr(text_line, 'confidence'):
                    confidences.append(text_line.confidence)
            
            full_text = '\n'.join(extracted_text)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(f"✅ Extracted {len(extracted_text)} text lines with avg confidence: {avg_confidence:.2f}")
            
            return {
                "success": True,
                "text": full_text,
                "lines": extracted_text,
                "bboxes": bboxes,
                "confidence": avg_confidence,
                "method": "surya_ocr",
                "languages": languages
            }
            
        except Exception as e:
            logger.error(f"❌ Surya OCR extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _load_image(self, image_source: str) -> Optional[Image.Image]:
        """
        Load image from file path or URL
        
        Args:
            image_source: File path or URL
        
        Returns:
            PIL Image or None
        """
        try:
            # Check if it's a URL
            if image_source.startswith('http://') or image_source.startswith('https://'):
                import requests
                from io import BytesIO
                
                response = requests.get(image_source, timeout=10)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content))
            else:
                # Local file path
                image = Image.open(image_source)
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            logger.error(f"Failed to load image from {image_source}: {e}")
            return None
    
    def extract_text_from_bytes(self, image_bytes: bytes, languages: List[str] = None) -> Dict[str, Any]:
        """
        Extract text from image bytes
        
        Args:
            image_bytes: Image data as bytes
            languages: List of language codes
        
        Returns:
            Dictionary with extracted text and metadata
        """
        if not self.models_loaded:
            return {"success": False, "error": "Models not loaded"}
        
        if languages is None:
            languages = ['en', 'hi']
        
        try:
            from io import BytesIO
            
            # Load image from bytes
            image = Image.open(BytesIO(image_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Run OCR
            from surya.ocr import run_ocr
            
            predictions = run_ocr(
                [image],
                [languages],
                self.det_model,
                self.det_processor,
                self.rec_model,
                self.rec_processor
            )
            
            if not predictions or len(predictions) == 0:
                return {"success": False, "error": "No text detected"}
            
            # Extract text
            result = predictions[0]
            extracted_text = [line.text for line in result.text_lines]
            full_text = '\n'.join(extracted_text)
            
            return {
                "success": True,
                "text": full_text,
                "lines": extracted_text,
                "method": "surya_ocr",
                "languages": languages
            }
            
        except Exception as e:
            logger.error(f"Failed to extract text from bytes: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_surya_ocr_instance = None

def get_surya_ocr(device: str = "auto") -> SuryaOCR:
    """Get singleton Surya OCR instance"""
    global _surya_ocr_instance
    if _surya_ocr_instance is None:
        _surya_ocr_instance = SuryaOCR(device=device)
    return _surya_ocr_instance


# Example usage
if __name__ == "__main__":
    # Initialize Surya OCR
    ocr = get_surya_ocr()
    
    # Extract text from image
    result = ocr.extract_text_from_image("product_image.jpg")
    
    if result["success"]:
        print(f"Extracted text:\n{result['text']}")
        print(f"Confidence: {result.get('confidence', 0):.2f}")
    else:
        print(f"Error: {result['error']}")
