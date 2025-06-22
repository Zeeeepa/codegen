"""
Comprehensive Codebase Analysis Engine

This module provides ALL analysis context for codebases including:
- ALL most important functions with full definitions
- ALL entry points detection across different patterns
- Issue detection and context analysis
- Symbol relationship analysis
- Dependency graph analysis

Compliant with graph-sitter standards using tree-sitter foundation.
"""

import ast
import re
import os
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict, Counter
import json

from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.file import SourceFile
from codegen.sdk.enums import SymbolType
from codegen.sdk.tree_sitter_parser import parse_file, get_lang_by_filepath_or_extension


@dataclass
class EntryPoint:
    """Represents a detected entry point in the codebase"""
    name: str
    type: str  # 'main', 'cli', 'web_endpoint', 'export', 'constructor', 'framework'
    filepath: str
    line_number: int
    source_code: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportantFunction:
    """Represents an important function with comprehensive details"""
    name: str
    full_name: str
    filepath: str
    line_number: int
    source_code: str
    importance_score: float
    usage_count: int
    dependency_count: int
    is_public_api: bool
    is_entry_point: bool
    call_graph_centrality: float
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeIssue:
    """Represents a detected code issue"""
    type: str  # 'unused_code', 'circular_dependency', 'missing_docs', 'architectural_violation'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    filepath: str
    line_number: Optional[int]
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SymbolContext:
    """Comprehensive context for a symbol"""
    symbol: Symbol
    usages: List[Dict[str, Any]]
    dependencies: List[Dict[str, Any]]
    definition_context: Dict[str, Any]
    related_symbols: List[Dict[str, Any]]


class ComprehensiveAnalyzer:
    """
    Comprehensive codebase analyzer that provides ALL analysis context.
    
    This analyzer extends the existing Codebase functionality to provide:
    - Complete function importance analysis
    - Comprehensive entry point detection
    - Issue detection and analysis
    - Symbol relationship mapping
    """
    
    def __init__(self, codebase_path: str, language: str = "python"):
        """Initialize the analyzer with a codebase"""
        self.codebase_path = Path(codebase_path)
        self.language = language
        self.codebase = Codebase(str(codebase_path), language=language)
        
        # Analysis caches
        self._entry_points_cache: Optional[List[EntryPoint]] = None
        self._important_functions_cache: Optional[List[ImportantFunction]] = None
        self._issues_cache: Optional[List[CodeIssue]] = None
        self._call_graph_cache: Optional[Dict[str, Set[str]]] = None
        
    def get_all_entry_points(self) -> List[EntryPoint]:
        """
        Detect ALL entry points in the codebase.
        
        Entry points include:
        - Main functions (__main__, if __name__ == "__main__")
        - CLI entry points (argparse, click, typer)
        - Web endpoints (FastAPI, Flask routes)
        - Exported functions (public API)
        - Class constructors
        - Framework-specific entry points
        """
        if self._entry_points_cache is not None:
            return self._entry_points_cache
            
        entry_points = []
        
        for file in self.codebase.files:
            file_entry_points = self._detect_file_entry_points(file)
            entry_points.extend(file_entry_points)
            
        self._entry_points_cache = entry_points
        return entry_points
    
    def _detect_file_entry_points(self, file: SourceFile) -> List[EntryPoint]:
        """Detect entry points in a specific file"""
        entry_points = []
        
        try:
            # Parse the file content
            if not os.path.exists(file.filepath):
                return entry_points
                
            with open(file.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use tree-sitter for parsing
            ts_node = parse_file(file.filepath, content)
            
            # Detect different types of entry points
            entry_points.extend(self._detect_main_functions(file, content, ts_node))
            entry_points.extend(self._detect_cli_entry_points(file, content, ts_node))
            entry_points.extend(self._detect_web_endpoints(file, content, ts_node))
            entry_points.extend(self._detect_exported_functions(file, content, ts_node))
            entry_points.extend(self._detect_framework_entry_points(file, content, ts_node))
            
        except Exception as e:
            print(f"Error analyzing file {file.filepath}: {e}")
            
        return entry_points
    
    def _detect_main_functions(self, file: SourceFile, content: str, ts_node) -> List[EntryPoint]:
        """Detect main function entry points"""
        entry_points = []
        lines = content.split('\n')
        
        # Look for if __name__ == "__main__" pattern
        for i, line in enumerate(lines):
            if re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', line):
                entry_points.append(EntryPoint(
                    name="__main__",
                    type="main",
                    filepath=file.filepath,
                    line_number=i + 1,
                    source_code=line.strip(),
                    context={"pattern": "if __name__ == '__main__'"}
                ))
        
        # Look for main() function definitions
        for func in file.functions:
            if func.name == "main":
                entry_points.append(EntryPoint(
                    name="main",
                    type="main",
                    filepath=file.filepath,
                    line_number=getattr(func, 'line_number', 0),
                    source_code=getattr(func, 'source', ''),
                    context={"function_type": "main_function"}
                ))
        
        return entry_points
    
    def _detect_cli_entry_points(self, file: SourceFile, content: str, ts_node) -> List[EntryPoint]:
        """Detect CLI entry points (argparse, click, typer)"""
        entry_points = []
        
        # Look for argparse patterns
        if 'argparse' in content:
            for func in file.functions:
                if any('argparse' in str(dep) for dep in func.dependencies):
                    entry_points.append(EntryPoint(
                        name=func.name,
                        type="cli",
                        filepath=file.filepath,
                        line_number=getattr(func, 'line_number', 0),
                        source_code=getattr(func, 'source', ''),
                        context={"cli_framework": "argparse"}
                    ))
        
        # Look for click decorators
        if '@click.' in content or 'import click' in content:
            for func in file.functions:
                if any('@click' in str(dec) for dec in getattr(func, 'decorators', [])):
                    entry_points.append(EntryPoint(
                        name=func.name,
                        type="cli",
                        filepath=file.filepath,
                        line_number=getattr(func, 'line_number', 0),
                        source_code=getattr(func, 'source', ''),
                        context={"cli_framework": "click"}
                    ))
        
        # Look for typer patterns
        if 'typer' in content:
            for func in file.functions:
                if any('typer' in str(dep) for dep in func.dependencies):
                    entry_points.append(EntryPoint(
                        name=func.name,
                        type="cli",
                        filepath=file.filepath,
                        line_number=getattr(func, 'line_number', 0),
                        source_code=getattr(func, 'source', ''),
                        context={"cli_framework": "typer"}
                    ))
        
        return entry_points
    
    def _detect_web_endpoints(self, file: SourceFile, content: str, ts_node) -> List[EntryPoint]:
        """Detect web endpoint entry points"""
        entry_points = []
        
        # FastAPI endpoints
        fastapi_patterns = [r'@app\.(get|post|put|delete|patch)', r'@router\.(get|post|put|delete|patch)']
        for pattern in fastapi_patterns:
            for func in file.functions:
                if any(re.search(pattern, str(dec)) for dec in getattr(func, 'decorators', [])):
                    entry_points.append(EntryPoint(
                        name=func.name,
                        type="web_endpoint",
                        filepath=file.filepath,
                        line_number=getattr(func, 'line_number', 0),
                        source_code=getattr(func, 'source', ''),
                        context={"framework": "fastapi", "endpoint_type": "REST"}
                    ))
        
        # Flask endpoints
        flask_patterns = [r'@app\.route', r'@bp\.route', r'@blueprint\.route']
        for pattern in flask_patterns:
            for func in file.functions:
                if any(re.search(pattern, str(dec)) for dec in getattr(func, 'decorators', [])):
                    entry_points.append(EntryPoint(
                        name=func.name,
                        type="web_endpoint",
                        filepath=file.filepath,
                        line_number=getattr(func, 'line_number', 0),
                        source_code=getattr(func, 'source', ''),
                        context={"framework": "flask", "endpoint_type": "route"}
                    ))
        
        return entry_points
    
    def _detect_exported_functions(self, file: SourceFile, content: str, ts_node) -> List[EntryPoint]:
        """Detect exported functions (public API)"""
        entry_points = []
        
        # Look for __all__ exports
        if '__all__' in content:
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == '__all__':
                                if isinstance(node.value, ast.List):
                                    for elt in node.value.elts:
                                        if isinstance(elt, ast.Str):
                                            func_name = elt.s
                                        elif isinstance(elt, ast.Constant):
                                            func_name = elt.value
                                        else:
                                            continue
                                        
                                        # Find the corresponding function
                                        for func in file.functions:
                                            if func.name == func_name:
                                                entry_points.append(EntryPoint(
                                                    name=func.name,
                                                    type="export",
                                                    filepath=file.filepath,
                                                    line_number=getattr(func, 'line_number', 0),
                                                    source_code=getattr(func, 'source', ''),
                                                    context={"export_type": "__all__"}
                                                ))
            except:
                pass
        
        # Public functions (not starting with _)
        for func in file.functions:
            if not func.name.startswith('_') and not func.is_method:
                entry_points.append(EntryPoint(
                    name=func.name,
                    type="export",
                    filepath=file.filepath,
                    line_number=getattr(func, 'line_number', 0),
                    source_code=getattr(func, 'source', ''),
                    context={"export_type": "public_function"}
                ))
        
        return entry_points
    
    def _detect_framework_entry_points(self, file: SourceFile, content: str, ts_node) -> List[EntryPoint]:
        """Detect framework-specific entry points"""
        entry_points = []
        
        # Django views
        if 'django' in content.lower():
            for func in file.functions:
                if any('request' in str(param) for param in getattr(func, 'parameters', [])):
                    entry_points.append(EntryPoint(
                        name=func.name,
                        type="framework",
                        filepath=file.filepath,
                        line_number=getattr(func, 'line_number', 0),
                        source_code=getattr(func, 'source', ''),
                        context={"framework": "django", "type": "view"}
                    ))
        
        # Celery tasks
        if '@task' in content or '@shared_task' in content:
            for func in file.functions:
                if any('@task' in str(dec) or '@shared_task' in str(dec) for dec in getattr(func, 'decorators', [])):
                    entry_points.append(EntryPoint(
                        name=func.name,
                        type="framework",
                        filepath=file.filepath,
                        line_number=getattr(func, 'line_number', 0),
                        source_code=getattr(func, 'source', ''),
                        context={"framework": "celery", "type": "task"}
                    ))
        
        return entry_points
    
    def get_all_important_functions(self) -> List[ImportantFunction]:
        """
        Get ALL most important functions in the codebase with their full definitions.
        
        Importance is calculated using multiple factors:
        - Usage frequency across codebase
        - Dependency centrality (how many functions depend on it)
        - Call graph centrality
        - Public API status
        - Entry point status
        - Cyclomatic complexity (used internally, not exposed)
        """
        if self._important_functions_cache is not None:
            return self._important_functions_cache
        
        important_functions = []
        call_graph = self._build_call_graph()
        
        for file in self.codebase.files:
            for func in file.functions:
                importance_score = self._calculate_function_importance(func, call_graph)
                
                if importance_score > 0.1:  # Threshold for importance
                    important_functions.append(ImportantFunction(
                        name=func.name,
                        full_name=f"{file.name}.{func.name}",
                        filepath=file.filepath,
                        line_number=getattr(func, 'line_number', 0),
                        source_code=getattr(func, 'source', ''),
                        importance_score=importance_score,
                        usage_count=len(func.call_sites),
                        dependency_count=len(func.dependencies),
                        is_public_api=not func.name.startswith('_'),
                        is_entry_point=self._is_entry_point(func),
                        call_graph_centrality=self._calculate_centrality(func.name, call_graph),
                        context={
                            "parameters": [str(p) for p in getattr(func, 'parameters', [])],
                            "return_type": getattr(func, 'return_type', None),
                            "decorators": [str(d) for d in getattr(func, 'decorators', [])],
                            "docstring": getattr(func, 'docstring', None)
                        }
                    ))
        
        # Sort by importance score
        important_functions.sort(key=lambda x: x.importance_score, reverse=True)
        
        self._important_functions_cache = important_functions
        return important_functions
    
    def _build_call_graph(self) -> Dict[str, Set[str]]:
        """Build a call graph for centrality calculations"""
        if self._call_graph_cache is not None:
            return self._call_graph_cache
        
        call_graph = defaultdict(set)
        
        for file in self.codebase.files:
            for func in file.functions:
                func_name = f"{file.name}.{func.name}"
                for call in func.function_calls:
                    if hasattr(call, 'function_definition') and call.function_definition:
                        called_func = call.function_definition
                        if hasattr(called_func, 'name'):
                            call_graph[func_name].add(called_func.name)
        
        self._call_graph_cache = dict(call_graph)
        return self._call_graph_cache
    
    def _calculate_function_importance(self, func: Function, call_graph: Dict[str, Set[str]]) -> float:
        """Calculate importance score for a function"""
        score = 0.0
        
        # Usage frequency (normalized)
        usage_count = len(func.call_sites)
        score += min(usage_count / 10.0, 1.0) * 0.3
        
        # Dependency count (how many things depend on this)
        dependency_count = len(func.dependencies)
        score += min(dependency_count / 20.0, 1.0) * 0.2
        
        # Public API bonus
        if not func.name.startswith('_'):
            score += 0.2
        
        # Entry point bonus
        if self._is_entry_point(func):
            score += 0.3
        
        # Call graph centrality
        centrality = self._calculate_centrality(func.name, call_graph)
        score += centrality * 0.2
        
        # Complexity factor (used internally only)
        complexity = self._estimate_complexity(func)
        if complexity > 5:  # High complexity functions are often important
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_centrality(self, func_name: str, call_graph: Dict[str, Set[str]]) -> float:
        """Calculate centrality in call graph"""
        # Simple degree centrality
        in_degree = sum(1 for calls in call_graph.values() if func_name in calls)
        out_degree = len(call_graph.get(func_name, set()))
        
        total_functions = len(call_graph)
        if total_functions <= 1:
            return 0.0
        
        return (in_degree + out_degree) / (2 * (total_functions - 1))
    
    def _estimate_complexity(self, func: Function) -> int:
        """Estimate cyclomatic complexity (used internally only)"""
        # Simple heuristic based on source code
        source = getattr(func, 'source', '')
        if not source:
            return 1
        
        # Count decision points
        complexity = 1  # Base complexity
        complexity += source.count('if ')
        complexity += source.count('elif ')
        complexity += source.count('for ')
        complexity += source.count('while ')
        complexity += source.count('except ')
        complexity += source.count('and ')
        complexity += source.count('or ')
        
        return complexity
    
    def _is_entry_point(self, func: Function) -> bool:
        """Check if function is an entry point"""
        entry_points = self.get_all_entry_points()
        return any(ep.name == func.name for ep in entry_points)
    
    def detect_issues(self) -> List[CodeIssue]:
        """Detect various code issues"""
        if self._issues_cache is not None:
            return self._issues_cache
        
        issues = []
        
        # Detect unused functions
        issues.extend(self._detect_unused_code())
        
        # Detect circular dependencies
        issues.extend(self._detect_circular_dependencies())
        
        # Detect missing documentation
        issues.extend(self._detect_missing_documentation())
        
        # Detect architectural violations
        issues.extend(self._detect_architectural_violations())
        
        self._issues_cache = issues
        return issues
    
    def _detect_unused_code(self) -> List[CodeIssue]:
        """Detect unused functions and classes"""
        issues = []
        
        for file in self.codebase.files:
            for func in file.functions:
                if len(func.call_sites) == 0 and not self._is_entry_point(func):
                    issues.append(CodeIssue(
                        type="unused_code",
                        severity="medium",
                        message=f"Function '{func.name}' appears to be unused",
                        filepath=file.filepath,
                        line_number=getattr(func, 'line_number', None),
                        context={"function_name": func.name, "type": "function"}
                    ))
        
        return issues
    
    def _detect_circular_dependencies(self) -> List[CodeIssue]:
        """Detect circular dependencies"""
        issues = []
        call_graph = self._build_call_graph()
        
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node, path):
            if node in rec_stack:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                return cycle
            
            if node in visited:
                return None
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in call_graph.get(node, set()):
                cycle = has_cycle(neighbor, path + [node])
                if cycle:
                    return cycle
            
            rec_stack.remove(node)
            return None
        
        for node in call_graph:
            if node not in visited:
                cycle = has_cycle(node, [])
                if cycle:
                    issues.append(CodeIssue(
                        type="circular_dependency",
                        severity="high",
                        message=f"Circular dependency detected: {' -> '.join(cycle)}",
                        filepath="",
                        line_number=None,
                        context={"cycle": cycle}
                    ))
        
        return issues
    
    def _detect_missing_documentation(self) -> List[CodeIssue]:
        """Detect functions missing documentation"""
        issues = []
        
        for file in self.codebase.files:
            for func in file.functions:
                if not func.name.startswith('_'):  # Only check public functions
                    docstring = getattr(func, 'docstring', None)
                    if not docstring or len(docstring.strip()) < 10:
                        issues.append(CodeIssue(
                            type="missing_docs",
                            severity="low",
                            message=f"Public function '{func.name}' lacks proper documentation",
                            filepath=file.filepath,
                            line_number=getattr(func, 'line_number', None),
                            context={"function_name": func.name}
                        ))
        
        return issues
    
    def _detect_architectural_violations(self) -> List[CodeIssue]:
        """Detect architectural violations"""
        issues = []
        
        # Example: Functions that are too complex
        for file in self.codebase.files:
            for func in file.functions:
                complexity = self._estimate_complexity(func)
                if complexity > 15:  # High complexity threshold
                    issues.append(CodeIssue(
                        type="architectural_violation",
                        severity="medium",
                        message=f"Function '{func.name}' has high complexity and should be refactored",
                        filepath=file.filepath,
                        line_number=getattr(func, 'line_number', None),
                        context={"function_name": func.name, "complexity": complexity}
                    ))
        
        return issues
    
    def get_symbol_context(self, symbol_name: str) -> Optional[SymbolContext]:
        """Get comprehensive context for a symbol"""
        symbol = None
        
        # Find the symbol
        for s in self.codebase.symbols:
            if s.name == symbol_name:
                symbol = s
                break
        
        if not symbol:
            return None
        
        # Build context
        usages = []
        for usage in symbol.symbol_usages:
            usages.append({
                "name": getattr(usage, 'name', str(usage)),
                "type": type(usage).__name__,
                "filepath": getattr(usage, 'filepath', ''),
                "line_number": getattr(usage, 'line_number', 0)
            })
        
        dependencies = []
        for dep in symbol.dependencies:
            dependencies.append({
                "name": getattr(dep, 'name', str(dep)),
                "type": type(dep).__name__,
                "filepath": getattr(dep, 'filepath', '')
            })
        
        return SymbolContext(
            symbol=symbol,
            usages=usages,
            dependencies=dependencies,
            definition_context={
                "filepath": getattr(symbol, 'filepath', ''),
                "line_number": getattr(symbol, 'line_number', 0),
                "source": getattr(symbol, 'source', ''),
                "symbol_type": symbol.symbol_type.value if hasattr(symbol, 'symbol_type') else 'unknown'
            },
            related_symbols=[]  # Could be expanded
        )
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get a comprehensive analysis summary"""
        entry_points = self.get_all_entry_points()
        important_functions = self.get_all_important_functions()
        issues = self.detect_issues()
        
        return {
            "codebase_path": str(self.codebase_path),
            "language": self.language,
            "total_files": len(list(self.codebase.files)),
            "total_functions": len(list(self.codebase.functions)),
            "total_classes": len(list(self.codebase.classes)),
            "total_symbols": len(list(self.codebase.symbols)),
            "entry_points": {
                "total": len(entry_points),
                "by_type": Counter(ep.type for ep in entry_points)
            },
            "important_functions": {
                "total": len(important_functions),
                "top_10": [
                    {
                        "name": func.name,
                        "importance_score": func.importance_score,
                        "filepath": func.filepath
                    }
                    for func in important_functions[:10]
                ]
            },
            "issues": {
                "total": len(issues),
                "by_type": Counter(issue.type for issue in issues),
                "by_severity": Counter(issue.severity for issue in issues)
            }
        }


def create_analyzer(codebase_path: str, language: str = "python") -> ComprehensiveAnalyzer:
    """Factory function to create a comprehensive analyzer"""
    return ComprehensiveAnalyzer(codebase_path, language)

