#!/usr/bin/env python3
"""
Command-line interface for the codebase analysis viewer.
"""

import argparse
import sys
from typing import Dict, List, Optional

try:
    from .codebase_analyzer import CodebaseAnalyzer
    from .codebase_comparator import CodebaseComparator
except ImportError:
    try:
        from codebase_analyzer import CodebaseAnalyzer
        from codebase_comparator import CodebaseComparator
    except ImportError:
        print(
            "Codebase analysis modules not found. "
            "Please ensure they're in the same directory."
        )
        sys.exit(1)


def setup_parser() -> argparse.ArgumentParser:
    """
    Set up the command-line argument parser.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Codebase Analysis Viewer - Analyze and compare codebases"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single codebase")
    analyze_parser.add_argument("path", help="Path to the codebase to analyze")
    analyze_parser.add_argument(
        "--output",
        help="Output file for the analysis results (default: stdout)",
        default=None,
    )
    analyze_parser.add_argument(
        "--format",
        choices=["text", "json", "yaml"],
        default="text",
        help="Output format (default: text)",
    )
    analyze_parser.add_argument(
        "--categories",
        nargs="+",
        help="Analysis categories to include (default: all)",
        default=None,
    )
    analyze_parser.add_argument(
        "--language",
        help="Filter analysis to specific programming language",
        default=None,
    )
    analyze_parser.add_argument(
        "--depth",
        type=int,
        help="Depth of analysis (1-3, where 3 is most detailed)",
        default=2,
    )

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two codebases")
    compare_parser.add_argument("path1", help="Path to the first codebase")
    compare_parser.add_argument("path2", help="Path to the second codebase")
    compare_parser.add_argument(
        "--output",
        help="Output file for the comparison results (default: stdout)",
        default=None,
    )
    compare_parser.add_argument(
        "--format",
        choices=["text", "json", "yaml"],
        default="text",
        help="Output format (default: text)",
    )
    compare_parser.add_argument(
        "--categories",
        nargs="+",
        help="Comparison categories to include (default: all)",
        default=None,
    )
    compare_parser.add_argument(
        "--language",
        help="Filter comparison to specific programming language",
        default=None,
    )
    compare_parser.add_argument(
        "--depth",
        type=int,
        help="Depth of comparison (1-3, where 3 is most detailed)",
        default=2,
    )

    # Interactive command
    interactive_parser = subparsers.add_parser(
        "interactive", help="Run in interactive mode"
    )
    interactive_parser.add_argument(
        "--path",
        help="Path to the codebase to analyze initially",
        default=None,
    )

    # Web command
    web_parser = subparsers.add_parser("web", help="Launch the web interface")
    web_parser.add_argument(
        "--port",
        type=int,
        help="Port to run the web interface on",
        default=7860,
    )
    web_parser.add_argument(
        "--host",
        help="Host to run the web interface on",
        default="127.0.0.1",
    )

    return parser


def analyze_codebase(
    path: str,
    output: Optional[str] = None,
    format_type: str = "text",
    categories: Optional[List[str]] = None,
    language: Optional[str] = None,
    depth: int = 2,
) -> Dict:
    """
    Analyze a codebase and return the results.

    Args:
        path: Path to the codebase to analyze.
        output: Output file for the analysis results.
        format_type: Output format (text, json, yaml).
        categories: Analysis categories to include.
        language: Filter analysis to specific programming language.
        depth: Depth of analysis (1-3, where 3 is most detailed).

    Returns:
        Dict: The analysis results.
    """
    analyzer = CodebaseAnalyzer(path)
    results = analyzer.analyze(categories=categories, language=language, depth=depth)

    if output:
        if format_type == "json":
            import json

            with open(output, "w") as f:
                json.dump(results, f, indent=2)
        elif format_type == "yaml":
            import yaml

            with open(output, "w") as f:
                yaml.dump(results, f)
        else:  # text
            with open(output, "w") as f:
                f.write(str(results))
    else:
        if format_type == "json":
            import json

            print(json.dumps(results, indent=2))
        elif format_type == "yaml":
            import yaml

            print(yaml.dump(results))
        else:  # text
            print(results)

    return results


def compare_codebases(
    path1: str,
    path2: str,
    output: Optional[str] = None,
    format_type: str = "text",
    categories: Optional[List[str]] = None,
    language: Optional[str] = None,
    depth: int = 2,
) -> Dict:
    """
    Compare two codebases and return the results.

    Args:
        path1: Path to the first codebase.
        path2: Path to the second codebase.
        output: Output file for the comparison results.
        format_type: Output format (text, json, yaml).
        categories: Comparison categories to include.
        language: Filter comparison to specific programming language.
        depth: Depth of comparison (1-3, where 3 is most detailed).

    Returns:
        Dict: The comparison results.
    """
    comparator = CodebaseComparator(path1, path2)
    results = comparator.compare(categories=categories, language=language, depth=depth)

    if output:
        if format_type == "json":
            import json

            with open(output, "w") as f:
                json.dump(results, f, indent=2)
        elif format_type == "yaml":
            import yaml

            with open(output, "w") as f:
                yaml.dump(results, f)
        else:  # text
            with open(output, "w") as f:
                f.write(str(results))
    else:
        if format_type == "json":
            import json

            print(json.dumps(results, indent=2))
        elif format_type == "yaml":
            import yaml

            print(yaml.dump(results))
        else:  # text
            print(results)

    return results


def run_interactive_mode(path: Optional[str] = None) -> None:
    """
    Run the analysis viewer in interactive mode.

    Args:
        path: Path to the codebase to analyze initially.
    """
    try:
        import cmd
        import readline  # noqa: F401
    except ImportError:
        pass

    class AnalysisShell(cmd.Cmd):
        intro = (
            "Welcome to the Codebase Analysis Interactive Shell. "
            "Type help or ? to list commands.\n"
        )
        prompt = "(analysis) "
        current_path = path
        analyzer = None
        comparator = None
        last_results = None

        def do_analyze(self, arg):
            """
            Analyze a codebase: analyze [path] [--categories cat1 cat2]
            [--language lang] [--depth 1-3]
            """
            args = arg.split()
            path_arg = self.current_path
            categories = None
            language = None
            depth = 2

            if args and not args[0].startswith("--"):
                path_arg = args[0]
                args = args[1:]

            i = 0
            while i < len(args):
                if args[i] == "--categories" and i + 1 < len(args):
                    categories = []
                    i += 1
                    while i < len(args) and not args[i].startswith("--"):
                        categories.append(args[i])
                        i += 1
                    continue
                elif args[i] == "--language" and i + 1 < len(args):
                    language = args[i + 1]
                    i += 2
                    continue
                elif args[i] == "--depth" and i + 1 < len(args):
                    try:
                        depth = int(args[i + 1])
                    except ValueError:
                        print("Depth must be an integer between 1 and 3")
                        return
                    i += 2
                    continue
                i += 1

            if not path_arg:
                print("Please specify a path to analyze")
                return

            self.current_path = path_arg
            self.analyzer = CodebaseAnalyzer(path_arg)
            self.last_results = self.analyzer.analyze(
                categories=categories, language=language, depth=depth
            )
            print(self.last_results)

        def do_compare(self, arg):
            """
            Compare two codebases: compare path1 path2 [--categories cat1 cat2]
            [--language lang] [--depth 1-3]
            """
            args = arg.split()
            if len(args) < 2:
                print("Please specify two paths to compare")
                return

            path1 = args[0]
            path2 = args[1]
            args = args[2:]

            categories = None
            language = None
            depth = 2

            i = 0
            while i < len(args):
                if args[i] == "--categories" and i + 1 < len(args):
                    categories = []
                    i += 1
                    while i < len(args) and not args[i].startswith("--"):
                        categories.append(args[i])
                        i += 1
                    continue
                elif args[i] == "--language" and i + 1 < len(args):
                    language = args[i + 1]
                    i += 2
                    continue
                elif args[i] == "--depth" and i + 1 < len(args):
                    try:
                        depth = int(args[i + 1])
                    except ValueError:
                        print("Depth must be an integer between 1 and 3")
                        return
                    i += 2
                    continue
                i += 1

            self.comparator = CodebaseComparator(path1, path2)
            self.last_results = self.comparator.compare(
                categories=categories, language=language, depth=depth
            )
            print(self.last_results)

        def do_save(self, arg):
            """
            Save the last analysis or comparison results:
            save filename [--format text|json|yaml]
            """
            if not self.last_results:
                print("No results to save. Run analyze or compare first.")
                return

            args = arg.split()
            if not args:
                print("Please specify a filename to save to")
                return

            filename = args[0]
            format_type = "text"

            if len(args) > 1 and args[1] == "--format" and len(args) > 2:
                if args[2] in ["text", "json", "yaml"]:
                    format_type = args[2]
                else:
                    print("Invalid format. Use text, json, or yaml.")
                    return

            if format_type == "json":
                import json

                with open(filename, "w") as f:
                    json.dump(self.last_results, f, indent=2)
            elif format_type == "yaml":
                import yaml

                with open(filename, "w") as f:
                    yaml.dump(self.last_results, f)
            else:  # text
                with open(filename, "w") as f:
                    f.write(str(self.last_results))

            print(f"Results saved to {filename}")

        def do_exit(self, arg):
            """Exit the interactive shell"""
            print("Goodbye!")
            return True

        def do_quit(self, arg):
            """Exit the interactive shell"""
            return self.do_exit(arg)

        def do_web(self, arg):
            """Launch the web interface"""
            try:
                from .analysis_viewer_web import launch_web_interface
            except ImportError:
                try:
                    from analysis_viewer_web import launch_web_interface
                except ImportError:
                    print("Web interface module not found")
                    return

            args = arg.split()
            port = 7860
            host = "127.0.0.1"

            if args and args[0] == "--port" and len(args) > 1:
                try:
                    port = int(args[1])
                except ValueError:
                    print("Port must be an integer")
                    return

            if len(args) > 2 and args[2] == "--host" and len(args) > 3:
                host = args[3]

            print(f"Launching web interface at http://{host}:{port}")
            launch_web_interface(host=host, port=port)

    AnalysisShell().cmdloop()


def run_web_interface(port: int = 7860, host: str = "127.0.0.1") -> None:
    """
    Launch the web interface for the analysis viewer.

    Args:
        port: Port to run the web interface on.
        host: Host to run the web interface on.
    """
    try:
        from .analysis_viewer_web import launch_web_interface
    except ImportError:
        try:
            from analysis_viewer_web import launch_web_interface
        except ImportError:
            print("Web interface module not found")
            sys.exit(1)

    launch_web_interface(host=host, port=port)


def main() -> None:
    """
    Main entry point for the codebase analysis viewer CLI.
    """
    parser = setup_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        analyze_codebase(
            args.path,
            args.output,
            args.format,
            args.categories,
            args.language,
            args.depth,
        )
    elif args.command == "compare":
        compare_codebases(
            args.path1,
            args.path2,
            args.output,
            args.format,
            args.categories,
            args.language,
            args.depth,
        )
    elif args.command == "interactive":
        run_interactive_mode(args.path)
    elif args.command == "web":
        run_web_interface(args.port, args.host)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
