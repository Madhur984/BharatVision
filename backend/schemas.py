
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class ExtractedFields(BaseModel):
    # Core Legal Metrology fields
    mrp_raw: Optional[str] = None
    mrp_value: Optional[float] = None
    net_quantity_raw: Optional[str] = None
    net_quantity_value: Optional[float] = None
    unit: Optional[str] = None
    manufacturer_name: Optional[str] = None
    mfg_date: Optional[str] = None
    expiry_date: Optional[str] = None
    country_of_origin: Optional[str] = None
    
    # Additional extracted fields
    batch_number: Optional[str] = None
    fssai_number: Optional[str] = None
    contact_number: Optional[str] = None
    
    # Legal Metrology compliance fields - Rules 2011
    manufacturer_address: Optional[str] = None
    consumer_care: Optional[str] = None
    pin_code: Optional[str] = None
    
    # Metadata
    extraction_confidence: Optional[float] = None
    extraction_timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    source_file: Optional[str] = None
    
    # Flexible storage for any additional data
    extra: Dict[str, Any] = Field(default_factory=dict)
    
    def calculate_confidence(self) -> float:
        """Calculate extraction confidence based on core fields found"""
        # Core Legal Metrology compliance fields
        core_fields = [
            self.mrp_raw, self.net_quantity_raw, self.unit,
            self.manufacturer_name, self.country_of_origin, self.mfg_date
        ]
        
        # Additional compliance fields for comprehensive assessment
        compliance_fields = [
            self.manufacturer_address, self.consumer_care, self.pin_code
        ]
        
        found_core = sum(1 for field in core_fields if field is not None)
        found_compliance = sum(1 for field in compliance_fields if field is not None)
        
        # Weight core fields more heavily (70%) and compliance fields (30%)
        core_score = (found_core / len(core_fields)) * 70
        compliance_score = (found_compliance / len(compliance_fields)) * 30
        
        return core_score + compliance_score

class ValidationIssue(BaseModel):
    field: str
    level: str  # INFO/WARN/ERROR
    message: str
    rule_id: Optional[str] = None
    suggested_fix: Optional[str] = None
    severity_score: Optional[int] = None  # 1-10 scale

class ValidationResult(BaseModel):
    is_compliant: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    score: float = 0.0
    
    # Enhanced metadata
    validation_timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    validator_version: Optional[str] = "1.0"
    processing_time_ms: Optional[float] = None
    
    # Compliance breakdown
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    
    def calculate_counts(self):
        """Calculate issue counts by severity"""
        self.error_count = sum(1 for issue in self.issues if issue.level == "ERROR")
        self.warning_count = sum(1 for issue in self.issues if issue.level == "WARN")
        self.info_count = sum(1 for issue in self.issues if issue.level == "INFO")

class SystemHealth(BaseModel):
    """System health and performance metrics"""
    status: str  # HEALTHY/WARNING/CRITICAL
    uptime_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    active_users: int
    total_validations: int
    last_validation: Optional[datetime] = None
    error_rate: float = 0.0
    response_time_avg_ms: float = 0.0