# config.py
"""
Configuration file for the OCR Pipeline
Contains all model paths, thresholds, and parameters
"""

import os
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent

# Model Configuration
YOLO_MODEL_PATH = PROJECT_ROOT / 'yolov8n.pt'  # Use absolute path from project root
# HF_MODEL_NAME removed - using compliance validator instead
# HF_MODEL_NAME = 'google/gemma-2-9b-it'  # Deprecated - using compliance validator now
SURYA_LANG_CODES = ['en', 'hi']  # English and Hindi support

# Since YOLOv8n isn't trained for text detection, we'll rely on Surya for both detection and recognition
USE_YOLO_FOR_TEXT_DETECTION = False  # Set to False to use only Surya

# Detection Thresholds
DETECTION_CONFIDENCE_THRESHOLD = 0.4
TEXT_CLUSTER_MIN_DISTANCE = 50  # Minimum distance to group text boxes
MIN_TEXT_BOXES_FOR_PANEL = 3  # Minimum text boxes to consider a valid panel

# Camera Configuration
CAMERA_INDEX = 0  # Default camera
DEFAULT_CAMERA_INDEX = 0  # Default camera index for Streamlit interface
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# GUI Configuration
ENABLE_GUI = True  # Set to False for headless mode
HEADLESS_MODE = False  # Automatically detected based on GUI availability

# Image Processing
GAUSSIAN_BLUR_KERNEL = (5, 5)
MORPHOLOGY_KERNEL_SIZE = (3, 3)
PERSPECTIVE_CORRECTION_MARGIN = 20

# UI Configuration
FONT_SCALE = 0.7
FONT_THICKNESS = 2
BOX_COLOR = (0, 255, 0)  # Green for detection boxes
TEXT_COLOR = (255, 255, 255)  # White for status text
STATUS_POSITION = (10, 30)

# NLP Configuration
MAX_INPUT_LENGTH = 512
MAX_OUTPUT_LENGTH = 256
GENERATION_TEMPERATURE = 0.1  # Low temperature for more deterministic output

# Structured Data Fields
EXPECTED_FIELDS = [
    'product_id',
    'category', 
    'manufacturer_details',
    'importer_details',
    'net_quantity',
    'mrp',
    'unit_sale_price',
    'country_of_origin',
    'date_of_manufacture',
    'date_of_import',
    'best_before_date',
    'consumer_care',
    'dimensions',
    'contents'
]

# System Configuration
DEVICE = 'cuda' if os.getenv('DEVICE') == 'cuda' else 'auto'  # auto will use GPU if available
PROJECT_ROOT = Path(__file__).parent
MODEL_CACHE_DIR = PROJECT_ROOT / "models"

# Ensure model cache directory exists
MODEL_CACHE_DIR.mkdir(exist_ok=True)

# Status Messages
STATUS_MESSAGES = {
    'ready': 'Ready. Press SPACE to capture.',
    'processing': 'Processing, please wait...',
    'no_text': 'Error: No text detected. Please try again.',
    'ocr_failed': 'Error: OCR failed. Please try again.',
    'structuring_failed': 'Error: Failed to structure data.',
    'success': 'Success! Check console for results.',
    'camera_error': 'Error: Cannot access camera.',
    'model_loading': 'Loading models, please wait...'
}