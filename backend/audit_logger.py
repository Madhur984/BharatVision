import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class AuditEvent:
    timestamp: str
    user: str
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLogger:
    def __init__(self):
        self.log_file = Path("app/data/audit_log.jsonl")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_event(self, user: str, action: str, resource: str, details: Dict[str, Any] = None):
        """Log an audit event"""
        if details is None:
            details = {}
        
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            user=user,
            action=action,
            resource=resource,
            details=details
        )
        
        # Append to log file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(asdict(event)) + "\n")
    
    def get_logs(self, user: Optional[str] = None, action: Optional[str] = None, limit: int = 1000) -> pd.DataFrame:
        """Retrieve audit logs with optional filtering"""
        if not self.log_file.exists():
            return pd.DataFrame()
        
        logs = []
        with open(self.log_file, "r") as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    if user and log_entry.get('user') != user:
                        continue
                    if action and log_entry.get('action') != action:
                        continue
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
        
        # Sort by timestamp (most recent first) and limit
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        logs = logs[:limit]
        
        return pd.DataFrame(logs)
    
    def get_user_activity_summary(self, user: str) -> Dict[str, Any]:
        """Get activity summary for a specific user"""
        user_logs = self.get_logs(user=user)
        
        if user_logs.empty:
            return {
                'total_actions': 0,
                'last_activity': None,
                'action_counts': {},
                'resources_accessed': set()
            }
        
        action_counts = user_logs['action'].value_counts().to_dict()
        resources = user_logs['resource'].unique().tolist()
        last_activity = user_logs.iloc[0]['timestamp'] if not user_logs.empty else None
        
        return {
            'total_actions': len(user_logs),
            'last_activity': last_activity,
            'action_counts': action_counts,
            'resources_accessed': resources
        }
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Remove log entries older than specified days"""
        if not self.log_file.exists():
            return
        
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        with open(self.log_file, "r") as f:
            lines = f.readlines()
        
        filtered_lines = []
        for line in lines:
            try:
                log_entry = json.loads(line.strip())
                log_timestamp = datetime.fromisoformat(log_entry['timestamp']).timestamp()
                if log_timestamp >= cutoff_date:
                    filtered_lines.append(line)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        
        with open(self.log_file, "w") as f:
            f.writelines(filtered_lines)

# Global audit logger instance
audit_logger = AuditLogger()

def log_user_action(user: str, action: str, resource: str, details: Dict[str, Any] = None):
    """Convenience function to log user actions"""
    audit_logger.log_event(user, action, resource, details)