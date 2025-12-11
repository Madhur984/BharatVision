import os
import logging
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Optional
import io
import torch

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock keys/config if needed or load from env
HF_MODEL_NAME = "google/gemma-2b-it" # Or whatever was in config.py
YOLO_MODEL_PATH = "yolov8n.pt" # Ensure this file is available or downloaded

class MLProcessor:
    def __init__(self):
        self.yolo_model = None
        self.foundation_predictor = None
        self.recognition_predictor = None
        self.detection_predictor = None
        self.nlp_tokenizer = None
        self.nlp_model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

    def load_models(self):
        """Load all models. Call this on startup."""
        logger.info("Loading ML models...")
        
        # 1. Load YOLO
        try:
            from ultralytics import YOLO
            # check if yolo weights exist, if not let YOLO download or fail gracefully if needed
            self.yolo_model = YOLO(YOLO_MODEL_PATH) 
            logger.info("YOLO model loaded.")
        except Exception as e:
            logger.error(f"Failed to load YOLO: {e}")

        # 2. Load Surya OCR
        try:
            from surya.foundation import FoundationPredictor
            from surya.recognition import RecognitionPredictor
            from surya.detection import DetectionPredictor
            
            self.foundation_predictor = FoundationPredictor(device=self.device)
            self.recognition_predictor = RecognitionPredictor(self.foundation_predictor)
            self.detection_predictor = DetectionPredictor(device=self.device)
            logger.info("Surya OCR models loaded.")
        except Exception as e:
            logger.error(f"Failed to load Surya OCR: {e}")

        # 3. Load NLP (Gemma/Transformers)
        # Note: Heavy model. Ensure cloud has RAM.
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            # Using a smaller model or the same one as before? 
            # The original code referenced HF_MODEL_NAME. 
            # If strictly text structuring, maybe a smaller model is fine.
            # For now, we wrap it in try/except to not block boot if OOM.
            self.nlp_tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME)
            self.nlp_model = AutoModelForSeq2SeqLM.from_pretrained(HF_MODEL_NAME, torch_dtype=torch.float32)
            self.nlp_model.to(self.device)
            logger.info("NLP model loaded.")
        except Exception as e:
             logger.warning(f"Failed to load NLP model: {e}. Structuring might be limited.")

    def process_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Full pipeline: Detection -> OCR -> Structuring
        """
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(image)
        
        # 1. Detection (YOLO) - Optional for pure text extraction but good for finding regions
        detections = []
        if self.yolo_model:
            results = self.yolo_model(img_np, verbose=False)
            for result in results:
                if result.boxes:
                    for box in result.boxes:
                        detections.append({
                            "bbox": box.xyxy[0].tolist(),
                            "conf": float(box.conf),
                            "cls": int(box.cls)
                        })
        
        # 2. OCR (Surya)
        raw_text = ""
        if self.recognition_predictor and self.detection_predictor:
            predictions = self.recognition_predictor([image], det_predictor=self.detection_predictor)
            text_lines = []
            for page in predictions:
                for line in page.text_lines:
                    text_lines.append(line.text)
            raw_text = "\n".join(text_lines)
        else:
            raw_text = "OCR Engine not available."

        # 3. Structuring (NLP + Regex)
        structured_data = self._structure_data(raw_text)

        return {
            "raw_text": raw_text,
            "structured_data": structured_data,
            "detections": detections
        }

    def _structure_data(self, text: str) -> Dict[str, Any]:
        # Basic regex parsing similar to original
        import re
        data = {}
        
        # Simple regex examples from original code
        mrp_match = re.search(r'mrp[:\s]*rs?\.?\s*(\d+(?:\.\d+)?)', text.lower())
        if mrp_match:
            data['mrp'] = f"Rs. {mrp_match.group(1)}"
            
        data['raw_text'] = text
        
        # If NLP model is available, could refine here
        # ...
        
        return data

# Singleton
processor = MLProcessor()
