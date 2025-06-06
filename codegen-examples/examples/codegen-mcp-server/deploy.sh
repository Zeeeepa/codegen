#!/bin/bash

# Exit on error
set -e

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if Modal is installed
if ! python3 -c "import modal" &> /dev/null; then
    echo "Modal is not installed. Installing now..."
    pip install modal
fi

# Check if Modal token is set up
if ! modal token list &> /dev/null; then
    echo "Modal token not set up. Please run 'modal token new' to set up your Modal token."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# GitHub credentials (for repository access)
GITHUB_TOKEN=your_github_token

# OpenAI credentials (if using OpenAI)
OPENAI_API_KEY=your_openai_api_key

# Modal configuration (optional)
MODAL_API_KEY=your_modal_api_key
EOL
    echo "Please edit the .env file with your credentials before deploying."
    exit 1
fi

# Check if LLM dependencies are installed
echo "Note: This server requires LLM dependencies. See llms-install.md for details."

# Deploy the application
echo "Deploying Codegen MCP Server to Modal..."
python3 server.py

echo "Deployment complete! You can check the status with 'modal app status codegen-mcp-server'"
echo "To view logs, run 'modal app logs codegen-mcp-server'"

