#!/bin/bash
# BharatVision Complete Stack Startup Script (Linux/Mac)

echo ""
echo "===================================================================="
echo "                    BharatVision Stack Startup"
echo "===================================================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found. Run 'python3 -m venv venv' first."
    exit 1
fi

# Activate venv
source venv/bin/activate

echo "[1/3] Installing dependencies..."
pip install -q fastapi uvicorn python-multipart pydantic 2>/dev/null

echo "[2/3] Starting FastAPI Backend (http://localhost:8000)..."
python backend/api_server.py &
API_PID=$!

sleep 3

echo "[3/3] Starting Streamlit Frontend (http://localhost:8502)..."
python -m streamlit run web/streamlit_app.py &
STREAMLIT_PID=$!

sleep 2

echo ""
echo "===================================================================="
echo ""
echo "✓ BharatVision Stack is starting!"
echo ""
echo "Frontend:  http://localhost:8502"
echo "API Docs:  http://localhost:8000/docs"
echo "HTML UI:   Open frontend/public/index.html in your browser"
echo ""
echo "PIDs: API=$API_PID, Streamlit=$STREAMLIT_PID"
echo "Kill services: kill $API_PID $STREAMLIT_PID"
echo ""
echo "===================================================================="
echo ""

wait
