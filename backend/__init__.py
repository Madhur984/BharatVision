"""Backend package for inference service."""

__all__ = []
"""
Backend module for Web Crawler and Compliance Checking
Handles imports and ensures compatibility across different environments
"""

import sys
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Ensure proper path resolution
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'backend'))

# Import main modules with better error handling
try:
    from .crawler import EcommerceCrawler, ProductData
    from .schemas import ExtractedFields, ValidationResult
    __all__ = ['EcommerceCrawler', 'ProductData', 'ExtractedFields', 'ValidationResult']
except ImportError as e:
    # Partial import is acceptable - selenium is optional
    logging.info(f"Note: Some optional dependencies may not be available: {e}")
    try:
        from .schemas import ExtractedFields, ValidationResult
        __all__ = ['ExtractedFields', 'ValidationResult']
    except ImportError:
        __all__ = []

