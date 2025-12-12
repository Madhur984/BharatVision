from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import os
import logging
from typing import Optional
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="BharatVision ML API",
    version="2.0.0",
    description="Cloud-hosted ML API for Legal Metrology Compliance using Gemma-2-9b-it"
)

# CORS Configuration - Allow Streamlit Cloud and localhost
ALLOWED_ORIGINS = [
    "https://bharatvision.streamlit.app",
    "https://*.streamlit.app",
    "http://localhost:8501",
    "http://localhost:3000",
    "http://127.0.0.1:8501",
]

# Add wildcard for development if needed
if os.getenv("ENVIRONMENT") == "development":
    ALLOWED_ORIGINS.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Hugging Face Configuration
# IMPORTANT: HF_TOKEN must be set as environment variable (no fallback for security)
HF_TOKEN = os.getenv("HF_TOKEN")
# HF_MODEL removed - not using Gemma anymore
# REPO_ID = os.getenv("HF_MODEL", "google/gemma-2-9b-it")
REPO_ID = None  # Disabled

# Validate HF_TOKEN is set
if not HF_TOKEN:
    logger.error("HF_TOKEN environment variable is not set!")
    logger.error("Please set HF_TOKEN in your environment or Space secrets")
    client = None
else:
    # Initialize HF client
    try:
        client = InferenceClient(token=HF_TOKEN)
        logger.info(f"Initialized HuggingFace client with model: {REPO_ID}")
    except Exception as e:
        logger.error(f"Failed to initialize HuggingFace client: {e}")
        client = None

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="Question about Legal Metrology")
    context: str = Field(default="", max_length=5000, description="Optional context for the question")

@app.get("/health")
@app.get("/api/health")
def health_check():
    """Health check endpoint with detailed status"""
    return {
        "status": "healthy",
        "service": "BharatVision HF API",
        "model": REPO_ID,
        "model_available": client is not None,
        "version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "production")
    }

@app.post("/api/ai/ask")
def ask_ai(request: AskRequest):
    """
    Query the Hugging Face Inference API for Legal Metrology questions.
    """
    logger.info(f"Received question: {request.question[:100]}...")
    
    # Check if client is available
    if client is None:
        logger.error("HuggingFace client not initialized")
        raise HTTPException(
            status_code=503,
            detail="AI service unavailable. Please check configuration."
        )
    
    try:
        # Construct the prompt for Gemma 2
        prompt = f"""<start_of_turn>user
You are an expert Legal Metrology assistant for India. 
Answer the following question clearly and concisely about proper labelling, compliance, and laws.

Question: {request.question}
{f"Context: {request.context}" if request.context else ""}
<end_of_turn>
<start_of_turn>model
"""
        
        logger.info(f"Calling HF API with model: {REPO_ID}")
        
        # Call HF API with timeout handling
        response = client.text_generation(
            prompt, 
            model=REPO_ID, 
            max_new_tokens=500,
            temperature=0.7,
            do_sample=True
        )
        
        logger.info(f"Successfully generated response (length: {len(response)})")
        
        return {
            "question": request.question,
            "answer": response,
            "success": True,
            "source": f"Hugging Face API ({REPO_ID})",
            "model": REPO_ID
        }
        
    except Exception as e:
        logger.error(f"HF API Error: {str(e)}", exc_info=True)
        
        # Return error response with details
        return {
            "success": False, 
            "error": str(e),
            "answer": "I apologize, but I'm experiencing technical difficulties connecting to the AI service. Please try again in a moment.",
            "question": request.question
        }

# ================= ML PROCESSING ENDPOINTS =================

class OCRRequest(BaseModel):
    """Request model for OCR extraction"""
    image_base64: str = Field(..., description="Base64 encoded image")

class ComplianceRequest(BaseModel):
    """Request model for compliance checking"""
    text: str = Field(..., description="Extracted text to validate")
    product_data: dict = Field(default={}, description="Additional product data")

@app.post("/api/ocr/extract")
async def extract_ocr(file: UploadFile = File(...)):
    """
    Extract text from image using HuggingFace OCR models
    """
    logger.info(f"OCR request received: {file.filename}")
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image
        contents = await file.read()
        
        # Use HuggingFace Inference API for OCR
        # Using Microsoft's TrOCR or similar OCR model
        if client:
            try:
                from PIL import Image
                import io
                import base64
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(contents))
                
                # Convert to RGB if needed
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Use image-to-text model for OCR
                # Note: This is a simplified version. For production, you might want to use
                # a dedicated OCR model or service
                result = client.image_to_text(
                    contents,
                    model="microsoft/trocr-base-printed"  # OCR model
                )
                
                extracted_text = result if isinstance(result, str) else result.get('generated_text', '')
                
                logger.info(f"OCR successful, extracted {len(extracted_text)} characters")
                
                return {
                    "success": True,
                    "text": extracted_text,
                    "confidence": 0.85,  # Placeholder
                    "method": "HuggingFace TrOCR"
                }
                
            except Exception as e:
                logger.error(f"HF OCR failed: {e}")
                # Fallback to simple text extraction
                return {
                    "success": False,
                    "text": "",
                    "error": str(e),
                    "method": "fallback"
                }
        else:
            raise HTTPException(status_code=503, detail="OCR service unavailable")
            
    except Exception as e:
        logger.error(f"OCR processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/detect/objects")
async def detect_objects(file: UploadFile = File(...)):
    """
    Detect objects in image using YOLO via HuggingFace
    """
    logger.info(f"Object detection request: {file.filename}")
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        
        if client:
            try:
                # Use HuggingFace object detection model
                result = client.object_detection(
                    contents,
                    model="facebook/detr-resnet-50"  # DETR object detection
                )
                
                logger.info(f"Detected {len(result)} objects")
                
                return {
                    "success": True,
                    "detections": result,
                    "count": len(result),
                    "method": "HuggingFace DETR"
                }
                
            except Exception as e:
                logger.error(f"Object detection failed: {e}")
                return {
                    "success": False,
                    "detections": [],
                    "error": str(e)
                }
        else:
            raise HTTPException(status_code=503, detail="Detection service unavailable")
            
    except Exception as e:
        logger.error(f"Detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compliance/check")
def check_compliance(request: ComplianceRequest):
    """
    Check Legal Metrology compliance for extracted text
    Focuses on 6 core mandatory fields as per Legal Metrology Act
    """
    logger.info(f"Compliance check for text length: {len(request.text)}")
    
    try:
        violations = []
        score = 100
        penalty_per_field = 100 / 6  # Equal weight for each of 6 fields
        
        # 6 Core Legal Metrology Requirements
        required_fields = {
            "Manufacturer Name & Address": [
                "manufactured by", "mfd by", "manufacturer", 
                "marketed by", "mkt by", "marketer"
            ],
            "Net Quantity": [
                "net qty", "net quantity", "net wt", "net weight",
                "net content", "contents:", "quantity:"
            ],
            "MRP (Maximum Retail Price)": [
                "mrp", "m.r.p", "maximum retail price", "retail price",
                "price:", "₹", "rs.", "rs "
            ],
            "Consumer Care Details": [
                "customer care", "consumer care", "helpline",
                "contact", "email", "phone", "toll free"
            ],
            "Date of Manufacture": [
                "mfg date", "mfd date", "manufactured on",
                "date of manufacture", "dom", "mfg:", "mfd:"
            ],
            "Country of Origin": [
                "made in", "country of origin", "origin:",
                "manufactured in", "product of"
            ]
        }
        
        text_lower = request.text.lower()
        
        for field, keywords in required_fields.items():
            found = any(kw in text_lower for kw in keywords)
            if not found:
                violations.append({
                    "field": field,
                    "severity": "critical",
                    "message": f"{field} is mandatory but not found on label"
                })
                score -= penalty_per_field
        
        is_compliant = len(violations) == 0
        
        return {
            "success": True,
            "compliant": is_compliant,
            "score": round(max(0, score), 2),
            "violations": violations,
            "fields_checked": list(required_fields.keys()),
            "total_fields": 6,
            "fields_found": 6 - len(violations)
        }
        
    except Exception as e:
        logger.error(f"Compliance check failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/process/image")
async def process_image_full(file: UploadFile = File(...)):
    """
    Full pipeline: OCR + Compliance checking
    """
    logger.info(f"Full processing request: {file.filename}")
    
    try:
        # Step 1: OCR
        ocr_result = await extract_ocr(file)
        
        if not ocr_result.get("success"):
            return {
                "success": False,
                "error": "OCR failed",
                "ocr_result": ocr_result
            }
        
        extracted_text = ocr_result.get("text", "")
        
        # Step 2: Compliance check
        compliance_request = ComplianceRequest(text=extracted_text)
        compliance_result = check_compliance(compliance_request)
        
        return {
            "success": True,
            "ocr": ocr_result,
            "compliance": compliance_result,
            "text": extracted_text
        }
        
    except Exception as e:
        logger.error(f"Full processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ================= MOCK ENDPOINTS FOR STREAMLIT COMPATIBILITY =================

@app.get("/api/dashboard/stats")
def get_stats():
    return {
        "total_scans": 332,
        "compliance_rate": 92.5,
        "violations_flagged": 156,
        "devices_online": 8,
        "recent_scans": [
            {"product_id": "75521466", "brand": "Dharan", "category": "Foodgrains", "status": "Compliant"},
            {"product_id": "21562728", "brand": "Myatique", "category": "Personal Care", "status": "Violation"},
            {"product_id": "21564729", "brand": "Cataris", "category": "Food & Bev", "status": "Compliant"}
        ]
    }

@app.get("/api/search/products")
def search_products(q: str = ""):
    return {
        "total": 4,
        "results": [
            {"id": 1, "name": "Premium Tea Gold", "brand": "Dharan Tea Co", "category": "Beverages", "status": "Compliant", "score": 92},
            {"id": 2, "name": "Digestive Biscuits", "brand": "CatarisBrew", "category": "Snacks", "status": "Partial", "score": 75},
            {"id": 3, "name": "Honey Pure", "brand": "NatureLand", "category": "Food", "status": "Compliant", "score": 88},
            {"id": 4, "name": "Face Cream", "brand": "BeautyCare", "category": "Personal Care", "status": "Violation", "score": 42}
        ]
    }

@app.post("/api/upload/process")
def process_upload(file: UploadFile = File(...)):
    # Mock OCR response for now - can integrate real OCR later
    return {
        "success": True,
        "extracted_text": "Sample Product Label\nMRP Rs. 500\nNet Qty: 1kg",
        "confidence": 95.5,
        "fields_detected": {"brand": True, "mrp": True, "quantity": True}
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
