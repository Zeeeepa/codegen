#!/bin/bash
# start.sh - Run the Codegen SDK demo

set -e  # Exit on error

echo "🚀 Starting Codegen SDK Demo..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if credentials are set
if [ -z "$CODEGEN_ORG_ID" ] || [ -z "$CODEGEN_TOKEN" ]; then
    echo "⚠️  Warning: CODEGEN_ORG_ID and CODEGEN_TOKEN are not set"
    echo ""
    echo "Please set your credentials:"
    echo "  export CODEGEN_ORG_ID='your-org-id'"
    echo "  export CODEGEN_TOKEN='your-api-token'"
    echo ""
    echo "Get them from: https://codegen.com/token"
    echo ""
    exit 1
fi

# Check if demo.py exists
if [ ! -f "demo.py" ]; then
    echo "❌ demo.py not found. Please run ./setup.sh first"
    exit 1
fi

# Run the demo
echo "▶️  Running demo..."
echo ""
python demo.py

echo ""
echo "✅ Demo completed!"

