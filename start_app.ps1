# start_app.ps1 — Bootstrap script for Windows (PowerShell)
# Activates venv (if present), installs requirements and starts Streamlit with AUTO_INSTALL_DEPS enabled.

$ErrorActionPreference = 'Stop'

# Activate venv if present
if (Test-Path .\venv\Scripts\Activate.ps1) {
    Write-Host "Activating virtualenv..."
    . .\venv\Scripts\Activate.ps1
}

# Ensure pip is up-to-date
python -m pip install --upgrade pip

# Install core requirements (non-blocking if already installed)
python -m pip install -r requirements.txt

# Optionally install full web/dev requirements if file exists
if (Test-Path .\web\requirements.local.txt) {
    Write-Host "Installing local web requirements..."
    python -m pip install -r .\web\requirements.local.txt
}

# Set env var to indicate auto-install completed
$env:AUTO_INSTALL_DEPS = "1"

# Start Streamlit
Write-Host "Starting Streamlit app..."
streamlit run web/streamlit_app.py
