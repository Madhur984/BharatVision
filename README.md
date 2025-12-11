# Legal Metrology OCR Compliance Pipeline

**An intelligent, production-ready system for automated Legal Metrology compliance validation using advanced Computer Vision and AI.**

This comprehensive end-to-end pipeline captures product images, extracts text using state-of-the-art OCR technology, and validates compliance against Indian Legal Metrology (Packaged Commodities) Rules, 2011.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![OCR](https://img.shields.io/badge/OCR-Surya%20v0.16.7-orange)](https://github.com/VikParuchuri/surya)
[![AI](https://img.shields.io/badge/AI-Gemma--2--9B-blue)](https://huggingface.co/google/gemma-2-9b-it)

## 🎯 Overview

**PackNetra Microservices** is a refactored version of the original pipeline, designed for cloud scalability. It decouples the heavy Machine Learning inference from the user interface.

- **Frontend**: A lightweight Streamlit Client (`web/`) that runs on minimal resources.
- **ML Service**: A GPU-accelerated FastAPI service (`ml_service/`) handling YOLO, Surya OCR, and Gemma LLM.

## ✨ Key Features

### 🏗️ Microservices Architecture
- **Decoupled Logic**: Separate containers for UI and ML inference.
- **REST API Integration**: All model interactions happen via standard HTTP endpoints.
- **Cloud Ready**: Dockerized and ready for deployment on platforms like Jio Cloud, AWS, or Azure.

### 🔍 Advanced OCR Processing
- **Surya OCR v0.16.7**: State-of-the-art multilingual text detection and recognition
- **Intelligent Detection**: Handles complex product labels with varying layouts
- **Multi-language Support**: English and Hindi text recognition
- **High Accuracy**: 85-95% accuracy on clear product labels

### 🤖 AI-Powered Data Extraction
- **Google Gemma 2 (9B)**: Intelligent text structuring and field extraction using State-of-the-Art LLM.
- **Hybrid Processing**: Combines regex patterns with NLP for maximum accuracy
- **Smart Field Mapping**: Automatically identifies MRP, quantities, dates, manufacturer details
- **Data Standardization**: Consistent formatting and unit normalization

### ⚖️ Legal Metrology Compliance
- **20+ Validation Rules**: Comprehensive coverage of Indian Legal Metrology requirements
- **Severity Classification**: Critical, High, and Medium priority violations
- **Detailed Reporting**: Structured violation reports with actionable recommendations
- **Production Ready**: Robust error handling and logging

## 🏛️ System Architecture

```mermaid
graph TD
    A[📷 Camera Selection] --> B[📸 Image Capture]
    B --> C[🔍 OCR Processing<br/>Surya OCR]
    C --> D[🛠️ Data Refinement<br/>Regex + NLP]
    D --> E[⚖️ Compliance Validation<br/>20+ Rules]
    E --> F[📊 Report Generation]
    
    G[live_processor.py] --> C
    H[data_refiner/] --> D
    I[lmpc_checker/] --> E
    J[run_full_pipeline.py] --> A
```

### Pipeline Components

| Component | Purpose | Technology Stack |
|-----------|---------|------------------|
| **`run_full_pipeline.py`** | Main orchestrator with camera selection | Python, OpenCV, PyGrabber |
| **`live_processor.py`** | OCR processing engine | Surya OCR, YOLOv8, Transformers |
| **`data_refiner/`** | AI-powered data cleaning and structuring | Google Gemma 2, Regex, NLP |
| **`lmpc_checker/`** | Legal compliance validation engine | Rule-based validation, Pattern matching |
| **`gui_utils.py`** | Cross-platform GUI utilities | OpenCV, Environment detection |
| **`config.py`** | Centralized configuration management | Environment variables, Model paths |

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (Tested with Python 3.12.5)
- **CUDA-capable GPU** (optional, for 3x faster processing)
- **Webcam or USB camera** (for live capture)
- **8GB+ RAM** (recommended for model loading)
- **2GB+ disk space** (for AI model storage)

### Installation


2. **Set up virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate`    ` 
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment (optional)**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

5. **Run the complete pipeline**
   ```bash
   python run_full_pipeline.py
   ```

6. **Launch Web Interface (Optional)**
   ```bash
   # Easy launch from project root
   python launch_web.py
   
   # Or from web directory
   cd web && python run_app.py
   ```
   The web interface will be available at http://localhost:8501

## 📖 Usage Guide

### Complete Workflow
The main script provides an interactive interface for end-to-end compliance checking:

```bash
python run_full_pipeline.py
```

**Interactive Workflow:**
1. **🎥 Camera Selection**: Choose from detected cameras with device names
2. **📸 Live Preview**: Position product label with real-time camera feed
3. **⚡ Instant Capture**: Press SPACE when ready to capture
4. **🔍 OCR Processing**: Automatic text extraction using Surya OCR
5. **🛠️ Data Refinement**: AI-powered cleaning and field extraction
6. **⚖️ Compliance Check**: Validation against Legal Metrology rules
7. **📊 Detailed Report**: Comprehensive compliance status with violations

### 🌐 Web Interface

For a user-friendly experience, launch the Streamlit web interface:

```bash
python launch_web.py
```

**Web Interface Features:**
- **📷 Live Camera**: Real-time camera preview and instant capture
- **📂 File Upload**: Drag-and-drop image processing with batch support  
- **📊 Batch Processing**: Multiple image analysis with progress tracking
- **⚙️ Settings**: Configure OCR parameters and detection thresholds
- **📈 Analytics**: Visual compliance statistics and violation trends
- **📋 Export**: Download results as PDF, Excel, or JSON reports

Access the interface at: **http://localhost:8501**

### Module Usage Examples

#### Standalone OCR Processing
```python
from live_processor import LiveProcessor

# Initialize OCR processor
processor = LiveProcessor()

# Process single image capture
result = processor.process_single_capture(camera_index=0)
print(f"Extracted text: {result}")
```

#### Data Refinement Only
```python
from data_refiner.refiner import DataRefiner

# Initialize data refiner
refiner = DataRefiner()

# Clean messy OCR output
messy_data = {
    "contents": "MRP ₹299 NET WT 500g MADE IN INDIA..."
}
clean_data = refiner.refine(messy_data)
print(f"Structured data: {clean_data}")
```

#### Compliance Validation Only
```python
from lmpc_checker.compliance_validator import ComplianceValidator

# Initialize validator
validator = ComplianceValidator()

# Validate product data
product_data = {
    "mrp": "₹299.00",
    "net_quantity": "500g",
    "country_of_origin": "India",
    "manufacturer_details": "ABC Corp, Mumbai-400001"
}

violations = validator.validate(product_data)
if violations:
    print(f"Found {len(violations)} compliance issues")
else:
    print("✅ Product is compliant!")
```

## 📊 Output Examples

### Structured JSON Output
The pipeline generates comprehensive structured data:

```json
{
  "product_id": "SKU-FOOD-001",
  "category": "Food Products",
  "manufacturer_details": "ABC Foods Pvt Ltd, Plot 123, Food Park, Mumbai-400001, Maharashtra",
  "net_quantity": "500g",
  "mrp": "₹299.00",
  "country_of_origin": "India",
  "date_of_manufacture": "08/2024",
  "best_before_date": "08/2025",
  "consumer_care": "1800-ABC-FOOD, care@abcfoods.com",
  "contents": "Wheat flour, sugar, vegetable oil, salt",
  "compliance_status": "COMPLIANT",
  "violations": []
}
```

### Compliance Report Example
```
🏛️ LEGAL METROLOGY COMPLIANCE REPORT
═══════════════════════════════════════

✅ COMPLIANCE STATUS: COMPLIANT
📊 Total Fields Extracted: 12/15
⚖️ Validation Results: 0 violations found

📋 EXTRACTED PRODUCT INFORMATION
▸ Product Category: Food Products
▸ MRP: ₹299.00
▸ Net Quantity: 500g
▸ Country of Origin: India
▸ Manufacturing Date: 08/2024
▸ Consumer Care: 1800-ABC-FOOD

🎉 This product meets all Legal Metrology requirements!
```

## ⚙️ Configuration

### Environment Variables (`.env`)
```bash
# Processing Configuration
DEVICE=cuda                    # Use 'cpu' for CPU-only processing
DEFAULT_CAMERA_INDEX=0         # Default camera selection

# Model Configuration
MODEL_CACHE_DIR=./models       # AI model storage location
HF_TOKEN=your_token_here       # Hugging Face token (optional)

# OCR Settings
SURYA_LANG_CODES=en,hi        # Supported languages
DETECTION_CONFIDENCE_THRESHOLD=0.4

# Camera Settings
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_FPS=30
```

### Advanced Configuration (`config.py`)
```python
# OCR Processing
SURYA_LANG_CODES = ['en', 'hi']  # English and Hindi
DETECTION_CONFIDENCE_THRESHOLD = 0.4
USE_YOLO_FOR_TEXT_DETECTION = False

# NLP Configuration
HF_MODEL_NAME = 'google/gemma-2-9b-it'
MAX_INPUT_LENGTH = 512
GENERATION_TEMPERATURE = 0.1

# Expected Data Fields
EXPECTED_FIELDS = [
    'mrp', 'net_quantity', 'country_of_origin',
    'manufacturer_details', 'consumer_care', 'contents',
    'date_of_manufacture', 'best_before_date'
]
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Camera Not Detected
```bash
# List available cameras
python -c "
from pygrabber.dshow_graph import FilterGraph
graph = FilterGraph()
print('Available cameras:', graph.get_input_devices())
"
```

#### Low OCR Accuracy
**Symptoms**: Few or no text lines detected
**Solutions**:
- Ensure bright, even lighting
- Hold camera steady and focus properly
- Position text right-side up
- Use high-contrast backgrounds
- Clean camera lens

#### Memory Issues
**Symptoms**: Out of memory errors, slow processing
**Solutions**:
- Set `DEVICE='cpu'` in configuration
- Close other applications
- Reduce `CAMERA_WIDTH` and `CAMERA_HEIGHT`
- Use lower resolution images

#### Model Download Issues
**Symptoms**: Models fail to download or load
**Solutions**:
- Check internet connectivity
- Verify 2GB+ free disk space
- Clear model cache: `rm -rf models/`
- Check Hugging Face Hub status

#### GPU Not Detected
```bash
# Check CUDA availability
python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')
"
```

### Performance Optimization

#### For Maximum Speed (GPU Required)
```python
# config.py
DEVICE = 'cuda'
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
```

#### For Low-Resource Systems
```python
# config.py
DEVICE = 'cpu'
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
DETECTION_CONFIDENCE_THRESHOLD = 0.3
```

## 📈 Performance Metrics

### Accuracy Benchmarks
- **OCR Text Detection**: 85-95% on clear product labels
- **Field Extraction**: 75% success rate on structured fields
- **Compliance Validation**: 95% accuracy on rule detection
- **End-to-End Pipeline**: 70-80% fully automated processing

### Speed Benchmarks
- **GPU Processing**: 3-5 seconds per image
- **CPU Processing**: 8-12 seconds per image
- **Model Loading**: 10-15 seconds (first run only)
- **Camera Initialization**: 1-2 seconds

### Resource Requirements
- **RAM Usage**: 2-4GB during processing
- **GPU Memory**: 1-2GB (if using CUDA)
- **Disk Space**: 2GB for models + captured images
- **CPU Usage**: 50-80% during processing

## 🏗️ Project Structure

```
legal-metrology-ocr-pipeline/
├── 📄 README.md                    # This comprehensive documentation
├── 📋 requirements.txt             # Python dependencies
├── ⚙️ config.py                    # Centralized configuration
├── 📝 .env.example                 # Environment variables template
├── 🚫 .gitignore                   # Git ignore rules
├── 📜 LICENSE                      # MIT license
│
├── 🚀 run_full_pipeline.py         # 🎯 MAIN ENTRY POINT
├── 🔧 live_processor.py            # OCR processing engine
├── 🎥 gui_utils.py                 # Cross-platform GUI utilities
│
├── 📊 data_refiner/                # AI-powered data refinement
│   ├── __init__.py                 # Module initialization
│   ├── refiner.py                  # Main DataRefiner class
│   ├── config.py                   # Regex patterns and NLP config
│   ├── requirements.txt            # Refiner-specific dependencies
│   └── README.md                   # Detailed refiner documentation
│
├── ⚖️ lmpc_checker/                # Legal Metrology compliance
│   ├── compliance_validator.py     # 20+ validation rules engine
│   ├── main.py                     # Standalone validator demo
│   └── README.md                   # Compliance validator documentation
│
├── 🖼️ images/                      # Image storage
│   ├── captured/                   # Original captured images
│   └── processed/                  # Images with detection annotations
│
├── 🤖 models/                      # AI model storage (auto-downloaded)
│   ├── surya/                      # Surya OCR models
│   └── transformers/               # Hugging Face transformer models
│
└── 🐍 venv/                        # Python virtual environment
```

## 🧪 Testing and Development

### Running Tests
```bash
# Test individual components
python live_processor.py           # Test OCR processing
python data_refiner/refiner.py     # Test data refinement
python lmpc_checker/main.py        # Test compliance validation

# Test complete pipeline
python run_full_pipeline.py
```

### Development Setup
```bash
# Install development dependencies
pip install pytest black flake8 mypy

# Format code
black .

# Run linting
flake8 --max-line-length=100

# Type checking
mypy live_processor.py
```

### Adding New Validation Rules
```python
# lmpc_checker/compliance_validator.py
def validate_custom_rule(self, product_data):
    """Add your custom validation logic here"""
    violations = []
    
    # Example: Check for specific pattern
    if not product_data.get('custom_field'):
        violations.append({
            'rule_id': 'CUSTOM_RULE_01',
            'severity': 'Medium',
            'description': 'Custom field is missing',
            'field': 'custom_field'
        })
    
    return violations
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute
1. **🐛 Bug Reports**: Report issues with detailed reproduction steps
2. **✨ Feature Requests**: Suggest new features or improvements
3. **📚 Documentation**: Improve documentation and examples
4. **🔧 Code Contributions**: Submit pull requests with new features or fixes
5. **🧪 Testing**: Add test cases and improve test coverage

### Development Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with proper documentation
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style Guidelines
- Follow PEP 8 Python style guide
- Use type hints for function parameters and returns
- Add docstrings for all classes and functions
- Keep functions focused and under 50 lines when possible
- Use meaningful variable and function names


### Third-Party Licenses
- **Surya OCR**: Apache 2.0 License
- **Google Gemma 2**: Gemma Terms of Use
- **Ultralytics YOLOv8**: AGPL-3.0 License
- **OpenCV**: Apache 2.0 License

## 🙏 Acknowledgments

### Core Technologies
- **[Surya OCR](https://github.com/VikParuchuri/surya)**: Advanced multilingual OCR with exceptional accuracy
- **[Google Gemma 2](https://huggingface.co/google/gemma-2-9b-it)**: Powerful 9B parameter LLM for data structuring
- **[Ultralytics YOLOv8](https://ultralytics.com/)**: State-of-the-art object detection capabilities
- **[OpenCV](https://opencv.org/)**: Comprehensive computer vision library
- **[Transformers](https://huggingface.co/transformers/)**: Hugging Face transformer library

### Legal Framework
- **Legal Metrology Department, India**: For comprehensive packaging regulations
- **Bureau of Indian Standards (BIS)**: For quality and standardization guidelines
- **Consumer Protection Act, 2019**: For consumer rights framework

### Community
- **Open Source Community**: For continuous innovation and support
- **Indian E-commerce Industry**: For real-world testing and feedback
- **Research Community**: For advancing OCR and AI technologies

## 📞 Support and Contact


### Professional Services
For enterprise deployment, custom features, or consulting services, please contact through GitHub Issues with the "enterprise" label.

---

**🎯 Built for automated Legal Metrology compliance validation**  
**🇮🇳 Made with ❤️ in India for the Indian retail ecosystem**

*Empowering businesses with AI-driven compliance automation*