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

# Add the codegen src directory to PYTHONPATH
CODEGEN_SRC=$(realpath "$ROOT_DIR/../src")
echo "Adding $CODEGEN_SRC to PYTHONPATH..."

# Create or update .env file with PYTHONPATH
ENV_FILE="$ROOT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    # Check if PYTHONPATH already exists in .env
    if grep -q "PYTHONPATH=" "$ENV_FILE"; then
        # Update existing PYTHONPATH
        sed -i "s|PYTHONPATH=.*|PYTHONPATH=$CODEGEN_SRC:\$PYTHONPATH|g" "$ENV_FILE"
    else
        # Add PYTHONPATH to .env
        echo "PYTHONPATH=$CODEGEN_SRC:\$PYTHONPATH" >> "$ENV_FILE"
    fi
else
    # Create new .env file with PYTHONPATH
    echo "PYTHONPATH=$CODEGEN_SRC:\$PYTHONPATH" > "$ENV_FILE"
fi

# Check if langgraph is installed in the virtual environment
if pip show langgraph > /dev/null; then
    echo "langgraph is installed successfully."
else
    echo "Warning: langgraph installation may have failed. Please check your Python environment."
fi

echo "Dependencies updated successfully!"
echo "You can now run the application using the start_frontend.sh and start_backend.sh scripts."