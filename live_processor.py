# live_processor.py
"""
Live OCR and Text Structuring Pipeline
Main module for the Automated Compliance Checker OCR component

NOTE: Heavy imports (YOLO, transformers, Surya) are done LAZILY inside classes
to avoid model loading at module import time. This is critical for Streamlit Cloud.
"""

# Initialize headless mode FIRST - before any OpenCV imports
import os
os.environ['OPENCV_HEADLESS'] = '1'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['MPLBACKEND'] = 'Agg'

import json
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import logging
from dotenv import load_dotenv

# Lazy import flags - actual imports happen inside classes
YOLO = None
AutoTokenizer = None
AutoModelForSeq2SeqLM = None
torch = None
CV2_AVAILABLE = False
SURYA_AVAILABLE = False

# Try cv2 (optional)
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Import configuration (lightweight)
from config import *

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelLoadError(Exception):
    """Custom exception for model loading failures"""
    pass


class LiveProcessor:
    """
    Main class for live OCR and text structuring pipeline
    """
    
    def __init__(self):
        """Initialize the LiveProcessor with all required models"""
        self.camera = None
        self.yolo_model = None
        self.nlp_tokenizer = None
        self.nlp_model = None
        self.foundation_predictor = None
        self.recognition_predictor = None
        self.detection_predictor = None
        self.models_loaded = False
        self._surya_available = False
        self._torch = None
        
        logger.info("Initializing LiveProcessor...")
        try:
            self._load_models()
            self.models_loaded = True
            logger.info("LiveProcessor initialized successfully!")
        except Exception as init_error:
            logger.warning(f"LiveProcessor initialization encountered issues: {init_error}")
            logger.warning("Application will attempt to use limited functionality.")
    
    def _is_running_on_cloud(self) -> bool:
        """Detect if running on Streamlit Cloud vs localhost"""
        import os
        if os.environ.get('STREAMLIT_SHARING_MODE'):
            return True
        if os.path.exists('/mount/src'):
            return True
        if os.environ.get('HOME', '').startswith('/home/appuser'):
            return True
        return False
    
    def _load_models(self):
        """Load all required models with comprehensive error handling - LAZY IMPORTS"""
        global SURYA_AVAILABLE
        
        # Lazy import torch
        import torch as _torch
        self._torch = _torch
        
        is_cloud = self._is_running_on_cloud()
        
        try:
            if is_cloud:
                # CLOUD MODE: Disable heavy models to save memory
                logger.info("☁️ Running on Streamlit Cloud - using lightweight mode")
                logger.info("YOLO model disabled (memory constraints)")
                self.yolo_model = None
                
                logger.info("Surya OCR disabled (memory constraints). Using Tesseract.")
                self._surya_available = False
                self.foundation_predictor = None
                self.recognition_predictor = None
                self.detection_predictor = None
            else:
                # LOCALHOST MODE: Load full models for best accuracy
                logger.info("🖥️ Running on localhost - loading full models")
                
                # Load YOLO model
                try:
                    logger.info("Loading YOLO model...")
                    from ultralytics import YOLO
                    self.yolo_model = YOLO(YOLO_MODEL_PATH)
                    logger.info("YOLO model loaded successfully")
                except Exception as yolo_err:
                    logger.warning(f"YOLO model failed to load: {yolo_err}. Continuing without YOLO.")
                    self.yolo_model = None
                
                # Load Surya OCR models
                try:
                    from surya.foundation import FoundationPredictor
                    from surya.recognition import RecognitionPredictor
                    from surya.detection import DetectionPredictor
                    SURYA_AVAILABLE = True
                    self._surya_available = True
                    logger.info("Loading Surya OCR models...")
                    
                    import os
                    os.environ['TORCH_HOME'] = str(MODEL_CACHE_DIR)
                    
                    self.foundation_predictor = FoundationPredictor(device='cpu')
                    self.recognition_predictor = RecognitionPredictor(self.foundation_predictor)
                    self.detection_predictor = DetectionPredictor(device='cpu')
                    logger.info("Surya OCR models loaded successfully")
                except ImportError as import_err:
                    logger.warning(f"Surya OCR import failed: {import_err}. Using fallback OCR.")
                    self._surya_available = False
                    self.foundation_predictor = None
                    self.recognition_predictor = None
                    self.detection_predictor = None
                except Exception as surya_error:
                    logger.warning(f"Surya OCR failed to load: {surya_error}. Using fallback OCR.")
                    self._surya_available = False
                    self.foundation_predictor = None
                    self.recognition_predictor = None
                    self.detection_predictor = None
            # Load NLP model for text structuring - lazy import
            logger.info(f"Loading NLP model: {HF_MODEL_NAME}...")
            try:
                from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
                self.nlp_tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME)
                # Use torch_dtype to avoid meta tensor issues
                self.nlp_model = AutoModelForSeq2SeqLM.from_pretrained(
                    HF_MODEL_NAME,
                    torch_dtype=_torch.float32
                )
                
                # Move to GPU if available
                if _torch.cuda.is_available() and DEVICE != 'cpu':
                    try:
                        self.nlp_model = self.nlp_model.to('cuda')
                        logger.info("NLP model moved to GPU")
                    except Exception as gpu_error:
                        logger.warning(f"Could not move to GPU: {gpu_error}. Using CPU.")
                        self.nlp_model = self.nlp_model.to('cpu')
                else:
                    self.nlp_model = self.nlp_model.to('cpu')
                
                logger.info("NLP model loaded successfully")
            except Exception as nlp_error:
                logger.error(f"Failed to load NLP model: {nlp_error}")
                self.nlp_tokenizer = None
                self.nlp_model = None
            
        except Exception as e:
            error_msg = f"Failed to load models: {str(e)}"
            logger.error(error_msg)
            # Don't raise - allow graceful degradation
            logger.warning("Some models failed to load. Application will use limited functionality.")
    
    def _initialize_camera(self) -> bool:
        """Initialize camera with error handling"""
        try:
            self.camera = cv2.VideoCapture(CAMERA_INDEX)
            if not self.camera.isOpened():
                logger.error("Cannot access camera")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            
            logger.info("Camera initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Camera initialization failed: {str(e)}")
            return False
    
    def _initialize_camera_with_index(self, camera_index: int) -> bool:
        """Initialize camera with specific index"""
        try:
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                logger.error(f"Cannot access camera at index {camera_index}")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            
            logger.info(f"Camera {camera_index} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Camera {camera_index} initialization failed: {str(e)}")
            return False
    
    def _detect_text_boxes(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect text boxes using Surya detection or YOLO model
        Returns list of detection dictionaries with bbox coordinates and confidence
        """
        try:
            if USE_YOLO_FOR_TEXT_DETECTION:
                # Use YOLO for text detection (general object detection)
                results = self.yolo_model(frame, verbose=False)
                detections = []
                
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            confidence = float(box.conf)
                            if confidence >= DETECTION_CONFIDENCE_THRESHOLD:
                                # Get bounding box coordinates
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                detections.append({
                                    'bbox': (x1, y1, x2, y2),
                                    'confidence': confidence
                                })
                
                return detections
            else:
                # Use Surya detection for text-specific detection
                if SURYA_AVAILABLE and self.detection_predictor:
                    from PIL import Image
                    
                    # Convert to PIL Image
                    if len(frame.shape) == 3:
                        if CV2_AVAILABLE:
                            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        else:
                            # Pure numpy BGR to RGB
                            pil_image = Image.fromarray(frame[:, :, ::-1].copy())
                    else:
                        pil_image = Image.fromarray(frame)
                    
                    # Run detection
                    logger.info("Running Surya text detection...")
                    predictions = self.detection_predictor([pil_image])
                    
                    detections = []
                    if predictions and len(predictions) > 0:
                        prediction = predictions[0]
                        logger.info(f"Surya detection result type: {type(prediction)}")
                        
                        # Check what attributes are available
                        if hasattr(prediction, 'bboxes'):
                            logger.info(f"Found {len(prediction.bboxes)} bboxes")
                            for i, bbox in enumerate(prediction.bboxes):
                                logger.info(f"Bbox {i}: type={type(bbox)}, content={bbox}")
                                
                                # Try different ways to access bbox coordinates
                                try:
                                    if hasattr(bbox, 'bbox'):
                                        # If it has a bbox attribute
                                        x1, y1, x2, y2 = bbox.bbox
                                    elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                                        # If it's a list/tuple of coordinates
                                        x1, y1, x2, y2 = bbox[:4]
                                    elif hasattr(bbox, 'polygon') and len(bbox.polygon) >= 4:
                                        # If it has polygon format
                                        points = bbox.polygon
                                        x_coords = [p[0] for p in points]
                                        y_coords = [p[1] for p in points]
                                        x1, y1, x2, y2 = min(x_coords), min(y_coords), max(x_coords), max(y_coords)
                                    else:
                                        logger.warning(f"Unknown bbox format: {bbox}")
                                        continue
                                    
                                    # Get confidence if available
                                    confidence = 0.9  # Default high confidence for Surya
                                    if hasattr(bbox, 'confidence'):
                                        confidence = float(bbox.confidence)
                                    elif hasattr(bbox, 'score'):
                                        confidence = float(bbox.score)
                                    
                                    if confidence >= DETECTION_CONFIDENCE_THRESHOLD:
                                        detections.append({
                                            'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                            'confidence': confidence
                                        })
                                        logger.info(f"Added detection: bbox=({x1},{y1},{x2},{y2}), conf={confidence}")
                                
                                except Exception as e:
                                    logger.error(f"Failed to process bbox {i}: {e}")
                                    continue
                        else:
                            logger.warning("No 'bboxes' attribute found in detection result")
                            logger.info(f"Available attributes: {dir(prediction)}")
                    else:
                        logger.warning("Surya detection returned no predictions")
                    
                    logger.info(f"Total detections found: {len(detections)}")
                    return detections
                else:
                    logger.warning("No text detection method available")
                    return []
            
        except Exception as e:
            logger.error(f"Text detection failed: {str(e)}")
            return []
    
    def _draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw bounding boxes and confidence scores on frame"""
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), BOX_COLOR, 2)
            
            # Draw confidence score
            label = f"{confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), BOX_COLOR, -1)
            cv2.putText(frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        return frame
    
    def _display_status(self, frame: np.ndarray, status: str) -> np.ndarray:
        """Display status text on frame"""
        # Create background rectangle for text
        text_size = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, FONT_THICKNESS)[0]
        cv2.rectangle(frame, STATUS_POSITION, 
                     (STATUS_POSITION[0] + text_size[0] + 10, STATUS_POSITION[1] + text_size[1] + 10),
                     (0, 0, 0), -1)
        
        # Display status text
        cv2.putText(frame, status, (STATUS_POSITION[0] + 5, STATUS_POSITION[1] + text_size[1] + 5),
                   cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS)
        
        return frame
    
    def _cluster_text_boxes(self, detections: List[Dict]) -> Optional[Tuple[int, int, int, int]]:
        """
        Find the largest cluster of text boxes to identify the declaration panel
        Returns the bounding box of the main text cluster or None if insufficient text
        """
        if len(detections) < MIN_TEXT_BOXES_FOR_PANEL:
            return None
        
        # Extract center points of all detections
        centers = []
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            centers.append(((x1 + x2) // 2, (y1 + y2) // 2))
        
        # Simple clustering: find the largest group of nearby text boxes
        clusters = []
        used_indices = set()
        
        for i, center in enumerate(centers):
            if i in used_indices:
                continue
                
            cluster = [i]
            used_indices.add(i)
            
            for j, other_center in enumerate(centers):
                if j in used_indices:
                    continue
                    
                # Calculate distance between centers
                distance = np.sqrt((center[0] - other_center[0])**2 + (center[1] - other_center[1])**2)
                if distance < TEXT_CLUSTER_MIN_DISTANCE:
                    cluster.append(j)
                    used_indices.add(j)
            
            clusters.append(cluster)
        
        # Find the largest cluster
        largest_cluster = max(clusters, key=len)
        
        if len(largest_cluster) < MIN_TEXT_BOXES_FOR_PANEL:
            return None
        
        # Calculate bounding box for the largest cluster
        cluster_boxes = [detections[i]['bbox'] for i in largest_cluster]
        x1 = min(box[0] for box in cluster_boxes)
        y1 = min(box[1] for box in cluster_boxes)
        x2 = max(box[2] for box in cluster_boxes)
        y2 = max(box[3] for box in cluster_boxes)
        
        return (x1, y1, x2, y2)
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Apply OpenCV preprocessing to improve OCR accuracy
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, GAUSSIAN_BLUR_KERNEL, 0)
        
        # Apply adaptive thresholding for binarization
        binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        # Apply morphological operations to clean up the image
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, MORPHOLOGY_KERNEL_SIZE)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def _extract_text_with_surya(self, image: np.ndarray) -> Optional[str]:
        """
        Extract text from image using Surya OCR
        Exactly matches the high-performance standalone implementation
        """
        try:
            if not self._surya_available or not self.recognition_predictor or not self.detection_predictor:
                logger.warning("Surya OCR not available, using fallback OCR")
                return self._extract_text_fallback(image)
                
            # Convert OpenCV numpy array to PIL Image (exactly like standalone code)
            from PIL import Image as PILImage
            
            # Convert BGR to RGB for PIL Image - use numpy if cv2 not available
            if len(image.shape) == 3:
                # BGR to RGB conversion
                if CV2_AVAILABLE:
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                else:
                    # Pure numpy BGR to RGB conversion
                    image_rgb = image[:, :, ::-1].copy()
            else:
                # If grayscale, convert to RGB
                if CV2_AVAILABLE:
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                else:
                    # Pure numpy grayscale to RGB
                    image_rgb = np.stack([image, image, image], axis=-1)
            
            # Create PIL Image exactly like standalone: image = Image.open(filename)
            pil_image = PILImage.fromarray(image_rgb)
            
            # Run Surya OCR using EXACT same API as standalone implementation
            logger.info("Performing OCR with Surya...")
            predictions = self.recognition_predictor([pil_image], det_predictor=self.detection_predictor)
            logger.info("OCR complete.")
            
            # Extract text using EXACT same logic as standalone implementation
            ocr_text_lines = []
            for page_predictions in predictions:
                for line in page_predictions.text_lines:
                    ocr_text_lines.append(line.text)
            
            # Log results exactly like standalone
            logger.info(f"OCR Results: Found {len(ocr_text_lines)} text lines")
            for i, text in enumerate(ocr_text_lines):
                logger.info(f"  {i+1}: {text}")
            
            # Join all text lines (like standalone joins them for processing)
            extracted_text = '\n'.join(ocr_text_lines).strip()
            return extracted_text if extracted_text else None
            
        except Exception as e:
            logger.error(f"Surya OCR failed: {str(e)}, trying fallback")
            return self._extract_text_fallback(image)

    def _extract_text_fallback(self, image: np.ndarray) -> Optional[str]:
        """
        Fallback OCR method using simple text extraction
        """
        try:
            # Simple fallback: save image and use basic text detection
            from PIL import Image
            
            # Convert to PIL Image
            if len(image.shape) == 2:
                pil_image = Image.fromarray(image, mode='L')
            else:
                if CV2_AVAILABLE:
                    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                else:
                    # Pure numpy BGR to RGB
                    pil_image = Image.fromarray(image[:, :, ::-1].copy())
            
            # Try to use EasyOCR as fallback
            try:
                import easyocr
                reader = easyocr.Reader(['en'], gpu=False)
                results = reader.readtext(np.array(pil_image))
                if results:
                    extracted_text = '\\n'.join([text for (bbox, text, confidence) in results if confidence > 0.3])
                    if extracted_text.strip():
                        return extracted_text.strip()
            except Exception as easyocr_error:
                logger.warning(f"EasyOCR fallback failed: {easyocr_error}")
            
            # Try pytesseract as last resort
            try:
                import pytesseract
                text = pytesseract.image_to_string(pil_image)
                if text.strip():
                    return text.strip()
            except Exception as tess_error:
                logger.warning(f"Tesseract fallback failed: {tess_error}")
            
            logger.warning("All OCR fallbacks failed")
            return None
            
        except Exception as e:
            logger.error(f"Fallback OCR also failed: {str(e)}")
            return None
    
    def _structure_text_with_nlp(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Structure extracted text using transformer model with better prompting
        """
        try:
            # Use regex-first extraction, NLP as supplement
            # This is more reliable than pure NLP for structured data
            structured_data = self._construct_json_from_text(raw_text)
            
            # Only use NLP for fields that regex couldn't extract
            if self.nlp_model and self.nlp_tokenizer:
                # Try to extract specific missing fields with targeted prompts
                missing_fields = [k for k, v in structured_data.items() if v is None]
                
                for field in missing_fields[:5]:  # Limit to avoid too many API calls
                    try:
                        value = self._extract_single_field_with_nlp(raw_text, field)
                        if value and value.lower() not in ['null', 'none', 'n/a', '']:
                            structured_data[field] = value
                    except Exception as e:
                        logger.warning(f"NLP extraction failed for {field}: {e}")
                        continue
            
            return structured_data
            
        except Exception as e:
            logger.error(f"NLP structuring failed: {str(e)}")
            return self._construct_json_from_text(raw_text)
    
    def _extract_single_field_with_nlp(self, text: str, field: str) -> Optional[str]:
        """Extract a single field using targeted NLP prompt"""
        field_prompts = {
            'mrp': f"What is the MRP (Maximum Retail Price) in this text? Answer with just the price value or 'none': {text[:500]}",
            'net_quantity': f"What is the net quantity/weight in this text? Answer with just the quantity or 'none': {text[:500]}",
            'manufacturer_details': f"Who is the manufacturer in this text? Answer with just the company name or 'none': {text[:500]}",
            'date_of_manufacture': f"What is the manufacturing date in this text? Answer with just the date or 'none': {text[:500]}",
            'best_before_date': f"What is the expiry/best before date in this text? Answer with just the date or 'none': {text[:500]}",
            'country_of_origin': f"What is the country of origin in this text? Answer with just the country name or 'none': {text[:500]}",
        }
        
        prompt = field_prompts.get(field)
        if not prompt:
            return None
            
        try:
            inputs = self.nlp_tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
            
            with self._torch.no_grad():
                outputs = self.nlp_model.generate(
                    **inputs,
                    max_new_tokens=50,  # Short output for single field
                    do_sample=False,
                    num_beams=1,
                    pad_token_id=self.nlp_tokenizer.eos_token_id
                )
            
            result = self.nlp_tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            
            # Clean up result
            if result.lower() in ['none', 'null', 'n/a', 'not found', 'not mentioned', '']:
                return None
            return result
            
        except Exception as e:
            logger.warning(f"Single field NLP extraction failed: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Text structuring failed: {str(e)}")
            return self._construct_json_from_text(raw_text)
    
    def _construct_json_from_text(self, raw_text: str) -> Dict[str, Any]:
        """
        Fallback method to extract structured data using simple pattern matching
        """
        import re
        
        structured_data = {}
        text_lower = raw_text.lower()
        
        # Initialize all fields as null
        for field in EXPECTED_FIELDS:
            structured_data[field] = None
        
        # Simple pattern matching for common fields
        try:
            # MRP extraction
            mrp_match = re.search(r'mrp[:\s]*rs?\.?\s*(\d+(?:\.\d+)?)', text_lower)
            if mrp_match:
                structured_data['mrp'] = f"Rs. {mrp_match.group(1)}"
            
            # Date extraction
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', raw_text)
            if date_match:
                structured_data['date_of_manufacture'] = date_match.group(1)
            
            # Country extraction
            if 'india' in text_lower:
                structured_data['country_of_origin'] = 'India'
            
            # Store the raw text as contents if no specific content field found
            structured_data['contents'] = raw_text
            
        except Exception as e:
            logger.error(f"Pattern matching failed: {str(e)}")
        
        return structured_data
    
    def process_single_capture(self, camera_index: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Process a single frame capture for orchestration workflow
        1. Capture image first
        2. Detect boxes on captured image  
        3. Apply OCR to detected boxes
        4. Save images in directories
        5. Extract and structure text
        
        Args:
            camera_index: Optional camera index to use. If None, uses default from config.
        
        Returns:
            Dict: Structured data from OCR processing, or None if capture failed/cancelled
        """
        import os
        from datetime import datetime
        
        # Use provided camera index or default
        if camera_index is not None:
            self.camera_index = camera_index
        
        if not self._initialize_camera_with_index(camera_index or CAMERA_INDEX):
            print(f"Error: {STATUS_MESSAGES['camera_error']}")
            return None
        
        print("🎥 Camera ready! Position product label and press SPACE to capture...")
        print("Press 'q' to cancel and return to main menu")
        
        captured_result = None
        
        try:
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    print("Failed to read frame from camera")
                    break
                
                # Show clean camera feed without live detection boxes
                display_frame = frame.copy()
                
                # Add simple capture instruction overlay
                cv2.putText(display_frame, "Press SPACE to capture, Q to quit", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Show frame
                cv2.imshow('Single Capture Mode', display_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("❌ Capture cancelled by user")
                    break
                elif key == ord(' '):
                    print("📸 Image captured! Processing...")
                    
                    # Generate timestamp for file naming
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Save captured image
                    captured_path = f"images/captured/capture_{timestamp}.jpg"
                    cv2.imwrite(captured_path, frame)
                    print(f"� Captured image saved: {captured_path}")
                    
                    # Process the captured frame
                    result = self._process_captured_image_with_detection(frame, timestamp)
                    
                    if result is None:
                        print("❌ No text detected in captured frame")
                    elif result == "ocr_failed":
                        print("❌ OCR processing failed")
                    elif result == "structuring_failed":
                        print("❌ Text structuring failed")
                    else:
                        print("✅ Frame processed successfully!")
                        captured_result = result
                        break  # Exit loop with successful result
                
        except KeyboardInterrupt:
            print("\n❌ Capture interrupted by user")
        
        finally:
            # Cleanup
            if self.camera:
                self.camera.release()
            cv2.destroyAllWindows()
            
        return captured_result
    
    def run_live_capture(self):
        """
        Main method to run the live camera capture and processing loop
        """
        if not self._initialize_camera():
            print(f"Error: {STATUS_MESSAGES['camera_error']}")
            return
        
        print("Live OCR Pipeline Started!")
        print("Controls:")
        print("- SPACE: Capture image and process with detection boxes")
        print("- 'q': Quit")
        print("- 'r': Reset/Continue")
        print("📸 Images will be saved to captured/ and processed/ directories")
        
        current_status = STATUS_MESSAGES['ready']
        
        try:
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    print("Failed to read frame from camera")
                    break
                
                # Create a copy for display
                display_frame = frame.copy()
                
                # Run real-time text detection for visual feedback
                if current_status == STATUS_MESSAGES['ready']:
                    detections = self._detect_text_boxes(frame)
                    display_frame = self._draw_detections(display_frame, detections)
                
                # Display status
                display_frame = self._display_status(display_frame, current_status)
                
                # Show frame
                cv2.imshow('Live OCR Pipeline', display_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    current_status = STATUS_MESSAGES['ready']
                elif key == ord(' ') and current_status == STATUS_MESSAGES['ready']:
                    # Capture and process frame
                    current_status = STATUS_MESSAGES['processing']
                    
                    # Update display immediately
                    display_frame = self._display_status(display_frame, current_status)
                    cv2.imshow('Live OCR Pipeline', display_frame)
                    cv2.waitKey(1)
                    
                    # Process the captured frame
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Save captured image
                    captured_path = f"images/captured/capture_{timestamp}.jpg"
                    cv2.imwrite(captured_path, frame)
                    print(f"💾 Captured image saved: {captured_path}")
                    
                    result = self._process_captured_image_with_detection(frame, timestamp)
                    
                    if result is None:
                        current_status = STATUS_MESSAGES['no_text']
                    elif result == "ocr_failed":
                        current_status = STATUS_MESSAGES['ocr_failed']
                    elif result == "structuring_failed":
                        current_status = STATUS_MESSAGES['structuring_failed']
                    else:
                        current_status = STATUS_MESSAGES['success']
                        print("\n" + "="*50)
                        print("STRUCTURED OCR RESULT:")
                        print("="*50)
                        print(json.dumps(result, indent=2, ensure_ascii=False))
                        print("="*50 + "\n")
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        
        finally:
            # Cleanup
            if self.camera:
                self.camera.release()
            cv2.destroyAllWindows()
            print("Pipeline stopped successfully")
    
    def _process_captured_image_with_detection(self, frame: np.ndarray, timestamp: str) -> Optional[Dict[str, Any]]:
        """
        Process a captured image - simplified to match standalone approach
        Just like your standalone: capture image, run OCR directly, no detection step
        
        Args:
            frame: Captured frame to process
            timestamp: Timestamp for file naming
        
        Returns:
            Structured data or error codes
        """
        # Save processed image (just the original for now)
        processed_path = f"images/processed/processed_{timestamp}.jpg"
        cv2.imwrite(processed_path, frame)
        print(f"🔍 Processed image saved: {processed_path}")
        
        # Extract text using Surya OCR directly on full image (like standalone)
        print("Performing OCR with Surya...")
        extracted_text = self._extract_text_with_surya(frame)
        print("OCR complete.")
        
        if not extracted_text:
            logger.warning("OCR failed to extract text")
            return "ocr_failed"
        
        # Count text lines like standalone
        text_lines = extracted_text.split('\n')
        text_lines = [line.strip() for line in text_lines if line.strip()]
        print(f"\nOCR Results: Found {len(text_lines)} text lines")
        for i, line in enumerate(text_lines):
            print(f"  {i+1}: {line}")
        
        logger.info(f"Extracted text: {extracted_text[:100]}...")  # Log first 100 chars
        
        # Structure the text using NLP
        structured_data = self._structure_text_with_nlp(extracted_text)
        
        if structured_data is None:
            logger.warning("Failed to structure extracted text")
            return "structuring_failed"
        
        return structured_data


def main():
    """Main function to run the live processor"""
    try:
        processor = LiveProcessor()
        processor.run_live_capture()
    except ModelLoadError as e:
        print(f"Failed to initialize: {e}")
        print("Please check your internet connection and try again.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.exception("Unexpected error occurred")


if __name__ == "__main__":
    main()