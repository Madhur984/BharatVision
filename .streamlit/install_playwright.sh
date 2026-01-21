#!/bin/bash
# Post-install script for Streamlit Cloud
# Installs Playwright browsers after pip install

echo "Installing Playwright browsers..."
playwright install chromium --with-deps

echo "Playwright installation complete!"
