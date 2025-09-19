#!/bin/bash

# Codegen Visual Orchestration CLI Integration Demo
# This script demonstrates the complete integration between CLI commands,
# project management APIs, MCP servers, and the self-evolving CI/CD system

set -e

echo "🚀 Codegen Visual Orchestration CLI Integration Demo"
echo "======================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Demo configuration
PROJECT_PATH=${1:-"./examples/demo-project"}
CONFIG_FILE="./examples/orchestration-config.yaml"

echo -e "${BLUE}📋 Demo Configuration:${NC}"
echo "  Project Path: $PROJECT_PATH"
echo "  Config File: $CONFIG_FILE"
echo ""

# Check if codegen CLI is available
if ! command -v codegen &> /dev/null; then
    echo -e "${RED}❌ codegen CLI not found. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ codegen CLI found${NC}"

# 1. Set up project management integrations
echo -e "\n${YELLOW}🔧 Step 1: Setting up project management integrations${NC}"

echo "Setting up Linear integration..."
codegen orchestrate project setup linear codegen-demo-team \
    --token "${LINEAR_TOKEN:-demo_token}" \
    --config "$CONFIG_FILE" \
    --webhook "https://webhook.site/unique-id" || echo "⚠️  Using mock Linear integration"

echo "Setting up GitHub integration..."
codegen orchestrate project setup github codegen-sh/codegen \
    --token "${GITHUB_TOKEN:-demo_token}" \
    --config "$CONFIG_FILE" \
    --webhook "https://webhook.site/unique-id" || echo "⚠️  Using mock GitHub integration"

# 2. List configured integrations
echo -e "\n${YELLOW}📋 Step 2: Listing configured integrations${NC}"
codegen orchestrate project list --config "$CONFIG_FILE" --format table

# 3. Analyze the project
echo -e "\n${YELLOW}🔍 Step 3: Analyzing project structure${NC}"
codegen orchestrate analyze "$PROJECT_PATH" --format table

# 4. Create intelligent pipeline
echo -e "\n${YELLOW}🛠️ Step 4: Creating intelligent pipeline${NC}"
codegen orchestrate create "$PROJECT_PATH" \
    --name "demo-pipeline" \
    --output "./demo-pipeline.yaml" \
    --requirements '{"security_level": "high", "deployment_targets": ["staging", "production"]}'

echo "Generated pipeline definition:"
if [ -f "./demo-pipeline.yaml" ]; then
    head -20 "./demo-pipeline.yaml"
    echo "... (truncated)"
fi

# 5. Test project management integrations
echo -e "\n${YELLOW}🧪 Step 5: Testing integrations${NC}"
codegen orchestrate project test linear --config "$CONFIG_FILE" || echo "⚠️  Linear test failed (expected in demo)"
codegen orchestrate project test github_issues --config "$CONFIG_FILE" || echo "⚠️  GitHub test failed (expected in demo)"

# 6. Sync with project management platforms
echo -e "\n${YELLOW}🔄 Step 6: Syncing with project management platforms${NC}"
codegen orchestrate project sync linear --config "$CONFIG_FILE" --dry-run

# 7. Monitor pipeline (simulated)
echo -e "\n${YELLOW}📊 Step 7: Monitoring pipeline execution${NC}"
echo "Starting pipeline execution simulation..."
codegen orchestrate monitor demo-pipeline --format json | head -10 || echo "⚠️  Monitoring requires pipeline execution"

# 8. Show analytics
echo -e "\n${YELLOW}📈 Step 8: Showing project management analytics${NC}"
codegen orchestrate project analytics linear --config "$CONFIG_FILE" --format table || echo "⚠️  Analytics unavailable in demo mode"

# 9. Evolve pipeline based on performance
echo -e "\n${YELLOW}🧠 Step 9: Pipeline evolution and optimization${NC}"
codegen orchestrate evolve demo-pipeline --dry-run || echo "⚠️  Evolution requires execution history"

# 10. List all pipelines
echo -e "\n${YELLOW}📝 Step 10: Listing all pipelines${NC}"
codegen orchestrate list --limit 5 --format table

# 11. Start web interface (optional)
if [ "${START_WEB_UI:-false}" = "true" ]; then
    echo -e "\n${YELLOW}🌐 Step 11: Starting web interface${NC}"
    echo "Web interface will start on http://localhost:8000"
    echo "Press Ctrl+C to stop the server"
    codegen orchestrate serve --port 8000 --host 0.0.0.0
else
    echo -e "\n${BLUE}ℹ️  To start the web interface, run:${NC}"
    echo "  START_WEB_UI=true $0 $*"
    echo "  or manually: codegen orchestrate serve"
fi

echo -e "\n${GREEN}✅ CLI Integration Demo completed successfully!${NC}"
echo ""
echo -e "${BLUE}📚 Available Commands Summary:${NC}"
echo "  • codegen orchestrate create <project> - Create intelligent pipeline"
echo "  • codegen orchestrate analyze <project> - Analyze project structure"  
echo "  • codegen orchestrate monitor <pipeline> - Monitor execution"
echo "  • codegen orchestrate evolve <pipeline> - Optimize pipeline"
echo "  • codegen orchestrate list - List all pipelines"
echo "  • codegen orchestrate serve - Start web interface"
echo ""
echo -e "${BLUE}📝 Project Management Commands:${NC}"
echo "  • codegen orchestrate project setup <platform> - Setup integration"
echo "  • codegen orchestrate project list - List integrations"
echo "  • codegen orchestrate project sync <integration> - Sync tasks"
echo "  • codegen orchestrate project analytics <integration> - Show analytics"
echo "  • codegen orchestrate project test <integration> - Test connection"
echo ""
echo -e "${BLUE}🔗 Next Steps:${NC}"
echo "  1. Configure real API tokens for Linear/GitHub/Jira"
echo "  2. Set up MCP servers for enhanced integrations"
echo "  3. Deploy to production with deploy-orchestration.py"
echo "  4. Integrate with existing CI/CD systems"
echo "  5. Customize pipeline templates in $CONFIG_FILE"
echo ""

# Clean up demo files (optional)
if [ "${CLEANUP:-false}" = "true" ]; then
    echo -e "${YELLOW}🧹 Cleaning up demo files...${NC}"
    rm -f "./demo-pipeline.yaml"
    echo "✅ Cleanup completed"
fi

echo "🎉 Demo finished! Thank you for trying Codegen Visual Orchestration System!"