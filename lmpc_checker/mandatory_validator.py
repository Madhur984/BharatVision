"""
Focused Legal Metrology Compliance Validator

Validates ONLY the 6 mandatory fields as per Legal Metrology (Packaged Commodities) Rules, 2011:
1. Name and address of manufacturer/importer
2. Country of origin (if imported)
3. Common, generic name of the commodity
4. Net quantity in standard unit
5. MRP including all taxes
6. Best before/use by date (for time-sensitive commodities)
"""

from typing import Dict, Any, List
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
    """Validator for 6 mandatory Legal Metrology fields"""
    
    MANDATORY_FIELDS = [
        'manufacturer_details',  # Name and address of manufacturer/importer
        'country_of_origin',     # Country of origin (if imported)
        'generic_name',          # Common/generic name of commodity
        'net_quantity',          # Net quantity in standard units
        'mrp',                   # Maximum Retail Price including all taxes
        'best_before_date',      # Best before/use by date (for time-sensitive items)
        'date_of_manufacture',   # Date of manufacture or import
        'unit_sale_price'        # Unit sale price (for packaged commodities)
    ]
    
    def __init__(self):
        self.field_patterns = {
            'net_quantity': r'\d+\.?\d*\s*(?:g|kg|ml|l|liter|litre|cm|m|unit|units|pc|pcs|piece|pieces)',
            'mrp': r'\d+\.?\d*',
        }
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate only mandatory fields"""
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
            # Special case: country_of_origin only required if imported
            if field == 'country_of_origin':
                importer = data.get('importer_details')
                if not importer or not str(importer).strip():
                    # Not imported, so country of origin not mandatory
                    return FieldValidation(
                        field_name=field,
                        required=False,
                        violated=False,
                        details="Not required (product not imported)",
                        severity="low"
                    )
            
            # Special case: best_before only required for time-sensitive items
            if field == 'best_before_date':
                category = str(data.get('category', '')).lower()
                is_time_sensitive = any(k in category for k in ['food', 'beverage', 'snack', 'cosmetic', 'medicine'])
                if not is_time_sensitive:
                    return FieldValidation(
                        field_name=field,
                        required=False,
                        violated=False,
                        details="Not required (non-perishable item)",
                        severity="low"
                    )
            
            # Special case: date_of_manufacture - check if date_of_import exists
            if field == 'date_of_manufacture':
                import_date = data.get('date_of_import')
                if import_date and str(import_date).strip():
                    # Has import date, so manufacture date not strictly required
                    return FieldValidation(
                        field_name=field,
                        required=False,
                        violated=False,
                        details="Date of import provided instead",
                        severity="low"
                    )
            
            # Special case: unit_sale_price only required for certain categories
            if field == 'unit_sale_price':
                category = str(data.get('category', '')).lower()
                requires_unit_price = any(k in category for k in ['food', 'beverage', 'grocery', 'snack'])
                if not requires_unit_price:
                    return FieldValidation(
                        field_name=field,
                        required=False,
                        violated=False,
                        details="Not required for this category",
                        severity="low"
                    )
            
            return FieldValidation(
                field_name=field,
                required=True,
                violated=True,
                details=f"Missing mandatory field: {self._get_field_label(field)}",
                severity="critical"
            )
        
        # Field-specific validation
        if field == 'net_quantity':
            return self._validate_net_quantity(value)
        elif field == 'mrp':
            return self._validate_mrp(value)
        elif field == 'manufacturer_details':
            return self._validate_manufacturer(value)
        elif field == 'country_of_origin':
            return self._validate_country(value)
        elif field == 'generic_name':
            return self._validate_generic_name(value)
        elif field == 'best_before_date':
            return self._validate_best_before(value)
        elif field == 'date_of_manufacture':
            return self._validate_date_of_manufacture(value)
        elif field == 'unit_sale_price':
            return self._validate_unit_sale_price(value)
        
        # Default: field present
        return FieldValidation(
            field_name=field,
            required=True,
            violated=False,
            details="Field present and valid",
            severity="low"
        )
    
    def _get_field_label(self, field: str) -> str:
        """Get human-readable field label"""
        labels = {
            'manufacturer_details': 'Name and address of manufacturer/importer',
            'country_of_origin': 'Country of origin',
            'generic_name': 'Common/generic name of commodity',
            'net_quantity': 'Net quantity in standard unit',
            'mrp': 'MRP including all taxes',
            'best_before_date': 'Best before/use by date'
        }
        return labels.get(field, field.replace('_', ' ').title())
    
    def _validate_net_quantity(self, value: str) -> FieldValidation:
        """Net quantity must have number + unit"""
        if not re.search(self.field_patterns['net_quantity'], str(value), re.I):
            return FieldValidation(
                field_name='net_quantity',
                required=True,
                violated=True,
                details=f"Invalid format: '{value}'. Must include number and unit (g, kg, ml, L, etc.)",
                severity="critical"
            )
        return FieldValidation('net_quantity', True, False, "Valid format")
    
    def _validate_mrp(self, value: str) -> FieldValidation:
        """MRP must be a valid number"""
        value_str = str(value).replace(',', '').replace('₹', '').replace('Rs', '').replace('.', '', 1).strip()
        if not value_str.replace('.', '').isdigit():
            return FieldValidation(
                field_name='mrp',
                required=True,
                violated=True,
                details=f"Invalid MRP format: '{value}'",
                severity="critical"
            )
        return FieldValidation('mrp', True, False, "Valid price")
    
    def _validate_manufacturer(self, value: str) -> FieldValidation:
        """Manufacturer should include name and address"""
        if len(str(value).strip()) < 10:
            return FieldValidation(
                field_name='manufacturer_details',
                required=True,
                violated=True,
                details=f"Manufacturer info too short: '{value}'. Should include full name and address",
                severity="high"
            )
        return FieldValidation('manufacturer_details', True, False, "Sufficient detail")
    
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
        """Best before should have date info"""
        value_str = str(value).strip()
        # Look for date patterns
        has_date_pattern = re.search(
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d+ months?|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec',
            value_str, re.I
        )
        if not has_date_pattern and len(value_str) < 5:
            return FieldValidation(
                field_name='best_before_date',
                required=True,
                violated=True,
                details=f"Best before info unclear: '{value}'",
                severity="high"
            )
        return FieldValidation('best_before_date', True, False, "Date info present")
    
    def _validate_date_of_manufacture(self, value: str) -> FieldValidation:
        """Date of manufacture should have date info"""
        value_str = str(value).strip()
        # Look for date patterns
        has_date_pattern = re.search(
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d+ months?|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec',
            value_str, re.I
        )
        if not has_date_pattern and len(value_str) < 5:
            return FieldValidation(
                field_name='date_of_manufacture',
                required=True,
                violated=True,
                details=f"Date of manufacture info unclear: '{value}'",
                severity="high"
            )
        return FieldValidation('date_of_manufacture', True, False, "Date info present")
    
    def _validate_unit_sale_price(self, value: str) -> FieldValidation:
        """Unit sale price should be a valid price"""
        value_str = str(value).replace(',', '').replace('₹', '').replace('Rs', '').replace('.', '', 1).strip()
        if not value_str.replace('.', '').isdigit():
            return FieldValidation(
                field_name='unit_sale_price',
                required=True,
                violated=True,
                details=f"Invalid unit sale price format: '{value}'",
                severity="high"
            )
        return FieldValidation('unit_sale_price', True, False, "Valid price")


# Singleton instance for batch processing
_validator_instance = None

def get_validator() -> MandatoryFieldsValidator:
    """Get singleton validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = MandatoryFieldsValidator()
    return _validator_instance
