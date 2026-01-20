#!/bin/bash
# BharatVision Development Environment Setup Script

set -e  # Exit on error

echo "🚀 Setting up BharatVision development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python_version=$(python --version 2>&1 | awk '{print $2}')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python $required_version or higher is required${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $python_version detected${NC}"

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install production dependencies
echo -e "${YELLOW}Installing production dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Production dependencies installed${NC}"

# Install development dependencies
echo -e "${YELLOW}Installing development dependencies...${NC}"
pip install -r requirements-dev.txt
echo -e "${GREEN}✓ Development dependencies installed${NC}"

# Setup environment file
echo -e "${YELLOW}Setting up environment configuration...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file from template${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env file with your configuration${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Install pre-commit hooks
echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
pre-commit install
echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p images/captured
mkdir -p images/processed
mkdir -p models
mkdir -p logs
mkdir -p tests/fixtures
echo -e "${GREEN}✓ Directories created${NC}"

# Download YOLO model if not exists
echo -e "${YELLOW}Checking YOLO model...${NC}"
if [ ! -f "yolov8n.pt" ] && [ ! -f "backend/yolov8n.pt" ]; then
    echo -e "${YELLOW}Downloading YOLOv8 model...${NC}"
    python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
    echo -e "${GREEN}✓ YOLO model downloaded${NC}"
else
    echo -e "${GREEN}✓ YOLO model already exists${NC}"
fi

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
pytest tests/ -v --tb=short || echo -e "${YELLOW}⚠️  Some tests failed (this is normal for initial setup)${NC}"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit .env file with your configuration"
echo "2. Run tests: pytest tests/ -v"
echo "3. Start API server: cd backend && python api_server.py"
echo "4. Start web app: python launch_web.py"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  Activate venv:  source venv/bin/activate"
echo "  Run tests:      pytest tests/ -v"
echo "  Format code:    black backend/ --line-length=100"
echo "  Lint code:      flake8 backend/"
echo "  Type check:     mypy backend/"
echo ""
