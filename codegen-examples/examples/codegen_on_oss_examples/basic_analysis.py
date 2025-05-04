"""
Example script demonstrating the use of the unified analysis module.

This script shows how to use the CodeAnalyzer and CodeMetrics classes
to perform comprehensive code analysis on a repository.
"""

import codegen
from codegen import Codebase

from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.metrics import CodeMetrics


@codegen.function("codegen-on-oss-basic-analysis")
def run(codebase: Codebase):
    """
    Perform basic code analysis on a codebase.
    
    This function:
    1. Initializes a CodeAnalyzer with the provided codebase
    2. Performs code quality analysis
    3. Calculates code metrics
    4. Returns a comprehensive analysis report
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        dict: A dictionary containing analysis results
    """
    print("Analyzing codebase...")
    
    # Initialize the analyzer
    analyzer = CodeAnalyzer(codebase)
    
    # Perform code quality analysis
    quality_report = analyzer.analyze_code_quality()
    
    # Calculate code metrics
    metrics = CodeMetrics(codebase)
    complexity_metrics = metrics.calculate_complexity_metrics()
    
    # Combine results
    results = {
        "quality_report": quality_report,
        "complexity_metrics": complexity_metrics,
    }
    
    print("Analysis complete!")
    return results


if __name__ == "__main__":
    print("Initializing codebase...")
    # You can replace this with any repository you want to analyze
    codebase = Codebase.from_repo("fastapi/fastapi")
    
    # Run the analysis
    results = run(codebase)
    
    # Print a summary of the results
    print("\nAnalysis Summary:")
    print(f"Quality Issues Found: {len(results['quality_report'].get('issues', []))}")
    print(f"Average Complexity: {results['complexity_metrics'].get('average_complexity', 'N/A')}")

