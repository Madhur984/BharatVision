@echo off
TITLE BharatVision Server Manager
echo ==================================================
echo   BharatVision Local Cloud Server
echo ==================================================

:: 1. Setup Environment
echo [1/4] Setting up Python Environment...
if not exist ".venv" (
    echo    Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements_frontend.txt

:: 2. Start ML API
echo [2/4] Starting ML API (Port 8000)...
start "BharatVision ML API" /min cmd /k "call .venv\Scripts\activate && uvicorn simple_api:app --host 0.0.0.0 --port 8000 --reload"

:: 3. Start Streamlit
echo [3/4] Starting Streamlit App (Port 8501)...
start "BharatVision Frontend" /min cmd /k "call .venv\Scripts\activate && streamlit run web/streamlit_app.py --server.port 8501 --server.address 0.0.0.0"

:: 4. Start Cloudflare Tunnel
echo [4/4] Exposing to Public Internet...
if exist "cloudflared.exe" (
    echo    Starting Cloudflare Tunnel...
    echo    ------------------------------------------
    echo    LOOK FOR THE URL BELOW (e.g., https://....trycloudflare.com)
    echo    ------------------------------------------
    cloudflared.exe tunnel --url http://localhost:8501
) else (
    echo    ERROR: cloudflared.exe not found in project root!
    pause
)
