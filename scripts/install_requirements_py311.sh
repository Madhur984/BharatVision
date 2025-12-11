#!/usr/bin/env bash
# Install full requirements into a Python 3.11 venv
# Usage: VENV_PATH=/home/adminuser/venv ./scripts/install_requirements_py311.sh


set -uo pipefail

# Allow the script to continue if optional packages fail to build;
# we'll report missing packages afterwards. This is important for
# environments (Windows / Python versions) where some heavy packages
# don't have wheels and fail to compile from source.

VENV_PATH="${VENV_PATH:-/home/adminuser/venv}"

if [ ! -x "$VENV_PATH/bin/python" ]; then
  echo "ERROR: python not found in venv at $VENV_PATH/bin/python"
  echo "Create a Python 3.11 venv first, e.g. with: python3.11 -m venv $VENV_PATH"
  exit 2
fi

PYTHON="$VENV_PATH/bin/python"
PIP="$VENV_PATH/bin/pip"

echo "Using python: $($PYTHON -V) at $PYTHON"

echo "Upgrading pip, setuptools, wheel..."
$PYTHON -m pip install --upgrade pip setuptools wheel || {
  echo "Warning: pip upgrade failed, continuing with existing pip.";
}

echo "Attempting to install PyTorch CPU wheels (pre-install) compatible with Linux manylinux..."
# Adjust torch versions here if you need a different one for your environment
TO_INSTALL_TORCH=("torch==2.1.2" "torchvision==0.16.2")

for pkg in "${TO_INSTALL_TORCH[@]}"; do
  echo "Installing $pkg from PyTorch CPU index..."
  $PIP install --index-url https://download.pytorch.org/whl/cpu "$pkg" --no-deps || {
    echo "Warning: could not install $pkg from CPU index. Will continue and try overall install."
  }
done

echo "Installing full requirements from requirements.full.txt (this may take a while)"
if [ ! -f requirements.full.txt ]; then
  echo "ERROR: requirements.full.txt not found in repo root."
  exit 3
fi

LOGFILE="install_full_requirements.log"
echo "Running: $PIP install -r requirements.full.txt | tee $LOGFILE"
# Run install but do not exit the script on failure; capture exit code
$PIP install -r requirements.full.txt 2>&1 | tee "$LOGFILE"
INSTALL_EXIT=${PIPESTATUS[0]:-${PIPESTATUS[0]}}

if [ "$INSTALL_EXIT" -ne 0 ]; then
  echo "Warning: pip install returned non-zero exit code: $INSTALL_EXIT"
  echo "Check the log file: $LOGFILE for details. We'll continue and run verification to list any missing modules."
else
  echo "pip install completed successfully."
fi

echo "Running post-install verification..."
# Use the venv python to run the verification script
$PYTHON scripts/verify_install.py || true

echo "Done. If any imports above failed, inspect $LOGFILE and consider installing the failing packages manually or using Docker for a reproducible Linux environment." 

