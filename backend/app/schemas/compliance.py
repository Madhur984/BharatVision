from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class ComplianceRequest(BaseModel):
    text: str
    product_data: Optional[Dict[str, Any]] = None

class RuleResult(BaseModel):
    rule_id: str
    description: str
    field: str
    severity: str
    violated: bool
    details: str

class ComplianceResponse(BaseModel):
    success: bool
    compliant: bool
    score: float
    violations: List[RuleResult]
    fields_checked: List[str]
    full_report: Dict[str, Any]
    data: Dict[str, Any]
    error: Optional[str] = None
