"""
OCR Integration Module for Web Crawler - Cloud API Version
Integrates text extraction from product images using cloud ML API
"""

import logging
from typing import Optional, Dict, List, Any
import os

logger = logging.getLogger(__name__)

class OCRIntegrator:
    """Integrates OCR capabilities with web crawler using cloud API"""
    
    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize OCR integrator with cloud API client
        
        Args:
            api_url: Optional ML API URL. If provided, will use cloud API.
                    If None, checks environment variable, then falls back to local OCR.
        """
        # Priority: 1. Parameter, 2. Environment variable, 3. Local fallback
        self.api_url = api_url or os.getenv("ML_API_URL")
        self.use_cloud_api = self.api_url is not None
        self.api_client = None
        
        if self.use_cloud_api:
            try:
                from web.api_client import get_api_client
                self.api_client = get_api_client()
                # Override the API client's URL if we have a specific one
                if api_url:
                    self.api_client.api_url = api_url
                logger.info(f"✅ OCR Integrator using CLOUD API: {self.api_url}")
            except Exception as e:
                logger.warning(f"Failed to initialize cloud API client: {e}")
                self.use_cloud_api = False
        
        if not self.use_cloud_api:
            logger.info("⚠️ Cloud API not available, using LOCAL OCR fallback")
            self._initialize_local_ocr()

    
    def _initialize_local_ocr(self):
        """Initialize local OCR as fallback (original implementation)"""
        import importlib
        
        self.yolo_model = None
        self.ocr_available = False
        self.tesseract_available = False
        
        try:
            # Try YOLO
            try:
                from ultralytics import YOLO
                from pathlib import Path
                repo_root = Path(__file__).resolve().parent.parent
                candidate = repo_root / 'best.pt'
                if candidate.exists():
                    self.yolo_model = YOLO(str(candidate))
                else:
                    self.yolo_model = YOLO('yolov8n.pt')
                logger.info("YOLO model loaded for text detection")
            except Exception as e:
                logger.warning(f"YOLO not available: {e}")
            
            # Try Surya
            try:
                if importlib.util.find_spec('surya') is not None:
                    import surya
                    self.ocr_available = True
                    logger.info("Surya OCR available")
                else:
                    logger.info("Surya package not installed; skipping Surya")
            except Exception as e:
                logger.warning(f"Surya OCR not available: {e}")
            
            # Try Tesseract
            try:
                if importlib.util.find_spec('pytesseract') is not None:
                    import pytesseract
                    self.tesseract_available = True
                    logger.info("Tesseract OCR available as fallback")
            except Exception as e:
                logger.debug(f"Tesseract not available: {e}")
                
        except Exception as e:
            logger.error(f"Error initializing local OCR: {e}")
    
    def extract_text_from_image_url(self, image_url: str) -> Optional[Dict[str, Any]]:
        """Extract text from product image URL"""
        try:
            if not image_url:
                return None
            
            # Use cloud API if available
            if self.use_cloud_api and self.api_client:
                return self._extract_text_cloud(image_url)
            else:
                return self._extract_text_local(image_url)
                
        except Exception as e:
            logger.debug(f"Error extracting text from image: {e}")
            return None
    
    def _extract_text_cloud(self, image_url: str) -> Optional[Dict[str, Any]]:
        """Extract text using cloud API"""
        try:
            import requests
            from io import BytesIO
            
            # Download image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image_bytes = response.content
            
            # Call cloud OCR API
            result = self.api_client.extract_ocr(image_bytes, "image.jpg")
            
            if result and result.get("success"):
                return {
                    'text': result.get('text', ''),
                    'source': 'cloud_ocr',
                    'method': result.get('method', 'cloud_api'),
                    'confidence': result.get('confidence', 0.0)
                }
            else:
                logger.debug(f"Cloud OCR failed: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.debug(f"Cloud OCR extraction failed: {e}")
            return None
    
    def _extract_text_local(self, image_url: str) -> Optional[Dict[str, Any]]:
        """Extract text using local OCR (fallback)"""
        try:
            import requests
            from io import BytesIO
            from PIL import Image
            
            # Download image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            img = Image.open(image_data).convert('RGB')
            
            # Convert to numpy array
            try:
                import numpy as np
                arr = np.array(img)
                try:
                    import cv2
                    image_array = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                except Exception:
                    image_array = arr
            except Exception:
                logger.debug("Failed to obtain numpy array for image")
                return None
            
            # Extract text using local OCR
            extracted_text = self._extract_text_from_array(image_array)
            
            if extracted_text:
                return {
                    'text': extracted_text,
                    'source': 'local_ocr',
                    'method': 'tesseract_fallback'
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Local OCR extraction failed: {e}")
            return None
    
    def _extract_text_from_array(self, image) -> Optional[str]:
        """Extract text from image array using local OCR engines"""
        
        # Try Surya OCR first
        if self.ocr_available:
            try:
                from surya.detection import DetectionPredictor
                from surya.recognition import RecognitionPredictor
                from surya.foundation import FoundationPredictor

                foundation = FoundationPredictor()
                detection = DetectionPredictor()
                recognition = RecognitionPredictor(foundation)

                detections = detection([image])
                texts = []
                for detection_result in detections:
                    if detection_result and hasattr(detection_result, 'bboxes'):
                        for bbox in detection_result.bboxes:
                            try:
                                x1, y1, x2, y2 = [int(c) for c in bbox[:4]]
                                region = image[y1:y2, x1:x2]
                                result = recognition([region])
                                if result and result[0]:
                                    texts.append(result[0].text)
                            except Exception:
                                continue

                return ' '.join(texts) if texts else None
            except Exception as e:
                logger.debug(f"Surya OCR failed: {e}")
        
        # Fallback to Tesseract
        if self.tesseract_available:
            try:
                import pytesseract
                text = pytesseract.image_to_string(image)
                return text if text.strip() else None
            except Exception as e:
                logger.debug(f"Tesseract OCR failed: {e}")
        
        return None
    
    def extract_metadata_from_text(self, text: str) -> Dict[str, Any]:
        """Extract metadata (quantity, price, brand) from OCR text"""
        import re
        
        metadata = {
            'quantity': None,
            'unit': None,
            'price': None,
            'brand': None,
            'mrp': None
        }
        
        try:
            # Extract quantity
            quantity_match = re.search(r'(\d+\.?\d*)\s*(kg|g|ml|l|piece|pcs|box|bottle|pack)', text, re.IGNORECASE)
            if quantity_match:
                metadata['quantity'] = float(quantity_match.group(1))
                metadata['unit'] = quantity_match.group(2).lower()
            
            # Extract price
            price_match = re.search(r'₹\s*(\d+\.?\d*)', text)
            if price_match:
                metadata['price'] = float(price_match.group(1))
            
            # Extract MRP
            mrp_match = re.search(r'MRP.*?₹\s*(\d+\.?\d*)', text, re.IGNORECASE)
            if mrp_match:
                metadata['mrp'] = float(mrp_match.group(1))
        
        except Exception as e:
            logger.debug(f"Error extracting metadata: {e}")
        
        return metadata


def get_ocr_integrator(api_url: Optional[str] = None) -> OCRIntegrator:
    """
    Factory function to get OCR integrator instance
    
    Args:
        api_url: Optional ML API URL for cloud OCR
    """
    return OCRIntegrator(api_url=api_url)
