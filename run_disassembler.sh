#!/bin/bash

# Run the module disassembler on the codegen-on-oss directory
# This script provides a convenient way to run the disassembler with default settings

# Set default values
REPO_PATH="."
FOCUS_DIR="codegen-on-oss"
OUTPUT_DIR="./restructured_modules"
REPORT_FILE="./disassembler_report.json"
SIMILARITY_THRESHOLD=0.8

# Print banner
echo "========================================================"
echo "  Module Disassembler for Codegen (SDK-Powered Version)"
echo "========================================================"
echo ""
echo "Running with settings:"
echo "  Repository path: $REPO_PATH"
echo "  Focus directory: $FOCUS_DIR"
echo "  Output directory: $OUTPUT_DIR"
echo "  Report file: $REPORT_FILE"
echo "  Similarity threshold: $SIMILARITY_THRESHOLD"
echo ""

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Run the disassembler
python example_usage.py \
  --repo-path "$REPO_PATH" \
  --focus-dir "$FOCUS_DIR" \
  --output-dir "$OUTPUT_DIR" \
  --report-file "$REPORT_FILE" \
  --similarity-threshold "$SIMILARITY_THRESHOLD"

# Check if the command was successful
if [ $? -eq 0 ]; then
  echo ""
  echo "========================================================"
  echo "  Disassembly Complete!"
  echo "========================================================"
  echo ""
  echo "Results:"
  echo "  - Restructured modules: $OUTPUT_DIR"
  echo "  - Analysis report: $REPORT_FILE"
  echo ""
  echo "Next steps:"
  echo "  1. Review the generated report to understand the codebase structure"
  echo "  2. Examine the restructured modules to see the new organization"
  echo "  3. Use the restructured modules as a reference for refactoring"
else
  echo ""
  echo "========================================================"
  echo "  Error: Disassembly Failed"
  echo "========================================================"
  echo ""
  echo "Please check the error messages above for details."
fi

