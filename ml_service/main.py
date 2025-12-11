from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from core import processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models on startup
    logger.info("Starting up ML Service...")
    processor.load_models()
    yield
    logger.info("Shutting down ML Service...")

app = FastAPI(title="Legal Metrology ML API", lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ml-api"}

@app.post("/extract")
async def extract_info(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        result = processor.process_image(contents)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ocr")
async def extract_ocr_only(file: UploadFile = File(...)):
    """Lightweight endpoint if only text is needed"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    try:
        contents = await file.read()
        # For efficiency, we might want a dedicated OCR-only method in core, 
        # but for now reusing process_image is fine as it does OCR anyway.
        result = processor.process_image(contents)
        return JSONResponse(content={"raw_text": result["raw_text"]})
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
