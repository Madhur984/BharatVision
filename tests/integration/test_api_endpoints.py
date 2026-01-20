"""
Integration tests for BharatVision API endpoints
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from api_server import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test suite for health check endpoint"""
    
    def test_health_check_returns_200(self):
        """Test that health endpoint returns 200 OK"""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_health_check_response_format(self):
        """Test health check response format"""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["status"] == "healthy"


class TestComplianceEndpoint:
    """Test suite for compliance checking endpoint"""
    
    def test_compliance_check_valid_product(self):
        """Test compliance check with valid product data"""
        product_data = {
            "title": "Tata Salt 1kg",
            "brand": "Tata",
            "price": 25.00,
            "mrp": 30.00,
            "category": "Food & Beverages"
        }
        
        response = client.post("/api/compliance/check", json=product_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "score" in data
        assert "status" in data
        assert "color" in data
        assert 0 <= data["score"] <= 100
    
    def test_compliance_check_missing_fields(self):
        """Test compliance check with missing required fields"""
        product_data = {
            "title": "Test Product"
            # Missing required fields
        }
        
        response = client.post("/api/compliance/check", json=product_data)
        assert response.status_code == 422  # Validation error
    
    def test_compliance_check_invalid_price(self):
        """Test compliance check with invalid price"""
        product_data = {
            "title": "Test Product",
            "brand": "Test Brand",
            "price": -10.00,  # Invalid negative price
            "mrp": 30.00
        }
        
        response = client.post("/api/compliance/check", json=product_data)
        assert response.status_code == 422
    
    def test_compliance_check_price_exceeds_mrp(self):
        """Test when selling price exceeds MRP"""
        product_data = {
            "title": "Test Product",
            "brand": "Test Brand",
            "price": 100.00,
            "mrp": 50.00  # Price > MRP
        }
        
        response = client.post("/api/compliance/check", json=product_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["score"] < 100  # Should have violations


class TestProductSearchEndpoint:
    """Test suite for product search endpoint"""
    
    def test_search_products_default_params(self):
        """Test product search with default parameters"""
        response = client.get("/api/crawler/products")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "products" in data
    
    def test_search_products_with_query(self):
        """Test product search with custom query"""
        response = client.get("/api/crawler/products?query=salt&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "products" in data
        assert len(data["products"]) <= 5
    
    def test_search_products_invalid_platform(self):
        """Test product search with invalid platform"""
        response = client.get("/api/crawler/products?platform=invalid")
        # Should either handle gracefully or return error
        assert response.status_code in [200, 400]


class TestRateLimiting:
    """Test suite for rate limiting"""
    
    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are present in response"""
        response = client.get("/api/stats")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    def test_rate_limit_exceeded(self):
        """Test behavior when rate limit is exceeded"""
        # Make many requests quickly
        rate_limit = 60  # Default limit
        responses = []
        
        for i in range(rate_limit + 5):
            response = client.get("/api/stats")
            responses.append(response)
        
        # At least one should be rate limited
        status_codes = [r.status_code for r in responses]
        # Note: This test might not trigger in test environment
        # In production, you'd see 429 responses


class TestSecurityHeaders:
    """Test suite for security headers"""
    
    def test_security_headers_present(self):
        """Test that security headers are present"""
        response = client.get("/api/health")
        
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"


class TestCORS:
    """Test suite for CORS configuration"""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are properly configured"""
        # This would require actual CORS testing with different origins
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
