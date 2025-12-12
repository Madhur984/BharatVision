#!/bin/bash

# BharatVision Streamlit Deployment on Oracle Cloud ARM
# Run this script on your Oracle Cloud VM instance

set -e

echo "=========================================="
echo "BharatVision Streamlit Deployment"
echo "Oracle Cloud ARM (Ubuntu 22.04)"
echo "=========================================="

# Update system
echo "[1/9] Updating system..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.11
echo "[2/9] Installing Python 3.11..."
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# Install system dependencies
echo "[3/9] Installing system dependencies..."
sudo apt-get install -y tesseract-ocr git curl

# Install Docker (for Ollama)
echo "[4/9] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Ollama
echo "[5/9] Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Pull 2 model
echo "[6/9] Pulling 2 model (15-20 minutes)..."
ollama pull 2

# Clone/upload project
echo "[7/9] Setting up project..."
cd ~
if [ ! -d "bharatvision" ]; then
    echo "Please upload your project to ~/bharatvision"
    echo "Use: scp -r /local/path ubuntu@<ip>:~/bharatvision"
    exit 1
fi

cd bharatvision

# Create virtual environment
echo "[8/9] Creating Python environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service for Streamlit
echo "[9/9] Creating Streamlit service..."
sudo tee /etc/systemd/system/bharatvision.service > /dev/null <<EOF
[Unit]
Description=BharatVision Streamlit App
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/bharatvision
Environment="PATH=$HOME/bharatvision/venv/bin"
ExecStart=$HOME/bharatvision/venv/bin/streamlit run web/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable bharatvision
sudo systemctl start bharatvision

# Open firewall
echo "Opening firewall port 8501..."
sudo ufw allow 8501
sudo ufw reload

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)

echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Your Streamlit app is running at:"
echo "http://$PUBLIC_IP:8501"
echo ""
echo "Next steps:"
echo "1. Configure Oracle Cloud Security List to allow port 8501"
echo "2. Visit the URL above to test"
echo "3. Use this URL in Flutter WebView app"
echo ""
echo "Service commands:"
echo "- Status: sudo systemctl status bharatvision"
echo "- Logs: sudo journalctl -u bharatvision -f"
echo "- Restart: sudo systemctl restart bharatvision"
echo "- Stop: sudo systemctl stop bharatvision"
echo "=========================================="
