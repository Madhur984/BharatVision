# Legal Metrology OCR Pipeline - Web Interface

This directory contains the Streamlit-based web interface for the Legal Metrology OCR Pipeline.

## 🏗️ Structure

```
web/
├── streamlit_app.py          # Main Streamlit application
├── run_app.py               # Startup script for easy launching
├── requirements.txt         # Web-specific Python dependencies
├── pages/                   # Streamlit pages
│   ├── 00__Login.py                 # Login page
│   ├── 02__Upload_Image.py          # File upload interface
│   ├── 03__Batch_Process.py         # Batch processing
│   ├── 04__Settings.py              # Application settings
│   ├── 06__User_Dashboard.py        # User dashboard
│   ├── 07__Admin_Dashboard.py       # Admin dashboard
│   ├── 08_Help_AI.py                # Help and AI assistance
│   ├── 10__ERP_Product_Management.py# ERP product management
│   ├── 11__Search_Heatmap.py        # Search heatmap analytics
│   ├── 18__Search_Products.py       # Product search
│   ├── Web_Crawler.py               # Standard web crawler
│   └── Web_Crawler_Enhanced.py      # Enhanced crawler with Surya OCR
├── components/              # Reusable UI components
│   ├── ui_components.py     # UI widgets and helpers
│   ├── result_display.py    # Result visualization components
│   └── report_generator.py  # Report generation utilities
└── assets/                  # Static assets (CSS, images, etc.)
    └── style.css           # Custom CSS styling
```

## 🚀 Quick Start

### Option 1: Using the Startup Script (Recommended)
```bash
cd web
python run_app.py
```

### Option 2: Direct Streamlit Launch
```bash
cd web
streamlit run streamlit_app.py
```

### Option 3: From Project Root
```bash
cd web && python -m streamlit run streamlit_app.py
```

## 📋 Requirements

Make sure you have installed the dependencies:

```bash
# Install main project dependencies first
pip install -r ../requirements.txt

# Install web-specific dependencies
pip install -r requirements.txt
```

## 🔧 Configuration

The web interface automatically imports configurations from the main project's `config.py` file. No additional configuration is needed.

## 📱 Features

### 📷 Live Camera Processing
- Real-time camera preview
- Instant capture and OCR processing
- Live compliance validation
- Camera settings and controls

### 📂 File Upload
- Drag-and-drop image upload
- Batch file processing
- Multiple format support (JPG, PNG, PDF)
- Progress tracking and results export

### 📊 Batch Processing
- Multiple image processing
- Progress monitoring
- Statistical analysis
- Batch report generation

### ⚙️ Settings
- OCR configuration
- Detection parameters
- Export preferences
- System diagnostics

## 🌐 Access

Once running, the web interface will be available at:
- **Local URL**: http://localhost:8501
- **Network URL**: http://[your-ip]:8501

## 📝 Notes

- The web interface is built with Streamlit for rapid development and deployment
- All core OCR and compliance logic is imported from the main project modules
- Session state is used to maintain data across page interactions
- The interface supports both single-image and batch processing workflows

## 🐛 Troubleshooting

If you encounter import errors:
1. Make sure you're running from the `web/` directory
2. Verify that the parent directory contains the main project modules
3. Use the provided `run_app.py` script which handles path configuration automatically

For camera issues:
1. Check camera permissions in your browser/OS
2. Ensure no other applications are using the camera
3. Try refreshing the camera detection in the Live Camera page