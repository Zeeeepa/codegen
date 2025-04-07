#!/bin/bash

# Set up environment
echo "Setting up environment..."
cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the FastAPI backend
echo "Starting FastAPI backend..."
cd "$ROOT_DIR"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Deactivate virtual environment on exit
trap "deactivate" EXIT