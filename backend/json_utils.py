"""JSON utility functions for safe JSON handling"""

import json
from typing import Any, Dict

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely convert object to JSON string"""
    try:
        return json.dumps(obj, default=str, **kwargs)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(obj).__name__})

def safe_json_dump(obj: Any, fp, **kwargs) -> None:
    """Safely dump object to JSON file"""
    try:
        json.dump(obj, fp, default=str, **kwargs)
    except Exception as e:
        json.dump({"error": str(e), "type": type(obj).__name__}, fp)

def parse_json_safe(json_str: str, default=None) -> Any:
    """Safely parse JSON string"""
    try:
        return json.loads(json_str)
    except Exception as e:
        return default if default is not None else {"error": str(e)}
