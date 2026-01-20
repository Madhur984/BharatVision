@echo off
REM BharatVision Development Environment Setup Script for Windows

echo Setting up BharatVision development environment...

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)
echo Python detected

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install production dependencies
echo Installing production dependencies...
pip install -r requirements.txt
echo Production dependencies installed

REM Install development dependencies
echo Installing development dependencies...
pip install -r requirements-dev.txt
echo Development dependencies installed

REM Setup environment file
if not exist ".env" (
    echo Setting up environment configuration...
    copy .env.example .env
    echo Created .env file from template
    echo WARNING: Please edit .env file with your configuration
) else (
    echo .env file already exists
)

REM Install pre-commit hooks
echo Installing pre-commit hooks...
pre-commit install
echo Pre-commit hooks installed

REM Create necessary directories
echo Creating necessary directories...
if not exist "images\captured" mkdir images\captured
if not exist "images\processed" mkdir images\processed
if not exist "models" mkdir models
if not exist "logs" mkdir logs
if not exist "tests\fixtures" mkdir tests\fixtures
echo Directories created

REM Download YOLO model if not exists
if not exist "yolov8n.pt" (
    if not exist "backend\yolov8n.pt" (
        echo Downloading YOLOv8 model...
        python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
        echo YOLO model downloaded
    )
) else (
    echo YOLO model already exists
)

REM Run tests
echo Running tests...
pytest tests/ -v --tb=short
if errorlevel 1 (
    echo WARNING: Some tests failed (this is normal for initial setup)
)

REM Summary
echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your configuration
echo 2. Run tests: pytest tests/ -v
echo 3. Start API server: cd backend ^&^& python api_server.py
echo 4. Start web app: python launch_web.py
echo.
echo Useful commands:
echo   Activate venv:  venv\Scripts\activate.bat
echo   Run tests:      pytest tests/ -v
echo   Format code:    black backend/ --line-length=100
echo   Lint code:      flake8 backend/
echo   Type check:     mypy backend/
echo.

pause
