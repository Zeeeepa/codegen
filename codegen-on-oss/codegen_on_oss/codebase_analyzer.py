#!/usr/bin/env python3
"""
Codebase Analyzer Module

This module provides a comprehensive codebase analysis system using the Codegen SDK.
It consolidates functionality from multiple analyzers into a single, cohesive interface
for retrieving context about a codebase, including code quality, structure, dependencies,
and more.
"""

import argparse
import datetime
import json
import logging
import os
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.sdk.core.codebase import Codebase
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.enums import EdgeType, SymbolType
    from codegen.shared.enums.programming_language import ProgrammingLanguage
except ImportError:
    print("Codegen SDK not found. Please install it first.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class IssueSeverity(str, Enum):
    """Severity levels for issues."""
    CRITICAL = "critical"  # Must be fixed immediately, blocks functionality
    ERROR = "error"        # Must be fixed, causes errors or undefined behavior
    WARNING = "warning"    # Should be fixed, may cause problems in future
    INFO = "info"          # Informational, could be improved but not critical


class IssueCategory(str, Enum):
    """Categories of issues that can be detected."""
    # Code Quality Issues
    UNUSED_CODE = "unused_code"
    COMPLEXITY = "complexity"
    STYLE = "style"
    MAINTAINABILITY = "maintainability"
    
    # Dependency Issues
    CIRCULAR_DEPENDENCY = "circular_dependency"
    DEPENDENCY_MISMATCH = "dependency_mismatch"
    IMPORT_ERROR = "import_error"
    
    # Implementation Issues
    PARAMETER_ERROR = "parameter_error"
    RETURN_TYPE_ERROR = "return_type_error"
    IMPLEMENTATION_ERROR = "implementation_error"
    
    # Structure Issues
    ARCHITECTURE = "architecture"
    COHESION = "cohesion"
    COUPLING = "coupling"


class CodeIssue:
    """Represents a code issue found during analysis."""
    
    def __init__(
        self,
        category: IssueCategory,
        severity: IssueSeverity,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        symbol_name: Optional[str] = None,
        symbol_type: Optional[str] = None,
        code_snippet: Optional[str] = None,
        suggestion: Optional[str] = None,
    ):
        self.category = category
        self.severity = severity
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
        self.symbol_name = symbol_name
        self.symbol_type = symbol_type
        self.code_snippet = code_snippet
        self.suggestion = suggestion
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the issue to a dictionary."""
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "symbol_name": self.symbol_name,
            "symbol_type": self.symbol_type,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
        }
    
    def __str__(self) -> str:
        """String representation of the issue."""
        location = f"{self.file_path}:{self.line_number}" if self.file_path else "Unknown location"
        symbol = f"{self.symbol_type} '{self.symbol_name}'" if self.symbol_name else ""
        return f"[{self.severity.upper()}] {self.category}: {self.message} in {location} {symbol}"


class CodebaseAnalyzer:
    """
    Comprehensive codebase analyzer using Codegen SDK.
    
    This class provides methods to analyze a codebase and extract detailed information
    about its structure, dependencies, code quality, and more.
    """
    
    def __init__(
        self,
        repo_path: Optional[str] = None,
        language: Optional[str] = None,
    ):
        """
        Initialize the CodebaseAnalyzer.
        
        Args:
            repo_path: Local path to the repository to analyze
            language: Programming language of the codebase (auto-detected if not provided)
        """
        self.repo_path = repo_path
        self.language = language
        self.codebase = None
        self.issues = []
        
        # Initialize the codebase if path is provided
        if repo_path:
            self._init_codebase(repo_path, language)
    
    def _init_codebase(self, repo_path: str, language: Optional[str] = None):
        """Initialize codebase from a local repository path."""
        try:
            # Configure the codebase
            config = CodebaseConfig(
                debug=False,
                allow_external=True,
                py_resolve_syspath=True,
            )
            
            secrets = SecretsConfig()
            
            # Initialize the codebase
            logger.info(f"Initializing codebase from {repo_path}...")
            
            prog_lang = None
            if language:
                prog_lang = ProgrammingLanguage(language.upper())
            
            self.codebase = Codebase(
                repo_path=repo_path,
                language=prog_lang,
                config=config,
                secrets=secrets
            )
            
            logger.info(f"Successfully initialized codebase from {repo_path}")
            
        except Exception as e:
            logger.error(f"Error initializing codebase from path: {e}")
            raise
    
    def analyze(self, output_format: str = "text", output_file: Optional[str] = None):
        """
        Perform a comprehensive analysis of the codebase.
        
        Args:
            output_format: Format of the output (text, json, html)
            output_file: Path to the output file
            
        Returns:
            Dict containing the analysis results
        """
        if not self.codebase:
            raise ValueError("Codebase not initialized. Please initialize the codebase first.")
        
        # Perform all analyses
        self._analyze_code_quality()
        self._analyze_dependencies()
        self._analyze_structure()
        
        # Generate report
        results = self._generate_report()
        
        # Output results
        if output_format == "json":
            self._output_json(results, output_file)
        elif output_format == "html":
            self._output_html(results, output_file)
        else:
            self._output_text(results, output_file)
        
        return results
    
    def _analyze_code_quality(self):
        """Analyze code quality issues."""
        logger.info("Analyzing code quality...")
        
        # Find unused functions
        self._find_unused_functions()
        
        # Find unused imports
        self._find_unused_imports()
        
        # Find functions with unused parameters
        self._find_unused_parameters()
        
        # Find complex functions
        self._find_complex_functions()
        
        logger.info(f"Found {len(self.issues)} code quality issues")
    
    def _find_unused_functions(self):
        """Find unused functions in the codebase."""
        for func in self.codebase.functions:
            if not func.usages:
                self.issues.append(CodeIssue(
                    category=IssueCategory.UNUSED_CODE,
                    severity=IssueSeverity.WARNING,
                    message="Function is never called",
                    file_path=func.file.file_path if hasattr(func, "file") else None,
                    symbol_name=func.name,
                    symbol_type="function",
                    suggestion="Consider removing this function or documenting why it's needed"
                ))
    
    def _find_unused_imports(self):
        """Find unused imports in the codebase."""
        for file in self.codebase.files:
            for import_stmt in file.imports:
                if not import_stmt.usages:
                    self.issues.append(CodeIssue(
                        category=IssueCategory.UNUSED_CODE,
                        severity=IssueSeverity.INFO,
                        message="Import is never used",
                        file_path=file.file_path,
                        symbol_name=import_stmt.source,
                        symbol_type="import",
                        suggestion="Remove this unused import"
                    ))
    
    def _find_unused_parameters(self):
        """Find functions with unused parameters."""
        for func in self.codebase.functions:
            for param in func.parameters:
                # Check if parameter is used in function body
                if param.name not in [dep.name for dep in func.dependencies]:
                    self.issues.append(CodeIssue(
                        category=IssueCategory.PARAMETER_ERROR,
                        severity=IssueSeverity.WARNING,
                        message=f"Parameter '{param.name}' is never used",
                        file_path=func.file.file_path if hasattr(func, "file") else None,
                        symbol_name=func.name,
                        symbol_type="function",
                        suggestion=f"Consider removing the unused parameter '{param.name}'"
                    ))
    
    def _find_complex_functions(self):
        """Find overly complex functions."""
        for func in self.codebase.functions:
            # Simple complexity heuristic based on source code length
            source_lines = func.source.count('\n') + 1
            if source_lines > 50:  # Arbitrary threshold
                self.issues.append(CodeIssue(
                    category=IssueCategory.COMPLEXITY,
                    severity=IssueSeverity.INFO,
                    message=f"Function is {source_lines} lines long, which may be too complex",
                    file_path=func.file.file_path if hasattr(func, "file") else None,
                    symbol_name=func.name,
                    symbol_type="function",
                    suggestion="Consider refactoring this function into smaller, more focused functions"
                ))
    
    def _analyze_dependencies(self):
        """Analyze dependency issues."""
        logger.info("Analyzing dependencies...")
        
        # Find parameter mismatches in function calls
        self._find_parameter_mismatches()
        
        # Find circular imports (simplified approach)
        self._find_circular_imports()
        
        logger.info(f"Found {len(self.issues)} dependency issues")
    
    def _find_parameter_mismatches(self):
        """Find parameter mismatches in function calls."""
        for func in self.codebase.functions:
            for call in func.call_sites:
                expected_params = set(p.name for p in func.parameters)
                actual_params = set(arg.parameter_name for arg in call.args if arg.parameter_name)
                missing = expected_params - actual_params
                if missing and not func.has_kwargs:
                    self.issues.append(CodeIssue(
                        category=IssueCategory.PARAMETER_ERROR,
                        severity=IssueSeverity.ERROR,
                        message=f"Missing required parameters: {missing}",
                        file_path=call.file.file_path if hasattr(call, "file") else None,
                        symbol_name=func.name,
                        symbol_type="function call",
                        suggestion=f"Add the missing parameters: {missing}"
                    ))
    
    def _find_circular_imports(self):
        """Find circular imports in the codebase (simplified approach)."""
        # This is a simplified approach that doesn't handle all cases
        # A more robust implementation would use a graph-based approach
        import_map = {}
        
        # Build import map
        for file in self.codebase.files:
            import_map[file.file_path] = []
            for import_stmt in file.imports:
                if hasattr(import_stmt, "resolved_file") and import_stmt.resolved_file:
                    import_map[file.file_path].append(import_stmt.resolved_file.file_path)
        
        # Check for circular imports (direct only)
        for file_path, imports in import_map.items():
            for imported_file in imports:
                if imported_file in import_map and file_path in import_map[imported_file]:
                    self.issues.append(CodeIssue(
                        category=IssueCategory.CIRCULAR_DEPENDENCY,
                        severity=IssueSeverity.WARNING,
                        message=f"Circular import detected between {file_path} and {imported_file}",
                        file_path=file_path,
                        suggestion="Refactor the code to break the circular dependency"
                    ))
    
    def _analyze_structure(self):
        """Analyze codebase structure issues."""
        logger.info("Analyzing codebase structure...")
        
        # Find large files
        self._find_large_files()
        
        # Find deeply nested functions
        self._find_deeply_nested_functions()
        
        logger.info(f"Found {len(self.issues)} structure issues")
    
    def _find_large_files(self):
        """Find excessively large files."""
        for file in self.codebase.files:
            if hasattr(file, "source") and file.source:
                line_count = file.source.count('\n') + 1
                if line_count > 500:  # Arbitrary threshold
                    self.issues.append(CodeIssue(
                        category=IssueCategory.MAINTAINABILITY,
                        severity=IssueSeverity.INFO,
                        message=f"File is {line_count} lines long, which may be too large",
                        file_path=file.file_path,
                        suggestion="Consider splitting this file into multiple smaller files"
                    ))
    
    def _find_deeply_nested_functions(self):
        """Find deeply nested functions."""
        # This is a simplified approach that doesn't handle all cases
        # A more robust implementation would parse the AST
        for func in self.codebase.functions:
            if hasattr(func, "source") and func.source:
                # Count indentation levels as a proxy for nesting
                lines = func.source.split('\n')
                max_indent = 0
                for line in lines:
                    indent = len(line) - len(line.lstrip())
                    max_indent = max(max_indent, indent)
                
                # Assuming 4 spaces or 1 tab per indentation level
                nesting_level = max_indent // 4
                if nesting_level > 4:  # Arbitrary threshold
                    self.issues.append(CodeIssue(
                        category=IssueCategory.COMPLEXITY,
                        severity=IssueSeverity.WARNING,
                        message=f"Function has a nesting level of {nesting_level}, which may be too deep",
                        file_path=func.file.file_path if hasattr(func, "file") else None,
                        symbol_name=func.name,
                        symbol_type="function",
                        suggestion="Consider refactoring to reduce nesting depth"
                    ))
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report of the analysis results."""
        # Basic codebase statistics
        stats = {
            "files": len(list(self.codebase.files)),
            "functions": len(list(self.codebase.functions)),
            "classes": len(list(self.codebase.classes)),
            "imports": len(list(self.codebase.imports)),
        }
        
        # Group issues by category
        issues_by_category = {}
        for issue in self.issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue.to_dict())
        
        # Group issues by severity
        issues_by_severity = {}
        for issue in self.issues:
            if issue.severity not in issues_by_severity:
                issues_by_severity[issue.severity] = []
            issues_by_severity[issue.severity].append(issue.to_dict())
        
        # Create report
        report = {
            "metadata": {
                "repo_path": self.repo_path,
                "language": self.language,
                "analysis_time": datetime.datetime.now().isoformat(),
            },
            "statistics": stats,
            "issues": {
                "total": len(self.issues),
                "by_category": issues_by_category,
                "by_severity": issues_by_severity,
            },
        }
        
        return report
    
    def _output_json(self, results: Dict[str, Any], output_file: Optional[str] = None):
        """Output results in JSON format."""
        json_str = json.dumps(results, indent=2)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_str)
            logger.info(f"Results saved to {output_file}")
        else:
            print(json_str)
    
    def _output_html(self, results: Dict[str, Any], output_file: Optional[str] = None):
        """Output results in HTML format."""
        if not output_file:
            output_file = "codebase_analysis_report.html"
        
        # Simple HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Codebase Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .section {{ margin-bottom: 30px; }}
                .issue {{ margin-bottom: 10px; padding: 10px; border-radius: 5px; }}
                .critical {{ background-color: #ffdddd; }}
                .error {{ background-color: #ffeeee; }}
                .warning {{ background-color: #ffffdd; }}
                .info {{ background-color: #eeeeff; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Codebase Analysis Report</h1>
            
            <div class="section">
                <h2>Metadata</h2>
                <p><strong>Repository:</strong> {results['metadata']['repo_path']}</p>
                <p><strong>Language:</strong> {results['metadata']['language'] or 'Auto-detected'}</p>
                <p><strong>Analysis Time:</strong> {results['metadata']['analysis_time']}</p>
            </div>
            
            <div class="section">
                <h2>Statistics</h2>
                <p><strong>Files:</strong> {results['statistics']['files']}</p>
                <p><strong>Functions:</strong> {results['statistics']['functions']}</p>
                <p><strong>Classes:</strong> {results['statistics']['classes']}</p>
                <p><strong>Imports:</strong> {results['statistics']['imports']}</p>
                <p><strong>Total Issues:</strong> {results['issues']['total']}</p>
            </div>
        """
        
        # Add issues by severity
        html += """
            <div class="section">
                <h2>Issues by Severity</h2>
        """
        
        for severity in ['critical', 'error', 'warning', 'info']:
            if severity in results['issues']['by_severity']:
                issues = results['issues']['by_severity'][severity]
                html += f"""
                <h3>{severity.title()} ({len(issues)})</h3>
                """
                
                if issues:
                    for issue in issues:
                        html += f"""
                        <div class="issue {severity}">
                            <p><strong>{issue['category']}:</strong> {issue['message']}</p>
                            <p><strong>Location:</strong> {issue['file_path'] or 'Unknown'}{':' + str(issue['line_number']) if issue['line_number'] else ''}</p>
                            {f"<p><strong>Symbol:</strong> {issue['symbol_type']} '{issue['symbol_name']}'</p>" if issue['symbol_name'] else ''}
                            {f"<p><strong>Suggestion:</strong> {issue['suggestion']}</p>" if issue['suggestion'] else ''}
                        </div>
                        """
        
        html += """
            </div>
        """
        
        # Add issues by category
        html += """
            <div class="section">
                <h2>Issues by Category</h2>
        """
        
        for category, issues in results['issues']['by_category'].items():
            html += f"""
            <h3>{category.replace('_', ' ').title()} ({len(issues)})</h3>
            """
            
            if issues:
                html += """
                <table>
                    <tr>
                        <th>Severity</th>
                        <th>Message</th>
                        <th>Location</th>
                        <th>Symbol</th>
                    </tr>
                """
                
                for issue in issues:
                    html += f"""
                    <tr>
                        <td>{issue['severity']}</td>
                        <td>{issue['message']}</td>
                        <td>{issue['file_path'] or 'Unknown'}{':' + str(issue['line_number']) if issue['line_number'] else ''}</td>
                        <td>{f"{issue['symbol_type']} '{issue['symbol_name']}'" if issue['symbol_name'] else ''}</td>
                    </tr>
                    """
                
                html += """
                </table>
                """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html)
        
        logger.info(f"HTML report saved to {output_file}")
    
    def _output_text(self, results: Dict[str, Any], output_file: Optional[str] = None):
        """Output results in plain text format."""
        text = f"""
Codebase Analysis Report
========================

Metadata:
- Repository: {results['metadata']['repo_path']}
- Language: {results['metadata']['language'] or 'Auto-detected'}
- Analysis Time: {results['metadata']['analysis_time']}

Statistics:
- Files: {results['statistics']['files']}
- Functions: {results['statistics']['functions']}
- Classes: {results['statistics']['classes']}
- Imports: {results['statistics']['imports']}
- Total Issues: {results['issues']['total']}

Issues by Severity:
"""
        
        for severity in ['critical', 'error', 'warning', 'info']:
            if severity in results['issues']['by_severity']:
                issues = results['issues']['by_severity'][severity]
                text += f"\n{severity.upper()} ({len(issues)}):\n"
                
                if issues:
                    for i, issue in enumerate(issues, 1):
                        location = f"{issue['file_path'] or 'Unknown'}{':' + str(issue['line_number']) if issue['line_number'] else ''}"
                        symbol = f"{issue['symbol_type']} '{issue['symbol_name']}'" if issue['symbol_name'] else ''
                        text += f"{i}. {issue['category']}: {issue['message']} in {location} {symbol}\n"
                        if issue['suggestion']:
                            text += f"   Suggestion: {issue['suggestion']}\n"
        
        text += "\nIssues by Category:\n"
        
        for category, issues in results['issues']['by_category'].items():
            text += f"\n{category.replace('_', ' ').upper()} ({len(issues)}):\n"
            
            if issues:
                for i, issue in enumerate(issues, 1):
                    location = f"{issue['file_path'] or 'Unknown'}{':' + str(issue['line_number']) if issue['line_number'] else ''}"
                    symbol = f"{issue['symbol_type']} '{issue['symbol_name']}'" if issue['symbol_name'] else ''
                    text += f"{i}. [{issue['severity'].upper()}] {issue['message']} in {location} {symbol}\n"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(text)
            logger.info(f"Results saved to {output_file}")
        else:
            print(text)


def main():
    """Main entry point for the codebase analyzer."""
    parser = argparse.ArgumentParser(description="Comprehensive Codebase Analyzer")
    
    # Repository source
    parser.add_argument(
        "--repo-path", required=True, help="Local path to the repository to analyze"
    )
    
    # Analysis options
    parser.add_argument(
        "--language",
        help="Programming language of the codebase (auto-detected if not provided)",
    )
    
    # Output options
    parser.add_argument(
        "--output-format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format",
    )
    parser.add_argument("--output-file", help="Path to the output file")
    
    args = parser.parse_args()
    
    try:
        # Initialize the analyzer
        analyzer = CodebaseAnalyzer(
            repo_path=args.repo_path,
            language=args.language,
        )
        
        # Perform the analysis
        analyzer.analyze(
            output_format=args.output_format,
            output_file=args.output_file,
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

