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

            return ComplianceResponse(
                success=True,
                compliant=result["overall_status"] == "COMPLIANT",
                score=round(100 - (result["violations_count"] * 16.6), 2),
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

        logger.info(f"LLM Fallback triggered for missing fields: {missing_fields}")
        
        fields_str = ", ".join(missing_fields)
        prompt = f"""<start_of_turn>user
You are a Legal Metrology Expert AI.
I have extracted some data but missed these mandatory fields: {fields_str}.
Please analyze the raw OCR text below. 
If you find the value for any of these fields, extract it EXACTLY as it appears.
If a value is not found, do not include it.

Raw OCR Text:
\"\"\"{text[:2000]}\"\"\"

Return ONLY a valid JSON object with the found values. Keys must be from: {fields_str}.
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
                if v and str(v).lower() not in ["not found", "none", "null", ""]:
                    # Sanitize key to match expected fields if LLM hallucinated slightly?
                    # Ideally we trust LLM to return requested keys.
                    if k in missing_fields or k in data: 
                         data[k] = v
                         corrections += 1
                         logger.info(f"LLM Corrected {k}: {v}")
            
            if corrections > 0:
                logger.info(f"LLM successfully corrected {corrections} fields.")
                
        except Exception as e:
            logger.warning(f"LLM correction failed (non-critical): {e}")

compliance_service = ComplianceService()
