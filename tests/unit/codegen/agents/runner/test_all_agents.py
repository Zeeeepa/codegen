#!/usr/bin/env python3
"""
Unified test runner for all agent tests.

This script runs all agent tests and collects errors, displaying them in a table format.
It will continue running tests even if some fail, to provide a comprehensive report.
"""

import os
import sys
import unittest
import importlib
import traceback
from typing import Dict, List, Tuple
from tabulate import tabulate
from colorama import Fore, Style, init

# Initialize colorama
init()

# Define agent test modules
AGENT_TEST_MODULES = [
    "tests.unit.codegen.agents.test_base_agent",
    "tests.unit.codegen.agents.chat.test_chat_agent",
    "tests.unit.codegen.agents.code.test_code_agent",
    "tests.unit.codegen.agents.mcp.test_mcp_agent",
    "tests.unit.codegen.agents.planning.test_planning_agent",
    "tests.unit.codegen.agents.pr_review.test_pr_review_agent",
    "tests.unit.codegen.agents.reflection.test_reflection_agent",
    "tests.unit.codegen.agents.research.test_research_agent",
    "tests.unit.codegen.agents.toolcall.test_toolcall_agent",
]

def run_test_module(module_name: str) -> Tuple[bool, Dict, str]:
    """
    Run tests from a specific module.
    
    Args:
        module_name: Name of the module to run tests from
        
    Returns:
        Tuple of (success, test_results, error_message)
    """
    try:
        # Import the module
        module = importlib.import_module(module_name)
        
        # Create a test suite from the module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # Run the tests
        runner = unittest.TextTestRunner(verbosity=0)
        result = runner.run(suite)
        
        # Check if all tests passed
        success = result.wasSuccessful()
        
        # Collect test results
        test_results = {
            "total": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
        }
        
        # Collect error messages
        error_messages = []
        for failure in result.failures:
            error_messages.append(f"FAILURE: {failure[0]}\n{failure[1]}")
        
        for error in result.errors:
            error_messages.append(f"ERROR: {error[0]}\n{error[1]}")
            
        error_message = "\n\n".join(error_messages)
        
        return success, test_results, error_message
    
    except Exception as e:
        # Handle import or other errors
        error_message = f"Failed to run tests from {module_name}: {str(e)}\n{traceback.format_exc()}"
        test_results = {
            "total": 0,
            "failures": 0,
            "errors": 1,
            "skipped": 0,
        }
        return False, test_results, error_message

def run_all_tests() -> None:
    """Run all agent tests and display results."""
    print(f"{Fore.CYAN}=== Running Agent Tests ==={Style.RESET_ALL}\n")
    
    # Collect results
    results = []
    all_errors = []
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0
    total_skipped = 0
    
    for module_name in AGENT_TEST_MODULES:
        # Extract agent name from module name
        agent_name = module_name.split(".")[-1].replace("test_", "")
        
        print(f"{Fore.YELLOW}Running tests for {agent_name}...{Style.RESET_ALL}")
        success, test_results, error_message = run_test_module(module_name)
        
        # Update totals
        total_tests += test_results["total"]
        total_passed += test_results["total"] - test_results["failures"] - test_results["errors"] - test_results["skipped"]
        total_failed += test_results["failures"]
        total_errors += test_results["errors"]
        total_skipped += test_results["skipped"]
        
        # Add to results table
        status = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if success else f"{Fore.RED}FAIL{Style.RESET_ALL}"
        results.append([
            agent_name,
            status,
            test_results["total"],
            test_results["total"] - test_results["failures"] - test_results["errors"] - test_results["skipped"],
            test_results["failures"],
            test_results["errors"],
            test_results["skipped"]
        ])
        
        # Collect errors
        if error_message:
            all_errors.append((agent_name, error_message))
    
    # Display results table
    print(f"\n{Fore.CYAN}=== Test Results ==={Style.RESET_ALL}\n")
    headers = ["Agent", "Status", "Total", "Passed", "Failed", "Errors", "Skipped"]
    print(tabulate(results, headers=headers, tablefmt="grid"))
    
    # Display summary
    print(f"\n{Fore.CYAN}=== Summary ==={Style.RESET_ALL}")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {Fore.GREEN}{total_passed}{Style.RESET_ALL}")
    print(f"Failed: {Fore.RED if total_failed > 0 else Fore.GREEN}{total_failed}{Style.RESET_ALL}")
    print(f"Errors: {Fore.RED if total_errors > 0 else Fore.GREEN}{total_errors}{Style.RESET_ALL}")
    print(f"Skipped: {Fore.YELLOW if total_skipped > 0 else Fore.GREEN}{total_skipped}{Style.RESET_ALL}")
    
    # Display errors
    if all_errors:
        print(f"\n{Fore.RED}=== Errors ==={Style.RESET_ALL}\n")
        for agent_name, error_message in all_errors:
            print(f"{Fore.YELLOW}=== {agent_name} ==={Style.RESET_ALL}")
            print(error_message)
            print()

if __name__ == "__main__":
    run_all_tests()
