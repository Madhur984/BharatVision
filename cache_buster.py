# CACHE BUSTER - Force Streamlit Cloud to reload modules
# Version: 2.0.2
# Last updated: 2026-01-21 14:08 IST
# This file forces Python to reload all modules by changing the import path

import sys
import importlib

# Force reload of crawler module
if 'backend.crawler' in sys.modules:
    importlib.reload(sys.modules['backend.crawler'])
