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

echo -e "${BLUE}Deploying Slack Chatbot to Modal...${NC}"

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
        echo -e "${YELLOW}No .env.template file found. Creating a basic .env template...${NC}"
        cat > .env.template << EOL
# Slack credentials
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_SIGNING_SECRET=your_slack_signing_secret

# OpenAI API key
OPENAI_API_KEY=your_openai_api_key

# Modal configuration (optional)
MODAL_API_KEY=your_modal_api_key
EOL
        cp .env.template .env
        echo -e "${RED}Please edit the .env file with your credentials before deploying.${NC}"
        exit 1
    fi
fi

# Check for required environment variables
if ! grep -q "SLACK_BOT_TOKEN" .env || ! grep -q "SLACK_SIGNING_SECRET" .env || ! grep -q "OPENAI_API_KEY" .env; then
    echo -e "${RED}Missing required environment variables in .env file.${NC}"
    echo -e "${YELLOW}Please ensure SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, and OPENAI_API_KEY are set.${NC}"
    exit 1
fi

# Deploy the application
echo -e "${BLUE}Deploying Slack Chatbot to Modal...${NC}"
python3 api.py

# Verify deployment
if modal app status slack-chatbot | grep -q "RUNNING"; then
    echo -e "${GREEN}Deployment complete! Slack Chatbot is now running.${NC}"
else
    echo -e "${YELLOW}Deployment completed, but the app may not be running yet.${NC}"
fi

echo -e "${BLUE}You can check the status with 'modal app status slack-chatbot'${NC}"
echo -e "${BLUE}To view logs, run 'modal app logs slack-chatbot'${NC}"

# Get the webhook URL
echo -e "${GREEN}Your Slack webhook URL is:${NC}"
modal app show slack-chatbot | grep -o "https://.*slack-chatbot.*" || echo -e "${YELLOW}URL not found. Run 'modal app show slack-chatbot' to get your webhook URL.${NC}"

echo -e "${BLUE}Remember to configure this URL in your Slack app settings.${NC}"
