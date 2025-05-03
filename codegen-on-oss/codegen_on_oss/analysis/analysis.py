import contextlib
import math
import os
import re
import subprocess
import tempfile
from datetime import datetime, timedelta
from typing import Any

import requests
import uvicorn
from codegen import Codebase
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import networkx as nx

# Import from other analysis modules
from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.analysis.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
)
from codegen_on_oss.analysis.codegen_sdk_codebase import (
    get_codegen_sdk_subdirectories,
    get_codegen_sdk_codebase,
)
from codegen_on_oss.analysis.current_code_codebase import (
    get_graphsitter_repo_path,
    get_codegen_codebase_base_path,
    get_current_code_codebase,
    import_all_codegen_sdk_module,
    DocumentedObjects,
    get_documented_objects,
)
from codegen_on_oss.analysis.document_functions import (
    hop_through_imports,
    get_extended_context,
    run as document_functions_run,
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
    parse_link,
)
from codegen_on_oss.analysis.module_dependencies import run as module_dependencies_run
from codegen_on_oss.analysis.symbolattr import print_symbol_attribution
from codegen_on_oss.analysis.analysis_import import (
    create_graph_from_codebase,
    convert_all_calls_to_kwargs,
    find_import_cycles,
    find_problematic_import_loops,
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


def get_monthly_commits(repo_path: str) -> dict[str, int]:
    """
    Get the number of commits per month for the last 12 months.

    Args:
        repo_path: Path to the git repository

    Returns:
        Dictionary with month-year as key and number of commits as value
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    date_format = "%Y-%m-%d"
    since_date = start_date.strftime(date_format)
    until_date = end_date.strftime(date_format)
    
    # Ensure repo_path is properly formatted to prevent command injection
    if not re.match(r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$', repo_path):
        print(f"Invalid repository path format: {repo_path}")
        return {}
        
    repo_url = f"https://github.com/{repo_path}"

    try:
        original_dir = os.getcwd()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Use subprocess with full path to git executable
            subprocess.run(["/usr/bin/git", "clone", repo_url, temp_dir], check=True)
            os.chdir(temp_dir)

            cmd = [
                "/usr/bin/git",
                "log",
                f"--since={since_date}",
                f"--until={until_date}",
                "--format=%aI",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
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

            os.chdir(original_dir)
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
    """Calculate the depth of inheritance for a given class."""
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

    lines = source.splitlines()
    loc = len(lines)
    lloc = 0
    sloc = 0
    in_multiline = False
    comments = 0
    code_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        code_part = line
        if not in_multiline and "#" in line:
            comment_start = line.find("#")
            if not re.search(r'["\'].*#.*["\']', line[:comment_start]):
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

    # Add timeout to requests call
    response = requests.get(api_url, timeout=10)

    if response.status_code == 200:
        repo_data = response.json()
        return repo_data.get("description", "No description available")
    else:
        return ""


class RepoRequest(BaseModel):
    """Request model for repository analysis."""

    repo_url: str


@app.post("/analyze_repo")
async def analyze_repo(request: RepoRequest) -> dict[str, Any]:
    """
    Analyze a repository and return comprehensive metrics.

    Args:
        request: The repository request containing the repo URL

    Returns:
        A dictionary of analysis results
    """
    repo_url = request.repo_url
    codebase = Codebase.from_repo(repo_url)

    num_files = len(codebase.files(extensions="*"))
    num_functions = len(codebase.functions)
    num_classes = len(codebase.classes)

    total_loc = total_lloc = total_sloc = total_comments = 0
    total_complexity = 0
    total_volume = 0
    total_mi = 0
    total_doi = 0

    monthly_commits = get_monthly_commits(repo_url)
    print(monthly_commits)

    for file in codebase.files:
        loc, lloc, sloc, comments = count_lines(file.source)
        total_loc += loc
        total_lloc += lloc
        total_sloc += sloc
        total_comments += comments

    callables = codebase.functions + [m for c in codebase.classes for m in c.methods]

    num_callables = 0
    for func in callables:
        if not hasattr(func, "code_block"):
            continue

        complexity = calculate_cyclomatic_complexity(func)
        operators, operands = get_operators_and_operands(func)
        volume, _, _, _, _ = calculate_halstead_volume(operators, operands)
        loc = len(func.code_block.source.splitlines())
        mi_score = calculate_maintainability_index(volume, complexity, loc)

        total_complexity += complexity
        total_volume += volume
        total_mi += mi_score
        num_callables += 1

    for cls in codebase.classes:
        doi = calculate_doi(cls)
        total_doi += doi

    desc = get_github_repo_description(repo_url)

    results = {
        "repo_url": repo_url,
        "line_metrics": {
            "total": {
                "loc": total_loc,
                "lloc": total_lloc,
                "sloc": total_sloc,
                "comments": total_comments,
                "comment_density": (
                    total_comments / total_loc * 100 if total_loc > 0 else 0
                ),
            },
        },
        "cyclomatic_complexity": {
            "average": (total_complexity / num_callables if num_callables > 0 else 0),
        },
        "depth_of_inheritance": {
            "average": (total_doi / len(codebase.classes) if codebase.classes else 0),
        },
        "halstead_metrics": {
            "total_volume": int(total_volume),
            "average_volume": (
                int(total_volume / num_callables) if num_callables > 0 else 0
            ),
        },
        "maintainability_index": {
            "average": (int(total_mi / num_callables) if num_callables > 0 else 0),
        },
        "description": desc,
        "num_files": num_files,
        "num_functions": num_functions,
        "num_classes": num_classes,
        "monthly_commits": monthly_commits,
    }

    return results


if __name__ == "__main__":
    # Run the FastAPI app locally with uvicorn
    # Use 127.0.0.1 instead of 0.0.0.0 for security
    uvicorn.run(app, host="127.0.0.1", port=8000)
