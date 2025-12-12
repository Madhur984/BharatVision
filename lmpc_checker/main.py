"""
Main pipeline for Legal Metrology OCR project **with YOLO panel detection**.

This exposes a single function:

    run_pipeline_for_image(image_bytes: bytes) -> dict

which:
  1. Opens the image from bytes
  2. Uses YOLOv8 to detect packaging panels:
        - brand_product_panel
        - mrp_panel
        - net_quantity_panel
        - mfg_or_packed_date_panel
        - best_before_or_expiry_panel
        - manufacturer_importer_panel
        - country_of_origin_panel
        - customer_care_panel
  3. For each detected panel, crops and runs OCR (Surya OCR if available, else pytesseract)
  4. Feeds tagged per-panel OCR text to  2 (LLM) to get structured fields (mrp, net_quantity, etc.)
  5. Validates the fields using ComplianceValidator
  6. Returns:
        {
            "structured_data": {...},
            "compliance_summary": {...},
            "raw_ocr_text": "...",     # combined panel text for debugging
            "panel_texts": {...},      # per-panel OCR
        }
"""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from .compliance_validator import ComplianceValidator

# Optional heavy deps – imported lazily
__tokenizer = None
__model = None

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# -------------------------------------------------------------------
# YOLO SETUP
# -------------------------------------------------------------------
try:
    from ultralytics import YOLO  # type: ignore
except Exception as e:  # pragma: no cover
    YOLO = None
    logger.warning(f"Ultralytics not available: {e}")

# Classes must match your synthetic dataset / dataset.yaml
CLASSES = [
    "brand_product_panel",         # 0
    "mrp_panel",                   # 1
    "net_quantity_panel",          # 2
    "mfg_or_packed_date_panel",    # 3
    "best_before_or_expiry_panel", # 4
    "manufacturer_importer_panel", # 5
    "country_of_origin_panel",     # 6
    "customer_care_panel",         # 7
]

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 🔧 This is where YOUR trained YOLO model lives
DEFAULT_YOLO_PATH = PROJECT_ROOT / "runs" / "detect" / "train" / "weights" / "best.pt"

_yolo_model: Optional[Any] = None


def get_yolo_model() -> Optional[Any]:
    """
    Lazy-load YOLO model once.
    """
    global _yolo_model
    if _yolo_model is not None:
        return _yolo_model

    if YOLO is None:
        logger.warning("Ultralytics YOLO not installed; skipping panel detection.")
        return None

    model_path = DEFAULT_YOLO_PATH
    if not model_path.exists():
        logger.warning(f"YOLO model not found at {model_path}. Panel detection will be skipped.")
        return None

    logger.info(f"Loading YOLO model from: {model_path}")
    _yolo_model = YOLO(str(model_path))
    return _yolo_model


# -------------------------------------------------------------------
# OCR HELPERS (same idea as your original, but used per panel)
# -------------------------------------------------------------------


def _ocr_with_surya(pil_image: Image.Image) -> Optional[str]:
    """
    Try OCR using Surya OCR.
    If anything fails, return None so we can fall back to pytesseract.
    """
    try:
        from surya.ocr import run_ocr
        from surya.model.detection import model as det_model
        from surya.model.recognition.model import load_model as load_rec_model
        from surya.model.recognition.processor import (
            load_processor as load_rec_processor,
        )

        logger.info("Running Surya OCR on crop...")
        langs = ["en", "hi"]

        det_processor = det_model.load_processor()
        detection_model = det_model.load_model()

        rec_model = load_rec_model()
        rec_processor = load_rec_processor()

        predictions = run_ocr(
            [pil_image],
            [langs],
            detection_model,
            det_processor,
            rec_model,
            rec_processor,
        )

        # predictions[0] is a list of dicts; each dict has "text"
        if not predictions:
            return None

        page_preds = predictions[0]
        lines = [p.get("text", "") for p in page_preds if p.get("text")]
        text = "\n".join(lines)
        return text.strip() or None

    except Exception as e:
        logger.warning(f"Surya OCR failed or not available, falling back. Error: {e}")
        return None


def _ocr_with_tesseract(pil_image: Image.Image) -> str:
    """
    Very simple pytesseract OCR as fallback.
    Requires `pytesseract` and Tesseract installed on system.
    """
    try:
        import pytesseract

        logger.info("Running pytesseract OCR on crop...")
        text = pytesseract.image_to_string(pil_image)
        return text.strip()
    except Exception as e:
        logger.error(
            f"Both Surya and pytesseract OCR unavailable. Error: {e}. Returning empty text."
        )
        return ""


def run_ocr_on_panel(pil_image: Image.Image) -> str:
    """
    Run OCR on a single cropped panel image.
    Surya first, Tesseract fallback.
    """
    text = _ocr_with_surya(pil_image)
    if text:
        return text
    return _ocr_with_tesseract(pil_image)


def run_ocr_pipeline_full(pil_image: Image.Image) -> str:
    """
    Fallback: run OCR on the whole image (used if YOLO finds no panels).
    """
    text = _ocr_with_surya(pil_image)
    if text:
        return text
    return _ocr_with_tesseract(pil_image)


# -------------------------------------------------------------------
# YOLO PANEL DETECTION
# -------------------------------------------------------------------


def detect_panels(pil_image: Image.Image) -> Dict[int, List[Tuple[float, float, float, float]]]:
    """
    Run YOLO on the full image and return a dict:
        {class_id: [(x1, y1, x2, y2), ...], ...}
    Coordinates are in pixel space.
    """
    model = get_yolo_model()
    if model is None:
        logger.warning("YOLO model not available; skipping panel detection.")
        return {}

    results = model(pil_image, verbose=False)
    boxes_per_class: Dict[int, List[Tuple[float, float, float, float]]] = {}

    for r in results:
        if r.boxes is None:
            continue
        for b in r.boxes:
            cls_id = int(b.cls.item())
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            boxes_per_class.setdefault(cls_id, []).append((x1, y1, x2, y2))

    return boxes_per_class


def extract_panel_texts(
    pil_image: Image.Image,
    boxes_per_class: Dict[int, List[Tuple[float, float, float, float]]],
) -> Dict[str, str]:
    """
    Crop each detected panel and run OCR. Merges multiple boxes of same class.
    Returns: {class_name: "ocr text\n...", ...}
    """
    panel_texts: Dict[str, str] = {}

    if not boxes_per_class:
        # No detection; we'll fall back later.
        return panel_texts

    w, h = pil_image.size

    for cls_id, boxes in boxes_per_class.items():
        if cls_id < 0 or cls_id >= len(CLASSES):
            continue
        class_name = CLASSES[cls_id]
        texts: List[str] = []

        for (x1, y1, x2, y2) in boxes:
            # clamp
            x1c = max(0, min(w - 1, x1))
            y1c = max(0, min(h - 1, y1))
            x2c = max(0, min(w, x2))
            y2c = max(0, min(h, y2))

            crop = pil_image.crop((x1c, y1c, x2c, y2c))
            t = run_ocr_on_panel(crop)
            if t:
                texts.append(t)

        if texts:
            panel_texts[class_name] = "\n".join(texts)

    return panel_texts


# -------------------------------------------------------------------
#  2 STRUCTURING
# -------------------------------------------------------------------



def _load_():
    """
    Lazy-load  2 (9B) with 4-bit quantization.
    Only loads once and caches globally.
    """
    global __tokenizer, __model  # Reuse existing global vars to avoid breaking other refs, structurally okay
    if __tokenizer is not None and __model is not None:
        return __tokenizer, __model

    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    import torch

    model_name = "google/-2-9b-it"
    logger.info(f"Loading  2 model: {model_name} (4-bit)...")
    
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

    __tokenizer = AutoTokenizer.from_pretrained(model_name)
    __model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto"
    )
    return __tokenizer, __model


def structure_ocr_from_panels(panel_texts: Dict[str, str]) -> Dict[str, Any]:
    """
    Use  2 to convert tagged per-panel OCR into structured fields.
    """
    # if we have no panel texts, return empty structure
    if not panel_texts:
        return {
            "raw_ocr": "",
            "mrp": None,
            "net_quantity": None,
            "country_of_origin": None,
            "manufacturer_details": None,
            "importer_details": None,
            "date_of_manufacture": None,
            "date_of_import": None,
            "best_before_date": None,
            "expiry_date": None,
            "customer_care_details": None,
            "category": None,
            "unit_sale_price": None,
        }

    tokenizer, model = _load_()

    # Build a prompt with explicit tags to help the model
    segments = []
    for k, v in panel_texts.items():
        segments.append(f"[{k.upper()}]\n{v}")
    tagged_text = "\n\n".join(segments)

    # Use strict Chat Template for 
    chat = [
        { "role": "user", "content": f"""
You are a Legal Metrology packaging assistant.

You will be given OCR text from specific panels of an Indian retail product package.
Each panel is tagged (e.g., [MRP_PANEL], [NET_QUANTITY_PANEL]).

Your task is to extract key Legal Metrology fields and return ONLY valid JSON
with these exact keys:
- "mrp": string or null
- "net_quantity": string or null
- "country_of_origin": string or null
- "manufacturer_details": string or null
- "importer_details": string or null
- "date_of_manufacture": string or null
- "date_of_import": string or null
- "best_before_date": string or null
- "expiry_date": string or null
- "customer_care_details": string or null
- "category": string or null
- "unit_sale_price": string or null
- "raw_ocr": (put the input text here)

If a field is not present, set it to null.
Do not add any extra keys.
Return ONLY JSON, without explanation or backticks.

PANEL_OCR_TEXT:
{tagged_text}
""" }
    ]

    prompt = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)

    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    ).to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=1024, # Increased for larger JSON
        do_sample=False,
        temperature=0.0
    )
    
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    # Try to parse as JSON
    try:
        # Some models wrap JSON in extra text; try to find the first {...} block.
        start = decoded.find("{")
        end = decoded.rfind("}")
        if start != -1 and end != -1 and end > start:
            decoded = decoded[start : end + 1]
        data = json.loads(decoded)
        if isinstance(data, dict):
            # Ensure at least the expected keys exist and normalize
            expected_keys = [
                "mrp", "net_quantity", "country_of_origin", "manufacturer_details",
                "importer_details", "date_of_manufacture", "date_of_import",
                "best_before_date", "expiry_date", "customer_care_details",
                "category", "unit_sale_price"
            ]
            for key in expected_keys:
                data.setdefault(key, None)
            
            # Ensure raw_ocr is preserved if model missed it
            if "raw_ocr" not in data or not data["raw_ocr"]:
                data["raw_ocr"] = tagged_text
                
            return data
    except Exception as e:
        logger.warning(f"Failed to parse  output as JSON: {e}. Output was: {decoded!r}")

    # Fallback: just return raw text in minimal structure
    return {
        "raw_ocr": tagged_text,
        "mrp": None,
        "net_quantity": None,
        "country_of_origin": None,
        "manufacturer_details": None,
        "importer_details": None,
        "date_of_manufacture": None,
        "date_of_import": None,
        "best_before_date": None,
        "expiry_date": None,
        "customer_care_details": None,
        "category": None,
        "unit_sale_price": None,
    }


# -------------------------------------------------------------------
# PUBLIC ENTRYPOINT
# -------------------------------------------------------------------


def run_pipeline_for_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Entry function used by the Streamlit app.

    Args:
        image_bytes: raw bytes of the uploaded image

    Returns:
        dict with keys:
            - "structured_data": dict of extracted fields
            - "compliance_summary": dict from ComplianceValidator.validate()
            - "raw_ocr_text": combined OCR text (tagged panels)
            - "panel_texts": per-panel OCR
    """
    # 1. Load image
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # 2. YOLO panel detection
    boxes_per_class = detect_panels(pil_image)

    # 3. OCR per panel (if any boxes); otherwise fallback to full-image OCR
    panel_texts = extract_panel_texts(pil_image, boxes_per_class)

    if not panel_texts:
        logger.info("No panels detected; running OCR on full image as fallback.")
        full_text = run_ocr_pipeline_full(pil_image)
        panel_texts = {"full_image": full_text}

    # 4. Structure text with  2
    structured_data = structure_ocr_from_panels(panel_texts)

    # 5. Validate with rule engine
    validator = ComplianceValidator()
    compliance_summary = validator.validate(structured_data)

    # Build raw_ocr_text as combined panel text (for debugging/UI)
    combined_ocr = "\n\n".join(
        f"[{k}]\n{v}" for k, v in panel_texts.items() if v
    )

    return {
        "structured_data": structured_data,
        "compliance_summary": compliance_summary,
        "raw_ocr_text": combined_ocr,
        "panel_texts": panel_texts,
    }


# Optional: simple CLI test if you run this file directly
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Legal Metrology YOLO+OCR pipeline on an image.")
    parser.add_argument("image_path", type=str, help="Path to image file.")
    args = parser.parse_args()

    img_path = Path(args.image_path)
    if not img_path.exists():
        print(f"Image not found: {img_path}")
    else:
        with img_path.open("rb") as f:
            out = run_pipeline_for_image(f.read())
        print(json.dumps(out, indent=2, ensure_ascii=False))
