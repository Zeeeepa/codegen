#!/usr/bin/env python3
"""
Script to identify flaky tests by running them multiple times.
This script runs specified tests multiple times and reports any tests that fail inconsistently.
"""

import argparse
import subprocess
import sys
import json
from collections import defaultdict
from typing import Dict, List, Set, Tuple


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Find flaky tests by running them multiple times")
    parser.add_argument(
        "--test-path",
        type=str,
        default="tests/",
        help="Path to test directory or file (default: tests/)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of times to run each test (default: 5)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/flaky_tests.json",
        help="Output file for the report (default: reports/flaky_tests.json)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose output",
    )
    return parser.parse_args()


def run_tests(test_path: str, verbose: bool = False) -> Tuple[Set[str], Set[str]]:
    """Run tests and return sets of passing and failing tests."""
    cmd = ["pytest", test_path, "-v", "--no-header", "--collect-only", "-q"]
    
    # Get list of all tests
    result = subprocess.run(cmd, capture_output=True, text=True)
    all_tests = set()
    for line in result.stdout.splitlines():
        if line.strip():
            all_tests.add(line.strip())
    
    # Run the tests
    cmd = ["pytest", test_path, "-v", "--no-header", "--junit-xml=reports/test_results.xml"]
    if verbose:
        print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parse the output to find passing and failing tests
    passing_tests = set()
    failing_tests = set()
    
    for line in result.stdout.splitlines():
        if " PASSED " in line:
            test_name = line.split(" PASSED ")[0].strip()
            passing_tests.add(test_name)
        elif " FAILED " in line:
            test_name = line.split(" FAILED ")[0].strip()
            failing_tests.add(test_name)
        elif " ERROR " in line:
            test_name = line.split(" ERROR ")[0].strip()
            failing_tests.add(test_name)
    
    return passing_tests, failing_tests


def find_flaky_tests(
    test_path: str, iterations: int, verbose: bool = False
) -> Dict[str, Dict[str, int]]:
    """Find flaky tests by running them multiple times."""
    results = defaultdict(lambda: {"pass": 0, "fail": 0})
    
    for i in range(iterations):
        if verbose:
            print(f"Iteration {i+1}/{iterations}")
        
        passing_tests, failing_tests = run_tests(test_path, verbose)
        
        for test in passing_tests:
            results[test]["pass"] += 1
        
        for test in failing_tests:
            results[test]["fail"] += 1
    
    return results


def generate_report(
    results: Dict[str, Dict[str, int]], output_file: str, verbose: bool = False
) -> List[str]:
    """Generate a report of flaky tests."""
    flaky_tests = []
    
    for test, counts in results.items():
        if counts["pass"] > 0 and counts["fail"] > 0:
            flaky_tests.append(test)
            if verbose:
                print(f"Flaky test: {test} (passed {counts['pass']}/{counts['pass'] + counts['fail']} times)")
    
    # Save the results to a JSON file
    with open(output_file, "w") as f:
        json.dump(
            {
                "flaky_tests": [
                    {"name": test, "results": results[test]} for test in flaky_tests
                ],
                "all_results": {test: results[test] for test in results},
            },
            f,
            indent=2,
        )
    
    return flaky_tests


def main():
    """Main function."""
    args = parse_args()
    
    print(f"Finding flaky tests in {args.test_path}...")
    print(f"Running each test {args.iterations} times")
    
    results = find_flaky_tests(args.test_path, args.iterations, args.verbose)
    flaky_tests = generate_report(results, args.output, args.verbose)
    
    if flaky_tests:
        print(f"\nFound {len(flaky_tests)} flaky tests:")
        for test in flaky_tests:
            print(f"  - {test}")
        print(f"\nDetailed report saved to {args.output}")
        return 1
    else:
        print("\nNo flaky tests found!")
        return 0


if __name__ == "__main__":
    sys.exit(main())

