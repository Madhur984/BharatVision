from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
import io
import os
import time
import tempfile
from pathlib import Path
import traceback

app = FastAPI(title="LMPC Inference Backend")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/infer")
async def infer(file: UploadFile = File(...)):
    filename = file.filename
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        contents = await file.read()

        # Save to a temporary file so OpenCV/Pillow can read it reliably
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        # Ensure we can read with PIL and normalize to RGB
        image = Image.open(io.BytesIO(contents))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(tmp_path)

        # Ensure project root is importable for local module imports
        project_root = Path(__file__).parents[1]
        import sys
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        # Lazy import heavy modules (torch, ultralytics, etc.)
        from live_processor import LiveProcessor
        from data_refiner.refiner import DataRefiner
        from lmpc_checker.compliance_validator import ComplianceValidator

        ocr_processor = LiveProcessor()
        data_refiner = DataRefiner()
        compliance_validator = ComplianceValidator()

        # Use OpenCV to read image for processing
        import cv2
        frame = cv2.imread(tmp_path)
        if frame is None:
            raise ValueError("Could not load image for processing")

        # Run OCR/extraction
        extracted_text = ocr_processor._extract_text_with_surya(frame)
        if not extracted_text:
            raise ValueError("No text could be extracted from the image")

        structured_data = ocr_processor._structure_text_with_nlp(extracted_text)
        if not structured_data:
            structured_data = ocr_processor._construct_json_from_text(extracted_text)

        refined_data = data_refiner.refine(structured_data if structured_data else extracted_text)
        violations = compliance_validator.validate(refined_data)

        processing_time = 0.0

        result = {
            'filename': filename,
            'file_size': len(contents),
            'timestamp': timestamp,
            'method': 'Remote Inference',
            'processing_time': processing_time,
            'ocr_result': extracted_text,
            'refined_data': refined_data,
            'violations': violations,
            'compliance_status': 'COMPLIANT' if not violations else 'NON_COMPLIANT',
            'image_dimensions': image.size
        }

        try:
            os.remove(tmp_path)
        except Exception:
            pass

        return JSONResponse(result)

    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse({
            'filename': filename,
            'timestamp': timestamp,
            'method': 'Remote Inference',
            'error': f"{str(e)}\n{tb}",
            'compliance_status': 'ERROR'
        }, status_code=500)
