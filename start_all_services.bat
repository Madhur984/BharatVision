@echo off
REM BharatVision Complete Stack Startup Script

echo.
echo ====================================================================
echo                    BharatVision Stack Startup
echo ====================================================================
echo.

REM Check if venv exists
if not exist venv (
    echo [ERROR] Virtual environment not found. Run 'python -m venv venv' first.
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

echo [1/3] Installing dependencies...
pip install -q fastapi uvicorn python-multipart pydantic 2>nul

echo [2/3] Starting FastAPI Backend (http://localhost:8000)...
start "BharatVision API Server" cmd /k "cd /d %cd% && python backend/api_server.py"

timeout /t 3 /nobreak

echo [3/3] Starting Streamlit Frontend (http://localhost:8502)...
start "BharatVision Streamlit App" cmd /k "cd /d %cd% && python -m streamlit run web/streamlit_app.py"

timeout /t 2 /nobreak

echo.
echo ====================================================================
echo.
echo ✓ BharatVision Stack is starting!
echo.
echo Frontend:  http://localhost:8502
echo API Docs:  http://localhost:8000/docs
echo HTML UI:   Open frontend/public/index.html in your browser
echo.
echo Close any window to stop that service.
echo.
echo ====================================================================
echo.

pause
