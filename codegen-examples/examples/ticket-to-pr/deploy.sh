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

# Check if .env file exists
if [ ! -f .env ]; then
    if [ -f .env.template ]; then
        echo ".env file not found. Creating from template..."
        cp .env.template .env
        echo "Please edit the .env file with your credentials before deploying."
        exit 1
    else
        echo "Neither .env nor .env.template file found. Please create a .env file with your credentials."
        exit 1
    fi
fi

# Deploy the application
echo "Deploying Linear Ticket-to-PR to Modal..."
python3 app.py

echo "Deployment complete! You can check the status with 'modal app status linear-bot'"
echo "To view logs, run 'modal app logs linear-bot'"

