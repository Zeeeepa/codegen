#!/usr/bin/env python3
"""
Script to analyze a codebase.

This script provides comprehensive analysis of a codebase, including:
- Code structure analysis
- Dependency analysis
- Complexity analysis
- Code quality metrics
- Error detection
- Documentation coverage
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from codegen_on_oss.analysis.wsl_client import WSLClient


class CodebaseAnalyzer:
    """
    Analyzer for comprehensive codebase analysis.
    """

    def __init__(
        self,
        repo_path: str,
        output_file: Optional[str] = None,
        output_format: str = "json",
        github_token: Optional[str] = None,
    ):
        """
        Initialize a new CodebaseAnalyzer.

        Args:
            repo_path: Path to the repository
            output_file: Optional file to write the results to
            output_format: Output format (json or markdown)
            github_token: GitHub token for authentication
        """
        self.repo_path = repo_path
        self.output_file = output_file
        self.output_format = output_format
        self.github_token = github_token
        self.results: Dict[str, Any] = {
            "repo_path": repo_path,
            "files": {},
            "modules": {},
            "classes": {},
            "functions": {},
            "dependencies": {},
            "metrics": {},
            "errors": [],
            "summary": {},
        }

    def run_analysis(self) -> Dict[str, Any]:
        """
        Run all codebase analysis.

        Returns:
            Analysis results
        """
        logger.info(f"Analyzing repository: {self.repo_path}")

        # Analyze code structure
        self._analyze_structure()

        # Analyze dependencies
        self._analyze_dependencies()

        # Analyze complexity
        self._analyze_complexity()

        # Analyze code quality
        self._analyze_code_quality()

        # Analyze documentation
        self._analyze_documentation()

        # Generate summary
        self._generate_summary()

        # Save results to file if requested
        if self.output_file:
            self._save_results()

        return self.results

    def _analyze_structure(self) -> None:
        """Analyze code structure."""
        logger.info("Analyzing code structure")

        # Find all Python files
        python_files = self._find_python_files()
        self.results["files"] = {file: {"path": file} for file in python_files}

        # Count files by type
        file_types = {}
        for file in python_files:
            ext = os.path.splitext(file)[1]
            if ext not in file_types:
                file_types[ext] = 0
            file_types[ext] += 1
        self.results["file_types"] = file_types

        # Analyze modules, classes, and functions
        for file in python_files:
            self._analyze_file_structure(file)

    def _analyze_file_structure(self, file_path: str) -> None:
        """
        Analyze the structure of a Python file.

        Args:
            file_path: Path to the Python file
        """
        try:
            # Make file path relative to repo path
            rel_path = os.path.relpath(file_path, self.repo_path)
            module_name = os.path.splitext(rel_path.replace("/", "."))[0]

            # Add module to results
            self.results["modules"][module_name] = {
                "file": rel_path,
                "classes": [],
                "functions": [],
                "imports": [],
            }

            # Parse the file to extract classes and functions
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            # Use ast to parse the file
            import ast

            try:
                tree = ast.parse(source)

                # Extract imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            self.results["modules"][module_name]["imports"].append(name.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            for name in node.names:
                                self.results["modules"][module_name]["imports"].append(
                                    f"{node.module}.{name.name}"
                                )

                # Extract classes
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = f"{module_name}.{node.name}"
                        self.results["classes"][class_name] = {
                            "module": module_name,
                            "name": node.name,
                            "methods": [],
                            "docstring": ast.get_docstring(node) or "",
                            "line": node.lineno,
                        }
                        self.results["modules"][module_name]["classes"].append(class_name)

                        # Extract methods
                        for method in [n for n in node.body if isinstance(n, ast.FunctionDef)]:
                            method_name = f"{class_name}.{method.name}"
                            self.results["functions"][method_name] = {
                                "class": class_name,
                                "name": method.name,
                                "docstring": ast.get_docstring(method) or "",
                                "line": method.lineno,
                                "args": [a.arg for a in method.args.args],
                            }
                            self.results["classes"][class_name]["methods"].append(method_name)

                # Extract functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and not any(
                        isinstance(parent, ast.ClassDef) for parent in ast.iter_child_nodes(tree)
                    ):
                        function_name = f"{module_name}.{node.name}"
                        self.results["functions"][function_name] = {
                            "module": module_name,
                            "name": node.name,
                            "docstring": ast.get_docstring(node) or "",
                            "line": node.lineno,
                            "args": [a.arg for a in node.args.args],
                        }
                        self.results["modules"][module_name]["functions"].append(function_name)

            except SyntaxError as e:
                logger.warning(f"Syntax error in {file_path}: {str(e)}")
                self.results["errors"].append({
                    "file": rel_path,
                    "error_type": "syntax_error",
                    "message": str(e),
                    "line": e.lineno or 0,
                })

        except Exception as e:
            logger.warning(f"Error analyzing file structure for {file_path}: {str(e)}")
            self.results["errors"].append({
                "file": os.path.relpath(file_path, self.repo_path),
                "error_type": "analysis_error",
                "message": str(e),
                "line": 0,
            })

    def _analyze_dependencies(self) -> None:
        """Analyze dependencies between modules."""
        logger.info("Analyzing dependencies")

        # Build dependency graph
        dependency_graph = {}
        for module_name, module_info in self.results["modules"].items():
            dependency_graph[module_name] = []
            for import_name in module_info["imports"]:
                # Check if the import is a module in the codebase
                for potential_module in self.results["modules"].keys():
                    if import_name == potential_module or import_name.startswith(f"{potential_module}."):
                        dependency_graph[module_name].append(potential_module)
                        break

        self.results["dependencies"] = dependency_graph

        # Detect circular dependencies
        circular_deps = self._detect_circular_dependencies(dependency_graph)
        if circular_deps:
            self.results["circular_dependencies"] = circular_deps
            logger.warning(f"Detected {len(circular_deps)} circular dependencies")

    def _detect_circular_dependencies(self, dependency_graph: Dict[str, List[str]]) -> List[List[str]]:
        """
        Detect circular dependencies in the dependency graph.

        Args:
            dependency_graph: Dependency graph

        Returns:
            List of circular dependencies
        """
        circular_deps = []
        visited = set()
        path = []

        def dfs(node):
            if node in path:
                # Found a cycle
                cycle_start = path.index(node)
                circular_deps.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for neighbor in dependency_graph.get(node, []):
                dfs(neighbor)

            path.pop()

        for node in dependency_graph:
            dfs(node)

        return circular_deps

    def _analyze_complexity(self) -> None:
        """Analyze code complexity."""
        logger.info("Analyzing code complexity")

        try:
            # Check if radon is installed
            import importlib.util
            if importlib.util.find_spec("radon") is None:
                logger.warning("radon is not installed, skipping complexity analysis")
                return

            import radon.complexity
            import radon.metrics

            # Analyze complexity for each file
            for file_path in self.results["files"]:
                full_path = os.path.join(self.repo_path, file_path)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        source = f.read()

                    # Calculate complexity metrics
                    complexity = radon.complexity.cc_visit(source)
                    maintainability = radon.metrics.mi_visit(source, True)

                    # Store complexity results
                    self.results["files"][file_path]["complexity"] = {
                        "functions": [
                            {
                                "name": func.name,
                                "complexity": func.complexity,
                                "rank": radon.complexity.rank(func.complexity),
                                "line": func.lineno,
                            }
                            for func in complexity
                        ],
                        "maintainability_index": maintainability,
                    }

                    # Flag high complexity functions
                    for func in complexity:
                        if func.complexity > 10:  # McCabe complexity > 10 is considered high
                            self.results["errors"].append({
                                "file": file_path,
                                "error_type": "high_complexity",
                                "message": f"Function '{func.name}' has high complexity ({func.complexity})",
                                "line": func.lineno,
                            })

                except Exception as e:
                    logger.warning(f"Error analyzing complexity for {file_path}: {str(e)}")

        except ImportError:
            logger.warning("radon is not installed, skipping complexity analysis")

    def _analyze_code_quality(self) -> None:
        """Analyze code quality."""
        logger.info("Analyzing code quality")

        try:
            # Check if pylint is installed
            import importlib.util
            if importlib.util.find_spec("pylint") is None:
                logger.warning("pylint is not installed, skipping code quality analysis")
                return

            from pylint.lint import Run
            from pylint.reporters.text import TextReporter

            # Analyze code quality for each file
            for file_path in self.results["files"]:
                full_path = os.path.join(self.repo_path, file_path)
                try:
                    # Run pylint on the file
                    from io import StringIO
                    output = StringIO()
                    reporter = TextReporter(output)
                    Run([full_path], reporter=reporter, exit=False)
                    pylint_output = output.getvalue()

                    # Parse pylint output
                    quality_issues = []
                    for line in pylint_output.splitlines():
                        if ":" in line and any(level in line for level in ["C:", "W:", "E:", "F:"]):
                            parts = line.split(":", 2)
                            if len(parts) >= 3:
                                try:
                                    line_num = int(parts[1])
                                    message = parts[2].strip()
                                    level = message[0]
                                    quality_issues.append({
                                        "line": line_num,
                                        "message": message,
                                        "level": level,
                                    })

                                    # Add high severity issues to errors
                                    if level in ["E", "F"]:
                                        self.results["errors"].append({
                                            "file": file_path,
                                            "error_type": "code_quality",
                                            "message": message,
                                            "line": line_num,
                                        })
                                except ValueError:
                                    pass

                    # Store code quality results
                    self.results["files"][file_path]["quality_issues"] = quality_issues

                except Exception as e:
                    logger.warning(f"Error analyzing code quality for {file_path}: {str(e)}")

        except ImportError:
            logger.warning("pylint is not installed, skipping code quality analysis")

    def _analyze_documentation(self) -> None:
        """Analyze documentation coverage."""
        logger.info("Analyzing documentation coverage")

        # Count documented vs undocumented entities
        doc_stats = {
            "modules": {"total": 0, "documented": 0},
            "classes": {"total": 0, "documented": 0},
            "functions": {"total": 0, "documented": 0},
        }

        # Check modules
        for module_name, module_info in self.results["modules"].items():
            doc_stats["modules"]["total"] += 1
            # Consider a module documented if its file has a module-level docstring
            if self._has_module_docstring(os.path.join(self.repo_path, module_info["file"])):
                doc_stats["modules"]["documented"] += 1

        # Check classes
        for class_name, class_info in self.results["classes"].items():
            doc_stats["classes"]["total"] += 1
            if class_info["docstring"]:
                doc_stats["classes"]["documented"] += 1
            else:
                # Flag undocumented classes
                self.results["errors"].append({
                    "file": self.results["modules"][class_info["module"]]["file"],
                    "error_type": "undocumented_class",
                    "message": f"Class '{class_info['name']}' is not documented",
                    "line": class_info["line"],
                })

        # Check functions
        for func_name, func_info in self.results["functions"].items():
            doc_stats["functions"]["total"] += 1
            if func_info["docstring"]:
                doc_stats["functions"]["documented"] += 1
            else:
                # Flag undocumented functions
                module = func_info.get("module", func_info.get("class", "").split(".")[0])
                file_path = self.results["modules"].get(module, {}).get("file", "unknown")
                self.results["errors"].append({
                    "file": file_path,
                    "error_type": "undocumented_function",
                    "message": f"Function '{func_info['name']}' is not documented",
                    "line": func_info["line"],
                })

        self.results["documentation"] = doc_stats

    def _has_module_docstring(self, file_path: str) -> bool:
        """
        Check if a module has a docstring.

        Args:
            file_path: Path to the Python file

        Returns:
            True if the module has a docstring, False otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            import ast
            tree = ast.parse(source)
            return ast.get_docstring(tree) is not None
        except Exception:
            return False

    def _generate_summary(self) -> None:
        """Generate summary statistics."""
        logger.info("Generating summary")

        summary = {
            "file_count": len(self.results["files"]),
            "module_count": len(self.results["modules"]),
            "class_count": len(self.results["classes"]),
            "function_count": len(self.results["functions"]),
            "error_count": len(self.results["errors"]),
        }

        # Add documentation coverage
        if "documentation" in self.results:
            doc = self.results["documentation"]
            summary["documentation_coverage"] = {
                "modules": doc["modules"]["documented"] / max(1, doc["modules"]["total"]),
                "classes": doc["classes"]["documented"] / max(1, doc["classes"]["total"]),
                "functions": doc["functions"]["documented"] / max(1, doc["functions"]["total"]),
                "overall": (
                    doc["modules"]["documented"] + doc["classes"]["documented"] + doc["functions"]["documented"]
                ) / max(1, doc["modules"]["total"] + doc["classes"]["total"] + doc["functions"]["total"]),
            }

        # Add complexity metrics
        complexity_sum = 0
        complexity_count = 0
        high_complexity_count = 0
        for file_info in self.results["files"].values():
            if "complexity" in file_info:
                for func in file_info["complexity"]["functions"]:
                    complexity_sum += func["complexity"]
                    complexity_count += 1
                    if func["complexity"] > 10:
                        high_complexity_count += 1

        if complexity_count > 0:
            summary["complexity"] = {
                "average": complexity_sum / complexity_count,
                "high_complexity_functions": high_complexity_count,
            }

        # Add error type counts
        error_types = {}
        for error in self.results["errors"]:
            error_type = error["error_type"]
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1
        summary["error_types"] = error_types

        self.results["summary"] = summary

    def _find_python_files(self) -> List[str]:
        """
        Find all Python files in the repository.

        Returns:
            List of Python file paths (relative to repo_path)
        """
        python_files = []
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(".py"):
                    rel_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                    python_files.append(rel_path)
        return python_files

    def _save_results(self) -> None:
        """Save results to a file."""
        if self.output_format.lower() == "markdown":
            with open(self.output_file, "w") as f:
                f.write(self._format_markdown())
        else:
            with open(self.output_file, "w") as f:
                json.dump(self.results, f, indent=2)

        logger.info(f"Results saved to {self.output_file}")

    def _format_markdown(self) -> str:
        """
        Format results as Markdown.

        Returns:
            Markdown-formatted string
        """
        summary = self.results["summary"]
        markdown = f"# Codebase Analysis Results: {self.repo_path}\n\n"
        markdown += "## Summary\n\n"
        markdown += f"- **Files**: {summary['file_count']}\n"
        markdown += f"- **Modules**: {summary['module_count']}\n"
        markdown += f"- **Classes**: {summary['class_count']}\n"
        markdown += f"- **Functions**: {summary['function_count']}\n"
        markdown += f"- **Errors**: {summary['error_count']}\n\n"

        if "documentation_coverage" in summary:
            doc = summary["documentation_coverage"]
            markdown += "### Documentation Coverage\n\n"
            markdown += f"- **Overall**: {doc['overall']:.2%}\n"
            markdown += f"- **Modules**: {doc['modules']:.2%}\n"
            markdown += f"- **Classes**: {doc['classes']:.2%}\n"
            markdown += f"- **Functions**: {doc['functions']:.2%}\n\n"

        if "complexity" in summary:
            complexity = summary["complexity"]
            markdown += "### Complexity\n\n"
            markdown += f"- **Average Complexity**: {complexity['average']:.2f}\n"
            markdown += f"- **High Complexity Functions**: {complexity['high_complexity_functions']}\n\n"

        if "error_types" in summary:
            markdown += "### Error Types\n\n"
            for error_type, count in summary["error_types"].items():
                markdown += f"- **{error_type.replace('_', ' ').title()}**: {count}\n"
            markdown += "\n"

        if "circular_dependencies" in self.results:
            markdown += "### Circular Dependencies\n\n"
            for cycle in self.results["circular_dependencies"]:
                markdown += f"- {' -> '.join(cycle)}\n"
            markdown += "\n"

        markdown += "## Errors\n\n"
        for error in self.results["errors"]:
            markdown += f"### {error['error_type'].replace('_', ' ').title()}\n\n"
            markdown += f"- **File**: {error['file']}\n"
            markdown += f"- **Line**: {error['line']}\n"
            markdown += f"- **Message**: {error['message']}\n\n"

        return markdown


def analyze_codebase(
    repo_path: str,
    output_file: Optional[str] = None,
    output_format: str = "json",
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze a codebase.

    Args:
        repo_path: Path to the repository
        output_file: Optional file to write the results to
        output_format: Output format (json or markdown)
        github_token: GitHub token for authentication

    Returns:
        Analysis results
    """
    analyzer = CodebaseAnalyzer(
        repo_path=repo_path,
        output_file=output_file,
        output_format=output_format,
        github_token=github_token,
    )
    return analyzer.run_analysis()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Analyze a codebase")

    parser.add_argument("repo_path", help="Path to the repository")
    parser.add_argument("--output", help="Output file to save results to")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format",
    )
    parser.add_argument("--github-token", help="GitHub token for authentication")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Analyze codebase
    results = analyze_codebase(
        repo_path=args.repo_path,
        output_file=args.output,
        output_format=args.format,
        github_token=args.github_token,
    )

    # Print summary
    if args.format == "markdown":
        print(f"# Codebase Analysis Summary\n\n")
        print(f"- **Files**: {results['summary']['file_count']}\n")
        print(f"- **Modules**: {results['summary']['module_count']}\n")
        print(f"- **Classes**: {results['summary']['class_count']}\n")
        print(f"- **Functions**: {results['summary']['function_count']}\n")
        print(f"- **Errors**: {results['summary']['error_count']}\n")
    else:
        print(json.dumps(results["summary"], indent=2))


if __name__ == "__main__":
    main()

