#!/bin/bash

# MCP Setup Verification Script
# Tests all MCP servers to ensure they're properly installed and functional

echo "=== MCP Setup Verification ==="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0
WARNINGS=0

# Helper function for test results
print_result() {
    local test_name=$1
    local result=$2
    local message=$3
    
    if [ "$result" = "pass" ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        PASSED=$((PASSED + 1))
    elif [ "$result" = "fail" ]; then
        echo -e "${RED}✗${NC} $test_name"
        [ -n "$message" ] && echo -e "   ${RED}Error:${NC} $message"
        FAILED=$((FAILED + 1))
    elif [ "$result" = "warn" ]; then
        echo -e "${YELLOW}⚠${NC} $test_name"
        [ -n "$message" ] && echo -e "   ${YELLOW}Warning:${NC} $message"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# Test 1: Node.js and npm
echo -e "${BLUE}Testing Node.js Environment${NC}"
echo "----------------------------"
if command -v node > /dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    print_result "Node.js installed ($NODE_VERSION)" "pass"
else
    print_result "Node.js installed" "fail" "Node.js not found in PATH"
fi

if command -v npm > /dev/null 2>&1; then
    NPM_VERSION=$(npm --version)
    print_result "npm installed ($NPM_VERSION)" "pass"
else
    print_result "npm installed" "fail" "npm not found in PATH"
fi

if command -v npx > /dev/null 2>&1; then
    print_result "npx available" "pass"
else
    print_result "npx available" "fail" "npx not found in PATH"
fi
echo ""

# Test 2: Playwright MCP
echo -e "${BLUE}Testing Playwright MCP${NC}"
echo "----------------------"
if npm list -g @playwright/mcp --depth=0 > /dev/null 2>&1; then
    PLAYWRIGHT_VERSION=$(npm list -g @playwright/mcp --depth=0 2>/dev/null | grep @playwright/mcp | awk '{print $2}')
    print_result "Playwright MCP package installed ($PLAYWRIGHT_VERSION)" "pass"
    
    # Test actual invocation
    if timeout 5 npx @playwright/mcp --help > /dev/null 2>&1; then
        print_result "Playwright MCP executable works" "pass"
    else
        print_result "Playwright MCP executable works" "warn" "Command timed out or returned error"
    fi
    
    # Check Chromium installation
    if [ -d "$HOME/.cache/ms-playwright/chromium"* ] 2>/dev/null || [ -d "/root/.cache/ms-playwright/chromium"* ] 2>/dev/null; then
        print_result "Chromium browser installed" "pass"
    else
        print_result "Chromium browser installed" "warn" "Chromium not found in cache directory"
    fi
else
    print_result "Playwright MCP package installed" "fail" "Package not found in global npm packages"
fi
echo ""

# Test 3: Context7 MCP
echo -e "${BLUE}Testing Context7 MCP${NC}"
echo "--------------------"
if npm list -g @upstash/context7-mcp --depth=0 > /dev/null 2>&1; then
    CONTEXT7_VERSION=$(npm list -g @upstash/context7-mcp --depth=0 2>/dev/null | grep @upstash/context7-mcp | awk '{print $2}')
    print_result "Context7 MCP package installed ($CONTEXT7_VERSION)" "pass"
    
    # Test actual invocation
    if timeout 5 npx @upstash/context7-mcp --help > /dev/null 2>&1; then
        print_result "Context7 MCP executable works" "pass"
    else
        print_result "Context7 MCP executable works" "warn" "Command timed out or returned error (may be normal)"
    fi
else
    print_result "Context7 MCP package installed" "fail" "Package not found in global npm packages"
fi
echo ""

# Test 4: Codegen MCP
echo -e "${BLUE}Testing Codegen MCP${NC}"
echo "-------------------"
CODEGEN_MCP_PATH="/tmp/Zeeeepa/codegen/src/codegen/cli/mcp"
if [ -d "$CODEGEN_MCP_PATH" ]; then
    print_result "Codegen MCP directory exists" "pass"
    
    # Check for server.py
    if [ -f "$CODEGEN_MCP_PATH/server.py" ]; then
        print_result "Codegen MCP server.py found" "pass"
        
        # Test if it's valid Python
        if python3 -m py_compile "$CODEGEN_MCP_PATH/server.py" 2>/dev/null; then
            print_result "Codegen MCP server.py is valid Python" "pass"
        else
            print_result "Codegen MCP server.py is valid Python" "fail" "Syntax errors in server.py"
        fi
    else
        print_result "Codegen MCP server.py found" "fail" "server.py not found at $CODEGEN_MCP_PATH/server.py"
    fi
else
    print_result "Codegen MCP directory exists" "fail" "Directory not found: $CODEGEN_MCP_PATH"
fi
echo ""

# Test 5: Configuration Files
echo -e "${BLUE}Testing Configuration Files${NC}"
echo "---------------------------"
if [ -f "/home/l/mcp/node_paths.txt" ]; then
    print_result "Node paths configuration exists" "pass"
else
    print_result "Node paths configuration exists" "warn" "File not found: /home/l/mcp/node_paths.txt"
fi

if [ -f "/home/l/mcp/mcp.json.template" ]; then
    print_result "MCP JSON template exists" "pass"
else
    print_result "MCP JSON template exists" "warn" "File not found: /home/l/mcp/mcp.json.template"
fi
echo ""

# Summary
echo "========================================="
echo "         Verification Summary"
echo "========================================="
echo ""
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC}   $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC} Your MCP setup is ready to use."
    else
        echo -e "${YELLOW}⚠ Setup complete with warnings.${NC} Review warnings above."
    fi
    echo ""
    echo "Next steps:"
    echo "  1. Copy /home/l/mcp/mcp.json.template to your MCP client config"
    echo "  2. Adjust paths if necessary"
    echo "  3. Restart your MCP client (Claude Desktop, Cline, etc.)"
    exit 0
else
    echo -e "${RED}✗ Some tests failed.${NC} Please review the errors above."
    echo ""
    echo "Troubleshooting:"
    echo "  1. Re-run: ./scripts/setup_mcp_fixed.sh"
    echo "  2. Check: docs/MCP_SETUP.md for detailed help"
    echo "  3. Verify npm globals: npm list -g --depth=0"
    exit 1
fi

