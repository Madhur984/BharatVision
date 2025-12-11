@echo off
echo ===========================================
echo Deploying BharatVision API to Hugging Face Cloud
echo ===========================================
echo.

REM Add Remote if not exists
git remote remove space 2>nul
git remote add space https://huggingface.co/spaces/madhur984/bharatvision-ml-api

echo [1/3] Adding files...
git add Dockerfile requirements_space.txt simple_api.py backend/ecommerce_scraper.py .env.cloud

echo [2/3] Committing changes...
git commit -m "Deploy Local OCR (Surya) -> Cloud Space"

echo [3/3] Pushing to Cloud (This might fail if you need login)...
git push space main -f

echo.
echo If the above command failed asking for password:
echo 1. Run 'huggingface-cli login' in terminal
echo 2. Run this script again.
echo.
pause
