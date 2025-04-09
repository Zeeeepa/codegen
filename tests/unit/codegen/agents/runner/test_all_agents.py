"""
Unified test runner for all agent tests.

This module provides a way to run all agent tests and collect results in a table format.
"""

import os
import sys
import importlib
import unittest
import traceback
from typing import Dict, List, Tuple, Any, Optional
from tabulate import tabulate
from colorama import Fore, Style, init

# Initialize colorama
init()

# Define agent test modules
AGENT_TEST_MODULES = {
    "base_agent": "tests.unit.codegen.agents.test_base_agent",
    "chat_agent": "tests.unit.codegen.agents.chat.test_chat_agent",
    "code_agent": "tests.unit.codegen.agents.code.test_code_agent",
    "mcp_agent": "tests.unit.codegen.agents.mcp.test_mcp_agent",
    "planning_agent": "tests.unit.codegen.agents.planning.test_planning_agent",
    "pr_review_agent": "tests.unit.codegen.agents.pr_review.test_pr_review_agent",
    "reflection_agent": "tests.unit.codegen.agents.reflection.test_reflection_agent",
    "research_agent": "tests.unit.codegen.agents.research.test_research_agent",
    "toolcall_agent": "tests.unit.codegen.agents.toolcall.test_toolcall_agent",
}

class TestResult:
    """Class to store test results."""
    
    def __init__(self, agent_name: str):
        """Initialize a TestResult.
        
        Args:
            agent_name: Name of the agent being tested
        """
        self.agent_name = agent_name
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.skipped = 0
        self.status = "PASS"
        self.error_messages = []
        
    def add_error(self, error_message: str):
        """Add an error message.
        
        Args:
            error_message: Error message to add
        """
        self.error_messages.append(error_message)
        self.status = "FAIL"
        
    def __str__(self):
        """Return a string representation of the test result."""
        return f"{self.agent_name}: {self.status} ({self.passed}/{self.total} passed)"


def run_test_module(module_name: str) -> Tuple[TestResult, List[str]]:
    """Run tests from a module.
    
    Args:
        module_name: Name of the module to run tests from
        
    Returns:
        TestResult object and list of error messages
    """
    result = TestResult(module_name.split('.')[-1])
    
    try:
        # Import the module
        module = importlib.import_module(module_name)
        
        # Create a test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # Run the tests
        test_result = unittest.TextTestRunner(verbosity=0).run(suite)
        
        # Update the result
        result.total = test_result.testsRun
        result.passed = result.total - len(test_result.errors) - len(test_result.failures) - len(test_result.skipped)
        result.failed = len(test_result.failures)
        result.errors = len(test_result.errors)
        result.skipped = len(test_result.skipped)
        
        if test_result.errors or test_result.failures:
            result.status = "FAIL"
            
            # Add error messages
            for test, error in test_result.errors:
                result.add_error(f"ERROR: {test}\n{error}")
                
            for test, failure in test_result.failures:
                result.add_error(f"FAILURE: {test}\n{failure}")
                
    except Exception as e:
        result.status = "FAIL"
        result.add_error(f"Failed to run tests from {module_name}: {str(e)}\n{traceback.format_exc()}")
        
    return result


def run_all_tests() -> Dict[str, TestResult]:
    """Run all agent tests.
    
    Returns:
        Dictionary mapping agent names to TestResult objects
    """
    results = {}
    
    for agent_name, module_name in AGENT_TEST_MODULES.items():
        print(f"Running tests for {agent_name}...")
        result = run_test_module(module_name)
        results[agent_name] = result
        
    return results


def print_results_table(results: Dict[str, TestResult]):
    """Print a table of test results.
    
    Args:
        results: Dictionary mapping agent names to TestResult objects
    """
    # Prepare table data
    table_data = []
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0
    total_skipped = 0
    
    for agent_name, result in results.items():
        status_color = Fore.GREEN if result.status == "PASS" else Fore.RED
        status = f"{status_color}{result.status}{Style.RESET_ALL}"
        
        table_data.append([
            agent_name,
            status,
            result.total,
            result.passed,
            result.failed,
            result.errors,
            result.skipped,
        ])
        
        total_tests += result.total
        total_passed += result.passed
        total_failed += result.failed
        total_errors += result.errors
        total_skipped += result.skipped
        
    # Print the table
    print("\n=== Test Results ===\n")
    print(tabulate(
        table_data,
        headers=["Agent", "Status", "Total", "Passed", "Failed", "Errors", "Skipped"],
        tablefmt="grid",
    ))
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Errors: {total_errors}")
    print(f"Skipped: {total_skipped}")
    
    # Print error messages
    print("\n=== Errors ===")
    for agent_name, result in results.items():
        if result.error_messages:
            print(f"\n=== {agent_name} ===")
            for error in result.error_messages:
                print(error)
                print()


if __name__ == "__main__":
    # Add the project root to the Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    sys.path.insert(0, project_root)
    
    # Run all tests
    results = run_all_tests()
    
    # Print results
    print_results_table(results)
    
    # Exit with non-zero status if any tests failed
    for result in results.values():
        if result.status == "FAIL":
            sys.exit(1)
            
    sys.exit(0)
