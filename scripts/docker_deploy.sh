#!/bin/bash
# Docker deployment script for LBW Decision System

set -e

echo "================================"
echo "LBW System - Docker Deployment"
echo "================================"
echo ""

# Parse arguments
ENVIRONMENT=${1:-production}
BUILD_FLAG=${2:-}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Deployment environment: ${ENVIRONMENT}${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed"
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo "Please edit .env file with your settings"
    echo ""
fi

# Build image if requested
if [ "$BUILD_FLAG" == "--build" ] || [ "$BUILD_FLAG" == "-b" ]; then
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker-compose build
    echo -e "${GREEN}✓ Image built successfully${NC}"
    echo ""
fi

# Check X11 forwarding for display
if [ "$ENVIRONMENT" == "production" ]; then
    echo -e "${YELLOW}Setting up X11 forwarding for display...${NC}"
    xhost +local:docker || echo "Warning: Could not set xhost"
    echo ""
fi

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose up -d

# Show logs
echo ""
echo -e "${GREEN}✓ Services started successfully${NC}"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
echo "To restart services:"
echo "  docker-compose restart"
echo ""
