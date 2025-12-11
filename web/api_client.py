"""
API Client for BharatVision Cloud ML API

This module provides a client wrapper for calling the cloud-hosted ML API
from the Streamlit frontend. It handles retries, error responses, and
supports both local and cloud API modes.
"""

import os
import requests
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class MLAPIClient:
    """Client for interacting with the BharatVision ML API"""
    
    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize the API client
        
        Args:
            api_url: Base URL of the ML API. If not provided, reads from ML_API_URL env var.
                    Falls back to localhost for development.
        """
        self.api_url = api_url or os.getenv(
            "ML_API_URL", 
            "http://localhost:8000"
        )
        self.timeout = int(os.getenv("API_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("API_MAX_RETRIES", "3"))
        
        logger.info(f"Initialized MLAPIClient with URL: {self.api_url}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the API is healthy and available
        
        Returns:
            Dict with health status information
        """
        try:
            response = requests.get(
                f"{self.api_url}/health",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def ask_ai(
        self, 
        question: str, 
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Ask the AI a question about Legal Metrology
        
        Args:
            question: The question to ask
            context: Optional context for the question
            
        Returns:
            Dict with answer and metadata
        """
        url = f"{self.api_url}/api/ai/ask"
        payload = {
            "question": question,
            "context": context
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Calling AI API (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"AI API call successful")
                return result
                
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": "Request timed out. Please try again.",
                        "answer": "The AI service is taking too long to respond. Please try again in a moment."
                    }
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "answer": "Unable to connect to the AI service. Please check your connection and try again."
                    }
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "answer": "An unexpected error occurred. Please try again."
                }
        
        return {
            "success": False,
            "error": "Max retries exceeded",
            "answer": "Unable to get a response after multiple attempts. Please try again later."
        }
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics (mock endpoint)"""
        try:
            response = requests.get(
                f"{self.api_url}/api/dashboard/stats",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {e}")
            return {
                "total_scans": 0,
                "compliance_rate": 0,
                "violations_flagged": 0,
                "devices_online": 0,
                "recent_scans": []
            }
    
    def search_products(self, query: str = "") -> Dict[str, Any]:
        """Search products (mock endpoint)"""
        try:
            response = requests.get(
                f"{self.api_url}/api/search/products",
                params={"q": query},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to search products: {e}")
            return {
                "total": 0,
                "results": []
            }
    
    def process_upload(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Process an uploaded image (mock endpoint)"""
        try:
            files = {"file": (filename, file_bytes, "image/jpeg")}
            response = requests.post(
                f"{self.api_url}/api/upload/process",
                files=files,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to process upload: {e}")
            return {
                "success": False,
                "error": str(e),
                "extracted_text": "",
                "confidence": 0
            }
    
    def extract_ocr(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract text from image using cloud OCR
        
        Args:
            file_bytes: Image file bytes
            filename: Name of the file
            
        Returns:
            Dict with extracted text and metadata
        """
        try:
            files = {"file": (filename, file_bytes, "image/jpeg")}
            response = requests.post(
                f"{self.api_url}/api/ocr/extract",
                files=files,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {
                "success": False,
                "text": "",
                "error": str(e)
            }
    
    def detect_objects(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Detect objects in image using cloud detection
        
        Args:
            file_bytes: Image file bytes
            filename: Name of the file
            
        Returns:
            Dict with detected objects
        """
        try:
            files = {"file": (filename, file_bytes, "image/jpeg")}
            response = requests.post(
                f"{self.api_url}/api/detect/objects",
                files=files,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return {
                "success": False,
                "detections": [],
                "error": str(e)
            }
    
    def check_compliance(self, text: str, product_data: Dict = None) -> Dict[str, Any]:
        """
        Check Legal Metrology compliance
        
        Args:
            text: Extracted text to validate
            product_data: Optional additional product data
            
        Returns:
            Dict with compliance results
        """
        try:
            payload = {
                "text": text,
                "product_data": product_data or {}
            }
            response = requests.post(
                f"{self.api_url}/api/compliance/check",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            return {
                "success": False,
                "compliant": False,
                "error": str(e)
            }
    
    def process_image_full(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Full pipeline: OCR + Compliance checking
        
        Args:
            file_bytes: Image file bytes
            filename: Name of the file
            
        Returns:
            Dict with OCR results and compliance status
        """
        try:
            files = {"file": (filename, file_bytes, "image/jpeg")}
            response = requests.post(
                f"{self.api_url}/api/process/image",
                files=files,
                timeout=self.timeout * 2  # Double timeout for full pipeline
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Full image processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }



# Global client instance
_client = None

def get_api_client() -> MLAPIClient:
    """Get or create the global API client instance"""
    global _client
    if _client is None:
        _client = MLAPIClient()
    return _client
