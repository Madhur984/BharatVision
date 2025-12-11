import os
import streamlit as st
from typing import Optional

class Settings:
    PROJECT_NAME: str = "BharatVision ML API"
    VERSION: str = "2.0.0"
    
    # API Config
    API_V1_STR: str = "/api/v1"
    
    # Security
    HF_TOKEN: Optional[str] = os.environ.get("HF_TOKEN")
    if not HF_TOKEN and "huggingface" in st.secrets:
        HF_TOKEN = st.secrets["huggingface"].get("token")
        
    # Models
    LLM_MODEL: str = "meta-llama/Llama-3.2-11B-Vision-Instruct"
    OCR_MODEL: str = "microsoft/trocr-base-printed"
    
    # Environment
    ENV: str = os.environ.get("ENV", "development")
    DEBUG: bool = ENV == "development"

settings = Settings()
