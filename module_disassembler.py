#!/usr/bin/env python3
"""
Module Disassembler for Codegen

This tool analyzes, restructures, and deduplicates code in the Codegen codebase,
particularly focusing on analysis modules. It extracts functions, identifies duplicates,
and reorganizes code based on functionality.
"""

import os
import sys
import ast
import argparse
import difflib
import hashlib
import re
import json
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union, Callable
from collections import defaultdict
import networkx as nx

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Import Codegen SDK
try:
    from codegen.sdk.core.codebase import Codebase
    from codegen.sdk.core.symbol import Function, Class, Symbol
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.shared.enums.programming_language import ProgrammingLanguage
except ImportError:
    logger.error("Codegen SDK not found. Please install it first.")
    sys.exit(1)

class FunctionInfo:
    """Represents information about a function extracted from the codebase."""
    
    def __init__(self, name: str, source: str, file_path: str, 
                 start_line: int, end_line: int, ast_node: ast.FunctionDef = None,
                 symbol: Function = None):
        self.name = name
        self.source = source
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.ast_node = ast_node
        self.symbol = symbol  # Store the Codegen SDK Function object
        self.hash = self._compute_hash()
        self.normalized_hash = self._compute_normalized_hash()
        self.dependencies = set()
        self.category = None
        self.is_duplicate = False
        self.duplicate_of = None
        self.similarity_scores = {}
        
    def _compute_hash(self) -> str:
        """Compute a hash of the function source code."""
        return hashlib.md5(self.source.encode('utf-8')).hexdigest()
    
    def _compute_normalized_hash(self) -> str:
        """Compute a hash of the normalized function source code (ignoring whitespace, comments, etc.)."""
        # Parse the function to AST
        tree = ast.parse(self.source)
        # Remove docstrings and comments
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                node.value.s = ""
        # Convert back to source and normalize whitespace
        normalized_source = ast.unparse(tree)
        normalized_source = re.sub(r'\s+', ' ', normalized_source)
        return hashlib.md5(normalized_source.encode('utf-8')).hexdigest()
    
    def compute_similarity(self, other: 'FunctionInfo') -> float:
        """Compute similarity between this function and another function."""
        # If we've already computed this, return the cached value
        if other.name in self.similarity_scores:
            return self.similarity_scores[other.name]
        
        # If the normalized hashes match, they're identical (after normalization)
        if self.normalized_hash == other.normalized_hash:
            similarity = 1.0
        else:
            # Use difflib to compute similarity
            seq_matcher = difflib.SequenceMatcher(None, self.source, other.source)
            similarity = seq_matcher.ratio()
        
        # Cache the result
        self.similarity_scores[other.name] = similarity
        other.similarity_scores[self.name] = similarity
        
        return similarity
    
    def __str__(self) -> str:
        return f"{self.name} ({self.file_path}:{self.start_line}-{self.end_line})"
    
    def __repr__(self) -> str:
        return self.__str__()


class ModuleDisassembler:
    """
    Analyzes, restructures, and deduplicates code in the Codegen codebase.
    
    This class provides methods to extract functions, identify duplicates,
    categorize functions by purpose, and reorganize code into a more
    maintainable structure.
    """
    
    # Function categories based on purpose
    CATEGORIES = {
        "analysis": ["analyze", "extract", "parse", "process", "get_", "find_", "detect", "identify"],
        "visualization": ["visualize", "plot", "draw", "render", "display", "show", "graph"],
        "utility": ["util", "helper", "format", "convert", "transform", "normalize"],
        "io": ["read", "write", "load", "save", "import", "export", "serialize", "deserialize"],
        "validation": ["validate", "check", "verify", "ensure", "assert", "is_", "has_"],
        "metrics": ["measure", "calculate", "compute", "count", "metric", "score", "rank"],
        "core": ["init", "main", "run", "execute", "start", "stop", "create", "build"]
    }
    
    def __init__(self, repo_path: str, language: str = None):
        """
        Initialize the ModuleDisassembler.
        
        Args:
            repo_path: Path to the repository to analyze
            language: Programming language of the codebase (auto-detected if not provided)
        """
        self.repo_path = Path(repo_path)
        self.language = language
        self.functions: Dict[str, FunctionInfo] = {}
        self.duplicate_groups: List[List[FunctionInfo]] = []
        self.similar_groups: List[List[FunctionInfo]] = []
        self.dependency_graph = nx.DiGraph()
        self.categorized_functions: Dict[str, List[FunctionInfo]] = defaultdict(list)
        
        # Initialize Codegen SDK codebase
        self.codebase = self._init_codebase()
        
    def _init_codebase(self) -> Codebase:
        """Initialize the Codegen SDK codebase."""
        try:
            # Configure the codebase
            config = CodebaseConfig(
                debug=False,
                allow_external=True,
                py_resolve_syspath=True,
            )
            
            secrets = SecretsConfig()
            
            # Initialize the codebase
            logger.info(f"Initializing codebase from {self.repo_path}...")
            
            prog_lang = None
            if self.language:
                prog_lang = ProgrammingLanguage(self.language.upper())
            
            codebase = Codebase(
                repo_path=str(self.repo_path),
                language=prog_lang,
                config=config,
                secrets=secrets
            )
            
            logger.info(f"Successfully initialized codebase from {self.repo_path}")
            return codebase
            
        except Exception as e:
            logger.error(f"Error initializing codebase: {e}")
            raise
        
    def analyze(self, similarity_threshold: float = 0.8):
        """
        Perform a complete analysis of the codebase.
        
        Args:
            similarity_threshold: Threshold for considering functions similar (0.0-1.0)
        """
        logger.info(f"Starting analysis of repository at {self.repo_path}")
        
        # Extract all functions from the codebase using Codegen SDK
        self._extract_functions_with_sdk()
        logger.info(f"Extracted {len(self.functions)} functions from the codebase")
        
        # Identify duplicate and similar functions
        self._identify_duplicates(similarity_threshold)
        logger.info(f"Identified {len(self.duplicate_groups)} duplicate groups and {len(self.similar_groups)} similar groups")
        
        # Build dependency graph
        self._build_dependency_graph_with_sdk()
        logger.info(f"Built dependency graph with {self.dependency_graph.number_of_nodes()} nodes and {self.dependency_graph.number_of_edges()} edges")
        
        # Categorize functions by purpose
        self._categorize_functions()
        logger.info(f"Categorized functions into {len(self.categorized_functions)} categories")
        
    def _extract_functions_with_sdk(self):
        """Extract all functions from the codebase using Codegen SDK."""
        try:
            # Get all functions from the codebase
            sdk_functions = list(self.codebase.functions)
            logger.info(f"Found {len(sdk_functions)} functions using Codegen SDK")
            
            for func in sdk_functions:
                try:
                    # Get function source and location information
                    source = func.source
                    file_path = func.file.file_path if hasattr(func, "file") else "Unknown"
                    start_line = func.start_line if hasattr(func, "start_line") else 0
                    end_line = func.end_line if hasattr(func, "end_line") else 0
                    
                    # Create a FunctionInfo object
                    function_info = FunctionInfo(
                        name=func.name,
                        source=source,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        symbol=func
                    )
                    
                    # Add to the functions dictionary
                    self.functions[f"{function_info.file_path}:{function_info.name}"] = function_info
                    
                except Exception as e:
                    logger.warning(f"Error processing function {func.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error extracting functions with SDK: {e}")
            # Fall back to AST-based extraction if SDK fails
            logger.info("Falling back to AST-based function extraction")
            self._extract_functions_with_ast()
    
    def _extract_functions_with_ast(self):
        """Extract all functions from Python files using AST (fallback method)."""
        python_files = list(self.repo_path.glob("**/*.py"))
        
        for file_path in python_files:
            # Skip virtual environments, tests, and other non-core code
            if any(part in str(file_path) for part in ["venv", "env", "node_modules", "__pycache__"]):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                # Parse the file
                tree = ast.parse(source)
                
                # Extract functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Get the function source code
                        start_line = node.lineno
                        end_line = node.end_lineno
                        function_source = "\n".join(source.splitlines()[start_line-1:end_line])
                        
                        # Create a FunctionInfo object
                        function_info = FunctionInfo(
                            name=node.name,
                            source=function_source,
                            file_path=str(file_path.relative_to(self.repo_path)),
                            start_line=start_line,
                            end_line=end_line,
                            ast_node=node
                        )
                        
                        # Add to the functions dictionary
                        self.functions[f"{function_info.file_path}:{function_info.name}"] = function_info
                        
            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {e}")
    
    def _identify_duplicates(self, similarity_threshold: float):
        """
        Identify duplicate and similar functions.
        
        Args:
            similarity_threshold: Threshold for considering functions similar (0.0-1.0)
        """
        # Group functions by their normalized hash to find exact duplicates
        hash_groups = defaultdict(list)
        for func in self.functions.values():
            hash_groups[func.normalized_hash].append(func)
        
        # Extract duplicate groups (more than one function with the same hash)
        self.duplicate_groups = [group for group in hash_groups.values() if len(group) > 1]
        
        # Mark duplicate functions
        for group in self.duplicate_groups:
            primary = group[0]  # Consider the first one as the primary
            for duplicate in group[1:]:
                duplicate.is_duplicate = True
                duplicate.duplicate_of = primary
        
        # Find similar functions (not exact duplicates)
        remaining_funcs = [f for f in self.functions.values() if not f.is_duplicate]
        
        # Compute similarity matrix
        for i, func1 in enumerate(remaining_funcs):
            for func2 in remaining_funcs[i+1:]:
                similarity = func1.compute_similarity(func2)
                if similarity >= similarity_threshold and similarity < 1.0:
                    # They're similar but not identical
                    self._add_to_similar_group(func1, func2)
    
    def _add_to_similar_group(self, func1: FunctionInfo, func2: FunctionInfo):
        """Add two similar functions to a similarity group."""
        # Check if either function is already in a group
        for group in self.similar_groups:
            if func1 in group:
                if func2 not in group:
                    group.append(func2)
                return
            elif func2 in group:
                group.append(func1)
                return
        
        # If we get here, neither function is in a group yet
        self.similar_groups.append([func1, func2])
    
    def _build_dependency_graph_with_sdk(self):
        """Build a dependency graph of functions using Codegen SDK."""
        try:
            # Add all functions as nodes
            for func in self.functions.values():
                self.dependency_graph.add_node(func.name)
            
            # Use SDK to get function calls
            for func in self.functions.values():
                if func.symbol:
                    # Get all calls made by this function
                    try:
                        # Use SDK's call graph if available
                        calls = func.symbol.calls if hasattr(func.symbol, "calls") else []
                        
                        for call in calls:
                            called_name = call.name if hasattr(call, "name") else str(call)
                            # Check if this is a call to another function we know about
                            if called_name in [f.name for f in self.functions.values()]:
                                # Add an edge from caller to callee
                                self.dependency_graph.add_edge(func.name, called_name)
                                func.dependencies.add(called_name)
                    except Exception as e:
                        logger.warning(f"Error getting calls for {func.name}: {e}")
                else:
                    # Fall back to AST-based dependency analysis
                    self._analyze_function_dependencies_with_ast(func)
        except Exception as e:
            logger.error(f"Error building dependency graph with SDK: {e}")
            # Fall back to AST-based dependency analysis
            logger.info("Falling back to AST-based dependency analysis")
            self._build_dependency_graph_with_ast()
    
    def _build_dependency_graph_with_ast(self):
        """Build a dependency graph of functions using AST (fallback method)."""
        # Add all functions as nodes
        for func in self.functions.values():
            self.dependency_graph.add_node(func.name)
        
        # Analyze dependencies for each function
        for func in self.functions.values():
            self._analyze_function_dependencies_with_ast(func)
    
    def _analyze_function_dependencies_with_ast(self, func: FunctionInfo):
        """Analyze function dependencies using AST."""
        if not func.ast_node:
            try:
                # Parse the function to get its AST
                func.ast_node = ast.parse(func.source).body[0]
            except Exception as e:
                logger.warning(f"Error parsing function {func.name}: {e}")
                return
        
        try:
            # Find all function calls in the AST
            for node in ast.walk(func.ast_node):
                if isinstance(node, ast.Call) and hasattr(node.func, 'id'):
                    called_name = node.func.id
                    # Check if this is a call to another function we know about
                    for potential_target in self.functions.values():
                        if potential_target.name == called_name:
                            # Add an edge from caller to callee
                            self.dependency_graph.add_edge(func.name, called_name)
                            func.dependencies.add(called_name)
        except Exception as e:
            logger.warning(f"Error analyzing dependencies in {func.name}: {e}")
    
    def _categorize_functions(self):
        """Categorize functions by their purpose based on naming patterns."""
        for func in self.functions.values():
            # Skip duplicates
            if func.is_duplicate:
                continue
                
            # Try to categorize based on name
            categorized = False
            for category, patterns in self.CATEGORIES.items():
                if any(pattern in func.name.lower() for pattern in patterns):
                    self.categorized_functions[category].append(func)
                    func.category = category
                    categorized = True
                    break
            
            # If not categorized, put in "other"
            if not categorized:
                self.categorized_functions["other"].append(func)
                func.category = "other"
    
    def generate_restructured_modules(self, output_dir: str):
        """
        Generate restructured modules based on the analysis.
        
        Args:
            output_dir: Directory to output the restructured modules
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create a directory for each category
        for category in self.categorized_functions.keys():
            category_dir = output_path / category
            category_dir.mkdir(exist_ok=True)
            
            # Create an __init__.py file
            with open(category_dir / "__init__.py", "w") as f:
                f.write(f"# {category.capitalize()} module\n")
                
                # Add imports for all functions in this category
                for func in self.categorized_functions[category]:
                    if not func.is_duplicate:
                        f.write(f"from .{func.name} import {func.name}\n")
                
                # Export all functions
                f.write("\n__all__ = [\n")
                for func in self.categorized_functions[category]:
                    if not func.is_duplicate:
                        f.write(f"    '{func.name}',\n")
                f.write("]\n")
            
            # Create a file for each function
            for func in self.categorized_functions[category]:
                # Skip duplicates
                if func.is_duplicate:
                    continue
                    
                with open(category_dir / f"{func.name}.py", "w") as f:
                    # Add imports
                    f.write("import os\nimport sys\nfrom typing import Dict, List, Set, Tuple, Any, Optional, Union\n\n")
                    
                    # Add Codegen SDK imports if needed
                    f.write("from codegen.sdk.core.codebase import Codebase\n")
                    f.write("from codegen.sdk.core.symbol import Function, Class, Symbol\n\n")
                    
                    # Add dependencies
                    for dep in func.dependencies:
                        # Find the category of the dependency
                        dep_category = None
                        for cat, funcs in self.categorized_functions.items():
                            if any(f.name == dep for f in funcs):
                                dep_category = cat
                                break
                        
                        if dep_category:
                            f.write(f"from ..{dep_category} import {dep}\n")
                    
                    f.write("\n\n")
                    
                    # Write the function
                    f.write(func.source)
        
        # Create a main __init__.py file
        with open(output_path / "__init__.py", "w") as f:
            f.write("# Restructured analysis modules\n\n")
            
            # Import each category
            for category in self.categorized_functions.keys():
                f.write(f"from . import {category}\n")
            
            # Export all categories
            f.write("\n__all__ = [\n")
            for category in self.categorized_functions.keys():
                f.write(f"    '{category}',\n")
            f.write("]\n")
        
        # Create a README.md file
        with open(output_path / "README.md", "w") as f:
            f.write("# Restructured Analysis Modules\n\n")
            f.write("This directory contains restructured and deduplicated analysis modules.\n\n")
            
            f.write("## Categories\n\n")
            for category, funcs in self.categorized_functions.items():
                non_duplicate_funcs = [func for func in funcs if not func.is_duplicate]
                f.write(f"### {category.capitalize()} ({len(non_duplicate_funcs)} functions)\n\n")
                for func in non_duplicate_funcs:
                    f.write(f"- `{func.name}`: From `{func.file_path}`\n")
                f.write("\n")
            
            f.write("## Duplicate Functions\n\n")
            if self.duplicate_groups:
                for i, group in enumerate(self.duplicate_groups):
                    f.write(f"### Group {i+1}\n\n")
                    for func in group:
                        f.write(f"- `{func.name}` in `{func.file_path}`\n")
                    f.write("\n")
            else:
                f.write("No duplicate functions found.\n\n")
            
            f.write("## Similar Functions\n\n")
            if self.similar_groups:
                for i, group in enumerate(self.similar_groups):
                    f.write(f"### Group {i+1}\n\n")
                    for func in group:
                        f.write(f"- `{func.name}` in `{func.file_path}`\n")
                    f.write("\n")
            else:
                f.write("No similar functions found.\n\n")
    
    def generate_report(self, output_file: str):
        """
        Generate a detailed report of the analysis.
        
        Args:
            output_file: Path to the output file
        """
        report = {
            "summary": {
                "total_functions": len(self.functions),
                "duplicate_groups": len(self.duplicate_groups),
                "similar_groups": len(self.similar_groups),
                "categories": {category: len(funcs) for category, funcs in self.categorized_functions.items()}
            },
            "duplicates": [
                {
                    "group_id": i,
                    "functions": [
                        {
                            "name": func.name,
                            "file_path": func.file_path,
                            "start_line": func.start_line,
                            "end_line": func.end_line
                        }
                        for func in group
                    ]
                }
                for i, group in enumerate(self.duplicate_groups)
            ],
            "similar": [
                {
                    "group_id": i,
                    "functions": [
                        {
                            "name": func.name,
                            "file_path": func.file_path,
                            "similarity_scores": {
                                other.name: score for other, score in 
                                [(other, func.compute_similarity(other)) for other in group if other != func]
                            }
                        }
                        for func in group
                    ]
                }
                for i, group in enumerate(self.similar_groups)
            ],
            "categories": {
                category: [
                    {
                        "name": func.name,
                        "file_path": func.file_path,
                        "is_duplicate": func.is_duplicate,
                        "duplicate_of": func.duplicate_of.name if func.duplicate_of else None,
                        "dependencies": list(func.dependencies)
                    }
                    for func in funcs
                ]
                for category, funcs in self.categorized_functions.items()
            }
        }
        
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)


def main():
    """Main entry point for the module disassembler."""
    parser = argparse.ArgumentParser(description="Module Disassembler for Codegen")
    
    parser.add_argument("--repo-path", required=True, help="Path to the repository to analyze")
    parser.add_argument("--output-dir", required=True, help="Directory to output the restructured modules")
    parser.add_argument("--report-file", default="disassembler_report.json", help="Path to the output report file")
    parser.add_argument("--similarity-threshold", type=float, default=0.8, help="Threshold for considering functions similar (0.0-1.0)")
    parser.add_argument("--language", help="Programming language of the codebase (auto-detected if not provided)")
    
    args = parser.parse_args()
    
    try:
        # Initialize the disassembler
        disassembler = ModuleDisassembler(repo_path=args.repo_path, language=args.language)
        
        # Perform the analysis
        disassembler.analyze(similarity_threshold=args.similarity_threshold)
        
        # Generate restructured modules
        disassembler.generate_restructured_modules(output_dir=args.output_dir)
        
        # Generate report
        disassembler.generate_report(output_file=args.report_file)
        
        logger.info(f"Analysis complete. Restructured modules saved to {args.output_dir}")
        logger.info(f"Report saved to {args.report_file}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
