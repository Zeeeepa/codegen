#!/bin/bash

# Navigate to the Next.js frontend directory
cd frontend/nextjs

# Install npm dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Start the Next.js development server
echo "Starting Next.js frontend..."
npm run dev