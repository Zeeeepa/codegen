def main():
    """Main entry point for the codebase analyzer."""
    parser = argparse.ArgumentParser(description="Comprehensive Codebase Analyzer")

    # Repository source
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo-url", help="URL of the repository to analyze")
    source_group.add_argument("--repo-path", help="Local path to the repository to analyze")

    # Analysis options
    parser.add_argument("--language", help="Programming language of the codebase (auto-detected if not provided)")
    parser.add_argument("--categories", nargs="+", help="Categories to analyze (default: all)")

    # PR comparison options
    parser.add_argument("--compare-commit", help="Commit SHA to compare with the current codebase")
    parser.add_argument("--pr-number", type=int, help="PR number to analyze")

    # Output options
    parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
    parser.add_argument("--output-file", help="Path to the output file")

    # Visualization options
    parser.add_argument("--visualize", choices=["call-graph", "dependency-map", "directory-tree", "import-cycles"], help="Generate visualization")
    parser.add_argument("--function-name", help="Function name for call graph visualization")
    parser.add_argument("--symbol-name", help="Symbol name for dependency trace visualization")
    parser.add_argument("--class-name", help="Class name for method relationships visualization")
    
    # Type analysis options
    parser.add_argument("--analyze-types", action="store_true", help="Analyze untyped code in the codebase")
    parser.add_argument("--summary", action="store_true", help="Get a summary of the codebase")
    parser.add_argument("--quality", action="store_true", help="Analyze code quality")
    parser.add_argument("--dependency-trace", action="store_true", help="Analyze dependency trace")
    parser.add_argument("--method-relationships", action="store_true", help="Analyze method relationships")
    parser.add_argument("--call-trace", action="store_true", help="Analyze call trace")
    parser.add_argument("--import-cycles", action="store_true", help="Find import cycles")
    
    # New analysis options
    parser.add_argument("--call-chain", action="store_true", help="Analyze call chains between functions")
    parser.add_argument("--dead-code", action="store_true", help="Detect dead code with filtering")
    parser.add_argument("--exclude-patterns", nargs="+", help="Patterns to exclude from dead code detection")
    parser.add_argument("--path-finding", action="store_true", help="Find paths between functions in call graphs")
    parser.add_argument("--source-function", help="Source function for path finding")
    parser.add_argument("--target-function", help="Target function for path finding")
    parser.add_argument("--max-depth", type=int, default=10, help="Maximum depth for path finding")
    parser.add_argument("--dead-symbols", action="store_true", help="Detect dead symbols in the codebase")
    parser.add_argument("--import-analysis", action="store_true", help="Analyze symbol imports in the codebase")

    args = parser.parse_args()

    try:
        # Initialize the analyzer
        analyzer = CodebaseAnalyzer(repo_url=args.repo_url, repo_path=args.repo_path, language=args.language)

        # Handle PR analysis
        if args.pr_number:
            pr_analysis = analyzer.get_pr_diff_analysis(args.pr_number)
            print(json.dumps(pr_analysis, indent=2))
            return

        # Handle comparison
        if args.compare_commit:
            analyzer.init_comparison_codebase(args.compare_commit)
            comparison = analyzer.compare_codebases()
            print(json.dumps(comparison, indent=2))
            return

        # Handle visualization
        if args.visualize:
            if args.visualize == "call-graph":
                visualization = analyzer.visualize_call_graph(args.function_name)
            elif args.visualize == "dependency-map":
                visualization = analyzer.visualize_dependency_map()
            elif args.visualize == "directory-tree":
                visualization = analyzer.visualize_directory_tree()
            elif args.visualize == "import-cycles":
                visualization = analyzer.visualize_import_cycles()
            
            print(json.dumps(visualization, indent=2))
            return
            
        # Handle type analysis
        if args.analyze_types:
            type_analysis = {
                "untyped_return_statements": analyzer.count_untyped_return_statements(),
                "untyped_parameters": analyzer.count_untyped_parameters(),
                "untyped_attributes": analyzer.count_untyped_attributes(),
                "unnamed_keyword_arguments": analyzer.count_unnamed_keyword_arguments(),
            }
            print(json.dumps(type_analysis, indent=2))
            return
            
        # Handle codebase summary
        if args.summary:
            summary = analyzer.get_codebase_summary()
            print(json.dumps(summary, indent=2))
            return
            
        # Handle code quality analysis
        if args.quality:
            quality = analyzer.analyze_codebase_quality()
            print(json.dumps(quality, indent=2))
            return
            
        # Handle dependency trace analysis
        if args.dependency_trace:
            if not args.symbol_name:
                print("Error: --symbol-name is required for dependency trace analysis")
                return
            dependency_trace = analyzer.analyze_dependency_trace(args.symbol_name)
            print(json.dumps(dependency_trace, indent=2))
            return
            
        # Handle method relationships analysis
        if args.method_relationships:
            if not args.class_name:
                print("Error: --class-name is required for method relationships analysis")
                return
            method_relationships = analyzer.analyze_method_relationships(args.class_name)
            print(json.dumps(method_relationships, indent=2))
            return
            
        # Handle call trace analysis
        if args.call_trace:
            if not args.function_name:
                print("Error: --function-name is required for call trace analysis")
                return
            call_trace = analyzer.analyze_call_trace(args.function_name)
            print(json.dumps(call_trace, indent=2))
            return
            
        # Handle import cycles analysis
        if args.import_cycles:
            import_cycles = analyzer.find_import_cycles()
            print(json.dumps(import_cycles, indent=2))
            return
            
        # Handle call chain analysis
        if args.call_chain:
            call_chain = analyzer.get_call_chain_analysis()
            print(json.dumps(call_chain, indent=2))
            return
            
        # Handle dead code detection
        if args.dead_code:
            dead_code = analyzer.get_dead_code_detection_with_filtering(args.exclude_patterns)
            print(json.dumps(dead_code, indent=2))
            return
            
        # Handle path finding
        if args.path_finding:
            path_finding = analyzer.get_path_finding_in_call_graphs(args.source_function, args.target_function, args.max_depth)
            print(json.dumps(path_finding, indent=2))
            return
            
        # Handle dead symbol detection
        if args.dead_symbols:
            dead_symbols = analyzer.get_dead_symbol_detection()
            print(json.dumps(dead_symbols, indent=2))
            return
            
        # Handle import analysis
        if args.import_analysis:
            import_analysis = analyzer.get_symbol_import_analysis()
            print(json.dumps(import_analysis, indent=2))
            return

        # Perform the analysis
        results = analyzer.analyze(categories=args.categories, output_format=args.output_format, output_file=args.output_file)

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
