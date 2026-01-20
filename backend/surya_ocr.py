"""
Surya OCR Integration - Official datalab-to/surya implementation
https://github.com/datalab-to/surya

Ensures Surya OCR is used for all image uploads with proper API
"""

import logging
from typing import Optional, Dict, List, Any
from PIL import Image
import io

logger = logging.getLogger(__name__)


class SuryaOCR:
    """Official Surya OCR implementation from datalab-to/surya"""
    
    def __init__(self):
        """Initialize Surya OCR with foundation, detection, and recognition predictors"""
        self.models_loaded = False
        self.foundation_predictor = None
        self.recognition_predictor = None
        self.detection_predictor = None
        
        logger.info("Initializing Surya OCR (datalab-to/surya)...")
        self._load_models()
    
    def _load_models(self):
        """Load Surya OCR models"""
        try:
            from surya.foundation import FoundationPredictor
            from surya.recognition import RecognitionPredictor
            from surya.detection import DetectionPredictor
            
            # Load foundation model
            logger.info("Loading Surya foundation model...")
            self.foundation_predictor = FoundationPredictor()
            
            # Load detection model
            logger.info("Loading Surya detection model...")
            self.detection_predictor = DetectionPredictor()
            
            # Load recognition model
            logger.info("Loading Surya recognition model...")
            self.recognition_predictor = RecognitionPredictor(self.foundation_predictor)
            
            self.models_loaded = True
            logger.info("✅ Surya OCR models loaded successfully")
            
        except ImportError as e:
            logger.error(f"❌ Surya OCR not installed. Install with: pip install surya-ocr")
            logger.error(f"Error: {e}")
            self.models_loaded = False
        except Exception as e:
            logger.error(f"❌ Failed to load Surya OCR models: {e}")
            self.models_loaded = False
    
    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from image using Surya OCR
        
        Args:
            image_path: Path to image file or URL
        
        Returns:
            Dictionary with extracted text and metadata
        """
        if not self.models_loaded:
            return {"success": False, "error": "Surya OCR models not loaded"}
        
        try:
            # Load image
            image = self._load_image(image_path)
            if image is None:
                return {"success": False, "error": "Failed to load image"}
            
            # Run OCR using official Surya API
            logger.info(f"Running Surya OCR on image...")
            predictions = self.recognition_predictor(
                [image], 
                det_predictor=self.detection_predictor
            )
            
            if not predictions or len(predictions) == 0:
                return {"success": False, "error": "No text detected"}
            
            # Extract text from predictions
            result = predictions[0]
            extracted_lines = []
            all_text = []
            confidences = []
            
            # Process text lines
            for text_line in result.text_lines:
                line_text = text_line.text
                all_text.append(line_text)
                extracted_lines.append({
                    "text": line_text,
                    "confidence": text_line.confidence,
                    "bbox": text_line.bbox,
                    "polygon": text_line.polygon
                })
                confidences.append(text_line.confidence)
            
            full_text = '\n'.join(all_text)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(f"✅ Surya OCR extracted {len(extracted_lines)} text lines (avg confidence: {avg_confidence:.2f})")
            
            return {
                "success": True,
                "text": full_text,
                "lines": extracted_lines,
                "confidence": avg_confidence,
                "method": "surya_ocr",
                "line_count": len(extracted_lines)
            }
            
        except Exception as e:
            logger.error(f"❌ Surya OCR extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_text_from_pil_image(self, pil_image: Image.Image) -> Dict[str, Any]:
        """
        Extract text from PIL Image using Surya OCR
        
        Args:
            pil_image: PIL Image object
        
        Returns:
            Dictionary with extracted text and metadata
        """
        if not self.models_loaded:
            return {"success": False, "error": "Surya OCR models not loaded"}
        
        try:
            # Ensure RGB
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Run OCR using official Surya API
            logger.info(f"Running Surya OCR on PIL image...")
            predictions = self.recognition_predictor(
                [pil_image], 
                det_predictor=self.detection_predictor
            )
            
            if not predictions or len(predictions) == 0:
                return {"success": False, "error": "No text detected"}
            
            # Extract text from predictions
            result = predictions[0]
            extracted_lines = []
            all_text = []
            confidences = []
            
            # Process text lines
            for text_line in result.text_lines:
                line_text = text_line.text
                all_text.append(line_text)
                extracted_lines.append({
                    "text": line_text,
                    "confidence": text_line.confidence,
                    "bbox": text_line.bbox,
                    "polygon": text_line.polygon
                })
                confidences.append(text_line.confidence)
            
            full_text = '\n'.join(all_text)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(f"✅ Surya OCR extracted {len(extracted_lines)} text lines (avg confidence: {avg_confidence:.2f})")
            
            return {
                "success": True,
                "text": full_text,
                "lines": extracted_lines,
                "confidence": avg_confidence,
                "method": "surya_ocr",
                "line_count": len(extracted_lines)
            }
            
        except Exception as e:
            logger.error(f"❌ Surya OCR extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_text_from_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text from image bytes
        
        Args:
            image_bytes: Image data as bytes
        
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            return self.extract_text_from_pil_image(image)
            
        except Exception as e:
            logger.error(f"Failed to extract text from bytes: {e}")
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
                
                response = requests.get(image_source, timeout=10)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content))
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


# Singleton instance
_surya_ocr_instance = None

def get_surya_ocr() -> SuryaOCR:
    """Get singleton Surya OCR instance"""
    global _surya_ocr_instance
    if _surya_ocr_instance is None:
        _surya_ocr_instance = SuryaOCR()
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
        print(f"Lines: {result.get('line_count', 0)}")
    else:
        print(f"Error: {result['error']}")
