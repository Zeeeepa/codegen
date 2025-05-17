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

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# GitHub credentials
GITHUB_TOKEN=your_github_token

# Modal configuration (optional)
MODAL_API_KEY=your_modal_api_key
EOL
    echo "Please edit the .env file with your credentials before deploying."
    exit 1
fi

# Deploy the backend API
echo "Deploying AI Impact Analysis Backend API to Modal..."
python3 dashboard/backend/api.py

echo "Deployment complete! You can check the status with 'modal app status ai-impact-analysis-api'"
echo "To view logs, run 'modal app logs ai-impact-analysis-api'"

# Instructions for frontend deployment
echo ""
echo "To deploy the frontend:"
echo "1. Navigate to the frontend directory: cd dashboard/frontend"
echo "2. Install dependencies: npm install"
echo "3. Update the API_URL in src/config.js to point to your Modal deployment"
echo "4. Build the frontend: npm run build"
echo "5. Deploy to your preferred hosting service (e.g., Vercel, Netlify, GitHub Pages)"

