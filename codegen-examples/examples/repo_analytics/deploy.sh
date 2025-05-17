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

# Create a basic pyproject.toml if it doesn't exist
if [ ! -f pyproject.toml ]; then
    echo "Creating pyproject.toml..."
    cat > pyproject.toml << EOL
[project]
name = "repo-analytics"
version = "0.1.0"
description = "Repository analytics example for Codegen"
requires-python = ">=3.13"
dependencies = [
  "modal>=0.73.25",
  "codegen>=0.52.19",
  "python-dotenv>=1.0.0",
]
EOL
fi

# Deploy the application
echo "Deploying Repository Analytics to Modal..."
python3 -m modal deploy run.py

echo "Deployment complete! You can check the status with 'modal app status repo-analytics'"
echo "To view logs, run 'modal app logs repo-analytics'"
