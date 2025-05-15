#!/usr/bin/env python3
"""
Codebase Analysis CLI Tool

This module provides a command-line interface for analyzing codebases using
the Codegen SDK. It combines functionality from the codebase_analyzer and
context_retriever modules to provide comprehensive analysis capabilities.
"""

import argparse
import logging
import sys
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the codebase analysis CLI tool."""
    parser = argparse.ArgumentParser(description="Codebase Analysis CLI Tool")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a codebase")
    analyze_parser.add_argument(
        "--repo-path", required=True, help="Local path to the repository to analyze"
    )
    analyze_parser.add_argument(
        "--language",
        help="Programming language of the codebase (auto-detected if not provided)",
    )
    analyze_parser.add_argument(
        "--output-format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format",
    )
    analyze_parser.add_argument("--output-file", help="Path to the output file")
    
    # Context command
    context_parser = subparsers.add_parser("context", help="Get context from a codebase")
    context_parser.add_argument(
        "--repo-path", required=True, help="Local path to the repository to analyze"
    )
    context_parser.add_argument(
        "--file", help="Get context for a specific file"
    )
    context_parser.add_argument(
        "--function", help="Get context for a specific function"
    )
    context_parser.add_argument(
        "--class", dest="class_name", help="Get context for a specific class"
    )
    context_parser.add_argument(
        "--output-file", help="Path to the output file"
    )
    
    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Get a summary of a codebase")
    summary_parser.add_argument(
        "--repo-path", required=True, help="Local path to the repository to analyze"
    )
    summary_parser.add_argument(
        "--output-file", help="Path to the output file"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "analyze":
            run_analyze_command(
                repo_path=args.repo_path,
                language=args.language,
                output_format=args.output_format,
                output_file=args.output_file,
            )
        elif args.command == "context":
            run_context_command(
                repo_path=args.repo_path,
                file_path=args.file,
                function_name=args.function,
                class_name=args.class_name,
                output_file=args.output_file,
            )
        elif args.command == "summary":
            run_summary_command(
                repo_path=args.repo_path,
                output_file=args.output_file,
            )
    
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_analyze_command(
    repo_path: str,
    language: Optional[str] = None,
    output_format: str = "text",
    output_file: Optional[str] = None,
):
    """Run the analyze command."""
    from codegen_on_oss.codebase_analyzer import CodebaseAnalyzer
    
    # Initialize the analyzer
    analyzer = CodebaseAnalyzer(
        repo_path=repo_path,
        language=language,
    )
    
    # Perform the analysis
    analyzer.analyze(
        output_format=output_format,
        output_file=output_file,
    )
    
    logger.info("Analysis complete")


def run_context_command(
    repo_path: str,
    file_path: Optional[str] = None,
    function_name: Optional[str] = None,
    class_name: Optional[str] = None,
    output_file: Optional[str] = None,
):
    """Run the context command."""
    import json
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.sdk.core.codebase import Codebase
    from codegen_on_oss.context_retriever import get_codebase_context
    
    # Initialize the codebase
    config = CodebaseConfig(
        debug=False,
        allow_external=True,
        py_resolve_syspath=True,
    )
    
    secrets = SecretsConfig()
    
    codebase = Codebase(
        repo_path=repo_path,
        config=config,
        secrets=secrets
    )
    
    # Get context
    context = get_codebase_context(codebase)
    
    # Get requested context
    result = None
    
    if file_path:
        result = context.get_file_context(file_path)
    elif function_name:
        result = context.get_function_context(function_name)
    elif class_name:
        result = context.get_class_context(class_name)
    else:
        result = {
            "error": "No context type specified. Use --file, --function, or --class"
        }
    
    # Output result
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Context saved to {output_file}")
    else:
        print(json.dumps(result, indent=2))


def run_summary_command(
    repo_path: str,
    output_file: Optional[str] = None,
):
    """Run the summary command."""
    import json
    from codegen_on_oss.context_retriever import analyze_codebase
    
    # Analyze the codebase
    results = analyze_codebase(repo_path)
    
    # Output result
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Summary saved to {output_file}")
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

