from fastapi import APIRouter, HTTPException
from backend.app.schemas.compliance import ComplianceRequest, ComplianceResponse
from backend.app.services.compliance import compliance_service

router = APIRouter()

@router.post("/check", response_model=ComplianceResponse)
async def check_compliance(request: ComplianceRequest):
    """
    Check Legal Metrology compliance for extracted text.
    Uses Hybrid Approach: Rules + LLM Correction.
    """
    return compliance_service.check_compliance(request)
