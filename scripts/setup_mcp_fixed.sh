#!/bin/bash

set -e  # Exit on error

echo "=== Starting MCP Setup ==="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Success/failure tracking
ERRORS=0

# Update system and install base dependencies
echo "📦 Installing system dependencies..."
sudo apt update > /dev/null 2>&1
sudo apt install -y nodejs npm git curl libnss3 libx11-6 libx11-xcb1 libxcb1 \
    libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 \
    libxrandr2 libxrender1 libxss1 libxtst6 libgtk-3-0 libasound2 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libgbm1 libpango-1.0-0 \
    libpangocairo-1.0-0 libatspi2.0-0 libxkbcommon0 libwayland-client0 \
    fonts-liberation xdg-utils wget ca-certificates > /dev/null 2>&1
echo -e "${GREEN}✓${NC} System dependencies installed"
echo ""

# Install codegen dependencies
echo "🐍 Installing codegen..."
pip install -e . > /dev/null 2>&1
pip install codegen-api-client > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Codegen installed"
echo ""

# Install nvm and Node.js LTS
echo "📦 Installing nvm and Node.js..."
if [ ! -d "$HOME/.nvm" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh 2>/dev/null | bash > /dev/null 2>&1
fi

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

nvm install --lts > /dev/null 2>&1
nvm use --lts > /dev/null 2>&1

# Get Node.js path for later
NODE_PATH=$(which node)
NPX_PATH=$(which npx)

echo -e "${GREEN}✓${NC} Node.js installed at: $NODE_PATH"
echo -e "${GREEN}✓${NC} npx installed at: $NPX_PATH"
echo ""

# Create MCP directory
echo "📁 Creating MCP directory..."
mkdir -p /home/l/mcp
echo -e "${GREEN}✓${NC} MCP directory created: /home/l/mcp"
echo ""

# Install Playwright MCP via NPM
echo "🎭 Installing Playwright MCP..."
npm install -g @playwright/mcp@latest > /dev/null 2>&1
npx playwright install chromium --with-deps

# Verify Playwright MCP installation
echo "   Verifying Playwright MCP..."
if npm list -g @playwright/mcp --depth=0 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Playwright MCP installed successfully"
else
    echo -e "${RED}✗${NC} Playwright MCP installation verification failed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Install Context7 MCP via NPM
echo "📚 Installing Context7 MCP..."
npm install -g @upstash/context7-mcp@latest > /dev/null 2>&1

# Verify Context7 MCP installation
echo "   Verifying Context7 MCP..."
if npm list -g @upstash/context7-mcp --depth=0 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Context7 MCP installed successfully"
else
    echo -e "${RED}✗${NC} Context7 MCP installation verification failed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Verify codegen MCP server
echo "🔧 Verifying Codegen MCP server..."
CODEGEN_MCP_PATH="/tmp/Zeeeepa/codegen/src/codegen/cli/mcp"
if [ -d "$CODEGEN_MCP_PATH" ]; then
    echo -e "${GREEN}✓${NC} Codegen MCP server found at: $CODEGEN_MCP_PATH"
else
    echo -e "${YELLOW}⚠${NC} Codegen MCP server not found at expected path"
    echo "   Expected: $CODEGEN_MCP_PATH"
    echo "   You may need to adjust the path in mcp.json"
fi
echo ""

# Save Node paths to a file for reference
echo "💾 Saving configuration..."
cat > /home/l/mcp/node_paths.txt << EOF
NODE_PATH=$NODE_PATH
NPX_PATH=$NPX_PATH
NVM_DIR=$NVM_DIR
PLAYWRIGHT_MCP=npx @playwright/mcp
CONTEXT7_MCP=npx @upstash/context7-mcp
CODEGEN_MCP=$CODEGEN_MCP_PATH
EOF
echo -e "${GREEN}✓${NC} Configuration saved to: /home/l/mcp/node_paths.txt"
echo ""

# Generate mcp.json template
echo "📝 Generating mcp.json template..."
cat > /home/l/mcp/mcp.json.template << 'EOF'
{
  "mcpServers": {
    "codegen": {
      "command": "python",
      "args": ["/tmp/Zeeeepa/codegen/src/codegen/cli/mcp/server.py"]
    },
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp"]
    },
    "context7": {
      "command": "npx",
      "args": ["@upstash/context7-mcp"]
    }
  }
}
EOF
echo -e "${GREEN}✓${NC} Template saved to: /home/l/mcp/mcp.json.template"
echo ""

# Summary
echo "========================================="
echo "           Setup Complete! 🎉"
echo "========================================="
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All MCP servers installed successfully!"
else
    echo -e "${YELLOW}⚠${NC} Setup completed with $ERRORS warning(s)"
    echo "   Review the output above for details"
fi

echo ""
echo "📦 Installed MCP Servers:"
echo "   1. Codegen:    $CODEGEN_MCP_PATH"
echo "   2. Playwright: npx @playwright/mcp"
echo "   3. Context7:   npx @upstash/context7-mcp"
echo ""
echo "📄 Configuration files:"
echo "   • Node paths: /home/l/mcp/node_paths.txt"
echo "   • MCP template: /home/l/mcp/mcp.json.template"
echo ""
echo "🔧 Next Steps:"
echo "   1. Run: ./scripts/verify_mcp_setup.sh (to test installations)"
echo "   2. Copy mcp.json.template to your MCP client config location"
echo "   3. Read: docs/MCP_SETUP.md for detailed instructions"
echo ""
echo "Test commands:"
echo "   npx @playwright/mcp --help"
echo "   npx @upstash/context7-mcp --help"
echo ""

