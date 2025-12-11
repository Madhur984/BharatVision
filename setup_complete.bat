@echo off
REM Complete Environment Setup and Verification Script
REM For Legal Metrology OCR Pipeline

cls
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo                      LEGAL METROLOGY SYSTEM - COMPLETE SETUP
echo ════════════════════════════════════════════════════════════════════════════════
echo.

REM Check Python installation
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python is installed
    python --version
) else (
    echo ✗ Python is not installed. Please install Python 3.8+
    exit /b 1
)

REM Activate venv if exists, create if not
echo.
echo [2/5] Activating virtual environment...
if exist venv\ (
    echo ✓ Virtual environment found
    call venv\Scripts\activate.bat
) else (
    echo ! Creating new virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo ✓ Virtual environment created and activated
)

REM Install/Update dependencies
echo.
echo [3/5] Installing required dependencies...
python -m pip install --upgrade pip -q
python -m pip install ^
    selenium webdriver-manager beautifulsoup4 lxml ^
    requests pydantic pillow pandas openpyxl ^
    -q
if %errorlevel% equ 0 (
    echo ✓ All dependencies installed successfully
) else (
    echo ✗ Failed to install dependencies
    exit /b 1
)

REM Run environment validation
echo.
echo [4/5] Validating environment...
python test_venv_environment.py
if %errorlevel% equ 0 (
    echo ✓ Environment validation successful
) else (
    echo ✗ Environment validation failed
    exit /b 1
)

REM Show instructions
echo.
echo [5/5] Setup Summary
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo ✓ All systems initialized successfully!
echo.
echo Next Steps:
echo ───────────
echo.
echo 1. Start Backend:
echo    python test_crawler.py
echo.
echo 2. Start Frontend (in separate terminal):
echo    cd frontend
echo    npm install
echo    npm start
echo.
echo 3. Test Image Extraction:
echo    python -c "from backend.image_extractor import ImageExtractor; print('✓ Ready')"
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo.
pause
