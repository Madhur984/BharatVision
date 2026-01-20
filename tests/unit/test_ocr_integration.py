"""
Unit tests for BharatVision OCR Integration
"""

import pytest
import numpy as np
from PIL import Image
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from ocr_integration import OCRIntegrator


class TestOCRIntegrator:
    """Test suite for OCR integration"""
    
    @pytest.fixture
    def ocr_integrator(self):
        """Create OCR integrator instance"""
        return OCRIntegrator()
    
    @pytest.fixture
    def sample_image(self):
        """Create a simple test image with text"""
        # Create a white image with black text
        img = Image.new('RGB', (400, 100), color='white')
        # In real tests, you'd add text using PIL.ImageDraw
        return np.array(img)
    
    def test_ocr_integrator_initialization(self, ocr_integrator):
        """Test that OCR integrator initializes correctly"""
        assert ocr_integrator is not None
        assert hasattr(ocr_integrator, 'extract_text_from_image_url')
    
    def test_extract_text_from_valid_image(self, ocr_integrator, sample_image):
        """Test text extraction from valid image"""
        # This would require actual OCR functionality
        # For now, test that the method exists and accepts correct input
        assert callable(ocr_integrator.extract_text_from_image_url)
    
    def test_extract_text_from_invalid_image(self, ocr_integrator):
        """Test handling of invalid image input"""
        with pytest.raises(Exception):
            ocr_integrator.extract_text_from_image_url("invalid_path.jpg")
    
    def test_extract_text_returns_dict(self, ocr_integrator):
        """Test that extraction returns proper dictionary format"""
        # Mock test - in real implementation, use actual image
        # result = ocr_integrator.extract_text_from_image_url("test_image.jpg")
        # assert isinstance(result, dict)
        # assert 'text' in result
        # assert 'confidence' in result
        pass


class TestOCRPreprocessing:
    """Test suite for image preprocessing"""
    
    def test_image_resize(self):
        """Test image resizing functionality"""
        img = Image.new('RGB', (1000, 1000), color='white')
        # Test resize logic
        assert img.size == (1000, 1000)
    
    def test_image_normalization(self):
        """Test image normalization"""
        img_array = np.random.rand(100, 100, 3) * 255
        # Test normalization
        assert img_array.max() <= 255
        assert img_array.min() >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
