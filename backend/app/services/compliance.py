import logging
import json
from typing import Dict, Any, List
from backend.app.schemas.compliance import ComplianceRequest, ComplianceResponse
from lmpc_checker.compliance_validator import ComplianceValidator
from backend.app.services.llm_service import llm_service

logger = logging.getLogger("bharatvision.compliance")

class ComplianceService:
    """
    Service for Legal Metrology Compliance Validation.
    Combines deterministic Rules Engine with LLM-based smart correction.
    """
    
    def __init__(self):
        self.validator = ComplianceValidator()

    def check_compliance(self, request: ComplianceRequest) -> ComplianceResponse:
        try:
            # 1. Initial Rule-Based Validation
            data = request.product_data or {}
            result = self.validator.validate(data)
            
            # 2. Hybrid LLM Fallback (Smart Correction)
            # Only trigger if violations exist and we have raw text to fallback on
            if result["violations_count"] > 0 and request.text:
                self._attempt_llm_correction(result, request.text, data)
                
                # Re-run validation with corrected data
                result = self.validator.validate(data)

            # Calculate score dynamically based on total rules (usually 9)
            total_rules = result.get("total_rules", 9)
            if total_rules > 0:
                score_val = max(0, 100 - (result["violations_count"] * (100 / total_rules)))
            else:
                score_val = 100.0 if result["violations_count"] == 0 else 0.0

            return ComplianceResponse(
                success=True,
                compliant=result["overall_status"] == "COMPLIANT",
                score=round(score_val, 2),
                violations=[r for r in result["rule_results"] if r["violated"]],
                fields_checked=[r["field"] for r in result["rule_results"]],
                full_report=result,
                data=data
            )
            
        except Exception as e:
            logger.error(f"Compliance check failed: {e}", exc_info=True)
            return ComplianceResponse(
                success=False,
                compliant=False,
                score=0.0,
                violations=[],
                fields_checked=[],
                full_report={},
                data={},
                error=str(e)
            )

    def _attempt_llm_correction(self, result: Dict[str, Any], text: str, data: Dict[str, Any]):
        """
        Identify missing mandatory fields and ask LLM to extract them from raw text.
        Updates 'data' in-place.
        """
        # Identify missing fields
        missing_fields = []
        for v in result["rule_results"]:
            if v["violated"] and "missing" in v["description"].lower():
                missing_fields.append(v["field"])
        
        if not missing_fields:
            return

        logger.info(f"LLM Fallback triggered for fields: {missing_fields}")
        
        # Increased context window and used Chain of Thought
        fields_str = ", ".join(missing_fields)
        prompt = f"""<start_of_turn>user
You are an expert Legal Metrology Auditor.
Your task is to extract specific mandatory declarations from Product Label Text.
The OCR text might be messy, unordered, or contain noise.

Target Fields to Extract: {fields_str}

**Extraction Rules:**
1. **Manufacturer**: Look for "Mfd By", "Manufactured by", "Marketed by", or address blocks.
2. **Net Quantity**: Look for "Net Qty", "Net Weight", "Vol", "N.W.", followed by number and unit (g, kg, ml, L).
3. **MRP**: Look for "MRP", "Price", "Rs.", "₹" (inclusive of taxes).
4. **Dates**: Look for "Pkd", "Unit Sale Price", "Use By", "Expiry", "Mfg Date" (DD/MM/YYYY or MM/YY).
5. **Consumer Care**: Look for "Customer Care", "Feedback", "Complaint", email ID or phone numbers.
6. **Country**: Look for "Made in", "Product of", "Country of Origin".

**Raw OCR Text:**
\"\"\"{text[:5000]}\"\"\"

**Instructions:**
- Analyze the text carefully.
- If a value is split across lines, join them.
- Return the result as a valid JSON object.
- If a field is strictly NOT found, use null.

Output Format: JSON ONLY.
<end_of_turn>
<start_of_turn>model
```json
"""
        try:
            # Call LLM Service
            found_values = llm_service.generate_json(prompt)
            
            # Update data with found values
            corrections = 0
            for k, v in found_values.items():
                # Allow fuzzy matching of keys if LLM returns slightly different names
                target_key = k
                if k not in data:
                    # Try to map common variations
                    if "mrp" in k.lower(): target_key = "mrp"
                    elif "date" in k.lower(): target_key = "date_of_manufacture"
                    elif "care" in k.lower(): target_key = "customer_care_details"
                    elif "origin" in k.lower(): target_key = "country_of_origin"
                    elif "quantity" in k.lower(): target_key = "net_quantity"
                    elif "manufacturer" in k.lower(): target_key = "manufacturer_details"

                # Update if valid value found
                if v and str(v).lower() not in ["not found", "none", "null", "", "n/a"]:
                     if target_key in missing_fields or target_key in data: 
                         data[target_key] = v
                         corrections += 1
                         logger.info(f"LLM Corrected {target_key}: {v}")
            
            if corrections > 0:
                logger.info(f"LLM successfully corrected {corrections} fields.")
                
        except Exception as e:
            logger.warning(f"LLM correction failed (non-critical): {e}")

compliance_service = ComplianceService()
