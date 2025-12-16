<h1 align="center">
🇮🇳 LEGAL METROLOGY OCR COMPLIANCE PIPELINE
</h1>

<h2 align="center">
AI-Powered Automated Compliance Validation for Packaged Commodities
</h2>

<p align="center">
<b>
An end-to-end, production-ready system that uses Computer Vision, OCR,  
and Large Language Models to automatically verify compliance with  
Indian Legal Metrology (Packaged Commodities) Rules, 2011.
</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue"/>
  <img src="https://img.shields.io/badge/OCR-Surya%20v0.16.7-orange"/>
  <img src="https://img.shields.io/badge/LLM-Gemma--2--9B-blue"/>
  <img src="https://img.shields.io/badge/Status-Production%20Ready-success"/>
  <img src="https://img.shields.io/badge/License-MIT-green"/>
</p>

<hr/>




🇮🇳 Legal Metrology OCR Compliance Pipeline
AI-Powered Automated Compliance Validation for Packaged Commodities

An end-to-end, production-ready system that uses Computer Vision, OCR, and Large Language Models to automatically verify Legal Metrology compliance of product labels — at scale.










🚀 Why This Project Matters

Every day, millions of packaged products are sold online in India.
Ensuring that each product complies with the Legal Metrology (Packaged Commodities) Rules, 2011 is:

❌ Manual

❌ Time-consuming

❌ Error-prone

✅ This project solves that.

By combining OCR + AI + Rule-based validation, this system can:

Instantly read product labels

Extract legally required declarations

Detect violations

Generate structured compliance reports

No manual inspection. No guesswork. Just compliance.

🧠 What This System Does (In Simple Words)

📷 Captures or uploads a product image

🔍 Reads all text from the packaging using advanced OCR

🤖 Structures messy text into clean fields using AI

⚖️ Checks every field against Legal Metrology rules

📊 Generates a clear compliance report with violations

🏗️ Architecture Overview

PackNetra Microservices Architecture
Designed for scalability, cloud deployment, and real-world usage.

Frontend (Streamlit)
        |
        | REST API
        ↓
ML Inference Service (FastAPI)
        |
        ├── YOLOv8 (Text Region Detection)
        ├── Surya OCR (Text Recognition)
        ├── Gemma 2 LLM (Data Structuring)
        └── Rule Engine (Legal Validation)

Why Microservices?

🔹 UI runs on low-resource machines

🔹 ML runs on GPU-enabled servers

🔹 Easy cloud deployment (AWS / Jio Cloud / Azure)

🔹 Scales independently

✨ Key Features
🧩 Modular & Scalable Design

Fully decoupled UI and ML services

REST-based communication

Docker-ready for cloud deployment

🔍 Advanced OCR Engine

Surya OCR v0.16.7

Multilingual support (English + Hindi)

Handles complex label layouts

Works on real-world noisy images

Accuracy: 85–95% on clear labels

🤖 AI-Driven Field Extraction

Google Gemma-2 (9B)

Converts raw OCR text into structured data

Hybrid approach:

Regex (precision)

NLP (context awareness)

Automatically extracts:

MRP

Net Quantity

Dates

Manufacturer details

Consumer care info

Country of origin

⚖️ Legal Metrology Compliance Engine

20+ validation rules

Severity classification:

🔴 Critical

🟠 High

🟡 Medium

Clear violation descriptions

Actionable recommendations

🧪 End-to-End Pipeline
graph TD
    A[Image Capture] --> B[Surya OCR]
    B --> C[Regex + NLP Refinement]
    C --> D[Legal Rule Validation]
    D --> E[Compliance Report]

🧰 Technology Stack
Layer	Tools
OCR	Surya OCR
Object Detection	YOLOv8
NLP / LLM	Google Gemma-2 (9B)
Backend	FastAPI
Frontend	Streamlit
Vision	OpenCV
Deployment	Docker
Language	Python
🚀 Quick Start
1️⃣ Clone the Repository
git clone https://github.com/your-repo/legal-metrology-ocr-pipeline.git
cd legal-metrology-ocr-pipeline

2️⃣ Create Virtual Environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Run the Full Pipeline
python run_full_pipeline.py

5️⃣ Launch Web Interface (Optional)
python launch_web.py


📍 Open: http://localhost:8501

🌐 Web Interface Highlights

📷 Live camera capture

📂 Batch image upload

📊 Visual compliance dashboard

📈 Violation analytics

📥 Export reports (PDF / Excel / JSON)

📊 Sample Output
Structured JSON
{
  "mrp": "₹299.00",
  "net_quantity": "500g",
  "country_of_origin": "India",
  "manufacturer_details": "ABC Foods Pvt Ltd, Mumbai",
  "compliance_status": "COMPLIANT",
  "violations": []
}

Compliance Report
✅ STATUS: COMPLIANT
📦 Fields Extracted: 12 / 15
⚖️ Violations Found: 0

🎉 Product meets all Legal Metrology requirements

⚙️ Configuration

Easily configurable using .env or config.py

DEVICE=cuda
SURYA_LANG_CODES=en,hi
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720

📈 Performance Benchmarks
Metric	Value
OCR Accuracy	85–95%
Compliance Accuracy	~95%
GPU Speed	3–5 sec/image
CPU Speed	8–12 sec/image
🏗️ Project Structure
legal-metrology-ocr-pipeline/
├── run_full_pipeline.py
├── live_processor.py
├── data_refiner/
├── lmpc_checker/
├── web/
├── models/
├── config.py
└── README.md

🧪 Testing
python live_processor.py
python data_refiner/refiner.py
python lmpc_checker/main.py

🤝 Contributing

Contributions are welcome!

🐛 Bug fixes

✨ New features

📚 Documentation

🧪 Test cases

Just fork → code → PR 🚀

📜 Licenses

Surya OCR — Apache 2.0

Gemma-2 — Google Terms

YOLOv8 — AGPL-3.0

OpenCV — Apache 2.0

🙏 Acknowledgements

Legal Metrology Department, India

Open-source community

SIH & research ecosystem

🎯 Final Note

This project is built not just as a prototype, but as a deployable, scalable, government-grade compliance system.

🇮🇳 Made in India — for India’s digital commerce ecosystem
💡 Automating trust with AI

