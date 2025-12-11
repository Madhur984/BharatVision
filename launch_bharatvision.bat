@echo off
echo Starting BharatVision...
echo.
echo [1/2] Launching ML Service (Port 8000)...
start "BharatVision ML Service" cmd /k "uvicorn ml_service.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Launching Web Dashboard...
start "BharatVision Web App" cmd /k "streamlit run web/streamlit_app.py"

echo.
echo Services launched in new windows!
echo Web App: http://localhost:8501
echo API Docs: http://localhost:8000/docs
