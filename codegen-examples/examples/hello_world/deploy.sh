#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

echo -e "${BLUE}Deploying hello_world to Modal...${NC}"

# Deploy the app
if modal deploy app.py; then
    echo -e "${GREEN}Deployment successful!${NC}"
    echo -e "Your web endpoint is now available at: https://hello-world--web-hello.modal.run"
    echo -e "Your scheduled function will run every hour."
    exit 0
else
    echo -e "${RED}Deployment failed.${NC}"
    exit 1
fi

