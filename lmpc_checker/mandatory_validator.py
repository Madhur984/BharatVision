"""
Focused Legal Metrology Compliance Validator
Validates ONLY the 7 mandatory fields for efficient batch processing
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import re

@dataclass
class FieldValidation:
    field_name: str
    required: bool
    violated: bool
    details: str
    severity: str = "critical"

class MandatoryFieldsValidator:
    """Fast validator for 7 mandatory Legal Metrology fields"""
    
    MANDATORY_FIELDS = [
        'manufacturer',  # Name and address of manufacturer/importer
        'country_of_origin',  # Country of origin
        'generic_name',  # Common/generic name of commodity
        'net_quantity',  # Net quantity in standard units
        'mrp',  # Maximum Retail Price
        'best_before',  # Best before date
        'consumer_care'  # Customer care information
    ]
    
    def __init__(self):
        self.field_patterns = {
            'net_quantity': r'\d+\.?\d*\s*(?:g|kg|ml|l|liter|litre)',
            'mrp': r'\d+\.?\d*',
            'fssai_license': r'\d{14}',
        }
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate only mandatory fields - optimized for batch processing"""
        results = []
        violations = 0
        
        for field in self.MANDATORY_FIELDS:
            validation = self._validate_field(field, data)
            results.append(validation)
            if validation.violated:
                violations += 1
        
        return {
            'overall_status': 'COMPLIANT' if violations == 0 else 'VIOLATION',
            'total_rules': len(self.MANDATORY_FIELDS),
            'violations_count': violations,
            'violations': [r for r in results if r.violated],
            'rule_results': results
        }
    
    def _validate_field(self, field: str, data: Dict[str, Any]) -> FieldValidation:
        """Validate a single field"""
        value = data.get(field)
        
        # Check if field is missing or empty
        if not value or (isinstance(value, str) and not value.strip()):
            return FieldValidation(
                field_name=field,
                required=True,
                violated=True,
                details=f"Missing mandatory field: {field.replace('_', ' ').title()}",
                severity="critical"
            )
        
        # Field-specific validation
        if field == 'net_quantity':
            return self._validate_net_quantity(value)
        elif field == 'mrp':
            return self._validate_mrp(value)
        elif field == 'manufacturer':
            return self._validate_manufacturer(value)
        elif field == 'country_of_origin':
            return self._validate_country(value)
        elif field == 'generic_name':
            return self._validate_generic_name(value)
        elif field == 'best_before':
            return self._validate_best_before(value)
        elif field == 'consumer_care':
            return self._validate_consumer_care(value)
        
        # Default: field present
        return FieldValidation(
            field_name=field,
            required=True,
            violated=False,
            details="Field present and valid",
            severity="low"
        )
    
    def _validate_net_quantity(self, value: str) -> FieldValidation:
        """Net quantity must have number + unit"""
        if not re.search(self.field_patterns['net_quantity'], str(value), re.I):
            return FieldValidation(
                field_name='net_quantity',
                required=True,
                violated=True,
                details=f"Invalid format: '{value}'. Must include number and unit (g, kg, ml, L)",
                severity="critical"
            )
        return FieldValidation('net_quantity', True, False, "Valid format")
    
    def _validate_mrp(self, value: str) -> FieldValidation:
        """MRP must be a valid number"""
        value_str = str(value).replace(',', '').replace('₹', '').replace('Rs', '').strip()
        if not re.match(self.field_patterns['mrp'], value_str):
            return FieldValidation(
                field_name='mrp',
                required=True,
                violated=True,
                details=f"Invalid MRP format: '{value}'",
                severity="critical"
            )
        return FieldValidation('mrp', True, False, "Valid price")
    
    def _validate_manufacturer(self, value: str) -> FieldValidation:
        """Manufacturer should include name and ideally address"""
        if len(str(value).strip()) < 10:
            return FieldValidation(
                field_name='manufacturer',
                required=True,
                violated=True,
                details=f"Manufacturer info too short: '{value}'. Should include full name and address",
                severity="high"
            )
        return FieldValidation('manufacturer', True, False, "Sufficient detail")
    
    def _validate_country(self, value: str) -> FieldValidation:
        """Country should be a valid country name"""
        if len(str(value).strip()) < 3:
            return FieldValidation(
                field_name='country_of_origin',
                required=True,
                violated=True,
                details=f"Invalid country: '{value}'",
                severity="critical"
            )
        return FieldValidation('country_of_origin', True, False, "Valid country")
    
    def _validate_generic_name(self, value: str) -> FieldValidation:
        """Generic name should be present"""
        if len(str(value).strip()) < 2:
            return FieldValidation(
                field_name='generic_name',
                required=True,
                violated=True,
                details=f"Generic name too short: '{value}'",
                severity="high"
            )
        return FieldValidation('generic_name', True, False, "Valid name")
    
    def _validate_best_before(self, value: str) -> FieldValidation:
        """Best before should have some date info"""
        value_str = str(value).strip()
        # Look for month patterns or numbers that could be dates
        has_date_pattern = re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d+ months?|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec', value_str, re.I)
        if not has_date_pattern and len(value_str) < 5:
            return FieldValidation(
                field_name='best_before',
                required=True,
                violated=True,
                details=f"Best before info unclear: '{value}'",
                severity="high"
            )
        return FieldValidation('best_before', True, False, "Date info present")
    
    def _validate_consumer_care(self, value: str) -> FieldValidation:
        """Consumer care should have contact info"""
        value_str = str(value).strip()
        # Look for phone pattern or email
        has_contact = re.search(r'\d{10,}|@|toll.?free|helpline|\d{3,4}[-\s]\d{3,4}', value_str, re.I)
        if not has_contact and len(value_str) < 8:
            return FieldValidation(
                field_name='consumer_care',
                required=True,
                violated=True,
                details=f"Consumer care info incomplete: '{value}'",
                severity="high"
            )
        return FieldValidation('consumer_care', True, False, "Contact info present")

# Singleton instance for batch processing
_validator_instance = None

def get_validator() -> MandatoryFieldsValidator:
    """Get singleton validator instance for efficient batch processing"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = MandatoryFieldsValidator()
    return _validator_instance
