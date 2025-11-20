#!/bin/bash

# Document Classification System Setup Script
# This script automates the setup process

set -e

echo "================================================"
echo "  Document Classification System Setup"
echo "  Multi-Agent AI with Groq & MCP"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

echo ""

# Create directory structure
echo "Creating directory structure..."
mkdir -p input_pdfs
mkdir -p output
mkdir -p data
mkdir -p logs
# mkdir -p src/{agents,api,config,database,mcp,tasks,ui,workflow}
echo -e "${GREEN}✓ Directories created${NC}"

echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Database Configuration
DATABASE_URL=postgresql://docuser:docpass123@postgres:5432/document_classifier
POSTGRES_USER=docuser
POSTGRES_PASSWORD=docpass123
POSTGRES_DB=document_classifier

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Application Settings
APP_NAME=DocumentClassifierAgent
APP_VERSION=1.0.0
DEBUG=True
LOG_LEVEL=INFO

# MCP Configuration
MCP_SERVER_HOST=mcp_server
MCP_SERVER_PORT=8001

# File System Configuration
INPUT_FOLDER=/app/input_pdfs
OUTPUT_BASE_FOLDER=/app/output
TEMP_FOLDER=/tmp/document_processing

# Model Configuration
GROQ_TEXT_MODEL=llama-3.3-70b-versatile
GROQ_VISION_MODEL=llama-3.2-90b-vision-preview

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Processing Configuration
MAX_PAGES_PER_DOCUMENT=100
BATCH_SIZE=5
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please edit .env and add your GROQ_API_KEY${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists, skipping creation${NC}"
fi

echo ""

# Check if GROQ_API_KEY is set
if ! grep -q "GROQ_API_KEY=gsk_" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠ Warning: GROQ_API_KEY not configured in .env${NC}"
    echo "Please obtain an API key from https://console.groq.com/"
    read -p "Press Enter to continue or Ctrl+C to exit and configure..."
fi

echo ""

# Create __init__.py files
# echo "Creating Python package files..."
# find src -type d -exec touch {}/__init__.py \;
# echo -e "${GREEN}✓ Package files created${NC}"

echo ""

# Build and start services
echo "Building Docker containers (this may take a few minutes)..."
docker-compose build

echo ""
echo -e "${GREEN}✓ Build completed${NC}"

echo ""
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U docuser > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL: Running${NC}"
else
    echo -e "${RED}✗ PostgreSQL: Not responding${NC}"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis: Running${NC}"
else
    echo -e "${RED}✗ Redis: Not responding${NC}"
fi

# Check API
sleep 5
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API Server: Running${NC}"
else
    echo -e "${YELLOW}⚠ API Server: Starting up...${NC}"
fi

# Check Streamlit
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Streamlit UI: Running${NC}"
else
    echo -e "${YELLOW}⚠ Streamlit UI: Starting up...${NC}"
fi

# Check MCP Server
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MCP Server: Running${NC}"
else
    echo -e "${YELLOW}⚠ MCP Server: Starting up...${NC}"
fi

echo ""
echo "================================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "================================================"
echo ""
echo "Access the system:"
echo "  • Streamlit UI:  http://localhost:8501"
echo "  • API Docs:      http://localhost:8000/docs"
echo "  • MCP Server:    http://localhost:8001"
echo ""
echo "Next steps:"
echo "  1. Ensure GROQ_API_KEY is set in .env"
echo "  2. Place PDF files in ./input_pdfs/"
echo "  3. Open http://localhost:8501 to start processing"
echo ""
echo "Useful commands:"
echo "  • View logs:     docker-compose logs -f"
echo "  • Stop system:   docker-compose down"
echo "  • Restart:       docker-compose restart"
echo "  • View status:   docker-compose ps"
echo ""
echo "For more information, see README.md"
echo "================================================"