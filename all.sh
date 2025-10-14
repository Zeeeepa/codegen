#!/bin/bash
# all.sh - Complete setup and run workflow for Codegen SDK demo

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Codegen SDK - Complete Setup & Run                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Function to print section headers
print_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Step 1: Setup
print_section "Step 1: Setup Environment"
if [ -f "./setup.sh" ]; then
    chmod +x ./setup.sh
    ./setup.sh
else
    echo "❌ setup.sh not found!"
    exit 1
fi

# Step 2: Check credentials
print_section "Step 2: Verify Credentials"
if [ -z "$CODEGEN_ORG_ID" ] || [ -z "$CODEGEN_TOKEN" ]; then
    echo "⚠️  Credentials not found in environment"
    echo ""
    echo "Please set your credentials before running the demo:"
    echo ""
    echo "  export CODEGEN_ORG_ID='your-org-id'"
    echo "  export CODEGEN_TOKEN='your-api-token'"
    echo ""
    echo "Get them from: https://codegen.com/token"
    echo ""
    echo "After setting credentials, run this script again:"
    echo "  ./all.sh"
    echo ""
    exit 1
else
    echo "✅ Credentials found:"
    echo "   ORG_ID: ${CODEGEN_ORG_ID:0:10}..."
    echo "   TOKEN: ${CODEGEN_TOKEN:0:10}..."
fi

# Step 3: Run demo
print_section "Step 3: Run Demo"
if [ -f "./start.sh" ]; then
    chmod +x ./start.sh
    ./start.sh
else
    echo "❌ start.sh not found!"
    exit 1
fi

# Step 4: Summary
print_section "✅ All Steps Completed"
echo "📋 What just happened:"
echo "   ✓ Environment set up with virtual environment"
echo "   ✓ Codegen SDK installed"
echo "   ✓ Demo executed successfully"
echo ""
echo "📚 Next steps:"
echo "   • Try custom prompts with: ./send_request.sh \"your prompt\""
echo "   • View the code in: demo.py"
echo "   • Read the docs: https://docs.codegen.com"
echo ""
echo "💡 Examples:"
echo "   ./send_request.sh \"Create a REST API endpoint for user login\""
echo "   ./send_request.sh \"Write unit tests for a sorting algorithm\""
echo "   ./send_request.sh \"Optimize this SQL query for performance\""
echo ""

