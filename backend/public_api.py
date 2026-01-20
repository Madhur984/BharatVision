"""
Public API for E-commerce Platform Integrations

This module provides public REST API endpoints for compliance validation
that can be integrated with any e-commerce platform.
"""

from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
import os
import uuid
from datetime import datetime
import logging

from lmpc_checker.compliance_validator import ComplianceValidator
from backend.ocr_config import OCRConfig, process_with_ocr

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="BharatVision Compliance API",
    description="Legal Metrology compliance validation for e-commerce platforms",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for e-commerce platforms
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
validation_results = {}
api_keys = {
    "demo_key_12345": {"name": "Demo Account", "tier": "free", "requests": 0, "limit": 100},
}


# ==================== Models ====================

class ProductValidationRequest(BaseModel):
    """Request model for product validation"""
    product_id: Optional[str] = Field(None, description="Your product ID")
    platform: str = Field(..., description="E-commerce platform name (amazon, flipkart, shopify, etc.)")
    manufacturer_details: Optional[str] = Field(None, description="Manufacturer name and address")
    country_of_origin: Optional[str] = Field(None, description="Country of origin")
    generic_name: Optional[str] = Field(None, description="Generic/common name of product")
    net_quantity: Optional[str] = Field(None, description="Net quantity with unit (e.g., 500g, 1L)")
    mrp: Optional[str] = Field(None, description="Maximum Retail Price")
    best_before_date: Optional[str] = Field(None, description="Best before/expiry date")
    date_of_manufacture: Optional[str] = Field(None, description="Manufacturing date")
    unit_sale_price: Optional[str] = Field(None, description="Unit sale price")
    category: Optional[str] = Field(None, description="Product category")
    image_url: Optional[HttpUrl] = Field(None, description="Product image URL for OCR")


class BatchValidationRequest(BaseModel):
    """Request model for batch validation"""
    platform: str
    products: List[ProductValidationRequest]


class ValidationResponse(BaseModel):
    """Response model for validation"""
    validation_id: str
    status: str  # "completed", "processing", "failed"
    overall_status: str  # "COMPLIANT", "VIOLATION"
    total_rules: int
    violations_count: int
    violations: List[Dict[str, Any]]
    timestamp: str
    product_id: Optional[str] = None


class APIKeyInfo(BaseModel):
    """API key information"""
    name: str
    tier: str
    requests_used: int
    requests_limit: int


# ==================== Authentication ====================

async def verify_api_key(x_api_key: str = Header(..., description="Your API key")):
    """Verify API key and check rate limits"""
    if x_api_key not in api_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    key_info = api_keys[x_api_key]
    
    # Check rate limit
    if key_info["tier"] == "free" and key_info["requests"] >= key_info["limit"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Free tier allows {key_info['limit']} requests/month"
        )
    
    # Increment request counter
    key_info["requests"] += 1
    
    return key_info


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "BharatVision Compliance API",
        "version": "1.0.0",
        "description": "Legal Metrology compliance validation for e-commerce",
        "documentation": "/docs",
        "status": "operational"
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "compliance-api"
    }


@app.post("/api/v1/validate/product", response_model=ValidationResponse)
async def validate_product(
    request: ProductValidationRequest,
    api_key_info: dict = Depends(verify_api_key)
):
    """
    Validate a single product for Legal Metrology compliance
    
    **Supported Platforms:**
    - amazon, flipkart, meesho, jiomart, myntra
    - shopify, woocommerce, magento, bigcommerce
    - snapdeal, paytm, indiamart, udaan
    """
    try:
        validation_id = str(uuid.uuid4())
        
        # Prepare product data
        product_data = {
            "manufacturer_details": request.manufacturer_details,
            "country_of_origin": request.country_of_origin,
            "generic_name": request.generic_name,
            "net_quantity": request.net_quantity,
            "mrp": request.mrp,
            "best_before_date": request.best_before_date,
            "date_of_manufacture": request.date_of_manufacture,
            "unit_sale_price": request.unit_sale_price,
            "category": request.category or "general"
        }
        
        # If image URL provided, process with Surya OCR
        if request.image_url:
            logger.info(f"Processing image with Surya OCR for platform: {request.platform}")
            try:
                from backend.surya_ocr import get_surya_ocr
                
                # Initialize Surya OCR
                surya = get_surya_ocr()
                
                # Extract text from image
                ocr_result = surya.extract_text_from_image(str(request.image_url))
                
                if ocr_result.get("success"):
                    logger.info(f"✅ Surya OCR extracted text: {len(ocr_result.get('text', ''))} characters")
                    
                    # TODO: Parse OCR text to extract product fields
                    # For now, log the extracted text
                    extracted_text = ocr_result.get('text', '')
                    logger.info(f"Extracted text preview: {extracted_text[:200]}...")
                else:
                    logger.warning(f"Surya OCR failed: {ocr_result.get('error')}")
            except Exception as e:
                logger.error(f"Error processing image with Surya OCR: {e}")
        
        # Validate compliance
        validator = ComplianceValidator()
        result = validator.validate(product_data)
        
        # Prepare response
        response = ValidationResponse(
            validation_id=validation_id,
            status="completed",
            overall_status=result["overall_status"],
            total_rules=result["total_rules"],
            violations_count=result["violations_count"],
            violations=[r for r in result["rule_results"] if r["violated"]],
            timestamp=datetime.now().isoformat(),
            product_id=request.product_id
        )
        
        # Store result
        validation_results[validation_id] = response.dict()
        
        logger.info(f"Validation completed: {validation_id} - {result['overall_status']}")
        return response
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@app.post("/api/v1/validate/batch")
async def validate_batch(
    request: BatchValidationRequest,
    background_tasks: BackgroundTasks,
    api_key_info: dict = Depends(verify_api_key)
):
    """
    Validate multiple products in batch
    
    Returns a batch ID for tracking. Results can be retrieved via /api/v1/validation/{batch_id}
    """
    batch_id = str(uuid.uuid4())
    
    # Process in background
    background_tasks.add_task(process_batch, batch_id, request.products, request.platform)
    
    return {
        "batch_id": batch_id,
        "status": "processing",
        "total_products": len(request.products),
        "message": f"Batch validation started. Check status at /api/v1/validation/{batch_id}"
    }


@app.get("/api/v1/validation/{validation_id}")
async def get_validation_result(
    validation_id: str,
    api_key_info: dict = Depends(verify_api_key)
):
    """Get validation result by ID"""
    if validation_id not in validation_results:
        raise HTTPException(status_code=404, detail="Validation not found")
    
    return validation_results[validation_id]


@app.get("/api/v1/stats")
async def get_stats(api_key_info: dict = Depends(verify_api_key)):
    """Get API usage statistics"""
    return {
        "account": api_key_info["name"],
        "tier": api_key_info["tier"],
        "requests_used": api_key_info["requests"],
        "requests_limit": api_key_info["limit"],
        "requests_remaining": api_key_info["limit"] - api_key_info["requests"]
    }


@app.post("/api/v1/webhooks/register")
async def register_webhook(
    webhook_url: HttpUrl,
    events: List[str],
    api_key_info: dict = Depends(verify_api_key)
):
    """
    Register a webhook for validation events
    
    **Supported Events:**
    - validation.completed
    - validation.failed
    - batch.completed
    """
    # Store webhook configuration
    webhook_id = str(uuid.uuid4())
    
    return {
        "webhook_id": webhook_id,
        "url": str(webhook_url),
        "events": events,
        "status": "active"
    }


# ==================== Helper Functions ====================

async def process_batch(batch_id: str, products: List[ProductValidationRequest], platform: str):
    """Process batch validation in background"""
    results = []
    validator = ComplianceValidator()
    
    for product in products:
        try:
            product_data = {
                "manufacturer_details": product.manufacturer_details,
                "country_of_origin": product.country_of_origin,
                "generic_name": product.generic_name,
                "net_quantity": product.net_quantity,
                "mrp": product.mrp,
                "best_before_date": product.best_before_date,
                "date_of_manufacture": product.date_of_manufacture,
                "unit_sale_price": product.unit_sale_price,
                "category": product.category or "general"
            }
            
            result = validator.validate(product_data)
            results.append({
                "product_id": product.product_id,
                "status": result["overall_status"],
                "violations_count": result["violations_count"]
            })
        except Exception as e:
            results.append({
                "product_id": product.product_id,
                "status": "ERROR",
                "error": str(e)
            })
    
    # Store batch results
    validation_results[batch_id] = {
        "batch_id": batch_id,
        "status": "completed",
        "total_products": len(products),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "public_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
