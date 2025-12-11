"""
Common utilities for Streamlit pages
Handles imports that may vary between local and cloud environments
"""

import sys
from pathlib import Path

def get_database():
    """Get database instance with robust import handling"""
    web_root = Path(__file__).parent
    project_root = web_root.parent
    
    # Ensure paths are set
    if str(web_root) not in sys.path:
        sys.path.insert(0, str(web_root))
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Try multiple import strategies
    try:
        from database import db
        return db
    except (ImportError, KeyError):
        pass
    
    try:
        from web.database import db
        return db
    except ImportError:
        pass
    
    # Last resort - direct file import
    try:
        import importlib.util
        db_path = web_root / "database.py"
        if db_path.exists():
            spec = importlib.util.spec_from_file_location("database", str(db_path))
            database_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(database_module)
            return database_module.db
    except Exception:
        pass
    
    raise ImportError("Could not import database module")


def get_config_fields():
    """Get EXPECTED_FIELDS from config with fallback"""
    web_root = Path(__file__).parent
    project_root = web_root.parent
    
    try:
        from config import EXPECTED_FIELDS
        return EXPECTED_FIELDS
    except ImportError:
        pass
    
    # Try loading from file
    try:
        import importlib.util
        config_path = project_root / "config.py"
        if config_path.exists():
            spec = importlib.util.spec_from_file_location("app_config", str(config_path))
            app_config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(app_config)
            return getattr(app_config, "EXPECTED_FIELDS", [])
    except Exception:
        pass
    
    return []
