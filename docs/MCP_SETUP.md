# MCP Setup Guide

Complete guide for setting up Model Context Protocol (MCP) servers for use with Claude Desktop, Cline, and other MCP-compatible clients.

## 🎯 What This Sets Up

This setup installs three MCP servers:

1. **Codegen MCP** - Advanced code generation and analysis tools
2. **Playwright MCP** - Browser automation and testing capabilities
3. **Context7 MCP** - Up-to-date library documentation access

## 📋 Prerequisites

- Linux-based system (tested on Ubuntu/Debian)
- Python 3.8+
- sudo access
- Internet connection

## 🚀 Quick Start

### Step 1: Run the Setup Script

```bash
cd /tmp/Zeeeepa/codegen
chmod +x scripts/setup_mcp_fixed.sh
./scripts/setup_mcp_fixed.sh
```

This script will:
- ✅ Install system dependencies (Node.js, npm, browser libraries)
- ✅ Install Codegen Python package
- ✅ Install Playwright MCP via npm
- ✅ Install Context7 MCP via npm
- ✅ Download Chromium browser for Playwright
- ✅ Generate configuration templates

**Expected Output:**
```
=== Starting MCP Setup ===
📦 Installing system dependencies...
✓ System dependencies installed
🐍 Installing codegen...
✓ Codegen installed
...
Setup Complete! 🎉
```

### Step 2: Verify Installation

```bash
chmod +x scripts/verify_mcp_setup.sh
./scripts/verify_mcp_setup.sh
```

This will test all MCP servers and report any issues.

### Step 3: Configure Your MCP Client

Copy the template configuration to your MCP client's config location:

#### For Claude Desktop (macOS):
```bash
cp config/mcp.json.template ~/Library/Application\ Support/Claude/mcp.json
```

#### For Claude Desktop (Linux):
```bash
cp config/mcp.json.template ~/.config/Claude/mcp.json
```

#### For Cline (VS Code Extension):
```bash
cp config/mcp.json.template ~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/mcp.json
```

#### For Other Clients:
Consult your MCP client's documentation for the correct config file location.

### Step 4: Restart Your MCP Client

After copying the configuration file, restart your MCP client application to load the new servers.

## 🔧 Configuration Details

### mcp.json Structure

```json
{
  "mcpServers": {
    "codegen": {
      "command": "python",
      "args": ["/path/to/codegen/server.py"]
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
```

### Customizing Paths

If your Codegen installation is in a different location:

1. Find your Codegen path:
   ```bash
   python -c "import codegen; print(codegen.__file__)"
   ```

2. Update `mcp.json`:
   ```json
   "codegen": {
     "command": "python",
     "args": ["/your/custom/path/codegen/cli/mcp/server.py"]
   }
   ```

## 🐛 Troubleshooting

### "Terminated" Error During Setup

**Problem:** Setup script shows "Terminated" after Playwright installation.

**Cause:** The original script used `which playwright`, but `playwright` isn't a standalone command.

**Solution:** Use the fixed script `setup_mcp_fixed.sh` which properly verifies npm packages.

### Playwright MCP Not Found

**Check installation:**
```bash
npm list -g @playwright/mcp --depth=0
```

**Reinstall if needed:**
```bash
npm install -g @playwright/mcp@latest
npx playwright install chromium --with-deps
```

### Context7 MCP Not Working

**Check installation:**
```bash
npm list -g @upstash/context7-mcp --depth=0
```

**Test invocation:**
```bash
npx @upstash/context7-mcp --help
```

### Codegen MCP Server Not Found

**Verify the server file exists:**
```bash
ls -la /tmp/Zeeeepa/codegen/src/codegen/cli/mcp/server.py
```

**Check Python can import codegen:**
```bash
python -c "import codegen; print('OK')"
```

### Node.js/npm Not Found

**Source NVM:**
```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
```

**Set as default:**
```bash
nvm alias default node
```

### Permission Errors

**Make scripts executable:**
```bash
chmod +x scripts/*.sh
```

**NPM global permission issues:**
```bash
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
export PATH=~/.npm-global/bin:$PATH
```

## 🧪 Testing MCP Servers

### Test Playwright MCP

```bash
npx @playwright/mcp --help
```

Expected: Help text or version information.

### Test Context7 MCP

```bash
npx @upstash/context7-mcp --help
```

Expected: Command output (may vary).

### Test Codegen MCP

```bash
python /tmp/Zeeeepa/codegen/src/codegen/cli/mcp/server.py
```

Expected: MCP server startup or help message.

## 📚 What Each MCP Server Does

### Codegen MCP
- **Purpose:** Advanced code generation and codebase analysis
- **Tools:** Code search, refactoring, pattern detection
- **Use Cases:** Large-scale code transformations, architecture analysis

### Playwright MCP
- **Purpose:** Browser automation and web testing
- **Tools:** Navigate, click, type, screenshot, console messages
- **Use Cases:** Web scraping, E2E testing, UI verification

### Context7 MCP
- **Purpose:** Real-time library documentation access
- **Tools:** Library search, API documentation retrieval
- **Use Cases:** Finding current API patterns, checking deprecations

## 🔄 Updating MCP Servers

### Update Playwright MCP
```bash
npm update -g @playwright/mcp
npx playwright install chromium --with-deps
```

### Update Context7 MCP
```bash
npm update -g @upstash/context7-mcp
```

### Update Codegen
```bash
cd /tmp/Zeeeepa/codegen
git pull
pip install -e . --upgrade
```

## 📖 Additional Resources

- [MCP Official Documentation](https://modelcontextprotocol.io/)
- [Playwright MCP GitHub](https://github.com/playwright-community/playwright-mcp)
- [Context7 Documentation](https://github.com/upstash/context7-mcp)
- [Codegen Documentation](https://docs.codegen.com/)

## 💡 Tips

### Using MCP Servers Effectively

1. **Playwright:** Use for visual testing and screenshots
   ```
   "Take a screenshot of the login page in mobile view"
   ```

2. **Context7:** Check library docs before coding
   ```
   "Show me the latest FastAPI routing patterns"
   ```

3. **Codegen:** Large refactoring tasks
   ```
   "Rename this function across the entire codebase"
   ```

### Performance Optimization

- **Disable unused servers:** Set `"disabled": true` in `mcp.json`
- **Use specific tools:** Reference servers by name for faster response
- **Cache browser state:** Playwright reuses browser instances

## 🆘 Getting Help

If you encounter issues not covered here:

1. **Run the verification script:** `./scripts/verify_mcp_setup.sh`
2. **Check logs:** Look in your MCP client's logs directory
3. **Test manually:** Try invoking each MCP server directly
4. **Review paths:** Ensure all paths in `mcp.json` are correct
5. **File an issue:** Provide verification script output

---

**Last Updated:** 2025-01-15  
**Script Version:** 1.0  
**Tested On:** Ubuntu 22.04, Node.js 20.x, Python 3.10

