"""
Complaint Management System
Handles filing, tracking, and managing complaints for Legal Metrology compliance issues
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from .json_utils import safe_json_dump, safe_json_dumps

class ComplaintStatus(Enum):
    """Complaint status enumeration"""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"

class ComplaintPriority(Enum):
    """Complaint priority levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ComplaintCategory(Enum):
    """Complaint categories"""
    DATA_QUALITY = "DATA_QUALITY"
    EXTRACTION_ERROR = "EXTRACTION_ERROR"
    VALIDATION_ISSUE = "VALIDATION_ISSUE"
    SYSTEM_BUG = "SYSTEM_BUG"
    COMPLIANCE_VIOLATION = "COMPLIANCE_VIOLATION"
    USER_ERROR = "USER_ERROR"
    OTHER = "OTHER"

@dataclass
class Complaint:
    """Complaint data model"""
    id: str
    title: str
    description: str
    category: ComplaintCategory
    priority: ComplaintPriority
    status: ComplaintStatus
    filed_by: str  # Admin username
    filed_date: str
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    resolution_date: Optional[str] = None
    related_files: List[str] = None
    evidence_files: List[str] = None
    tags: List[str] = None
    notes: List[Dict[str, str]] = None  # List of {timestamp, user, note}
    
    def __post_init__(self):
        if self.related_files is None:
            self.related_files = []
        if self.evidence_files is None:
            self.evidence_files = []
        if self.tags is None:
            self.tags = []
        if self.notes is None:
            self.notes = []

class ComplaintManager:
    """Manages complaint filing, tracking, and resolution"""
    
    def __init__(self):
        self.complaints_file = Path("app/data/complaints.json")
        self.complaints_file.parent.mkdir(parents=True, exist_ok=True)
        self.complaints = self._load_complaints()
    
    def _load_complaints(self) -> List[Complaint]:
        """Load complaints from file"""
        if not self.complaints_file.exists():
            return []
        
        try:
            with open(self.complaints_file, 'r') as f:
                data = json.load(f)
                complaints = []
                for item in data:
                    # Convert enum values back to enum objects
                    item['category'] = ComplaintCategory(item['category'])
                    item['priority'] = ComplaintPriority(item['priority'])
                    item['status'] = ComplaintStatus(item['status'])
                    complaints.append(Complaint(**item))
                return complaints
        except Exception as e:
            print(f"Error loading complaints: {e}")
            return []
    
    def _save_complaints(self):
        """Save complaints to file"""
        try:
            # Convert complaints to dictionaries
            data = []
            for complaint in self.complaints:
                complaint_dict = asdict(complaint)
                # Convert enums to string values
                complaint_dict['category'] = complaint.category.value
                complaint_dict['priority'] = complaint.priority.value
                complaint_dict['status'] = complaint.status.value
                data.append(complaint_dict)
            
            with open(self.complaints_file, 'w') as f:
                safe_json_dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving complaints: {e}")
    
    def generate_complaint_id(self) -> str:
        """Generate unique complaint ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        count = len([c for c in self.complaints if c.id.startswith(timestamp)])
        return f"COMP-{timestamp}-{count:03d}"
    
    def file_complaint(self, title: str, description: str, category: ComplaintCategory,
                      priority: ComplaintPriority, filed_by: str, 
                      related_files: List[str] = None, evidence_files: List[str] = None,
                      tags: List[str] = None) -> Complaint:
        """File a new complaint"""
        
        complaint = Complaint(
            id=self.generate_complaint_id(),
            title=title,
            description=description,
            category=category,
            priority=priority,
            status=ComplaintStatus.OPEN,
            filed_by=filed_by,
            filed_date=datetime.now().isoformat(),
            related_files=related_files or [],
            evidence_files=evidence_files or [],
            tags=tags or []
        )
        
        self.complaints.append(complaint)
        self._save_complaints()
        
        return complaint
    
    def get_complaint(self, complaint_id: str) -> Optional[Complaint]:
        """Get complaint by ID"""
        for complaint in self.complaints:
            if complaint.id == complaint_id:
                return complaint
        return None
    
    def get_all_complaints(self) -> List[Complaint]:
        """Get all complaints"""
        return self.complaints
    
    def get_complaints_by_status(self, status: ComplaintStatus) -> List[Complaint]:
        """Get complaints by status"""
        return [c for c in self.complaints if c.status == status]
    
    def get_complaints_by_priority(self, priority: ComplaintPriority) -> List[Complaint]:
        """Get complaints by priority"""
        return [c for c in self.complaints if c.priority == priority]
    
    def get_complaints_by_category(self, category: ComplaintCategory) -> List[Complaint]:
        """Get complaints by category"""
        return [c for c in self.complaints if c.category == category]
    
    def get_complaints_by_filer(self, filed_by: str) -> List[Complaint]:
        """Get complaints filed by specific user"""
        return [c for c in self.complaints if c.filed_by == filed_by]
    
    def update_complaint_status(self, complaint_id: str, new_status: ComplaintStatus, 
                               updated_by: str) -> bool:
        """Update complaint status"""
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            return False
        
        old_status = complaint.status
        complaint.status = new_status
        
        # Add note about status change
        complaint.notes.append({
            "timestamp": datetime.now().isoformat(),
            "user": updated_by,
            "note": f"Status changed from {old_status.value} to {new_status.value}"
        })
        
        # Set resolution date if resolved/closed
        if new_status in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]:
            complaint.resolution_date = datetime.now().isoformat()
        
        self._save_complaints()
        return True
    
    def assign_complaint(self, complaint_id: str, assigned_to: str, assigned_by: str) -> bool:
        """Assign complaint to a user"""
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            return False
        
        complaint.assigned_to = assigned_to
        
        # Add note about assignment
        complaint.notes.append({
            "timestamp": datetime.now().isoformat(),
            "user": assigned_by,
            "note": f"Complaint assigned to {assigned_to}"
        })
        
        self._save_complaints()
        return True
    
    def add_complaint_note(self, complaint_id: str, note: str, user: str) -> bool:
        """Add note to complaint"""
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            return False
        
        complaint.notes.append({
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "note": note
        })
        
        self._save_complaints()
        return True
    
    def resolve_complaint(self, complaint_id: str, resolution: str, resolved_by: str) -> bool:
        """Resolve a complaint"""
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            return False
        
        complaint.status = ComplaintStatus.RESOLVED
        complaint.resolution = resolution
        complaint.resolution_date = datetime.now().isoformat()
        
        # Add resolution note
        complaint.notes.append({
            "timestamp": datetime.now().isoformat(),
            "user": resolved_by,
            "note": f"Complaint resolved: {resolution}"
        })
        
        self._save_complaints()
        return True
    
    def get_complaint_statistics(self) -> Dict[str, Any]:
        """Get complaint statistics"""
        total = len(self.complaints)
        
        if total == 0:
            return {
                "total_complaints": 0,
                "by_status": {},
                "by_priority": {},
                "by_category": {},
                "avg_resolution_time_hours": 0,
                "open_complaints": 0,
                "critical_complaints": 0
            }
        
        # Count by status
        status_counts = {}
        for status in ComplaintStatus:
            status_counts[status.value] = len(self.get_complaints_by_status(status))
        
        # Count by priority
        priority_counts = {}
        for priority in ComplaintPriority:
            priority_counts[priority.value] = len(self.get_complaints_by_priority(priority))
        
        # Count by category
        category_counts = {}
        for category in ComplaintCategory:
            category_counts[category.value] = len(self.get_complaints_by_category(category))
        
        # Calculate average resolution time
        resolved_complaints = [c for c in self.complaints if c.resolution_date]
        if resolved_complaints:
            total_hours = 0
            for complaint in resolved_complaints:
                filed_date = datetime.fromisoformat(complaint.filed_date)
                resolved_date = datetime.fromisoformat(complaint.resolution_date)
                hours = (resolved_date - filed_date).total_seconds() / 3600
                total_hours += hours
            avg_resolution_time = total_hours / len(resolved_complaints)
        else:
            avg_resolution_time = 0
        
        return {
            "total_complaints": total,
            "by_status": status_counts,
            "by_priority": priority_counts,
            "by_category": category_counts,
            "avg_resolution_time_hours": round(avg_resolution_time, 2),
            "open_complaints": status_counts.get("OPEN", 0),
            "critical_complaints": priority_counts.get("CRITICAL", 0)
        }
    
    def search_complaints(self, query: str) -> List[Complaint]:
        """Search complaints by title, description, or tags"""
        query_lower = query.lower()
        results = []
        
        for complaint in self.complaints:
            if (query_lower in complaint.title.lower() or 
                query_lower in complaint.description.lower() or
                any(query_lower in tag.lower() for tag in complaint.tags)):
                results.append(complaint)
        
        return results

# Global complaint manager instance
complaint_manager = ComplaintManager()