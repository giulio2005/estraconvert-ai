#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 EstraConvert Setup Script${NC}"
echo "============================"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js found${NC}"

# Check for Redis (optional for setup, but needed for run)
if ! command -v redis-server &> /dev/null; then
    echo -e "${YELLOW}⚠️  Redis server not found. Please install Redis before running the application.${NC}"
    echo "   macOS: brew install redis"
    echo "   Ubuntu: sudo apt-get install redis-server"
else
    echo -e "${GREEN}✅ Redis server found${NC}"
fi

# Check for Tesseract (needed for OCR)
if ! command -v tesseract &> /dev/null; then
    echo -e "${YELLOW}⚠️  Tesseract OCR not found. Please install Tesseract before processing PDFs.${NC}"
    echo "   macOS: brew install tesseract"
    echo "   Ubuntu: sudo apt-get install tesseract-ocr"
else
    echo -e "${GREEN}✅ Tesseract OCR found${NC}"
fi

echo ""
echo -e "${YELLOW}📦 Setting up Backend...${NC}"
cd backend

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs
mkdir -p uploads

# Check .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit backend/.env and add your API keys!${NC}"
    else
        echo -e "${RED}❌ .env.example not found!${NC}"
    fi
fi

cd ..

echo ""
echo -e "${YELLOW}📦 Setting up Frontend...${NC}"
cd frontend

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

cd ..

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "To start the application:"
echo "  ./start_all.sh"
