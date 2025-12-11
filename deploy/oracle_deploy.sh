#!/bin/bash

# BharatVision Oracle Cloud ARM Deployment Script
# Run this on your Oracle Cloud VM.Standard.A1.Flex instance

set -e

echo "======================================"
echo "BharatVision Deployment Script"
echo "Oracle Cloud ARM (Ubuntu 22.04)"
echo "======================================"

# Update system
echo "[1/8] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "[2/8] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "[3/8] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo apt-get install -y docker-compose
    echo "Docker Compose installed"
else
    echo "Docker Compose already installed"
fi

# Install Ollama
echo "[4/8] Installing Ollama (ARM version)..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
    echo "Ollama installed successfully"
else
    echo "Ollama already installed"
fi

# Pull Gemma2 model
echo "[5/8] Pulling Gemma2 model (this may take 10-15 minutes)..."
ollama pull gemma2

# Clone repository (if not already done)
echo "[6/8] Setting up project..."
if [ ! -d "bharatvision" ]; then
    echo "Please upload your project files to this server"
    echo "You can use: scp -r /path/to/project ubuntu@<your-ip>:~/bharatvision"
    exit 1
fi

cd bharatvision/bharatvision_api

# Build and start services
echo "[7/8] Building and starting Docker containers..."
docker-compose down
docker-compose build
docker-compose up -d

# Wait for services to be healthy
echo "[8/8] Waiting for services to start..."
sleep 30

# Check health
echo "======================================"
echo "Checking service health..."
echo "======================================"

API_HEALTH=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "unhealthy")
OLLAMA_HEALTH=$(curl -s http://localhost:11434/api/tags 2>/dev/null && echo "healthy" || echo "unhealthy")

echo "API Status: $API_HEALTH"
echo "Ollama Status: $OLLAMA_HEALTH"

if [ "$API_HEALTH" == "healthy" ] && [ "$OLLAMA_HEALTH" == "healthy" ]; then
    echo "======================================"
    echo "✅ Deployment Successful!"
    echo "======================================"
    echo ""
    echo "Your API is now running at:"
    echo "http://$(curl -s ifconfig.me):8000"
    echo ""
    echo "Next steps:"
    echo "1. Configure Oracle Cloud Security List to allow port 8000"
    echo "2. Test API: curl http://$(curl -s ifconfig.me):8000/health"
    echo "3. Configure your mobile app to connect to this endpoint"
    echo ""
    echo "View logs: docker-compose logs -f"
    echo "Stop services: docker-compose down"
    echo "======================================"
else
    echo "❌ Deployment failed. Check logs:"
    echo "docker-compose logs"
fi
