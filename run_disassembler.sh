#!/bin/bash
# Run the module disassembler on the codegen-on-oss directory

# Ensure the script is executable
# chmod +x run_disassembler.sh

# Set the paths
REPO_PATH="."
FOCUS_DIR="codegen-on-oss"
OUTPUT_DIR="./restructured_modules"
REPORT_FILE="./disassembler_report.json"

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Run the module disassembler
python example_usage.py --repo-path "$REPO_PATH" --focus-dir "$FOCUS_DIR" --output-dir "$OUTPUT_DIR" --report-file "$REPORT_FILE"

# Print completion message
echo "Module disassembler completed!"
echo "Restructured modules are in: $OUTPUT_DIR"
echo "Report file: $REPORT_FILE"

