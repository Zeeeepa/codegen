#!/usr/bin/env python3
"""
Patch for Codebase Analyzer

This script applies the enhanced features to the codebase analyzer.
"""

import sys
import os
import importlib.util

def main():
    """
    Main entry point for the patch.
    """
    # Check if codebase_analyzer.py exists
    if not os.path.exists("codebase_analyzer.py"):
        print("Error: codebase_analyzer.py not found")
        sys.exit(1)
    
    # Check if enhanced_analyzer.py exists
    if not os.path.exists("enhanced_analyzer.py"):
        print("Error: enhanced_analyzer.py not found")
        sys.exit(1)
    
    # Load the codebase_analyzer module
    spec = importlib.util.spec_from_file_location("codebase_analyzer", "codebase_analyzer.py")
    codebase_analyzer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codebase_analyzer)
    
    # Load the enhanced_analyzer module
    spec = importlib.util.spec_from_file_location("enhanced_analyzer", "enhanced_analyzer.py")
    enhanced_analyzer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(enhanced_analyzer)
    
    # Enhance the CodebaseAnalyzer class
    if hasattr(codebase_analyzer, "CodebaseAnalyzer"):
        codebase_analyzer.CodebaseAnalyzer = enhanced_analyzer.enhance_codebase_analyzer(codebase_analyzer.CodebaseAnalyzer)
        print("Successfully enhanced CodebaseAnalyzer")
    else:
        print("Error: CodebaseAnalyzer class not found in codebase_analyzer.py")
        sys.exit(1)
    
    # Update the main function to include our enhanced features
    if hasattr(codebase_analyzer, "main"):
        original_main = codebase_analyzer.main
        
        def enhanced_main():
            """
            Enhanced main function with additional command-line arguments.
            """
            import argparse
            
            parser = argparse.ArgumentParser(description="Comprehensive Codebase Analyzer")
            
            # Repository source
            source_group = parser.add_mutually_exclusive_group(required=True)
            source_group.add_argument("--repo-url", help="URL of the repository to analyze")
            source_group.add_argument("--repo-path", help="Local path to the repository to analyze")
            
            # Analysis options
            parser.add_argument("--language", help="Programming language of the codebase (auto-detected if not provided)")
            parser.add_argument("--categories", nargs="+", help="Categories to analyze (default: all)")
            
            # Output options
            parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
            parser.add_argument("--output-file", help="Path to the output file")
            
            # Enhanced features
            parser.add_argument("--call-chain", action="store_true", help="Analyze call chains between functions")
            parser.add_argument("--dead-code", action="store_true", help="Detect dead code in the codebase")
            parser.add_argument("--exclude-patterns", nargs="+", help="Regex patterns to exclude from dead code detection")
            parser.add_argument("--path-finding", action="store_true", help="Find paths between functions in the call graph")
            parser.add_argument("--source-function", help="Source function for path finding")
            parser.add_argument("--target-function", help="Target function for path finding")
            parser.add_argument("--max-depth", type=int, default=10, help="Maximum depth for path finding")
            parser.add_argument("--dead-symbols", action="store_true", help="Detect dead symbols in the codebase")
            parser.add_argument("--import-analysis", action="store_true", help="Analyze symbol imports in the codebase")
            
            args = parser.parse_args()
            
            try:
                # Initialize the analyzer
                analyzer = codebase_analyzer.CodebaseAnalyzer(
                    repo_url=args.repo_url,
                    repo_path=args.repo_path,
                    language=args.language
                )
                
                # Perform the analysis
                results = analyzer.analyze(
                    categories=args.categories,
                    output_format=args.output_format,
                    output_file=args.output_file
                )
                
                # Perform enhanced analysis if requested
                if args.call_chain:
                    call_chain_results = analyzer.get_call_chain_analysis()
                    print("Call Chain Analysis Results:")
                    print(json.dumps(call_chain_results, indent=2))
                
                if args.dead_code:
                    dead_code_results = analyzer.get_dead_code_detection_with_filtering(args.exclude_patterns)
                    print("Dead Code Detection Results:")
                    print(json.dumps(dead_code_results, indent=2))
                
                if args.path_finding:
                    path_finding_results = analyzer.get_path_finding_in_call_graphs(
                        args.source_function,
                        args.target_function,
                        args.max_depth
                    )
                    print("Path Finding Results:")
                    print(json.dumps(path_finding_results, indent=2))
                
                if args.dead_symbols:
                    dead_symbol_results = analyzer.get_dead_symbol_detection()
                    print("Dead Symbol Detection Results:")
                    print(json.dumps(dead_symbol_results, indent=2))
                
                if args.import_analysis:
                    import_analysis_results = analyzer.get_symbol_import_analysis()
                    print("Symbol Import Analysis Results:")
                    print(json.dumps(import_analysis_results, indent=2))
                
                # Print success message
                if args.output_format == "json" and args.output_file:
                    print(f"Analysis results saved to {args.output_file}")
                elif args.output_format == "html":
                    print(f"HTML report saved to {args.output_file or 'codebase_analysis_report.html'}")
                
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        
        # Replace the main function
        codebase_analyzer.main = enhanced_main
        print("Successfully enhanced main function")
    else:
        print("Error: main function not found in codebase_analyzer.py")
        sys.exit(1)
    
    # Save the updated codebase_analyzer.py
    with open("codebase_analyzer.py", "w") as f:
        f.write(spec.loader.get_source("codebase_analyzer"))
    
    print("Successfully patched codebase_analyzer.py")

if __name__ == "__main__":
    main()

