"""
Health Check Page - Diagnostic page for Streamlit Cloud deployment
No authentication required
"""

import streamlit as st
import sys
import os
from pathlib import Path

st.set_page_config(page_title="Health Check", page_icon="🔍", layout="wide")

st.title("🔍 System Health Check")

st.markdown("---")

# Basic info
st.subheader("📊 Environment Info")
col1, col2 = st.columns(2)
with col1:
    st.write(f"**Python Version:** {sys.version}")
    st.write(f"**Working Directory:** {os.getcwd()}")
with col2:
    st.write(f"**Platform:** {sys.platform}")
    st.write(f"**Script Path:** {__file__}")

st.markdown("---")

# Check imports
st.subheader("📦 Package Availability")

packages = {
    "streamlit": None,
    "numpy": None,
    "pandas": None,
    "PIL (Pillow)": None,
    "torch": None,
    "transformers": None,
    "ultralytics": None,
    "surya": None,
    "easyocr": None,
    "cv2 (opencv)": None,
}

for pkg_name in packages.keys():
    try:
        if pkg_name == "PIL (Pillow)":
            import PIL
            packages[pkg_name] = PIL.__version__
        elif pkg_name == "surya":
            import surya
            packages[pkg_name] = "0.17.0"  # Surya doesn't expose version well
        elif pkg_name == "cv2 (opencv)":
            import cv2
            packages[pkg_name] = cv2.__version__
        else:
            mod = __import__(pkg_name)
            packages[pkg_name] = getattr(mod, "__version__", "installed")
    except ImportError as e:
        packages[pkg_name] = f"❌ Not installed: {e}"
    except Exception as e:
        packages[pkg_name] = f"⚠️ Error: {e}"

for pkg, version in packages.items():
    if version and not str(version).startswith("❌") and not str(version).startswith("⚠️"):
        st.success(f"✅ **{pkg}**: {version}")
    else:
        st.error(f"{version}")

st.markdown("---")

# Check Surya OCR specifically
st.subheader("🔬 Surya OCR Check")
try:
    from surya.foundation import FoundationPredictor
    from surya.recognition import RecognitionPredictor
    from surya.detection import DetectionPredictor
    st.success("✅ Surya OCR imports successful!")
    
    if st.button("🧪 Test Surya Model Loading (may take time)"):
        with st.spinner("Loading Surya models..."):
            try:
                fp = FoundationPredictor(device='cpu')
                rp = RecognitionPredictor(fp)
                dp = DetectionPredictor(device='cpu')
                st.success("✅ Surya models loaded successfully!")
            except Exception as e:
                st.error(f"❌ Failed to load Surya models: {e}")
except ImportError as e:
    st.error(f"❌ Surya OCR import failed: {e}")

st.markdown("---")

# Check LiveProcessor
st.subheader("🔧 LiveProcessor Check")
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from live_processor import LiveProcessor
    st.success("✅ LiveProcessor import successful!")
    
    if st.button("🧪 Test LiveProcessor Initialization"):
        with st.spinner("Initializing LiveProcessor (loading models)..."):
            try:
                lp = LiveProcessor()
                st.success(f"✅ LiveProcessor initialized! Surya available: {lp._surya_available}")
            except Exception as e:
                st.error(f"❌ LiveProcessor init failed: {e}")
except ImportError as e:
    st.error(f"❌ LiveProcessor import failed: {e}")

st.markdown("---")
st.info("This page is for diagnostic purposes. Refresh to re-check.")
