#!/bin/bash

# Set up environment
echo "Setting up environment..."
cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

# Check if Python virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing updated dependencies..."
pip install -r requirements.txt

# Install langgraph explicitly to ensure it's available
echo "Ensuring langgraph is installed..."
pip install langgraph>=0.3.20

# Check if langgraph is installed in the virtual environment
if pip show langgraph > /dev/null; then
    echo "langgraph is installed successfully."
else
    echo "Warning: langgraph installation may have failed. Please check your Python environment."
fi

echo "Dependencies updated successfully!"
echo "You can now run the application using the start_frontend.sh and start_backend.sh scripts."