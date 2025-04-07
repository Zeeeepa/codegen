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

# Check for ForwardRef._evaluate error
if python -c "import sys; sys.exit(0 if hasattr(__import__('typing').ForwardRef, '_evaluate') and len(__import__('inspect').signature(__import__('typing').ForwardRef._evaluate).parameters) >= 4 else 1)" 2>/dev/null; then
    echo "ForwardRef._evaluate compatibility check passed."
else
    echo "Fixing ForwardRef._evaluate compatibility issue..."
    # Create a patch file for typing.py
    SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
    TYPING_PATH="$SITE_PACKAGES/pydantic/typing.py"
    
    # Backup the original file
    cp "$TYPING_PATH" "$TYPING_PATH.bak"
    
    # Apply the patch
    sed -i 's/return cast(Any, type_)._evaluate(globalns, localns, set())/return cast(Any, type_)._evaluate(globalns, localns, set(), set())/g' "$TYPING_PATH"
    
    echo "Compatibility fix applied."
fi

# Start the FastAPI backend
echo "Starting FastAPI backend..."
cd "$ROOT_DIR"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Deactivate virtual environment on exit
trap "deactivate" EXIT