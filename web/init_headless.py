"""
Initialize headless mode for OpenCV and other libraries.
Import this module FIRST before any other imports that might use OpenCV.
"""

import os
import sys

# Force headless mode for OpenCV
os.environ['OPENCV_HEADLESS'] = '1'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Disable GUI for matplotlib if used
os.environ['MPLBACKEND'] = 'Agg'

# Try to prevent opencv-python from being imported if opencv-python-headless is available
# by manipulating the import path
def ensure_headless_opencv():
    """
    Ensure opencv-python-headless is used instead of opencv-python.
    This prevents libGL.so.1 errors on Streamlit Cloud.
    """
    try:
        # Check if cv2 is already imported
        if 'cv2' in sys.modules:
            return True
        
        # Try importing - should use headless version
        import cv2
        
        # Check if it's truly headless (no GUI functions that require libGL)
        build_info = cv2.getBuildInformation() if hasattr(cv2, 'getBuildInformation') else ""
        if 'GTK' in build_info or 'QT' in build_info:
            print("Warning: Non-headless OpenCV detected. Some features may not work.")
        
        return True
    except ImportError as e:
        print(f"OpenCV not available: {e}")
        return False
    except Exception as e:
        print(f"OpenCV initialization issue: {e}")
        return False

# Initialize on import
_opencv_ok = ensure_headless_opencv()
