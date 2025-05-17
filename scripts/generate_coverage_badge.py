#!/usr/bin/env python3
"""
Script to generate a test coverage badge.
This script parses the coverage report and generates a badge that can be included in the README.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate a test coverage badge")
    parser.add_argument(
        "--output",
        type=str,
        default="reports/coverage_badge.svg",
        help="Output file for the badge (default: reports/coverage_badge.svg)",
    )
    return parser.parse_args()


def get_coverage_percentage():
    """Get the coverage percentage from the coverage report."""
    try:
        # Run coverage report in JSON format
        result = subprocess.run(
            ["coverage", "report", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        
        # Parse the JSON output
        coverage_data = json.loads(result.stdout)
        
        # Get the total coverage percentage
        total_coverage = coverage_data["totals"]["percent_covered"]
        
        return total_coverage
    except subprocess.CalledProcessError as e:
        print(f"Error running coverage report: {e}")
        print(f"stderr: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing coverage report: {e}")
        return None
    except KeyError as e:
        print(f"Error extracting coverage percentage: {e}")
        return None


def generate_badge(coverage_percentage, output_file):
    """Generate a coverage badge."""
    if coverage_percentage is None:
        print("No coverage data available")
        return False
    
    # Determine badge color based on coverage
    if coverage_percentage >= 90:
        color = "brightgreen"
    elif coverage_percentage >= 80:
        color = "green"
    elif coverage_percentage >= 70:
        color = "yellowgreen"
    elif coverage_percentage >= 60:
        color = "yellow"
    elif coverage_percentage >= 50:
        color = "orange"
    else:
        color = "red"
    
    # Generate badge using shields.io
    badge_url = f"https://img.shields.io/badge/coverage-{coverage_percentage:.1f}%25-{color}"
    
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Download the badge
        subprocess.run(
            ["curl", "-s", "-o", output_file, badge_url],
            check=True,
        )
        
        print(f"Coverage badge generated: {output_file}")
        print(f"Coverage: {coverage_percentage:.1f}%")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating badge: {e}")
        return False


def main():
    """Main function."""
    args = parse_args()
    
    print("Generating coverage badge...")
    
    # Get coverage percentage
    coverage_percentage = get_coverage_percentage()
    
    # Generate badge
    success = generate_badge(coverage_percentage, args.output)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

