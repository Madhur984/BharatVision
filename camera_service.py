"""
Camera Service Module - Raspberry Pi Integration

Handles camera capture for Raspberry Pi systems with fallback support.
Provides real-time camera preview and image capture functionality.
"""

import cv2
import numpy as np
import time
import threading
from pathlib import Path
from typing import Optional, Tuple
import streamlit as st
from PIL import Image
import io


class CameraService:
    """
    Handle camera operations for Raspberry Pi and desktop systems.
    Supports multiple camera interfaces and fallback mechanisms.
    """
    
    def __init__(self, camera_index: int = 0):
        """
        Initialize camera service
        
        Args:
            camera_index: Camera device index (0 for primary camera)
        """
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        self.frame_buffer = None
        self.lock = threading.Lock()
        
    def initialize_camera(self) -> bool:
        """
        Initialize camera connection with fallback support
        
        Returns:
            bool: True if camera initialized successfully
        """
        try:
            # Try primary camera
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                raise ValueError(f"Cannot open camera at index {self.camera_index}")
            
            # Set optimal camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            
            # Warm up camera
            for _ in range(5):
                ret, _ = self.cap.read()
                if not ret:
                    raise ValueError("Failed to read from camera during warmup")
            
            self.is_running = True
            return True
            
        except Exception as e:
            st.error(f"❌ Camera initialization failed: {str(e)}")
            return False
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from camera
        
        Returns:
            np.ndarray: Captured frame or None if failed
        """
        if self.cap is None or not self.cap.isOpened():
            return None
        
        try:
            ret, frame = self.cap.read()
            
            if not ret:
                raise ValueError("Failed to capture frame")
            
            # Ensure frame is in RGB format for Streamlit
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            with self.lock:
                self.frame_buffer = frame_rgb
            
            return frame_rgb
            
        except Exception as e:
            st.error(f"❌ Frame capture failed: {str(e)}")
            return None
    
    def capture_image(self, output_path: Optional[str] = None) -> Tuple[bool, Optional[np.ndarray], str]:
        """
        Capture an image from camera and optionally save it
        
        Args:
            output_path: Optional path to save captured image
            
        Returns:
            Tuple of (success, frame, message)
        """
        try:
            frame = self.capture_frame()
            
            if frame is None:
                return False, None, "Failed to capture frame"
            
            # Convert RGB back to BGR for saving
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            if output_path:
                success = cv2.imwrite(output_path, frame_bgr)
                if not success:
                    return False, frame, "Failed to save image"
            
            return True, frame, "Image captured successfully"
            
        except Exception as e:
            return False, None, f"Capture error: {str(e)}"
    
    def get_camera_info(self) -> dict:
        """
        Get camera information and properties
        
        Returns:
            dict: Camera properties
        """
        if self.cap is None or not self.cap.isOpened():
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(self.cap.get(cv2.CAP_PROP_FPS)),
            "brightness": int(self.cap.get(cv2.CAP_PROP_BRIGHTNESS)),
            "contrast": int(self.cap.get(cv2.CAP_PROP_CONTRAST))
        }
    
    def adjust_brightness(self, value: float) -> bool:
        """
        Adjust camera brightness
        
        Args:
            value: Brightness value (-100 to 100)
            
        Returns:
            bool: Success status
        """
        if self.cap is None:
            return False
        
        try:
            # Normalize value to camera scale
            normalized = (value + 100) / 2
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, normalized)
            return True
        except:
            return False
    
    def adjust_contrast(self, value: float) -> bool:
        """
        Adjust camera contrast
        
        Args:
            value: Contrast value (-100 to 100)
            
        Returns:
            bool: Success status
        """
        if self.cap is None:
            return False
        
        try:
            # Normalize value to camera scale
            normalized = (value + 100) / 2
            self.cap.set(cv2.CAP_PROP_CONTRAST, normalized)
            return True
        except:
            return False
    
    def release_camera(self):
        """Release camera resources"""
        if self.cap is not None:
            self.is_running = False
            self.cap.release()
            self.cap = None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.release_camera()


def create_camera_placeholder_image(width: int = 320, height: int = 240) -> Image.Image:
    """
    Create a placeholder image for when camera is not available
    
    Args:
        width: Image width
        height: Image height
        
    Returns:
        PIL Image: Placeholder image
    """
    # Create a gradient placeholder
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create gradient background
    for i in range(height):
        img_array[i, :] = [100 + i // 3, 150 + i // 4, 200 + i // 5]
    
    # Add text overlay
    img_pil = Image.fromarray(img_array)
    
    return img_pil


def verify_camera_availability() -> bool:
    """
    Check if camera is available on the system
    
    Returns:
        bool: True if camera is available
    """
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.release()
            return True
        return False
    except:
        return False
