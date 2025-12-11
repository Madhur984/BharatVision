@echo off
REM Expose BharatVision API (Port 8000) to Public Internet
echo ==========================================
echo Exposing BharatVision API to Public Internet
echo ==========================================
echo.
echo [1/2] Checking if API is running...
netstat -ano | findstr :8000 > nul
if %errorlevel% neq 0 (
    echo WARNING: API does not seem to be running on port 8000.
    echo Please run 'python simple_api.py' in another terminal first!
    pause
    exit /b
) else (
    echo API is running.
)

echo.
echo [2/2] Creating Tunnel...
echo.
echo ******************************************************
echo COPY THE URL BELOW THAT LOOKS LIKE:
echo https://something-random.trycloudflare.com
echo ******************************************************
echo.

REM Check for cloudflared
where cloudflared > nul 2>&1
if %errorlevel% neq 0 (
    echo cloudflared not found. Downloading...
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe -o cloudflared.exe
)

REM Run tunnel
cloudflared tunnel --url http://localhost:8000
