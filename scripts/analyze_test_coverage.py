#!/usr/bin/env python3
"""
Script to analyze test coverage and identify modules with low coverage.
Run this script after running pytest with coverage to generate a report of modules
that need more test coverage.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse


def run_coverage_report(format: str = "json") -> Optional[str]:
    """Run coverage report and return the output"""
    try:
        result = subprocess.run(
            ["coverage", "report", f"--{format}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running coverage report: {e}")
        print(f"stderr: {e.stderr}")
        return None


def parse_json_coverage(json_data: str) -> Dict:
    """Parse JSON coverage data"""
    try:
        return json.loads(json_data)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON coverage data: {e}")
        sys.exit(1)


def identify_low_coverage_modules(
    coverage_data: Dict, threshold: int = 50
) -> List[Tuple[str, float]]:
    """Identify modules with coverage below the threshold"""
    low_coverage_modules = []
    
    for file_path, file_data in coverage_data["files"].items():
        if not file_path.startswith("src/codegen"):
            continue
            
        coverage_percent = file_data["summary"]["percent_covered"]
        if coverage_percent < threshold:
            low_coverage_modules.append((file_path, coverage_percent))
    
    # Sort by coverage (ascending)
    low_coverage_modules.sort(key=lambda x: x[1])
    return low_coverage_modules


def identify_critical_modules(coverage_data: Dict) -> List[str]:
    """Identify critical modules that should have high test coverage"""
    critical_modules = []
    
    # Define patterns for critical modules
    critical_patterns = [
        "src/codegen/sdk/",
        "src/codegen/agents/",
        "src/codegen/cli/",
        "src/codegen/extensions/",
    ]
    
    for file_path in coverage_data["files"].keys():
        if any(file_path.startswith(pattern) for pattern in critical_patterns):
            critical_modules.append(file_path)
    
    return critical_modules


def generate_report(
    low_coverage_modules: List[Tuple[str, float]], 
    critical_modules: List[str],
    threshold: int,
    output_file: Optional[str] = None
) -> None:
    """Generate a report of modules with low coverage"""
    report_lines = [
        "# Test Coverage Analysis Report",
        f"\n## Modules with coverage below {threshold}%\n",
    ]
    
    for module, coverage in low_coverage_modules:
        critical_marker = " 🔴" if module in critical_modules else ""
        report_lines.append(f"- {module}: {coverage:.1f}%{critical_marker}")
    
    # Add statistics
    total_modules = len(low_coverage_modules)
    critical_low_coverage = sum(1 for m, _ in low_coverage_modules if m in critical_modules)
    
    report_lines.extend([
        f"\n## Statistics",
        f"\n- Total modules with low coverage: {total_modules}",
        f"- Critical modules with low coverage: {critical_low_coverage}",
        f"\n🔴 = Critical module that should have high test coverage",
    ])
    
    report_text = "\n".join(report_lines)
    
    if output_file:
        with open(output_file, "w") as f:
            f.write(report_text)
        print(f"Report written to {output_file}")
    else:
        print(report_text)


def main():
    parser = argparse.ArgumentParser(description="Analyze test coverage and identify modules with low coverage")
    parser.add_argument("--threshold", type=int, default=50, help="Coverage threshold percentage (default: 50)")
    parser.add_argument("--output", type=str, help="Output file for the report (default: print to stdout)")
    args = parser.parse_args()
    
    # Create scripts directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    # Run coverage report
    json_data = run_coverage_report(format="json")
    if not json_data:
        print("Failed to generate coverage report. Make sure you've run pytest with coverage.")
        sys.exit(1)
    
    # Parse coverage data
    coverage_data = parse_json_coverage(json_data)
    
    # Identify modules with low coverage
    low_coverage_modules = identify_low_coverage_modules(coverage_data, args.threshold)
    
    # Identify critical modules
    critical_modules = identify_critical_modules(coverage_data)
    
    # Generate report
    output_file = args.output or "reports/coverage_analysis.md"
    generate_report(low_coverage_modules, critical_modules, args.threshold, output_file)


if __name__ == "__main__":
    main()

