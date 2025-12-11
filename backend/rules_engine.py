"""
Legal Metrology Compliance Rules Engine
Validates products against Indian legal metrology standards
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ValidationIssue:
    field: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    rule_id: str

@dataclass
class ValidationResult:
    is_compliant: bool
    score: float
    issues: List[ValidationIssue]
    warnings: List[str]

def load_rules() -> Dict[str, Any]:
    """Load legal metrology compliance rules"""
    return {
        "mrp_required": True,
        "quantity_required": True,
        "expiry_required": True,
        "manufacturer_required": True,
        "ingredients_required": True,
        "min_font_size": 2.0,  # mm
        "date_format": "DD/MM/YYYY"
    }

def validate(product_data: Dict[str, Any]) -> ValidationResult:
    """
    Validate product against legal metrology rules
    """
    issues = []
    warnings = []
    score = 100
    
    # Check MRP
    if not product_data.get('mrp'):
        issues.append(ValidationIssue(
            field='mrp',
            severity='error',
            message='MRP (Maximum Retail Price) is required',
            rule_id='MRP_001'
        ))
        score -= 15
    
    # Check Quantity
    if not product_data.get('quantity'):
        issues.append(ValidationIssue(
            field='quantity',
            severity='error',
            message='Net quantity must be displayed',
            rule_id='QTY_001'
        ))
        score -= 20
    
    # Check Expiry
    if not product_data.get('expiry_date'):
        warnings.append('Expiry date not found - may not be applicable for all products')
        score -= 5
    
    # Check Manufacturer
    if not product_data.get('manufacturer'):
        warnings.append('Manufacturer information missing')
        score -= 10
    
    # Check Ingredients (for food items)
    if product_data.get('category', '').lower() in ['food', 'beverages', 'snacks']:
        if not product_data.get('ingredients'):
            warnings.append('Ingredients list not found')
            score -= 10
    
    score = max(0, min(100, score))
    
    is_compliant = len([i for i in issues if i.severity == 'error']) == 0 and score >= 60
    
    return ValidationResult(
        is_compliant=is_compliant,
        score=score,
        issues=issues,
        warnings=warnings
    )

def validate_label_text(text: str) -> Dict[str, bool]:
    """Check if extracted text contains required elements"""
    text_lower = text.lower()
    
    return {
        'has_mrp': 'mrp' in text_lower or 'price' in text_lower,
        'has_quantity': any(q in text_lower for q in ['ml', 'g', 'kg', 'liter', 'litre']),
        'has_expiry': any(e in text_lower for e in ['exp', 'expiry', 'best before', 'best by']),
        'has_manufacturer': any(m in text_lower for m in ['mfg', 'manufactured', 'made by', 'packed by']),
        'has_brand': len(text_lower.split()) > 2  # Basic brand check
    }

def calculate_compliance_score(validation_result: ValidationResult) -> float:
    """Calculate final compliance percentage"""
    base_score = validation_result.score
    
    # Reduce score for warnings
    warning_reduction = len(validation_result.warnings) * 5
    
    # Reduce score for issues
    issue_reduction = len([i for i in validation_result.issues if i.severity == 'error']) * 15
    
    final_score = max(0, base_score - warning_reduction - issue_reduction)
    return min(100, final_score)
