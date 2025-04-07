#!/bin/bash
# Simple script to start the Projector application

# Ensure the script is run from the project root
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    exit 1
fi

# Check if Streamlit is installed
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "Streamlit not found. Installing requirements..."
    python3 -m pip install -r requirements.txt
fi

# Run the application
echo "Starting Projector..."
python3 -m streamlit run frontend/streamlit_app.py "$@"
