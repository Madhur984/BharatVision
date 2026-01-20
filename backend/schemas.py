"""
Input validation schemas for BharatVision API
Uses Pydantic for robust validation and automatic documentation
"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List
from datetime import datetime
import re


class ComplianceCheckRequest(BaseModel):
    """Enhanced request model for compliance checking with validation"""
    title: str = Field(..., min_length=1, max_length=500, description="Product title")
    brand: str = Field(..., min_length=1, max_length=200, description="Brand name")
    price: float = Field(..., gt=0, description="Current selling price (must be positive)")
    mrp: float = Field(..., gt=0, description="Maximum Retail Price (must be positive)")
    image: Optional[HttpUrl] = Field(None, description="Product image URL")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    description: Optional[str] = Field(None, max_length=5000, description="Product description")
    
    @validator('price', 'mrp')
    def validate_price_format(cls, v):
        """Ensure prices are reasonable (not too large)"""
        if v > 10000000:  # 1 crore max
            raise ValueError('Price seems unreasonably high')
        return round(v, 2)
    
    @validator('title', 'brand')
    def validate_no_special_chars(cls, v):
        """Prevent injection attacks via special characters"""
        if re.search(r'[<>{}]', v):
            raise ValueError('Special characters not allowed')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Tata Salt 1kg",
                "brand": "Tata",
                "price": 25.00,
                "mrp": 30.00,
                "image": "https://example.com/image.jpg",
                "category": "Food & Beverages",
                "description": "Premium quality iodized salt"
            }
        }


class ProductSearchRequest(BaseModel):
    """Request model for product search"""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    platform: str = Field("amazon", pattern="^(amazon|flipkart|jiomart)$", description="E-commerce platform")
    limit: int = Field(10, ge=1, le=100, description="Number of results (1-100)")
    
    @validator('query')
    def validate_query(cls, v):
        """Sanitize search query"""
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>{}]', '', v)
        return sanitized.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "query": "packaged food",
                "platform": "amazon",
                "limit": 10
            }
        }


class ImageUploadRequest(BaseModel):
    """Request model for image upload and analysis"""
    image_url: Optional[HttpUrl] = Field(None, description="URL of the image to analyze")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image data")
    
    @validator('image_base64')
    def validate_base64(cls, v):
        """Validate base64 image data"""
        if v:
            # Check if it's valid base64
            import base64
            try:
                # Limit size to 10MB
                if len(v) > 10 * 1024 * 1024:
                    raise ValueError('Image too large (max 10MB)')
                base64.b64decode(v)
            except Exception:
                raise ValueError('Invalid base64 image data')
        return v
    
    @validator('image_url', 'image_base64')
    def validate_at_least_one(cls, v, values):
        """Ensure at least one image source is provided"""
        if not v and not values.get('image_url') and not values.get('image_base64'):
            raise ValueError('Either image_url or image_base64 must be provided')
        return v


class ComplianceCheckResponse(BaseModel):
    """Response model for compliance check"""
    score: int = Field(..., ge=0, le=100, description="Compliance score (0-100)")
    status: str = Field(..., pattern="^(Compliant|Partial|Non-Compliant)$", description="Compliance status")
    color: str = Field(..., pattern="^(green|yellow|red)$", description="Status color indicator")
    details: dict = Field(..., description="Detailed compliance information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "score": 95,
                "status": "Compliant",
                "color": "green",
                "details": {
                    "mrp_check": True,
                    "brand_check": True,
                    "category_check": True,
                    "issues": []
                },
                "timestamp": "2026-01-20T15:00:00Z"
            }
        }


class ProductResponse(BaseModel):
    """Product response model with validation"""
    id: int = Field(..., ge=1, description="Product ID")
    title: str = Field(..., min_length=1, max_length=500)
    brand: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0)
    mrp: float = Field(..., gt=0)
    image: HttpUrl
    category: str = Field(..., max_length=100)
    
    @validator('price', 'mrp')
    def round_prices(cls, v):
        """Round prices to 2 decimal places"""
        return round(v, 2)


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "details": {"field": "price", "issue": "must be positive"},
                "timestamp": "2026-01-20T15:00:00Z"
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$")
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Optional[dict] = Field(None, description="Individual component health")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "service": "BharatVision API",
                "version": "1.0.0",
                "timestamp": "2026-01-20T15:00:00Z",
                "checks": {
                    "database": "healthy",
                    "ocr_service": "healthy",
                    "ml_models": "healthy"
                }
            }
        }