#!/usr/bin/env python3
"""
Real-world error analyzer for the codegen codebase.
This script demonstrates the enhanced LSP diagnostics system by analyzing actual errors
from the codebase and providing comprehensive context extraction and correlation analysis.
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import ast
import inspect
import traceback
from collections import Counter, defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProjectError:
    """Represents an error found in the project."""
    error_type: str
    file_path: str
    line_number: int
    column: int
    message: str
    severity: str
    source: str  # 'lsp', 'runtime', 'syntax', 'import', etc.
    context: Dict[str, Any]

class RealCodebaseAnalyzer:
    """Analyzes the real codegen codebase for errors and provides enhanced diagnostics."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.errors: List[ProjectError] = []
        self.file_cache: Dict[str, str] = {}
        
        logger.info(f"Initializing analyzer for project: {self.project_root}")
        
    def get_file_content(self, file_path: str) -> str:
        """Get file content with caching."""
        if file_path not in self.file_cache:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.file_cache[file_path] = f.read()
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {e}")
                self.file_cache[file_path] = ""
        return self.file_cache[file_path]
    
    def find_python_files(self) -> List[str]:
        """Find all Python files in the project."""
        python_files = []
        
        # Common directories to check
        check_dirs = ['src', 'tests', 'examples', 'scripts']
        
        for check_dir in check_dirs:
            dir_path = self.project_root / check_dir
            if dir_path.exists():
                for py_file in dir_path.rglob('*.py'):
                    if not any(part.startswith('.') for part in py_file.parts):
                        python_files.append(str(py_file))
        
        # Also check root level Python files
        for py_file in self.project_root.glob('*.py'):
            python_files.append(str(py_file))
            
        logger.info(f"Found {len(python_files)} Python files")
        return python_files
    
    def analyze_syntax_errors(self) -> List[ProjectError]:
        """Analyze Python files for syntax errors."""
        syntax_errors = []
        python_files = self.find_python_files()
        
        logger.info("🔍 Analyzing syntax errors...")
        
        for file_path in python_files:
            try:
                content = self.get_file_content(file_path)
                if not content.strip():
                    continue
                    
                # Try to parse the AST
                try:
                    ast.parse(content, filename=file_path)
                except SyntaxError as e:
                    relative_path = os.path.relpath(file_path, self.project_root)
                    error = ProjectError(
                        error_type="SyntaxError",
                        file_path=relative_path,
                        line_number=e.lineno or 0,
                        column=e.offset or 0,
                        message=str(e.msg),
                        severity="error",
                        source="syntax",
                        context={
                            "text": e.text or "",
                            "filename": e.filename or file_path
                        }
                    )
                    syntax_errors.append(error)
                    logger.warning(f"Syntax error in {relative_path}:{e.lineno}: {e.msg}")
                    
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
                
        logger.info(f"Found {len(syntax_errors)} syntax errors")
        return syntax_errors
    
    def analyze_import_errors(self) -> List[ProjectError]:
        """Analyze Python files for import errors."""
        import_errors = []
        python_files = self.find_python_files()
        
        logger.info("🔍 Analyzing import errors...")
        
        for file_path in python_files:
            try:
                content = self.get_file_content(file_path)
                if not content.strip():
                    continue
                
                # Parse AST to find imports
                try:
                    tree = ast.parse(content, filename=file_path)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                try:
                                    __import__(alias.name)
                                except ImportError as e:
                                    relative_path = os.path.relpath(file_path, self.project_root)
                                    error = ProjectError(
                                        error_type="ImportError",
                                        file_path=relative_path,
                                        line_number=node.lineno,
                                        column=node.col_offset,
                                        message=f"Cannot import '{alias.name}': {str(e)}",
                                        severity="error",
                                        source="import",
                                        context={
                                            "import_name": alias.name,
                                            "import_type": "direct"
                                        }
                                    )
                                    import_errors.append(error)
                                    
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                try:
                                    __import__(node.module)
                                except ImportError as e:
                                    relative_path = os.path.relpath(file_path, self.project_root)
                                    error = ProjectError(
                                        error_type="ImportError",
                                        file_path=relative_path,
                                        line_number=node.lineno,
                                        column=node.col_offset,
                                        message=f"Cannot import from '{node.module}': {str(e)}",
                                        severity="error",
                                        source="import",
                                        context={
                                            "import_name": node.module,
                                            "import_type": "from",
                                            "imported_names": [alias.name for alias in node.names]
                                        }
                                    )
                                    import_errors.append(error)
                                    
                except SyntaxError:
                    # Skip files with syntax errors (already handled)
                    continue
                    
            except Exception as e:
                logger.warning(f"Error analyzing imports in {file_path}: {e}")
                
        logger.info(f"Found {len(import_errors)} import errors")
        return import_errors
    
    def analyze_runtime_patterns(self) -> List[ProjectError]:
        """Analyze code patterns that commonly lead to runtime errors."""
        pattern_errors = []
        python_files = self.find_python_files()
        
        logger.info("🔍 Analyzing runtime error patterns...")
        
        for file_path in python_files:
            try:
                content = self.get_file_content(file_path)
                if not content.strip():
                    continue
                
                lines = content.split('\n')
                relative_path = os.path.relpath(file_path, self.project_root)
                
                for line_num, line in enumerate(lines, 1):
                    line_stripped = line.strip()
                    
                    # Check for common runtime error patterns
                    patterns = [
                        # Dictionary access without checking
                        (r'.*\[.*\].*(?!.*\.get\()', "Potential KeyError: Dictionary access without .get()"),
                        # List access without bounds checking
                        (r'.*\[\d+\].*', "Potential IndexError: List access without bounds checking"),
                        # Division without zero check
                        (r'.*/.*(?!.*if.*!=.*0)', "Potential ZeroDivisionError: Division without zero check"),
                        # File operations without exception handling
                        (r'.*open\(.*\).*(?!.*try)', "Potential FileNotFoundError: File operation without try/except"),
                        # None access
                        (r'.*\..*(?=.*None)', "Potential AttributeError: Method call on None"),
                    ]
                    
                    for pattern, message in patterns:
                        import re
                        if re.search(pattern, line_stripped) and not line_stripped.startswith('#'):
                            error = ProjectError(
                                error_type="RuntimePattern",
                                file_path=relative_path,
                                line_number=line_num,
                                column=0,
                                message=message,
                                severity="warning",
                                source="pattern",
                                context={
                                    "line_content": line_stripped,
                                    "pattern_type": message.split(':')[0]
                                }
                            )
                            pattern_errors.append(error)
                            
            except Exception as e:
                logger.warning(f"Error analyzing patterns in {file_path}: {e}")
                
        logger.info(f"Found {len(pattern_errors)} runtime pattern issues")
        return pattern_errors
    
    def analyze_code_quality_issues(self) -> List[ProjectError]:
        """Analyze code quality issues that could lead to errors."""
        quality_errors = []
        python_files = self.find_python_files()
        
        logger.info("🔍 Analyzing code quality issues...")
        
        for file_path in python_files:
            try:
                content = self.get_file_content(file_path)
                if not content.strip():
                    continue
                
                relative_path = os.path.relpath(file_path, self.project_root)
                lines = content.split('\n')
                
                # Analyze AST for quality issues
                try:
                    tree = ast.parse(content, filename=file_path)
                    
                    for node in ast.walk(tree):
                        # Check for functions with too many parameters
                        if isinstance(node, ast.FunctionDef):
                            if len(node.args.args) > 7:  # Arbitrary threshold
                                error = ProjectError(
                                    error_type="CodeQuality",
                                    file_path=relative_path,
                                    line_number=node.lineno,
                                    column=node.col_offset,
                                    message=f"Function '{node.name}' has {len(node.args.args)} parameters (consider refactoring)",
                                    severity="info",
                                    source="quality",
                                    context={
                                        "function_name": node.name,
                                        "parameter_count": len(node.args.args),
                                        "issue_type": "too_many_parameters"
                                    }
                                )
                                quality_errors.append(error)
                        
                        # Check for deeply nested code
                        if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                            depth = self._calculate_nesting_depth(node)
                            if depth > 4:  # Arbitrary threshold
                                error = ProjectError(
                                    error_type="CodeQuality",
                                    file_path=relative_path,
                                    line_number=node.lineno,
                                    column=node.col_offset,
                                    message=f"Deeply nested code (depth: {depth}) - consider refactoring",
                                    severity="info",
                                    source="quality",
                                    context={
                                        "nesting_depth": depth,
                                        "node_type": type(node).__name__,
                                        "issue_type": "deep_nesting"
                                    }
                                )
                                quality_errors.append(error)
                                
                except SyntaxError:
                    # Skip files with syntax errors
                    continue
                    
            except Exception as e:
                logger.warning(f"Error analyzing quality in {file_path}: {e}")
                
        logger.info(f"Found {len(quality_errors)} code quality issues")
        return quality_errors
    
    def _calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate the maximum nesting depth of a node."""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
                
        return max_depth
    
    def analyze_dependency_issues(self) -> List[ProjectError]:
        """Analyze dependency and configuration issues."""
        dependency_errors = []
        
        logger.info("🔍 Analyzing dependency issues...")
        
        # Check for missing requirements files
        req_files = ['requirements.txt', 'pyproject.toml', 'setup.py', 'uv.lock']
        found_req_files = []
        
        for req_file in req_files:
            if (self.project_root / req_file).exists():
                found_req_files.append(req_file)
        
        if not found_req_files:
            error = ProjectError(
                error_type="DependencyError",
                file_path=".",
                line_number=0,
                column=0,
                message="No dependency management files found (requirements.txt, pyproject.toml, etc.)",
                severity="warning",
                source="dependency",
                context={
                    "missing_files": req_files,
                    "issue_type": "missing_dependency_files"
                }
            )
            dependency_errors.append(error)
        
        # Check pyproject.toml for issues
        pyproject_path = self.project_root / 'pyproject.toml'
        if pyproject_path.exists():
            try:
                import tomllib
                with open(pyproject_path, 'rb') as f:
                    pyproject_data = tomllib.load(f)
                
                # Check for missing project metadata
                if 'project' not in pyproject_data:
                    error = ProjectError(
                        error_type="DependencyError",
                        file_path="pyproject.toml",
                        line_number=1,
                        column=0,
                        message="Missing [project] section in pyproject.toml",
                        severity="warning",
                        source="dependency",
                        context={
                            "issue_type": "missing_project_section"
                        }
                    )
                    dependency_errors.append(error)
                    
            except Exception as e:
                error = ProjectError(
                    error_type="DependencyError",
                    file_path="pyproject.toml",
                    line_number=1,
                    column=0,
                    message=f"Error parsing pyproject.toml: {str(e)}",
                    severity="error",
                    source="dependency",
                    context={
                        "parse_error": str(e),
                        "issue_type": "parse_error"
                    }
                )
                dependency_errors.append(error)
        
        logger.info(f"Found {len(dependency_errors)} dependency issues")
        return dependency_errors
    
    def extract_caller_context(self, error: ProjectError) -> Dict[str, Any]:
        """Extract caller context for an error (simulated)."""
        try:
            # Get the current stack for demonstration
            stack = inspect.stack()
            caller_frame = stack[1] if len(stack) > 1 else stack[0]
            
            return {
                "caller_frame": {
                    "function": caller_frame.function,
                    "filename": caller_frame.filename,
                    "lineno": caller_frame.lineno
                },
                "code_context": {
                    "lines": caller_frame.code_context or [],
                    "line_number": caller_frame.lineno
                },
                "stack_trace": [str(frame) for frame in stack[:3]]
            }
        except Exception as e:
            return {"error": f"Could not extract caller context: {e}"}
    
    def extract_module_context(self, file_path: str) -> Dict[str, Any]:
        """Extract module context for a file."""
        try:
            content = self.get_file_content(file_path)
            if not content.strip():
                return {"error": "Empty file"}
            
            # Parse AST to extract module information
            tree = ast.parse(content)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "args": [arg.arg for arg in node.args.args]
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "bases": [ast.unparse(base) for base in node.bases]
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            "type": "import",
                            "name": alias.name,
                            "asname": alias.asname,
                            "lineno": node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    imports.append({
                        "type": "from_import",
                        "module": node.module,
                        "names": [alias.name for alias in node.names],
                        "lineno": node.lineno
                    })
            
            return {
                "file_path": file_path,
                "definitions": {
                    "functions": functions,
                    "classes": classes
                },
                "imports": imports,
                "total_lines": len(content.split('\n'))
            }
            
        except Exception as e:
            return {"error": f"Could not extract module context: {e}"}
    
    def analyze_error_correlation(self, errors: List[ProjectError]) -> Dict[str, Any]:
        """Analyze correlations between different errors."""
        correlation_data = {
            "error_patterns": {},
            "cross_module_errors": [],
            "frequency_analysis": {},
            "severity_correlation": {},
            "file_error_distribution": {}
        }
        
        try:
            # Error pattern analysis
            error_signatures = {}
            for error in errors:
                signature = f"{error.error_type}:{error.message[:50]}"
                if signature not in error_signatures:
                    error_signatures[signature] = []
                error_signatures[signature].append(error)
            
            correlation_data["error_patterns"] = {
                sig: {
                    "count": len(errs),
                    "files": list(set(e.file_path for e in errs)),
                    "severity_distribution": Counter(e.severity for e in errs)
                }
                for sig, errs in error_signatures.items()
            }
            
            # Cross-module error analysis
            file_errors = defaultdict(list)
            for error in errors:
                file_errors[error.file_path].append(error)
            
            for file_path, file_error_list in file_errors.items():
                if len(file_error_list) > 1:
                    correlation_data["cross_module_errors"].append({
                        "file": file_path,
                        "error_count": len(file_error_list),
                        "error_types": list(set(e.error_type for e in file_error_list))
                    })
            
            # Frequency analysis
            correlation_data["frequency_analysis"] = {
                "by_type": dict(Counter(e.error_type for e in errors)),
                "by_severity": dict(Counter(e.severity for e in errors)),
                "by_source": dict(Counter(e.source for e in errors))
            }
            
            # File error distribution
            correlation_data["file_error_distribution"] = {
                file: len(errs) for file, errs in file_errors.items()
            }
            
        except Exception as e:
            correlation_data["analysis_error"] = str(e)
            
        return correlation_data
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive error analysis on the codebase."""
        logger.info("🚀 Starting comprehensive codebase analysis...")
        
        all_errors = []
        
        # Run different types of analysis
        all_errors.extend(self.analyze_syntax_errors())
        all_errors.extend(self.analyze_import_errors())
        all_errors.extend(self.analyze_runtime_patterns())
        all_errors.extend(self.analyze_code_quality_issues())
        all_errors.extend(self.analyze_dependency_issues())
        
        self.errors = all_errors
        
        # Generate enhanced diagnostics for each error
        enhanced_diagnostics = []
        
        logger.info("🔍 Generating enhanced diagnostics...")
        
        for error in all_errors[:10]:  # Limit to first 10 for demonstration
            try:
                # Extract contexts
                caller_context = self.extract_caller_context(error)
                module_context = self.extract_module_context(
                    str(self.project_root / error.file_path) if error.file_path != "." else str(self.project_root)
                )
                
                # Create enhanced diagnostic
                enhanced_diagnostic = {
                    "diagnostic": {
                        "code": error.error_type,
                        "message": error.message,
                        "severity": error.severity,
                        "source": error.source
                    },
                    "file_path": error.file_path,
                    "line_number": error.line_number,
                    "column": error.column,
                    "caller_context": caller_context,
                    "module_context": module_context,
                    "error_context": error.context,
                    "file_content_snippet": self._get_code_snippet(error),
                }
                
                enhanced_diagnostics.append(enhanced_diagnostic)
                
            except Exception as e:
                logger.warning(f"Error creating enhanced diagnostic: {e}")
        
        # Analyze error correlations
        correlation_analysis = self.analyze_error_correlation(all_errors)
        
        # Generate summary report
        summary = {
            "total_errors": len(all_errors),
            "error_breakdown": {
                "syntax_errors": len([e for e in all_errors if e.source == "syntax"]),
                "import_errors": len([e for e in all_errors if e.source == "import"]),
                "runtime_patterns": len([e for e in all_errors if e.source == "pattern"]),
                "quality_issues": len([e for e in all_errors if e.source == "quality"]),
                "dependency_issues": len([e for e in all_errors if e.source == "dependency"])
            },
            "severity_distribution": dict(Counter(e.severity for e in all_errors)),
            "most_problematic_files": sorted(
                correlation_analysis["file_error_distribution"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        
        return {
            "summary": summary,
            "enhanced_diagnostics": enhanced_diagnostics,
            "correlation_analysis": correlation_analysis,
            "all_errors": [self._error_to_dict(e) for e in all_errors]
        }
    
    def _get_code_snippet(self, error: ProjectError, context_lines: int = 3) -> str:
        """Get code snippet around the error location."""
        try:
            if error.file_path == ".":
                return ""
                
            file_path = self.project_root / error.file_path
            if not file_path.exists():
                return ""
                
            content = self.get_file_content(str(file_path))
            lines = content.split('\n')
            
            start_line = max(0, error.line_number - context_lines - 1)
            end_line = min(len(lines), error.line_number + context_lines)
            
            snippet_lines = []
            for i in range(start_line, end_line):
                line_num = i + 1
                marker = ">>> " if line_num == error.line_number else "    "
                snippet_lines.append(f"{marker}{line_num:4d}: {lines[i]}")
            
            return '\n'.join(snippet_lines)
            
        except Exception as e:
            return f"Error getting snippet: {e}"
    
    def _error_to_dict(self, error: ProjectError) -> Dict[str, Any]:
        """Convert ProjectError to dictionary."""
        return {
            "error_type": error.error_type,
            "file_path": error.file_path,
            "line_number": error.line_number,
            "column": error.column,
            "message": error.message,
            "severity": error.severity,
            "source": error.source,
            "context": error.context
        }

def main():
    """Main function to run the real codebase analysis."""
    print("🔬 Real Codebase Error Analysis - Enhanced LSP Diagnostics Demo")
    print("=" * 70)
    
    # Initialize analyzer
    analyzer = RealCodebaseAnalyzer()
    
    # Run comprehensive analysis
    results = analyzer.run_comprehensive_analysis()
    
    # Display results
    print("\n📊 ANALYSIS SUMMARY")
    print("-" * 30)
    summary = results["summary"]
    print(f"Total Errors Found: {summary['total_errors']}")
    print(f"Error Breakdown:")
    for error_type, count in summary["error_breakdown"].items():
        print(f"  - {error_type}: {count}")
    
    print(f"\nSeverity Distribution:")
    for severity, count in summary["severity_distribution"].items():
        print(f"  - {severity}: {count}")
    
    print(f"\nMost Problematic Files:")
    for file_path, error_count in summary["most_problematic_files"][:5]:
        print(f"  - {file_path}: {error_count} errors")
    
    # Display enhanced diagnostics
    print("\n🔍 ENHANCED DIAGNOSTICS (Sample)")
    print("-" * 40)
    
    for i, diagnostic in enumerate(results["enhanced_diagnostics"][:3], 1):
        print(f"\n{i}. {diagnostic['diagnostic']['code']} in {diagnostic['file_path']}")
        print(f"   Line {diagnostic['line_number']}: {diagnostic['diagnostic']['message']}")
        print(f"   Severity: {diagnostic['diagnostic']['severity']}")
        
        if diagnostic.get('file_content_snippet'):
            print("   Code Context:")
            for line in diagnostic['file_content_snippet'].split('\n')[:5]:
                print(f"   {line}")
    
    # Display correlation analysis
    print("\n🔗 ERROR CORRELATION ANALYSIS")
    print("-" * 35)
    
    correlation = results["correlation_analysis"]
    print(f"Error Pattern Analysis:")
    for pattern, data in list(correlation["error_patterns"].items())[:3]:
        print(f"  - {pattern[:50]}...")
        print(f"    Count: {data['count']}, Files: {len(data['files'])}")
    
    print(f"\nFrequency Analysis:")
    freq = correlation["frequency_analysis"]
    print(f"  By Type: {dict(list(freq['by_type'].items())[:5])}")
    print(f"  By Severity: {freq['by_severity']}")
    
    # Save detailed results
    output_file = "codebase_analysis_results.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Could not save results: {e}")
    
    print("\n✅ Analysis Complete!")
    print("This demonstrates the enhanced LSP diagnostics system with:")
    print("  - Real error detection from actual codebase")
    print("  - Context extraction (caller & module)")
    print("  - Error correlation analysis")
    print("  - Comprehensive diagnostic information")

if __name__ == "__main__":
    main()
