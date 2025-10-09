#!/bin/bash
set -e

# 🚀 Code Quality Check - One-Liner Execution Script
# Usage: bash run_quality_check.sh [OPTIONS]

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Code Quality Check - Ultimate Edition${NC}"
echo "=================================================="
echo ""

# Default values
TARGET_DIR="${1:-.}"
OUTPUT_FORMAT="${2:-html}"
OUTPUT_FILE="${3:-quality_report.html}"

# Parse options
AUTO_FIX=false
GIT_DIFF=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-fix)
            AUTO_FIX=true
            shift
            ;;
        --git-diff)
            GIT_DIFF="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: bash run_quality_check.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --auto-fix          Automatically fix issues"
            echo "  --git-diff BRANCH   Check only files changed from branch"
            echo "  --verbose           Show detailed output"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  bash run_quality_check.sh"
            echo "  bash run_quality_check.sh --auto-fix"
            echo "  bash run_quality_check.sh --git-diff main"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

echo -e "${YELLOW}📥 Step 1/4: Downloading scripts...${NC}"

# Create temp directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download main script
echo "  → Downloading code_quality_ultimate.py..."
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/codegen/codegen-artifacts-store/scripts/code_quality_ultimate.py -o code_quality_ultimate.py

# Download dependency installer
echo "  → Downloading install_dependencies.py..."
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/codegen/codegen-artifacts-store/scripts/install_dependencies.py -o install_dependencies.py

echo -e "${GREEN}✅ Scripts downloaded${NC}"
echo ""

# Check Python
echo -e "${YELLOW}🔍 Step 2/4: Checking Python environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed!${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${GREEN}✅ Found: $PYTHON_VERSION${NC}"
echo ""

# Check and install dependencies
echo -e "${YELLOW}🔧 Step 3/4: Installing dependencies...${NC}"
echo "  This may take a minute on first run..."

# Quick check if essential tools are installed
MISSING_TOOLS=0
for tool in black ruff mypy; do
    if ! python3 -c "import $tool" 2>/dev/null; then
        MISSING_TOOLS=$((MISSING_TOOLS + 1))
    fi
done

if [ $MISSING_TOOLS -gt 0 ]; then
    echo "  → Installing essential quality tools..."
    python3 install_dependencies.py --skip-node 2>&1 | grep -E "(Installing|✅|Success)" || true
else
    echo -e "${GREEN}✅ All essential tools already installed${NC}"
fi
echo ""

# Run quality check
echo -e "${YELLOW}🔍 Step 4/4: Running quality analysis...${NC}"
echo "  Target: $TARGET_DIR"
echo ""

# Build command
CMD="python3 code_quality_ultimate.py"

# Add options
if [ "$AUTO_FIX" = true ]; then
    CMD="$CMD --auto-fix"
fi

if [ -n "$GIT_DIFF" ]; then
    CMD="$CMD --git-diff $GIT_DIFF"
fi

if [ "$VERBOSE" = true ]; then
    CMD="$CMD --verbose"
fi

# Always generate HTML report
CMD="$CMD --html $OUTPUT_FILE"

# Change to target directory and run
cd "$TARGET_DIR" 2>/dev/null || {
    echo -e "${RED}❌ Directory not found: $TARGET_DIR${NC}"
    exit 1
}

echo "Running: $CMD"
echo "=================================================="
echo ""

eval "$CMD"

RESULT=$?

echo ""
echo "=================================================="

if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Quality check completed!${NC}"
    echo ""
    echo "📊 Report generated: $OUTPUT_FILE"
    echo ""
    echo "To view the report:"
    echo "  • Mac:     open $OUTPUT_FILE"
    echo "  • Linux:   xdg-open $OUTPUT_FILE"
    echo "  • Windows: start $OUTPUT_FILE"
else
    echo -e "${YELLOW}⚠️  Quality check completed with issues${NC}"
    echo ""
    echo "📊 Report generated: $OUTPUT_FILE"
fi

# Cleanup
cd /
rm -rf "$TEMP_DIR"

echo ""
echo -e "${BLUE}🎉 Done!${NC}"

exit $RESULT