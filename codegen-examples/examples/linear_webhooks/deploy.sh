#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Modal CLI is installed
if ! command -v modal &> /dev/null; then
    echo -e "${RED}Error: Modal CLI is not installed.${NC}"
    echo -e "Please install it with: pip install modal"
    exit 1
fi

# Check if Modal is authenticated
if ! modal token list &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with Modal.${NC}"
    echo -e "Please run: modal token new"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found.${NC}"
    echo -e "Creating .env file from template..."
    
    if [ -f .env.template ]; then
        cp .env.template .env
        echo -e "${YELLOW}Please edit the .env file with your Linear API key and webhook secret.${NC}"
        echo -e "Do you want to continue with deployment? (y/n)"
        read -r continue
        
        if [ "$continue" != "y" ] && [ "$continue" != "Y" ]; then
            echo -e "${RED}Deployment cancelled.${NC}"
            exit 0
        fi
    else
        echo -e "${RED}Error: .env.template file not found.${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}Deploying linear_webhooks to Modal...${NC}"

# Deploy the app
if modal deploy webhooks.py; then
    echo -e "${GREEN}Deployment successful!${NC}"
    echo -e "Your webhook handler is now available at: https://test-linear--linear-event-handlers-test.modal.run"
    echo -e "${YELLOW}Remember to configure this URL in your Linear webhook settings.${NC}"
    exit 0
else
    echo -e "${RED}Deployment failed.${NC}"
    exit 1
fi

