# gui_utils.py
"""
GUI utilities for handling OpenCV display in different environments
"""

import cv2
import logging
from config import ENABLE_GUI

logger = logging.getLogger(__name__)

def check_gui_support():
    """Check if GUI support is available"""
    try:
        # Try to create a test window
        test_window = 'test_gui_support'
        cv2.namedWindow(test_window, cv2.WINDOW_NORMAL)
        cv2.destroyWindow(test_window)
        return True
    except cv2.error as e:
        logger.warning(f"GUI support not available: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking GUI support: {e}")
        return False

# Global GUI support detection
GUI_AVAILABLE = check_gui_support() and ENABLE_GUI

def safe_imshow(window_name, image):
    """Safely show image, returns True if successful"""
    if not GUI_AVAILABLE:
        logger.debug(f"GUI not available, skipping imshow for '{window_name}'")
        return False
    
    try:
        cv2.imshow(window_name, image)
        return True
    except cv2.error as e:
        logger.warning(f"Failed to show image in window '{window_name}': {e}")
        return False

def safe_named_window(window_name, flags=cv2.WINDOW_NORMAL):
    """Safely create named window, returns True if successful"""
    if not GUI_AVAILABLE:
        logger.debug(f"GUI not available, skipping namedWindow for '{window_name}'")
        return False
    
    try:
        cv2.namedWindow(window_name, flags)
        return True
    except cv2.error as e:
        logger.warning(f"Failed to create window '{window_name}': {e}")
        return False

def safe_destroy_all_windows():
    """Safely destroy all windows"""
    if not GUI_AVAILABLE:
        return
    
    try:
        cv2.destroyAllWindows()
    except cv2.error as e:
        logger.warning(f"Failed to destroy windows: {e}")

def safe_wait_key(delay=1):
    """Safely wait for key press, returns key code or -1"""
    if not GUI_AVAILABLE:
        return -1
    
    try:
        return cv2.waitKey(delay)
    except cv2.error:
        return -1

def print_gui_status():
    """Print current GUI status for debugging"""
    print(f"🖥️  GUI Support: {'✅ Available' if GUI_AVAILABLE else '❌ Not Available'}")
    if not GUI_AVAILABLE:
        print("   → Running in headless mode")
        print("   → Visual displays will be skipped")
        print("   → Use matplotlib for visualization instead")