# Legal Metrology Compliance Checker

## Mandatory Declarations Validated

This compliance checker validates the **8 mandatory declarations** as per Legal Metrology (Packaged Commodities) Rules, 2011:

### 1. Name and Address of Manufacturer/Importer ✓
- **Field**: `manufacturer_details` or `importer_details`
- **Requirement**: Full name and address must be present
- **Validation**: Minimum 10 characters

### 2. Country of Origin (if imported) ✓
- **Field**: `country_of_origin`
- **Requirement**: Mandatory only for imported products
- **Validation**: Valid country name (minimum 3 characters)

### 3. Common, Generic Name of the Commodity ✓
- **Field**: `generic_name`
- **Requirement**: Generic/common name must be present
- **Validation**: Minimum 2 characters

### 4. Net Quantity in Standard Unit ✓
- **Field**: `net_quantity`
- **Requirement**: Quantity with standard unit (W or M or number)
- **Valid Units**: g, kg, ml, L, cm, m, units, pieces
- **Format**: Number + Unit (e.g., "500g", "1L", "10 units")

### 5. MRP Including All Taxes ✓
- **Field**: `mrp`
- **Requirement**: Maximum Retail Price must be displayed
- **Format**: ₹XX.XX or Rs. XX or plain number
- **Validation**: Must be a valid positive number

### 6. Best Before/Use By Date ✓
- **Field**: `best_before_date` or `expiry_date`
- **Requirement**: Mandatory for commodities that become unfit over time
- **Applies to**: Food, beverages, snacks, cosmetics, medicines
- **Format**: Date, month, and year

### 7. Date of Manufacture or Import ✓
- **Field**: `date_of_manufacture` or `date_of_import`
- **Requirement**: At least one must be present
- **Format**: Date, month, and year

### 8. Unit Sale Price ✓
- **Field**: `unit_sale_price`
- **Requirement**: Mandatory for packaged commodities (food, beverages, grocery)
- **Format**: Price per unit (e.g., "₹50/kg")

---

## OCR Configuration

### E-commerce Platforms
- **Behavior**: Skip image OCR processing
- **Reason**: Use scraped product data directly
- **Platforms**: Amazon, Flipkart, JioMart, Myntra, Snapdeal

### Image Upload & Batch Processing
- **OCR Engine**: Surya OCR (Primary)
- **Fallback**: Tesseract OCR
- **Languages**: English + Hindi
- **Device**: Auto-detect (GPU if available, else CPU)

---

## Usage

### Python API

```python
from lmpc_checker.compliance_validator import ComplianceValidator
from backend.ocr_config import OCRConfig, process_with_ocr

# For e-commerce products (skip OCR)
config = OCRConfig.get_ocr_config('amazon')
# config['skip_ocr'] = True

# For image uploads (use Surya OCR)
ocr_result = process_with_ocr('product_image.jpg', source='upload')

# Validate compliance
validator = ComplianceValidator()

product_data = {
    "manufacturer_details": "ABC Foods Pvt Ltd, Mumbai, Maharashtra",
    "country_of_origin": "India",
    "generic_name": "Iodized Salt",
    "net_quantity": "1kg",
    "mrp": "₹40.00",
    "best_before_date": "12 months from manufacture",
    "date_of_manufacture": "01/2026",
    "unit_sale_price": "₹40/kg",
    "category": "Food"
}

result = validator.validate(product_data)

print(f"Status: {result['overall_status']}")
print(f"Violations: {result['violations_count']}/{result['total_rules']}")
```

---

## Validation Rules

| Rule ID | Description | Field | Severity | Condition |
|---------|-------------|-------|----------|-----------|
| LM_RULE_01 | Manufacturer/Importer name & address | `manufacturer_details` | Critical | Always |
| LM_RULE_02 | Country of origin | `country_of_origin` | Critical | If imported |
| LM_RULE_03 | Generic name | `generic_name` | Critical | Always |
| LM_RULE_04 | Net quantity | `net_quantity` | Critical | Always |
| LM_RULE_04_UNIT | Net quantity unit validation | `net_quantity` | High | Always |
| LM_RULE_05 | MRP | `mrp` | Critical | Always |
| LM_RULE_05_FORMAT | MRP format validation | `mrp` | High | Always |
| LM_RULE_06 | Best before date | `best_before_date` | Critical | Time-sensitive items |
| LM_RULE_07 | Date of manufacture/import | `date_of_manufacture` | Critical | Always |
| LM_RULE_08 | Unit sale price | `unit_sale_price` | Critical | Food/beverage/grocery |

---

## Testing

```bash
# Run compliance validator tests
pytest tests/unit/test_compliance_validator.py -v

# Test with sample data
python lmpc_checker/main.py
```

---

*Last Updated: January 20, 2026*  
*Validation Rules: 10 (8 mandatory fields)*  
*OCR: Surya (for uploads/batch), Skip (for e-commerce)*