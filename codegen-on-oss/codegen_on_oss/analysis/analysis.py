"""
Unified Analysis Module for Codegen-on-OSS

This module serves as a central hub for all code analysis functionality, integrating
various specialized analysis components into a cohesive system.
"""

import contextlib
import math
import os
import re
import subprocess
import tempfile
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import networkx as nx
import requests
import uvicorn
from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import from other analysis modules
from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.analysis.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)
from codegen_on_oss.analysis.codegen_sdk_codebase import (
    get_codegen_sdk_subdirectories,
    get_codegen_sdk_codebase
)
from codegen_on_oss.analysis.current_code_codebase import (
    get_graphsitter_repo_path,
    get_codegen_codebase_base_path,
    get_current_code_codebase,
    import_all_codegen_sdk_modules,
    DocumentedObjects,
    get_documented_objects
)
from codegen_on_oss.analysis.document_functions import (
    hop_through_imports,
    get_extended_context,
    run as document_functions_run
)
from codegen_on_oss.analysis.mdx_docs_generation import (
    render_mdx_page_for_class,
    render_mdx_page_title,
    render_mdx_inheritence_section,
    render_mdx_attributes_section,
    render_mdx_methods_section,
    render_mdx_for_attribute,
    format_parameter_for_mdx,
    format_parameters_for_mdx,
    format_return_for_mdx,
    render_mdx_for_method,
    get_mdx_route_for_class,
    format_type_string,
    resolve_type_string,
    format_builtin_type_string,
    span_type_string_by_pipe,
    parse_link
)
from codegen_on_oss.analysis.module_dependencies import run as module_dependencies_run
from codegen_on_oss.analysis.symbolattr import print_symbol_attribution
from codegen_on_oss.analysis.analysis_import import (
    create_graph_from_codebase,
    convert_all_calls_to_kwargs,
    find_import_cycles,
    find_problematic_import_loops
)

# Import new analysis modules
from codegen_on_oss.analysis.error_detection import (
    ErrorSeverity,
    ErrorCategory,
    CodeError,
    ErrorDetector,
    ParameterValidator,
    CallValidator,
    ReturnValidator,
    CodeAnalysisError,
    analyze_errors
)
from codegen_on_oss.analysis.function_call_analysis import (
    FunctionCallGraph,
    ParameterAnalysis,
    analyze_function_calls
)
from codegen_on_oss.analysis.type_validation import (
    TypeValidationError,
    TypeIssue,
    TypeValidator,
    TypeInferenceEngine,
    analyze_types
)

# Create FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodeAnalyzer:
    """
    Central class for code analysis that integrates all analysis components.
    
    This class serves as the main entry point for all code analysis functionality,
    providing a unified interface to access various analysis capabilities.
    """
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the CodeAnalyzer with a codebase.
        
        Args:
            codebase: The Codebase object to analyze
        """
        self.codebase = codebase
        self._context = None
        self._initialized = False
        
    def initialize(self):
        """
        Initialize the analyzer by setting up the context and other necessary components.
        This is called automatically when needed but can be called explicitly for eager initialization.
        """
        if self._initialized:
            return
            
        # Initialize context if not already done
        if self._context is None:
            self._context = self._create_context()
            
        self._initialized = True
    
    def _create_context(self) -> CodebaseContext:
        """
        Create a CodebaseContext instance for the current codebase.
        
        Returns:
            A new CodebaseContext instance
        """
        # If the codebase already has a context, use it
        if hasattr(self.codebase, "ctx") and self.codebase.ctx is not None:
            return self.codebase.ctx
            
        # Otherwise, create a new context from the codebase's configuration
        from codegen.sdk.codebase.config import ProjectConfig
        from codegen.configs.models.codebase import CodebaseConfig
        
        # Create a project config from the codebase
        project_config = ProjectConfig(
            repo_operator=self.codebase.repo_operator,
            programming_language=self.codebase.programming_language,
            base_path=self.codebase.base_path
        )
        
        # Create and return a new context
        return CodebaseContext([project_config], config=CodebaseConfig())
    
    @property
    def context(self) -> CodebaseContext:
        """
        Get the CodebaseContext for the current codebase.
        
        Returns:
            A CodebaseContext object for the codebase
        """
        if not self._initialized:
            self.initialize()
            
        return self._context
    
    def get_codebase_summary(self) -> str:
        """
        Get a comprehensive summary of the codebase.
        
        Returns:
            A string containing summary information about the codebase
        """
        return get_codebase_summary(self.codebase)
    
    def get_file_summary(self, file_path: str) -> str:
        """
        Get a summary of a specific file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A string containing summary information about the file
        """
        file = self.codebase.get_file(file_path)
        if file is None:
            return f"File not found: {file_path}"
        return get_file_summary(file)
    
    def get_class_summary(self, class_name: str) -> str:
        """
        Get a summary of a specific class.
        
        Args:
            class_name: Name of the class to analyze
            
        Returns:
            A string containing summary information about the class
        """
        for cls in self.codebase.classes:
            if cls.name == class_name:
                return get_class_summary(cls)
        return f"Class not found: {class_name}"
    
    def get_function_summary(self, function_name: str) -> str:
        """
        Get a summary of a specific function.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A string containing summary information about the function
        """
        for func in self.codebase.functions:
            if func.name == function_name:
                return get_function_summary(func)
        return f"Function not found: {function_name}"
    
    def get_symbol_summary(self, symbol_name: str) -> str:
        """
        Get a summary of a specific symbol.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            A string containing summary information about the symbol
        """
        for symbol in self.codebase.symbols:
            if symbol.name == symbol_name:
                return get_symbol_summary(symbol)
        return f"Symbol not found: {symbol_name}"
    
    def find_symbol_by_name(self, symbol_name: str) -> Optional[Symbol]:
        """
        Find a symbol by its name.
        
        Args:
            symbol_name: Name of the symbol to find
            
        Returns:
            The Symbol object if found, None otherwise
        """
        for symbol in self.codebase.symbols:
            if symbol.name == symbol_name:
                return symbol
        return None
    
    def find_file_by_path(self, file_path: str) -> Optional[SourceFile]:
        """
        Find a file by its path.
        
        Args:
            file_path: Path to the file to find
            
        Returns:
            The SourceFile object if found, None otherwise
        """
        return self.codebase.get_file(file_path)
    
    def find_class_by_name(self, class_name: str) -> Optional[Class]:
        """
        Find a class by its name.
        
        Args:
            class_name: Name of the class to find
            
        Returns:
            The Class object if found, None otherwise
        """
        for cls in self.codebase.classes:
            if cls.name == class_name:
                return cls
        return None
    
    def find_function_by_name(self, function_name: str) -> Optional[Function]:
        """
        Find a function by its name.
        
        Args:
            function_name: Name of the function to find
            
        Returns:
            The Function object if found, None otherwise
        """
        for func in self.codebase.functions:
            if func.name == function_name:
                return func
        return None
    
    def document_functions(self) -> None:
        """
        Generate documentation for functions in the codebase.
        """
        document_functions_run(self.codebase)
    
    def analyze_imports(self) -> Dict[str, Any]:
        """
        Analyze import relationships in the codebase.
        
        Returns:
            A dictionary containing import analysis results
        """
        # Create a graph from the codebase
        graph = create_graph_from_codebase(self.codebase)
        
        # Find import cycles
        cycles = find_import_cycles(graph)
        
        # Find problematic import loops
        problematic_loops = find_problematic_import_loops(graph)
        
        # Return the analysis results
        return {
            "import_cycles": cycles,
            "problematic_loops": problematic_loops,
            "total_imports": len(list(self.codebase.imports)),
            "external_modules": len(list(self.codebase.external_modules))
        }
    
    def analyze_complexity(self) -> Dict[str, Any]:
        """
        Analyze code complexity metrics for the codebase.
        
        Returns:
            A dictionary containing complexity analysis results
        """
        # Initialize results
        results = {
            "cyclomatic_complexity": {},
            "line_metrics": {},
            "maintainability_index": {}
        }
        
        # Calculate complexity metrics for each function
        for function in self.codebase.functions:
            # Skip functions without code blocks
            if not hasattr(function, "code_block"):
                continue
                
            # Calculate cyclomatic complexity
            complexity = calculate_cyclomatic_complexity(function)
            rank = cc_rank(complexity)
            
            # Calculate line metrics
            source = function.code_block.source
            loc, lloc, sloc, comments = count_lines(source)
            
            # Calculate Halstead volume
            operators, operands = get_operators_and_operands(function)
            volume, N1, N2, n1, n2 = calculate_halstead_volume(operators, operands)
            
            # Calculate maintainability index
            mi_score = calculate_maintainability_index(volume, complexity, loc)
            mi_rank = get_maintainability_rank(mi_score)
            
            # Store results
            function_key = f"{function.filepath}:{function.name}"
            results["cyclomatic_complexity"][function_key] = {
                "complexity": complexity,
                "rank": rank
            }
            results["line_metrics"][function_key] = {
                "loc": loc,
                "lloc": lloc,
                "sloc": sloc,
                "comments": comments
            }
            results["maintainability_index"][function_key] = {
                "score": mi_score,
                "rank": mi_rank
            }
        
        return results
    
    def analyze_errors(self) -> Dict[str, Any]:
        """
        Analyze the codebase for errors and issues.
        
        Returns:
            A dictionary containing error analysis results
        """
        return analyze_errors(self.codebase, self.context)
    
    def analyze_function_calls(self) -> Dict[str, Any]:
        """
        Analyze function calls in the codebase.
        
        Returns:
            A dictionary containing function call analysis results
        """
        return analyze_function_calls(self.codebase, self.context)
    
    def analyze_types(self) -> Dict[str, Any]:
        """
        Analyze types in the codebase.
        
        Returns:
            A dictionary containing type analysis results
        """
        return analyze_types(self.codebase, self.context)
    
    def get_function_call_graph(self) -> FunctionCallGraph:
        """
        Get a function call graph for the codebase.
        
        Returns:
            A FunctionCallGraph object
        """
        return FunctionCallGraph(self.codebase, self.context)
    
    def get_parameter_analysis(self) -> ParameterAnalysis:
        """
        Get a parameter analyzer for the codebase.
        
        Returns:
            A ParameterAnalysis object
        """
        return ParameterAnalysis(self.codebase, self.context)
    
    def get_error_detector(self) -> CodeAnalysisError:
        """
        Get an error detector for the codebase.
        
        Returns:
            A CodeAnalysisError object
        """
        return CodeAnalysisError(self.codebase, self.context)
    
    def get_type_validator(self) -> TypeValidator:
        """
        Get a type validator for the codebase.
        
        Returns:
            A TypeValidator object
        """
        return TypeValidator(self.codebase, self.context)
    
    def get_type_inference_engine(self) -> TypeInferenceEngine:
        """
        Get a type inference engine for the codebase.
        
        Returns:
            A TypeInferenceEngine object
        """
        return TypeInferenceEngine(self.codebase, self.context)
    
    def analyze_all(self) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of the codebase.
        
        Returns:
            A dictionary containing all analysis results
        """
        return {
            "complexity": self.analyze_complexity(),
            "imports": self.analyze_imports(),
            "errors": self.analyze_errors(),
            "function_calls": self.analyze_function_calls(),
            "types": self.analyze_types()
        }

def get_monthly_commits(repo_path: str) -> Dict[str, int]:
    """
    Get the number of commits per month for the last 12 months.

    Args:
        repo_path: Path to the git repository

    Returns:
        Dictionary with month-year as key and number of commits as value
    """
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=365)

    date_format = "%Y-%m-%d"
    since_date = start_date.strftime(date_format)
    until_date = end_date.strftime(date_format)

    # Validate repo_path format (should be owner/repo)
    if not re.match(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$", repo_path):
        print(f"Invalid repository path format: {repo_path}")
        return {}

    repo_url = f"https://github.com/{repo_path}"

    # Validate URL
    try:
        parsed_url = urlparse(repo_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            print(f"Invalid URL: {repo_url}")
            return {}
    except Exception:
        print(f"Invalid URL: {repo_url}")
        return {}

    try:
        original_dir = os.getcwd()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Using a safer approach with a list of arguments and shell=False
            subprocess.run(
                ["git", "clone", repo_url, temp_dir],
                check=True,
                capture_output=True,
                shell=False,
                text=True,
            )
            os.chdir(temp_dir)

            # Using a safer approach with a list of arguments and shell=False
            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"--since={since_date}",
                    f"--until={until_date}",
                    "--format=%aI",
                ],
                capture_output=True,
                text=True,
                check=True,
                shell=False,
            )
            commit_dates = result.stdout.strip().split("\n")

            monthly_counts = {}
            current_date = start_date
            while current_date <= end_date:
                month_key = current_date.strftime("%Y-%m")
                monthly_counts[month_key] = 0
                current_date = (
                    current_date.replace(day=1) + timedelta(days=32)
                ).replace(day=1)

            for date_str in commit_dates:
                if date_str:  # Skip empty lines
                    commit_date = datetime.fromisoformat(date_str.strip())
                    month_key = commit_date.strftime("%Y-%m")
                    if month_key in monthly_counts:
                        monthly_counts[month_key] += 1

            return dict(sorted(monthly_counts.items()))

    except subprocess.CalledProcessError as e:
        print(f"Error executing git command: {e}")
        return {}
    except Exception as e:
        print(f"Error processing git commits: {e}")
        return {}
    finally:
        with contextlib.suppress(Exception):
            os.chdir(original_dir)


def calculate_cyclomatic_complexity(function):
    """
    Calculate the cyclomatic complexity of a function.
    
    Args:
        function: The function to analyze
        
    Returns:
        The cyclomatic complexity score
    """
    def analyze_statement(statement):
        complexity = 0

        if isinstance(statement, IfBlockStatement):
            complexity += 1
            if hasattr(statement, "elif_statements"):
                complexity += len(statement.elif_statements)

        elif isinstance(statement, ForLoopStatement | WhileStatement):
            complexity += 1

        elif isinstance(statement, TryCatchStatement):
            complexity += len(getattr(statement, "except_blocks", []))

        if hasattr(statement, "condition") and isinstance(statement.condition, str):
            complexity += statement.condition.count(
                " and "
            ) + statement.condition.count(" or ")

        if hasattr(statement, "nested_code_blocks"):
            for block in statement.nested_code_blocks:
                complexity += analyze_block(block)

        return complexity

    def analyze_block(block):
        if not block or not hasattr(block, "statements"):
            return 0
        return sum(analyze_statement(stmt) for stmt in block.statements)

    return (
        1 + analyze_block(function.code_block) if hasattr(function, "code_block") else 1
    )


def cc_rank(complexity):
    """
    Convert cyclomatic complexity score to a letter grade.
    
    Args:
        complexity: The cyclomatic complexity score
        
    Returns:
        A letter grade from A to F
    """
    if complexity < 0:
        raise ValueError("Complexity must be a non-negative value")

    ranks = [
        (1, 5, "A"),
        (6, 10, "B"),
        (11, 20, "C"),
        (21, 30, "D"),
        (31, 40, "E"),
        (41, float("inf"), "F"),
    ]
    for low, high, rank in ranks:
        if low <= complexity <= high:
            return rank
    return "F"


def calculate_doi(cls):
    """
    Calculate the depth of inheritance for a given class.
    
    Args:
        cls: The class to analyze
        
    Returns:
        The depth of inheritance
    """
    return len(cls.superclasses)


def get_operators_and_operands(function):
    """
    Extract operators and operands from a function.
    
    Args:
        function: The function to analyze
        
    Returns:
        A tuple of (operators, operands)
    """
    operators = []
    operands = []

    for statement in function.code_block.statements:
        for call in statement.function_calls:
            operators.append(call.name)
            for arg in call.args:
                operands.append(arg.source)

        if hasattr(statement, "expressions"):
            for expr in statement.expressions:
                if isinstance(expr, BinaryExpression):
                    operators.extend([op.source for op in expr.operators])
                    operands.extend([elem.source for elem in expr.elements])
                elif isinstance(expr, UnaryExpression):
                    operators.append(expr.ts_node.type)
                    operands.append(expr.argument.source)
                elif isinstance(expr, ComparisonExpression):
                    operators.extend([op.source for op in expr.operators])
                    operands.extend([elem.source for elem in expr.elements])

        if hasattr(statement, "expression"):
            expr = statement.expression
            if isinstance(expr, BinaryExpression):
                operators.extend([op.source for op in expr.operators])
                operands.extend([elem.source for elem in expr.elements])
            elif isinstance(expr, UnaryExpression):
                operators.append(expr.ts_node.type)
                operands.append(expr.argument.source)
            elif isinstance(expr, ComparisonExpression):
                operators.extend([op.source for op in expr.operators])
                operands.extend([elem.source for elem in expr.elements])

    return operators, operands


def calculate_halstead_volume(operators, operands):
    """
    Calculate Halstead volume metrics.
    
    Args:
        operators: List of operators
        operands: List of operands
        
    Returns:
        A tuple of (volume, N1, N2, n1, n2)
    """
    n1 = len(set(operators))
    n2 = len(set(operands))

    N1 = len(operators)
    N2 = len(operands)

    N = N1 + N2
    n = n1 + n2

    if n > 0:
        volume = N * math.log2(n)
        return volume, N1, N2, n1, n2
    return 0, N1, N2, n1, n2


def count_lines(source: str):
    """
    Count different types of lines in source code.
    
    Args:
        source: The source code as a string
        
    Returns:
        A tuple of (loc, lloc, sloc, comments)
    """
    if not source.strip():
        return 0, 0, 0, 0

    lines = [line.strip() for line in source.splitlines()]
    loc = len(lines)
    sloc = len([line for line in lines if line])

    in_multiline = False
    comments = 0
    code_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        code_part = line
        if not in_multiline and "#" in line:
            comment_start = line.find("#")
            if not re.search(r'[\"\\\']\s*#\s*[\"\\\']\s*', line[:comment_start]):
                code_part = line[:comment_start].strip()
                if line[comment_start:].strip():
                    comments += 1

        if ('"""' in line or "'''" in line) and not (
            line.count('"""') % 2 == 0 or line.count("'''") % 2 == 0
        ):
            if in_multiline:
                in_multiline = False
                comments += 1
            else:
                in_multiline = True
                comments += 1
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    code_part = ""
        elif in_multiline or line.strip().startswith("#"):
            comments += 1
            code_part = ""

        if code_part.strip():
            code_lines.append(code_part)

        i += 1

    lloc = 0
    continued_line = False
    for line in code_lines:
        if continued_line:
            if not any(line.rstrip().endswith(c) for c in ("\\", ",", "{", "[", "(")):
                continued_line = False
            continue

        lloc += len([stmt for stmt in line.split(";") if stmt.strip()])

        if any(line.rstrip().endswith(c) for c in ("\\", ",", "{", "[", "(")):
            continued_line = True

    return loc, lloc, sloc, comments


def calculate_maintainability_index(
    halstead_volume: float, cyclomatic_complexity: float, loc: int
) -> int:
    """
    Calculate the normalized maintainability index for a given function.
    
    Args:
        halstead_volume: The Halstead volume
        cyclomatic_complexity: The cyclomatic complexity
        loc: Lines of code
        
    Returns:
        The maintainability index score (0-100)
    """
    if loc <= 0:
        return 100

    try:
        raw_mi = (
            171
            - 5.2 * math.log(max(1, halstead_volume))
            - 0.23 * cyclomatic_complexity
            - 16.2 * math.log(max(1, loc))
        )
        normalized_mi = max(0, min(100, raw_mi * 100 / 171))
        return int(normalized_mi)
    except (ValueError, TypeError):
        return 0


def get_maintainability_rank(mi_score: float) -> str:
    """
    Convert maintainability index score to a letter grade.
    
    Args:
        mi_score: The maintainability index score
        
    Returns:
        A letter grade from A to F
    """
    if mi_score >= 85:
        return "A"
    elif mi_score >= 65:
        return "B"
    elif mi_score >= 45:
        return "C"
    elif mi_score >= 25:
        return "D"
    else:
        return "F"


def get_github_repo_description(repo_url):
    """
    Get the description of a GitHub repository.
    
    Args:
        repo_url: The repository URL in the format 'owner/repo'
        
    Returns:
        The repository description
    """
    api_url = f"https://api.github.com/repos/{repo_url}"

    response = requests.get(api_url)

    if response.status_code == 200:
        repo_data = response.json()
        return repo_data.get("description", "No description available")
    else:
        return ""


class RepoRequest(BaseModel):
    """Request model for repository analysis."""
    repo_url: str


@app.post("/analyze_repo")
async def analyze_repo(request: RepoRequest) -> Dict[str, Any]:
    """
    Analyze a repository and return comprehensive metrics.
    
    Args:
        request: The repository request containing the repo URL
        
    Returns:
        A dictionary of analysis results
    """
    repo_url = request.repo_url
    codebase = Codebase.from_repo(repo_url)
    
    # Create analyzer instance
    analyzer = CodeAnalyzer(codebase)
    
    # Perform comprehensive analysis
    analysis_results = analyzer.analyze_all()
    
    # Get repository description
    desc = get_github_repo_description(repo_url)
    
    # Combine all results
    results = {
        "repo_url": repo_url,
        "description": desc,
        "num_files": len(codebase.files),
        "num_functions": len(codebase.functions),
        "num_classes": len(codebase.classes),
        "complexity_metrics": analysis_results["complexity"],
        "import_analysis": analysis_results["imports"],
        "error_analysis": analysis_results["errors"],
        "function_call_analysis": analysis_results["function_calls"],
        "type_analysis": analysis_results["types"]
    }
    
    return results


class FileAnalysisRequest(BaseModel):
    """Request model for file analysis."""
    repo_url: str
    file_path: str


@app.post("/analyze_file")
async def analyze_file(request: FileAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze a specific file in a repository.
    
    Args:
        request: The file analysis request
        
    Returns:
        A dictionary of analysis results for the file
    """
    repo_url = request.repo_url
    file_path = request.file_path
    codebase = Codebase.from_repo(repo_url)
    
    # Create analyzer instance
    analyzer = CodeAnalyzer(codebase)
    
    # Get the file
    file = analyzer.find_file_by_path(file_path)
    if file is None:
        return {"error": f"File not found: {file_path}"}
    
    # Get file summary
    summary = analyzer.get_file_summary(file_path)
    
    # Get error analysis
    error_analysis = analyzer.analyze_errors()
    file_errors = error_analysis["errors_by_file"].get(file_path, [])
    
    # Get type analysis
    type_analysis = analyzer.analyze_types()
    file_type_issues = type_analysis["issues_by_file"].get(file_path, [])
    
    # Get complexity metrics
    complexity_analysis = analyzer.analyze_complexity()
    file_complexity = {}
    for metric_type, metrics in complexity_analysis.items():
        file_complexity[metric_type] = {k: v for k, v in metrics.items() if k.startswith(file_path)}
    
    # Return the results
    return {
        "repo_url": repo_url,
        "file_path": file_path,
        "summary": summary,
        "errors": file_errors,
        "type_issues": file_type_issues,
        "complexity": file_complexity
    }


class FunctionAnalysisRequest(BaseModel):
    """Request model for function analysis."""
    repo_url: str
    function_name: str


@app.post("/analyze_function")
async def analyze_function(request: FunctionAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze a specific function in a repository.
    
    Args:
        request: The function analysis request
        
    Returns:
        A dictionary of analysis results for the function
    """
    repo_url = request.repo_url
    function_name = request.function_name
    codebase = Codebase.from_repo(repo_url)
    
    # Create analyzer instance
    analyzer = CodeAnalyzer(codebase)
    
    # Get the function
    function = analyzer.find_function_by_name(function_name)
    if function is None:
        return {"error": f"Function not found: {function_name}"}
    
    # Get function summary
    summary = analyzer.get_function_summary(function_name)
    
    # Get call graph analysis
    call_graph = analyzer.get_function_call_graph()
    callers = call_graph.get_callers(function_name)
    callees = call_graph.get_callees(function_name)
    call_depth = call_graph.get_call_depth(function_name)
    
    # Get parameter analysis
    param_analysis = analyzer.get_parameter_analysis()
    param_usage = param_analysis.analyze_parameter_usage(function)
    
    # Get error analysis
    error_detector = analyzer.get_error_detector()
    errors = [error.to_dict() for error in error_detector.detect_errors() 
              if error.function_name == function_name]
    
    # Get complexity metrics
    complexity = calculate_cyclomatic_complexity(function)
    
    # Get Halstead metrics
    operators, operands = get_operators_and_operands(function)
    volume, N1, N2, n1, n2 = calculate_halstead_volume(operators, operands)
    
    # Calculate maintainability index
    if hasattr(function, "code_block"):
        loc = len(function.code_block.source.splitlines())
        mi_score = calculate_maintainability_index(volume, complexity, loc)
        mi_rank = get_maintainability_rank(mi_score)
    else:
        loc = 0
        mi_score = 0
        mi_rank = "N/A"
    
    # Return the results
    return {
        "repo_url": repo_url,
        "function_name": function_name,
        "summary": summary,
        "file_path": function.filepath,
        "line_number": function.line_number,
        "callers": [caller.name for caller in callers],
        "callees": [callee.name for callee in callees],
        "call_depth": call_depth,
        "parameter_analysis": param_usage,
        "errors": errors,
        "complexity": {
            "cyclomatic_complexity": complexity,
            "rank": cc_rank(complexity),
            "halstead_volume": volume,
            "unique_operators": n1,
            "unique_operands": n2,
            "total_operators": N1,
            "total_operands": N2,
            "maintainability_index": mi_score,
            "maintainability_rank": mi_rank,
            "loc": loc
        }
    }


class ErrorAnalysisRequest(BaseModel):
    """Request model for error analysis."""
    repo_url: str
    severity_filter: Optional[str] = None
    category_filter: Optional[str] = None


@app.post("/analyze_errors")
async def analyze_errors_endpoint(request: ErrorAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze errors in a repository with optional filtering.
    
    Args:
        request: The error analysis request
        
    Returns:
        A dictionary of error analysis results
    """
    repo_url = request.repo_url
    codebase = Codebase.from_repo(repo_url)
    
    # Create analyzer instance
    analyzer = CodeAnalyzer(codebase)
    
    # Get error analysis
    error_analysis = analyzer.analyze_errors()
    
    # Apply filters if specified
    if request.severity_filter:
        # Filter errors by severity
        filtered_errors = []
        for error in error_analysis["all_errors"]:
            if error["severity"] == request.severity_filter:
                filtered_errors.append(error)
        error_analysis["all_errors"] = filtered_errors
        
        # Update summary
        error_analysis["summary"]["total_errors"] = len(filtered_errors)
    
    if request.category_filter:
        # Filter errors by category
        filtered_errors = []
        for error in error_analysis["all_errors"]:
            if error["category"] == request.category_filter:
                filtered_errors.append(error)
        error_analysis["all_errors"] = filtered_errors
        
        # Update summary
        error_analysis["summary"]["total_errors"] = len(filtered_errors)
    
    # Return the results
    return {
        "repo_url": repo_url,
        "error_analysis": error_analysis
    }


if __name__ == "__main__":
    # Run the FastAPI app locally with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
