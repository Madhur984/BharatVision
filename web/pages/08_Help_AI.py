"""
AI Assistant Help Page - Legal Metrology OCR

Interactive AI assistant providing real-time guidance and support for compliance checking,
OCR processing, and legal metrology regulations.
"""

import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any
import os
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent  # goes up to /web
STYLE_PATH = BASE_DIR / "assets" / "style.css"

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import API client for cloud-based AI
try:
    from web.api_client import get_api_client
    API_CLIENT_AVAILABLE = True
    api_client = get_api_client()
except Exception as e:
    st.warning(f"⚠️ API Client not available: {str(e)}")
    API_CLIENT_AVAILABLE = False
    api_client = None

# Page configuration
st.set_page_config(
    page_title="AI Assistant - Legal Metrology OCR",
    page_icon="🆘",
    layout="wide"
)

# Corrected path for style.css
try:
    with open(STYLE_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass  # Style file not found, continue without it

# Header with Logo
st.markdown(
    """
    <div class="header">
        <img src="../assets/logo.png" alt="BharatVision Logo" class="logo">
        <h1>Help AI - Legal Metrology Compliance</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Custom CSS for Help AI page
def load_help_css():
    """Load custom CSS for help AI page"""
    css = """
    <style>
    /* Hide streamlit_app from sidebar navigation */
    [data-testid="stSidebarNav"] li:first-child {
        display: none !important;
    }
    
    .stApp {
        background: #FFFFFF !important;
    }
    
    .help-header {
        background: #3866D5;
        color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: none;
    }
    
    .help-header h1 {
        font-size: 2.1rem;
        font-weight: 700;
        margin: 0;
        text-shadow: none;
        color: #FFFFFF !important;
    }
    
    .help-header p {
        color: #FFFFFF !important;
    }
    
    .chat-container {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        box-shadow: none;
        border: 1px solid #e5e7eb;
        max-height: 600px;
        overflow-y: auto;
        color: #000000;
    }
    
    .user-message {
        background: #e3f2fd;
        border-left: 4px solid #3866D5;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        text-align: right;
        color: #000000;
    }
    
    .assistant-message {
        background: #f5f7fb;
        border-left: 4px solid #3866D5;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        color: #000000;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

load_help_css()

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_status" not in st.session_state:
    # Check API health on first load
    if API_CLIENT_AVAILABLE and api_client:
        health = api_client.health_check()
        st.session_state.api_status = health.get("status", "unknown")
    else:
        st.session_state.api_status = "unavailable"

# Header
st.markdown("""
<div class="help-header">
    <h1>🤖 AI Assistant for Legal Metrology</h1>
    <p>Get expert guidance on compliance checking, OCR processing, and legal metrology regulations</p>
</div>
""", unsafe_allow_html=True)

# Main layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Chat with AI Assistant")
    
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["type"] == "user":
            st.markdown(f'<div class="user-message"><b>You:</b><br>{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-message"><b>AI:</b><br>{message["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area
    user_input = st.text_input(
        "Ask about legal metrology compliance...",
        placeholder="e.g., What are the requirements for net quantity labeling?",
        label_visibility="collapsed"
    )
    
    col_send, col_clear = st.columns([4, 1])
    with col_send:
        if st.button("Send 📤"):
            if user_input.strip():
                # Add user message to history
                st.session_state.chat_history.append({
                    "type": "user",
                    "content": user_input,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Get AI response from cloud API
                if API_CLIENT_AVAILABLE and api_client:
                    with st.spinner("🤔 Thinking..."):
                        try:
                            result = api_client.ask_ai(question=user_input)
                            
                            if result.get("success", False):
                                response = result.get("answer", "No response received.")
                            else:
                                response = result.get("answer", "Sorry, I couldn't process your question. Please try again.")
                                
                        except Exception as e:
                            response = f"Error connecting to AI service: {str(e)}"
                else:
                    # Fallback responses when API is not available
                    responses = {
                        "net quantity": "Net quantity must be clearly displayed on the product label in both metric and imperial units where applicable.",
                        "compliance": "Compliance requires: manufacturer name/address, net quantity, MFG date, and country of origin.",
                        "ocr": "Our OCR system extracts text from images with high accuracy. Use clear, well-lit images for best results.",
                        "date": "Manufacturing dates should be in DD/MM/YYYY format. Best before dates are optional but recommended.",
                        "manufacturer": "Manufacturer details including name and address must be clearly displayed as per Legal Metrology requirements."
                    }
                    
                    response = "I'm here to help with legal metrology compliance! Please ask about specific requirements."
                    for key, val in responses.items():
                        if key.lower() in user_input.lower():
                            response = val
                            break
                
                # Add AI response to history
                st.session_state.chat_history.append({
                    "type": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })
                
                st.rerun()
    
    with col_clear:
        if st.button("Clear 🗑️"):
            st.session_state.chat_history = []
            st.rerun()

with col2:
    st.subheader("📚 Quick Resources")
    
    # API Status
    if API_CLIENT_AVAILABLE and api_client:
        status = st.session_state.get("api_status", "unknown")
        if status == "healthy":
            st.success("✅ Cloud AI Connected")
        else:
            st.warning("⚠️ Using Fallback Mode")
    else:
        st.info("ℹ️ Offline Mode")
    
    st.subheader("❓ FAQs")
    faqs = [
        ("What is Legal Metrology?", "Science of weights and measures for trade compliance."),
        ("Required fields?", "Manufacturer, Net quantity, MFG date, Country of origin."),
        ("Supported formats?", "JPG, PNG, BMP, WebP (max 10MB)."),
        ("Date format?", "DD/MM/YYYY format recommended."),
    ]
    
    for q, a in faqs:
        with st.expander(q):
            st.write(a)
    
    st.subheader("💡 Popular Topics")
    topics = ["Net Quantity", "Compliance Rules", "OCR Tips", "Date Formats"]
    for topic in topics:
        st.button(topic)

st.divider()
st.metric("Chat Messages", len(st.session_state.chat_history))

# Footer
st.markdown(
    """
    <footer>
        <p>© 2025 BharatVision. All rights reserved.</p>
    </footer>
    """,
    unsafe_allow_html=True,
)




