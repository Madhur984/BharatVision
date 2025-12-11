"""Database models for BharatVision validation system"""
from datetime import datetime
from enum import Enum
import json

class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non-compliant"

class ValidationResult:
    """Model for storing validation results"""
    
    def __init__(self, 
                 product_name: str,
                 status: str,
                 compliance_score: float,
                 present_items: dict,
                 missing_items: dict,
                 flagged_items: dict,
                 ocr_text: str,
                 image_path: str = None,
                 upload_date: datetime = None,
                 id: int = None):
        
        self.id = id
        self.product_name = product_name
        self.status = status
        self.compliance_score = compliance_score
        self.present_items = present_items
        self.missing_items = missing_items
        self.flagged_items = flagged_items
        self.ocr_text = ocr_text
        self.image_path = image_path
        self.upload_date = upload_date or datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_name': self.product_name,
            'status': self.status,
            'compliance_score': self.compliance_score,
            'present_items': self.present_items,
            'missing_items': self.missing_items,
            'flagged_items': self.flagged_items,
            'ocr_text': self.ocr_text,
            'image_path': self.image_path,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

class ValidationStatistics:
    """Model for storing validation statistics"""
    
    def __init__(self, 
                 total_validations: int = 0,
                 compliant_count: int = 0,
                 non_compliant_count: int = 0,
                 average_score: float = 0.0):
        
        self.total_validations = total_validations
        self.compliant_count = compliant_count
        self.non_compliant_count = non_compliant_count
        self.average_score = average_score
    
    def to_dict(self):
        return {
            'total_validations': self.total_validations,
            'compliant_count': self.compliant_count,
            'non_compliant_count': self.non_compliant_count,
            'average_score': self.average_score
        }
