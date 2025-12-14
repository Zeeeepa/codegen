#!/bin/bash

echo "🚀 Starting CodeGen Chain Dashboard on Port 3000..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Start the development server
echo "🔥 Starting development server..."
npm run dev

