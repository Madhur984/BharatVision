@echo off
REM BharatVision Local Testing with Public URL
REM This makes your local Streamlit accessible from anywhere

echo ==========================================
echo BharatVision Public URL Setup
echo ==========================================
echo.

REM Check if Streamlit is running
echo [1/3] Checking if Streamlit is running...
netstat -ano | findstr :8501 > nul
if %errorlevel% equ 0 (
    echo Streamlit is already running on port 8501
) else (
    echo Starting Streamlit...
    start "Streamlit Server" python launch_web.py
    timeout /t 10
)

REM Install cloudflared if needed
echo.
echo [2/3] Setting up Cloudflare Tunnel...
where cloudflared > nul 2>&1
if %errorlevel% neq 0 (
    echo Downloading cloudflared...
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe -o cloudflared.exe
)

REM Create tunnel
echo.
echo [3/3] Creating public URL for your Streamlit app...
echo.
echo ==========================================
echo Your app will be accessible at a public URL
echo Keep this window open!
echo ==========================================
echo.

cloudflared tunnel --url http://localhost:8501

pause
