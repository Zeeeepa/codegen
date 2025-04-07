#!/bin/bash

# Set up environment
echo "Setting up environment..."
cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

# Navigate to the Next.js frontend directory
cd "$ROOT_DIR/frontend/nextjs"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Would you like to install it? (y/n)"
    read -r install_node
    if [[ "$install_node" =~ ^[Yy]$ ]]; then
        echo "Installing Node.js using nvm..."
        # Install nvm if not already installed
        if ! command -v nvm &> /dev/null; then
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
            export NVM_DIR="$HOME/.nvm"
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        fi
        # Install and use the latest LTS version of Node.js
        nvm install --lts
        nvm use --lts
    else
        echo "Node.js is required to run the frontend. Please install it and try again."
        exit 1
    fi
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install npm and try again."
    exit 1
fi

# Install dependencies
echo "Installing frontend dependencies..."
npm install

# Start the Next.js development server
echo "Starting Next.js development server..."
npm run dev