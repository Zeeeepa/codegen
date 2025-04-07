#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start FastAPI backend
echo "Starting FastAPI backend..."
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000