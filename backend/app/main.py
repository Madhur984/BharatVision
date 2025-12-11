from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.routers import compliance, ocr, mock, scraper

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Professional Legal Metrology ML API (v2)"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(compliance.router, prefix="/api/compliance", tags=["Compliance"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR"])
app.include_router(mock.router, prefix="/api", tags=["Mock"]) 
app.include_router(scraper.router, prefix="/api/scrape", tags=["Scraper"])

# Add legacy compatibility endpoint for /api/process/image which calls both
# We can add this to compliance router or here.
from fastapi import UploadFile, File
@app.post("/api/process/image", tags=["Pipeline"])
async def process_image_full(file: UploadFile = File(...)):
    # Re-implementing the orchestration logic
    # 1. OCR
    from backend.app.services.compliance import compliance_service
    from backend.app.schemas.compliance import ComplianceRequest
    
    # Call OCR (We can reuse the logic from OCR router or service if separated)
    # For speed, reusing OCR router logic mostly involves request context, better to split service.
    # But here I'll just call the OCR logic directly.
    import requests
    try:
        contents = await file.read()
        API_URL = f"https://router.huggingface.co/models/{settings.OCR_MODEL}"
        headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}
        resp = requests.post(API_URL, headers=headers, data=contents)
        text = ""
        if resp.status_code == 200:
            res = resp.json()
            if isinstance(res, list): text = res[0].get('generated_text', '')
            elif isinstance(res, dict): text = res.get('generated_text', '')
        
        # 2. Compliance
        comp_req = ComplianceRequest(text=text)
        comp_res = compliance_service.check_compliance(comp_req)
        
        return {
            "success": True,
            "ocr": {"text": text, "success": True},
            "compliance": comp_res.dict(),
            "text": text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.VERSION}
