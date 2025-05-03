#!/usr/bin/env python3
"""
Script to analyze code integrity in a repository.

This script analyzes code integrity in a repository, including:
- Finding all functions and classes
- Identifying errors in functions and classes
- Detecting improper parameter usage
- Finding incorrect function callback points
- Comparing error counts between branches
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, Any, Optional

from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from codegen_on_oss.analysis.code_integrity_analyzer import (
    CodeIntegrityAnalyzer,
    compare_branches,
    analyze_pr,
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_codebase(repo_path: str, branch: Optional[str] = None, commit: Optional[str] = None) -> Codebase:
    """
    Load a codebase from a repository.
    
    Args:
        repo_path: Path to the repository
        branch: Optional branch to load
        commit: Optional commit to load
        
    Returns:
        Loaded codebase
    """
    logger.info(f"Loading codebase from {repo_path}")
    
    if branch:
        logger.info(f"Using branch: {branch}")
    
    if commit:
        logger.info(f"Using commit: {commit}")
    
    # Load the codebase
    codebase = Codebase.from_repo(
        repo_path,
        branch=branch,
        commit=commit
    )
    
    logger.info(f"Loaded codebase with {len(list(codebase.files))} files")
    
    return codebase


def analyze_codebase(codebase: Codebase, output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze a codebase for integrity issues.
    
    Args:
        codebase: The codebase to analyze
        output_file: Optional file to write the results to
        
    Returns:
        Analysis results
    """
    logger.info("Analyzing codebase for integrity issues")
    
    # Create analyzer
    analyzer = CodeIntegrityAnalyzer(codebase)
    
    # Analyze codebase
    results = analyzer.analyze()
    
    # Print summary
    logger.info(f"Found {results['total_errors']} errors in {results['total_functions']} functions and {results['total_classes']} classes")
    
    # Write results to file if requested
    if output_file:
        logger.info(f"Writing results to {output_file}")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    return results


def compare_codebases(main_codebase: Codebase, branch_codebase: Codebase, output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Compare two codebases for integrity issues.
    
    Args:
        main_codebase: The main branch codebase
        branch_codebase: The feature branch codebase
        output_file: Optional file to write the results to
        
    Returns:
        Comparison results
    """
    logger.info("Comparing codebases for integrity issues")
    
    # Compare branches
    comparison = compare_branches(main_codebase, branch_codebase)
    
    # Print summary
    logger.info(f"Main branch has {comparison['main_error_count']} errors")
    logger.info(f"Feature branch has {comparison['branch_error_count']} errors")
    logger.info(f"Difference: {comparison['error_diff']} errors")
    logger.info(f"New errors: {len(comparison['new_errors'])}")
    logger.info(f"Fixed errors: {len(comparison['fixed_errors'])}")
    
    # Write results to file if requested
    if output_file:
        logger.info(f"Writing results to {output_file}")
        with open(output_file, 'w') as f:
            json.dump(comparison, f, indent=2)
    
    return comparison


def analyze_pull_request(main_codebase: Codebase, pr_codebase: Codebase, output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze a pull request for integrity issues.
    
    Args:
        main_codebase: The main branch codebase
        pr_codebase: The PR branch codebase
        output_file: Optional file to write the results to
        
    Returns:
        Analysis results
    """
    logger.info("Analyzing pull request for integrity issues")
    
    # Analyze PR
    pr_analysis = analyze_pr(main_codebase, pr_codebase)
    
    # Print summary
    logger.info(f"PR adds {pr_analysis['new_functions']} new functions and {pr_analysis['new_classes']} new classes")
    logger.info(f"PR modifies {pr_analysis['modified_functions']} functions and {pr_analysis['modified_classes']} classes")
    logger.info(f"PR introduces {pr_analysis['total_new_errors']} new errors")
    
    # Write results to file if requested
    if output_file:
        logger.info(f"Writing results to {output_file}")
        with open(output_file, 'w') as f:
            json.dump(pr_analysis, f, indent=2)
    
    return pr_analysis


def generate_html_report(results: Dict[str, Any], output_file: str) -> None:
    """
    Generate an HTML report from analysis results.
    
    Args:
        results: Analysis results
        output_file: File to write the report to
    """
    logger.info(f"Generating HTML report to {output_file}")
    
    # Generate HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Code Integrity Analysis Report</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            h1, h2, h3 {
                color: #2c3e50;
            }
            .summary {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .error {
                background-color: #ffebee;
                padding: 10px;
                margin: 5px 0;
                border-radius: 3px;
            }
            .error-type {
                font-weight: bold;
                color: #c62828;
            }
            .file-path {
                color: #1565c0;
                font-family: monospace;
            }
            .line-number {
                color: #6a1b9a;
                font-family: monospace;
            }
            .message {
                margin-top: 5px;
            }
            .tabs {
                display: flex;
                margin-bottom: 10px;
            }
            .tab {
                padding: 10px 15px;
                cursor: pointer;
                background-color: #e0e0e0;
                margin-right: 5px;
                border-radius: 3px 3px 0 0;
            }
            .tab.active {
                background-color: #2196f3;
                color: white;
            }
            .tab-content {
                display: none;
                padding: 15px;
                background-color: #f5f5f5;
                border-radius: 0 3px 3px 3px;
            }
            .tab-content.active {
                display: block;
            }
        </style>
    </head>
    <body>
        <h1>Code Integrity Analysis Report</h1>
    """
    
    # Add summary
    html += """
        <div class="summary">
            <h2>Summary</h2>
    """
    
    if "total_functions" in results:
        # Single codebase analysis
        html += f"""
            <p>Analyzed {results['total_functions']} functions and {results['total_classes']} classes.</p>
            <p>Found {results['total_errors']} errors:</p>
            <ul>
                <li>{results['function_errors']} function errors</li>
                <li>{results['class_errors']} class errors</li>
                <li>{results['parameter_errors']} parameter usage errors</li>
                <li>{results['callback_errors']} callback point errors</li>
            </ul>
        """
    elif "comparison" in results:
        # PR analysis
        comparison = results["comparison"]
        html += f"""
            <p>PR adds {results['new_functions']} new functions and {results['new_classes']} new classes.</p>
            <p>PR modifies {results['modified_functions']} functions and {results['modified_classes']} classes.</p>
            <p>PR introduces {results['total_new_errors']} new errors.</p>
            <p>Main branch has {comparison['main_error_count']} errors.</p>
            <p>PR branch has {comparison['branch_error_count']} errors.</p>
            <p>Difference: {comparison['error_diff']} errors.</p>
            <p>New errors: {len(comparison['new_errors'])}</p>
            <p>Fixed errors: {len(comparison['fixed_errors'])}</p>
        """
    else:
        # Branch comparison
        html += f"""
            <p>Main branch has {results['main_error_count']} errors.</p>
            <p>Feature branch has {results['branch_error_count']} errors.</p>
            <p>Difference: {results['error_diff']} errors.</p>
            <p>New errors: {len(results['new_errors'])}</p>
            <p>Fixed errors: {len(results['fixed_errors'])}</p>
        """
    
    html += """
        </div>
    """
    
    # Add tabs
    html += """
        <div class="tabs">
    """
    
    if "total_functions" in results:
        # Single codebase analysis
        html += """
            <div class="tab active" onclick="showTab('errors')">Errors</div>
            <div class="tab" onclick="showTab('codebase')">Codebase Summary</div>
        """
    elif "comparison" in results:
        # PR analysis
        html += """
            <div class="tab active" onclick="showTab('new-errors')">New Errors</div>
            <div class="tab" onclick="showTab('fixed-errors')">Fixed Errors</div>
            <div class="tab" onclick="showTab('comparison')">Comparison</div>
        """
    else:
        # Branch comparison
        html += """
            <div class="tab active" onclick="showTab('new-errors')">New Errors</div>
            <div class="tab" onclick="showTab('fixed-errors')">Fixed Errors</div>
            <div class="tab" onclick="showTab('comparison')">Comparison</div>
        """
    
    html += """
        </div>
    """
    
    # Add tab content
    if "total_functions" in results:
        # Single codebase analysis
        html += """
        <div id="errors" class="tab-content active">
            <h2>Errors</h2>
        """
        
        for error in results["errors"]:
            html += f"""
            <div class="error">
                <div class="error-type">{error['error_type']}</div>
                <div class="file-path">{error['filepath']}</div>
                <div class="line-number">Line: {error['line']}</div>
                <div class="message">{error['message']}</div>
            </div>
            """
        
        html += """
        </div>
        
        <div id="codebase" class="tab-content">
            <h2>Codebase Summary</h2>
            <pre>{results['codebase_summary']}</pre>
        </div>
        """
    elif "comparison" in results:
        # PR analysis
        comparison = results["comparison"]
        
        html += """
        <div id="new-errors" class="tab-content active">
            <h2>New Errors</h2>
        """
        
        for error in results["new_function_errors"] + results["new_class_errors"] + results["modified_function_errors"] + results["modified_class_errors"]:
            html += f"""
            <div class="error">
                <div class="error-type">{error['error_type']}</div>
                <div class="file-path">{error['filepath']}</div>
                <div class="line-number">Line: {error['line']}</div>
                <div class="message">{error['message']}</div>
            </div>
            """
        
        html += """
        </div>
        
        <div id="fixed-errors" class="tab-content">
            <h2>Fixed Errors</h2>
        """
        
        for error in comparison["fixed_errors"]:
            html += f"""
            <div class="error">
                <div class="error-type">{error['error_type']}</div>
                <div class="file-path">{error['filepath']}</div>
                <div class="line-number">Line: {error['line']}</div>
                <div class="message">{error['message']}</div>
            </div>
            """
        
        html += """
        </div>
        
        <div id="comparison" class="tab-content">
            <h2>Comparison</h2>
            <h3>Main Branch Summary</h3>
            <pre>{comparison['main_summary']}</pre>
            <h3>PR Branch Summary</h3>
            <pre>{comparison['branch_summary']}</pre>
        </div>
        """
    else:
        # Branch comparison
        html += """
        <div id="new-errors" class="tab-content active">
            <h2>New Errors</h2>
        """
        
        for error in results["new_errors"]:
            html += f"""
            <div class="error">
                <div class="error-type">{error['error_type']}</div>
                <div class="file-path">{error['filepath']}</div>
                <div class="line-number">Line: {error['line']}</div>
                <div class="message">{error['message']}</div>
            </div>
            """
        
        html += """
        </div>
        
        <div id="fixed-errors" class="tab-content">
            <h2>Fixed Errors</h2>
        """
        
        for error in results["fixed_errors"]:
            html += f"""
            <div class="error">
                <div class="error-type">{error['error_type']}</div>
                <div class="file-path">{error['filepath']}</div>
                <div class="line-number">Line: {error['line']}</div>
                <div class="message">{error['message']}</div>
            </div>
            """
        
        html += """
        </div>
        
        <div id="comparison" class="tab-content">
            <h2>Comparison</h2>
            <h3>Main Branch Summary</h3>
            <pre>{results['main_summary']}</pre>
            <h3>Feature Branch Summary</h3>
            <pre>{results['branch_summary']}</pre>
        </div>
        """
    
    # Add JavaScript
    html += """
        <script>
            function showTab(tabId) {
                // Hide all tabs
                var tabContents = document.getElementsByClassName('tab-content');
                for (var i = 0; i < tabContents.length; i++) {
                    tabContents[i].classList.remove('active');
                }
                
                // Show selected tab
                document.getElementById(tabId).classList.add('active');
                
                // Update tab buttons
                var tabs = document.getElementsByClassName('tab');
                for (var i = 0; i < tabs.length; i++) {
                    tabs[i].classList.remove('active');
                }
                
                // Find the tab button that corresponds to the tabId
                for (var i = 0; i < tabs.length; i++) {
                    if (tabs[i].getAttribute('onclick').includes(tabId)) {
                        tabs[i].classList.add('active');
                    }
                }
            }
        </script>
    </body>
    </html>
    """
    
    # Write HTML to file
    with open(output_file, 'w') as f:
        f.write(html)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Analyze code integrity in a repository')
    parser.add_argument('--repo', required=True, help='Repository path or URL')
    parser.add_argument('--output', help='Output file for results (JSON)')
    parser.add_argument('--html', help='Output file for HTML report')
    parser.add_argument('--mode', choices=['analyze', 'compare', 'pr'], default='analyze', help='Analysis mode')
    parser.add_argument('--main-branch', default='main', help='Main branch name (for compare and pr modes)')
    parser.add_argument('--feature-branch', help='Feature branch name (for compare and pr modes)')
    parser.add_argument('--pr-number', type=int, help='PR number (for pr mode)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if args.mode in ['compare', 'pr'] and not args.feature_branch and not args.pr_number:
        parser.error('--feature-branch or --pr-number is required for compare and pr modes')
    
    # Load codebases
    if args.mode == 'analyze':
        # Load single codebase
        codebase = load_codebase(args.repo)
        
        # Analyze codebase
        results = analyze_codebase(codebase, args.output)
    elif args.mode == 'compare':
        # Load main branch codebase
        main_codebase = load_codebase(args.repo, branch=args.main_branch)
        
        # Load feature branch codebase
        feature_branch = args.feature_branch
        feature_codebase = load_codebase(args.repo, branch=feature_branch)
        
        # Compare codebases
        results = compare_codebases(main_codebase, feature_codebase, args.output)
    elif args.mode == 'pr':
        # Load main branch codebase
        main_codebase = load_codebase(args.repo, branch=args.main_branch)
        
        # Load PR branch codebase
        if args.feature_branch:
            pr_codebase = load_codebase(args.repo, branch=args.feature_branch)
        elif args.pr_number:
            # TODO: Implement loading PR codebase by PR number
            logger.error("Loading PR by number is not implemented yet")
            sys.exit(1)
        
        # Analyze PR
        results = analyze_pull_request(main_codebase, pr_codebase, args.output)
    
    # Generate HTML report if requested
    if args.html:
        generate_html_report(results, args.html)


if __name__ == '__main__':
    main()

