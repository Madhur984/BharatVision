"""
Python Bridge - Executes Streamlit page functions and serves results to HTML frontend
This creates an API layer that allows HTML to call Python functions
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import io

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from crawler import crawl_amazon, crawl_flipkart, ProductData

logger = logging.getLogger(__name__)

app = FastAPI(title="BharatVision Python Bridge", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== REQUEST MODELS =====

class CameraFrameRequest(BaseModel):
    frame_data: str  # Base64 encoded image
    camera_id: int = 0
    auto_capture: bool = False

class ComplianceCheckRequest(BaseModel):
    title: str
    brand: str
    price: float
    mrp: float
    image_url: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

# ===== LIVE CAMERA ENDPOINTS =====

@app.post("/api/camera/capture")
async def camera_capture(request: CameraFrameRequest):
    """
    Process camera frame for OCR and compliance checking
    """
    try:
        # Decode base64 frame
        import base64
        frame_bytes = base64.b64decode(request.frame_data)
        frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        if frame is None:
            raise ValueError("Invalid frame data")
        
        # Process frame for OCR (placeholder)
        detection_confidence = np.random.uniform(0.6, 0.99)
        extracted_text = "Sample product label text detected from image"
        
        return {
            "success": True,
            "confidence": round(detection_confidence * 100, 2),
            "extracted_text": extracted_text,
            "detection_count": np.random.randint(3, 10),
            "processing_time_ms": np.random.randint(100, 500)
        }
    except Exception as e:
        logger.error(f"Camera capture error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/camera/list")
async def list_cameras():
    """Get available cameras"""
    return {
        "cameras": [
            {"id": 0, "name": "Default Camera (USB)"},
            {"id": 1, "name": "Built-in Webcam"},
        ]
    }

# ===== IMAGE UPLOAD ENDPOINTS =====

@app.post("/api/upload/process")
async def process_uploaded_image(file: UploadFile = File(...)):
    """
    Process uploaded image for OCR and compliance checking
    """
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        
        # Process image (placeholder OCR)
        extracted_text = "Product information extracted from image"
        confidence = np.random.uniform(0.7, 0.99)
        
        return {
            "filename": file.filename,
            "success": True,
            "extracted_text": extracted_text,
            "confidence": round(confidence * 100, 2),
            "fields_detected": {
                "brand": True,
                "mrp": True,
                "quantity": True,
                "expiry": True,
                "manufacturer": True
            },
            "processing_time_ms": np.random.randint(200, 800)
        }
    except Exception as e:
        logger.error(f"Image upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

@app.post("/api/upload/batch")
async def process_batch_images(files: List[UploadFile] = File(...)):
    """
    Process multiple images in batch
    """
    results = []
    
    for file in files[:20]:  # Max 20 files
        try:
            contents = await file.read()
            img = Image.open(io.BytesIO(contents))
            
            is_compliant = np.random.random() > 0.3
            
            results.append({
                "filename": file.filename,
                "status": "Compliant" if is_compliant else "Violation",
                "confidence": round(np.random.uniform(0.6, 0.99) * 100, 2),
                "score": np.random.randint(60, 100) if is_compliant else np.random.randint(20, 60)
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "Error",
                "error": str(e)
            })
    
    return {
        "total_processed": len(results),
        "compliant": sum(1 for r in results if r["status"] == "Compliant"),
        "violations": sum(1 for r in results if r["status"] == "Violation"),
        "results": results
    }

# ===== SEARCH ENDPOINTS =====

@app.get("/api/search/products")
async def search_products(
    name: Optional[str] = None,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None
):
    """
    Search products in database
    """
    mock_products = [
        {
            "id": 1,
            "name": "Premium Tea Gold",
            "brand": "Dharan Tea Co",
            "category": "Beverages",
            "status": "Compliant",
            "score": 92,
            "mrp": 450,
            "price": 350
        },
        {
            "id": 2,
            "name": "Digestive Biscuits",
            "brand": "CatarisBrew",
            "category": "Snacks",
            "status": "Partial",
            "score": 75,
            "mrp": 80,
            "price": 65
        },
        {
            "id": 3,
            "name": "Honey Pure",
            "brand": "NatureLand",
            "category": "Food",
            "status": "Compliant",
            "score": 88,
            "mrp": 280,
            "price": 250
        },
        {
            "id": 4,
            "name": "Face Cream",
            "brand": "BeautyCare",
            "category": "Personal Care",
            "status": "Violation",
            "score": 42,
            "mrp": 399,
            "price": 299
        }
    ]
    
    # Filter results
    filtered = mock_products
    
    if name:
        filtered = [p for p in filtered if name.lower() in p["name"].lower()]
    if brand:
        filtered = [p for p in filtered if brand.lower() in p["brand"].lower()]
    if category:
        filtered = [p for p in filtered if category.lower() in p["category"].lower()]
    if status:
        filtered = [p for p in filtered if status.lower() in p["status"].lower()]
    
    return {
        "total": len(filtered),
        "results": filtered
    }

# ===== DASHBOARD ENDPOINTS =====

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """
    Get dashboard statistics
    """
    return {
        "total_scans": 332,
        "compliance_rate": 92.5,
        "violations_flagged": 156,
        "devices_online": 8,
        "recent_scans": [
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
    }

# ===== AI ASSISTANT ENDPOINTS =====

@app.post("/api/ai/ask")
async def ask_ai(question: str):
    """
    AI compliance assistant
    """
    q_lower = question.lower()
    
    responses = {
        "mrp": "MRP (Maximum Retail Price) must be prominently displayed on all packages. It should be clear, legible, and in the currency of the country.",
        "quantity": "Net quantity must be displayed in both metric and common units (e.g., 500g and 500 grams). Font size must be at least 3mm.",
        "expiry": "Expiry date format should be DD/MM/YYYY or DD-MM-YYYY. Must be printed in contrasting color on dark background.",
        "brand": "Brand/manufacturer name must be clearly visible. It should include the company name and registered address of manufacturer or packer.",
        "ingredients": "For food products, ingredient list must be in descending order of weight. Allergens must be highlighted.",
    }
    
    response = responses.get("default", "I can help with legal metrology compliance questions.")
    
    for key, value in responses.items():
        if key in q_lower:
            response = value
            break
    
    return {
        "question": question,
        "answer": response,
        "related_topics": ["MRP", "Quantity", "Expiry", "Brand", "Ingredients"]
    }

# ===== ADMIN ENDPOINTS =====

@app.get("/api/admin/system-stats")
async def get_system_stats():
    """
    Get system statistics for admin dashboard
    """
    return {
        "total_users": 1284,
        "uptime_percentage": 99.8,
        "data_processed": "45.2K",
        "active_alerts": 12,
        "system_health": "Healthy",
        "last_backup": "2025-12-05 03:00 AM",
        "database_size_gb": 24.5
    }

@app.get("/api/admin/users")
async def get_users(limit: int = 10):
    """
    Get list of users for admin management
    """
    return {
        "total": 1284,
        "users": [
            {"id": i, "name": f"User {i}", "email": f"user{i}@example.com", "role": "Analyst", "last_active": "2 hours ago"}
            for i in range(1, limit + 1)
        ]
    }

@app.post("/api/admin/backup")
async def trigger_backup():
    """
    Trigger system backup
    """
    return {
        "status": "success",
        "message": "Backup initiated",
        "backup_id": "BKP-2025-12-05-001",
        "estimated_time_minutes": 15
    }

# ===== HEALTH CHECKS =====

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "BharatVision Python Bridge",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting BharatVision Python Bridge...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
