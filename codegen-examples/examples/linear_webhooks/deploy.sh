#!/bin/bash

# Exit on error
set -e

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Deploying Linear Webhooks to Modal...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check if Modal is installed
if ! python3 -c "import modal" &> /dev/null; then
    echo -e "${YELLOW}Modal is not installed. Installing now...${NC}"
    pip install modal==1.0.0
fi

# Check Modal version
MODAL_VERSION=$(python3 -c "import modal; print(modal.__version__)")
echo -e "${GREEN}Using Modal version: $MODAL_VERSION${NC}"

# Check if Modal token is set up
if ! modal token list &> /dev/null; then
    echo -e "${RED}Modal token not set up. Please run 'modal token new' to set up your Modal token.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    if [ -f .env.template ]; then
        echo -e "${YELLOW}.env file not found. Creating from template...${NC}"
        cp .env.template .env
        echo -e "${RED}Please edit the .env file with your credentials before deploying.${NC}"
        exit 1
    else
        echo -e "${RED}Neither .env nor .env.template file found. Please create a .env file with your credentials.${NC}"
        exit 1
    fi
fi

# Check for required environment variables
if ! grep -q "LINEAR_ACCESS_TOKEN" .env || ! grep -q "LINEAR_SIGNING_SECRET" .env; then
    echo -e "${RED}Missing required environment variables in .env file.${NC}"
    echo -e "${YELLOW}Please ensure LINEAR_ACCESS_TOKEN and LINEAR_SIGNING_SECRET are set.${NC}"
    exit 1
fi

# Deploy the application
echo -e "${BLUE}Deploying Linear Webhooks to Modal...${NC}"
python3 webhooks.py

# Verify deployment
if modal app status linear-webhooks | grep -q "RUNNING"; then
    echo -e "${GREEN}Deployment complete! Linear Webhooks is now running.${NC}"
else
    echo -e "${YELLOW}Deployment completed, but the app may not be running yet.${NC}"
fi

echo -e "${BLUE}You can check the status with 'modal app status linear-webhooks'${NC}"
echo -e "${BLUE}To view logs, run 'modal app logs linear-webhooks'${NC}"

# Get the webhook URL
echo -e "${GREEN}Your Linear webhook URL is:${NC}"
modal app show linear-webhooks | grep -o "https://.*linear-webhooks.*" || echo -e "${YELLOW}URL not found. Run 'modal app show linear-webhooks' to get your webhook URL.${NC}"

echo -e "${BLUE}Remember to configure this URL in your Linear workspace settings.${NC}"
