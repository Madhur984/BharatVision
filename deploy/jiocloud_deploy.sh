#!/bin/bash

# Jio Cloud Deployment Script for Legal Metrology Pipeline
# Supports Ubuntu/Debian based VMs
# Usage: ./jiocloud_deploy.sh

set -e

echo "=========================================="
echo "🚀 Jio Cloud Deployment - Legal Metrology pipeline"
echo "=========================================="

# 1. Update System
echo "[1/7] 📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Docker
echo "[2/7] 🐳 Installing Docker environment..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installed."
else
    echo "✅ Docker already installed."
fi

# 3. Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt-get install -y docker-compose-plugin
    # Alias if needed or rely on 'docker compose'
else
     echo "✅ Docker Compose already installed."
fi

# 4. Install Ollama (Native) - Required for local LLM inference
echo "[3/7] 🦙 Installing Ollama (for Gemma2 model)..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
    echo "✅ Ollama installed."
else
    echo "✅ Ollama already installed."
fi

# 5. Pull ML Models
echo "[4/7] 📥 Downloading Gemma2 Model (This may take time)..."
# Check if model exists or just pull
ollama pull gemma2
echo "✅ Gemma2 Model ready."

# 6. Setup Project Directory
PROJECT_DIR="legal-metrology-ocr"
echo "[5/7] 📂 Setting up project context..."

# We assume the user creates/commands this from the root of the project
# If this script is run remotely, we expect the files to be there.

if [ ! -f "docker-compose.yml" ]; then
    echo "⚠️  WARNING: docker-compose.yml not found in current directory."
    echo "   Please make sure you have uploaded your project files to this server."
    echo "   Running: pwd"
    pwd
    echo "   Listing files:"
    ls -la
    
    if [ -d "$PROJECT_DIR" ]; then
        echo "   Found $PROJECT_DIR directory. Entering..."
        cd "$PROJECT_DIR"
    else
        echo "❌ Deployment halted. Please upload your code first." 
        exit 1
    fi
fi

# 7. Build and Run
echo "[6/7] 🏗️  Building and Starting Services..."
# Stop existing
sudo docker compose down || true

# Build
sudo docker compose build

# Up
sudo docker compose up -d

echo "[7/7] ⏳ Waiting for services to initialize..."
sleep 20

# Health Check
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
WEB_Status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/_stcore/health || echo "000")

echo "=========================================="
echo "✅ Deployment Finished!"
echo "=========================================="
echo "📊 Status Report:"
echo "   - ML API: $API_STATUS (Expected 200/404)"
echo "   - Web App: $WEB_Status (Expected 200)"
echo ""
echo "🌍 Access your application at:"
echo "   - Streamlit App: http://<YOUR_PUBLIC_IP>:8501"
echo "   - ML API Docs:   http://<YOUR_PUBLIC_IP>:8000/docs"
echo ""
echo "👉 Note: Ensure functionality of Port 8501 and 8000 in your Jio Cloud Security Group / Firewall."
echo "=========================================="
