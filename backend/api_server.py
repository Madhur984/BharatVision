"""
FastAPI Backend Server for BharatVision Frontend
Provides REST API endpoints for crawler and compliance checking
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from crawler import crawl_amazon, crawl_flipkart, ProductData
from ocr_integration import OCRIntegrator
from compliance_validator import validate_compliance_score

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="BharatVision API",
    description="Legal Metrology Compliance Checking API",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== REQUEST/RESPONSE MODELS =====
class ComplianceCheckRequest(BaseModel):
    """Request model for compliance checking"""
    title: str
    brand: str
    price: float
    mrp: float
    image: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

class ComplianceCheckResponse(BaseModel):
    """Response model for compliance check"""
    score: int
    status: str  # 'Compliant', 'Partial', 'Non-Compliant'
    color: str  # 'green', 'yellow', 'red'
    details: Dict[str, Any]

class ProductResponse(BaseModel):
    """Product response model"""
    id: int
    title: str
    brand: str
    price: float
    mrp: float
    image: str
    category: str

# ===== API ENDPOINTS =====

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "BharatVision API"}


@app.get("/api/crawler/products")
async def get_products(
    query: str = "packaged food",
    platform: str = "amazon",
    limit: int = 10
):
    """
    Fetch products from e-commerce platform
    
    Args:
        query: Search query
        platform: amazon, flipkart, jiomart
        limit: Number of products to return
    
    Returns:
        List of products or error message if crawling fails
    """
    try:
        logger.info(f"Crawling {platform} for: {query}")
        
        # Get products from crawler
        try:
            if platform.lower() == "flipkart":
                products = crawl_flipkart(query)
            else:  # Default to Amazon
                products = crawl_amazon(query)
        except Exception as crawler_error:
            logger.warning(f"Crawler returned error: {crawler_error}")
            # Return empty list instead of crashing
            return {
                "status": "error",
                "message": f"Crawling failed (website may be blocking requests): {str(crawler_error)}",
                "products": [],
                "query": query,
                "platform": platform
            }
        
        # Convert to response format
        result = []
        for i, product in enumerate(products[:limit]):
            if isinstance(product, ProductData):
                result.append({
                    "id": i + 1,
                    "title": product.title,
                    "brand": product.brand,
                    "price": product.price,
                    "mrp": product.mrp,
                    "image": product.image_urls[0] if product.image_urls else "https://via.placeholder.com/300x300?text=Product",
                    "category": product.category or "General"
                })
            else:
                result.append(product)
        
        return {
            "status": "success",
            "products": result,
            "query": query,
            "platform": platform,
            "count": len(result)
        }
    
    except Exception as e:
        logger.error(f"Crawler error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"Unexpected error during crawling: {str(e)}",
            "products": [],
            "query": query,
            "platform": platform
        }


@app.post("/api/compliance/check")
async def check_product_compliance(request: ComplianceCheckRequest):
    """
    Check product compliance against legal metrology rules
    
    Args:
        request: Product data
    
    Returns:
        Compliance check result with score and status
    """
    try:
        logger.info(f"Checking compliance for: {request.title}")
        
        # Simple compliance scoring based on fields
        score = 100
        issues = []
        
        # Check MRP display
        if request.mrp <= 0:
            score -= 15
            issues.append("MRP must be displayed")
        elif request.price > request.mrp:
            score -= 10
            issues.append("Price cannot exceed MRP")
        
        # Check brand/manufacturer
        if not request.brand or len(request.brand.strip()) < 2:
            score -= 15
            issues.append("Valid brand/manufacturer required")
        
        # Check category
        if not request.category or request.category.strip() == "":
            score -= 5
            issues.append("Category should be specified")
        
        # Determine status
        if score >= 85:
            status = "Compliant"
            color = "green"
        elif score >= 60:
            status = "Partial"
            color = "yellow"
        else:
            status = "Non-Compliant"
            color = "red"
        
        return ComplianceCheckResponse(
            score=max(0, score),
            status=status,
            color=color,
            details={
                "mrp_check": request.mrp > 0,
                "brand_check": bool(request.brand),
                "category_check": bool(request.category),
                "issues": issues
            }
        )
    
    except Exception as e:
        logger.error(f"Compliance check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "total_scans": 332,
        "compliance_rate": 92.5,
        "violations_flagged": 156,
        "devices_online": 8,
        "total_products_checked": 2847
    }


@app.get("/api/recent-scans")
async def get_recent_scans():
    """Get recent product scans"""
    return [
        {
            "product_id": "75521466",
            "brand": "Dharan",
            "category": "Foodgrains",
            "status": "Compliant"
        },
        {
            "product_id": "21562728",
            "brand": "Myatique",
            "category": "Personal Care",
            "status": "Violation"
        },
        {
            "product_id": "21564729",
            "brand": "Cataris",
            "category": "Food & Bev",
            "status": "Compliant"
        }
    ]


@app.post("/api/upload-image")
async def upload_and_analyze_image(file_path: str):
    """
    Upload and analyze product image for compliance
    
    Args:
        file_path: Path to image
    
    Returns:
        OCR extracted text and compliance analysis
    """
    try:
        ocr = OCRIntegrator()
        result = ocr.extract_text_from_image_url(file_path)
        return {
            "extracted_text": result.get('text', ''),
            "confidence": result.get('confidence', 0),
            "analysis": "Ready for compliance check"
        }
    except Exception as e:
        logger.error(f"Image upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "BharatVision API",
        "version": "1.0.0",
        "description": "Legal Metrology Compliance Checking System",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting BharatVision API Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
