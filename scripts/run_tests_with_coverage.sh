#!/bin/bash
# Script to run tests with coverage and generate reports

set -e

# Create directories for reports
mkdir -p reports
mkdir -p coverage_html_report

# Default values
COVERAGE_THRESHOLD=70
TEST_PATH="tests/"
REPORT_FORMAT="term"
PARALLEL=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --path)
      TEST_PATH="$2"
      shift 2
      ;;
    --threshold)
      COVERAGE_THRESHOLD="$2"
      shift 2
      ;;
    --format)
      REPORT_FORMAT="$2"
      shift 2
      ;;
    --parallel)
      PARALLEL="-n auto"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --path PATH        Path to test directory or file (default: tests/)"
      echo "  --threshold N      Coverage threshold percentage (default: 70)"
      echo "  --format FORMAT    Coverage report format: term, html, xml (default: term)"
      echo "  --parallel         Run tests in parallel using pytest-xdist"
      echo "  --help             Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Running tests with coverage..."
echo "Test path: $TEST_PATH"
echo "Coverage threshold: $COVERAGE_THRESHOLD%"
echo "Report format: $REPORT_FORMAT"
if [ -n "$PARALLEL" ]; then
  echo "Running in parallel mode"
fi

# Run pytest with coverage
python -m pytest $TEST_PATH --cov=src/codegen $PARALLEL -v

# Generate coverage report
if [ "$REPORT_FORMAT" = "html" ]; then
  python -m coverage html
  echo "HTML coverage report generated in coverage_html_report/"
elif [ "$REPORT_FORMAT" = "xml" ]; then
  python -m coverage xml
  echo "XML coverage report generated as coverage.xml"
else
  python -m coverage report
fi

# Run coverage analysis script
echo "Analyzing test coverage..."
python scripts/analyze_test_coverage.py --threshold $COVERAGE_THRESHOLD --output reports/coverage_analysis.md

echo "Done! Coverage analysis report saved to reports/coverage_analysis.md"

