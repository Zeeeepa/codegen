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

# Check Python version
python_version=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Using Python $python_version"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Ensure langgraph is installed (especially important for Python 3.13)
if ! pip show langgraph > /dev/null; then
    echo "Installing langgraph..."
    pip install langgraph>=0.3.20
fi

# Start the FastAPI backend
echo "Starting FastAPI backend..."
cd "$ROOT_DIR"
PYTHONPATH="$ROOT_DIR:$PYTHONPATH" uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Deactivate virtual environment on exit
trap "deactivate" EXIT