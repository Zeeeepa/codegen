#!/bin/bash
# Simple script to start the Projector application

# Ensure the script is executable
# chmod +x start.sh

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if Streamlit is installed
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "Streamlit is not installed. Installing required packages..."
    pip install -r projector/requirements.txt
fi

# Run the application
echo "Starting Projector..."
python3 projector/main.py "$@"
