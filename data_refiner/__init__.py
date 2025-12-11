# data_refiner/__init__.py
"""
Data Refinement and Formatting Module for Compliance JSON

This module takes messy OCR output from the ocr_pipeline and produces
clean, structured JSON ready for compliance validation.
"""

from .refiner import DataRefiner

__version__ = "1.0.0"
__author__ = "OCR Pipeline Team"

__all__ = ["DataRefiner"]