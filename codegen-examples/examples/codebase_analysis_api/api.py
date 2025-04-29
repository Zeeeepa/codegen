import os
from typing import Dict, Any, List, Optional
from enum import Enum
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import tempfile
import shutil
import zipfile
import networkx as nx
from pathlib import Path
import time
import re
import math
from collections import Counter, defaultdict

import codegen
from codegen import Codebase
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression

# Configuration
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
MAX_REPO_SIZE = int(os.getenv("MAX_REPO_SIZE", "100")) * 1024 * 1024  # in bytes
ANALYSIS_TIMEOUT = int(os.getenv("ANALYSIS_TIMEOUT", "300"))  # in seconds

app = FastAPI(
    title="Codebase Analysis API",
    description="A comprehensive API for analyzing codebases using Codegen SDK",
    version="1.0.0",
)

# Models
class VisualizationType(str, Enum):
    CALL_GRAPH = "call_graph"
    DEPENDENCY_GRAPH = "dependency_graph"
    SYMBOL_TREE = "symbol_tree"
    MODULE_DEPENDENCY = "module_dependency"
    INHERITANCE_HIERARCHY = "inheritance_hierarchy"

class LanguageType(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    AUTO = "auto"

class AnalysisRequest(BaseModel):
    repo_path: str
    language: LanguageType = LanguageType.AUTO
    include_visualizations: bool = False
    max_depth: int = Field(default=3, ge=1, le=10)

class AnalysisResponse(BaseModel):
    overall_statistics: Dict[str, Any]
    important_files: List[Dict[str, Any]]
    project_structure: Dict[str, Any]
    code_quality_issues: Dict[str, Any]
    visualization_options: List[str]
    analysis_time: float

# Cache for analysis results
analysis_cache = {}

# Helper functions
def calculate_cyclomatic_complexity(function):
    """Calculate cyclomatic complexity for a function"""

    def analyze_statement(statement):
        complexity = 0

        if isinstance(statement, IfBlockStatement):
            complexity += 1
            if hasattr(statement, "elif_statements"):
                complexity += len(statement.elif_statements)

        elif isinstance(statement, (ForLoopStatement, WhileStatement)):
            complexity += 1

        elif isinstance(statement, TryCatchStatement):
            complexity += len(getattr(statement, "except_blocks", []))

        if hasattr(statement, "condition") and isinstance(statement.condition, str):
            complexity += statement.condition.count(" and ") + statement.condition.count(" or ")

        if hasattr(statement, "nested_code_blocks"):
            for block in statement.nested_code_blocks:
                complexity += analyze_block(block)

        return complexity

    def analyze_block(block):
        if not block or not hasattr(block, "statements"):
            return 0
        return sum(analyze_statement(stmt) for stmt in block.statements)

    return 1 + analyze_block(function.code_block) if hasattr(function, "code_block") else 1

def cc_rank(complexity):
    """Convert cyclomatic complexity to a letter grade"""
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

def get_operators_and_operands(function):
    """Extract operators and operands from a function"""
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
    """Calculate Halstead volume for a function"""
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
    """Count different types of lines in source code"""
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
            if not re.search(r'[\"\\'].*#.*[\"\\']', line[:comment_start]):
                code_part = line[:comment_start].strip()
                if line[comment_start:].strip():
                    comments += 1

        if ('"""' in line or "'''" in line) and not (line.count('"""') % 2 == 0 or line.count("'''") % 2 == 0):
            if in_multiline:
                in_multiline = False
                comments += 1
            else:
                in_multiline = True
                comments += 1
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    code_part = ""
        elif in_multiline:
            comments += 1
            code_part = ""
        elif line.strip().startswith("#"):
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

def calculate_maintainability_index(halstead_volume: float, cyclomatic_complexity: float, loc: int) -> int:
    """Calculate the normalized maintainability index for a given function"""
    if loc <= 0:
        return 100

    try:
        raw_mi = 171 - 5.2 * math.log(max(1, halstead_volume)) - 0.23 * cyclomatic_complexity - 16.2 * math.log(max(1, loc))
        normalized_mi = max(0, min(100, raw_mi * 100 / 171))
        return int(normalized_mi)
    except (ValueError, TypeError):
        return 0

def get_maintainability_rank(mi_score: int) -> str:
    """Convert maintainability index to a letter grade"""
    if mi_score >= 85:
        return "A"
    elif mi_score >= 65:
        return "B"
    elif mi_score >= 40:
        return "C"
    elif mi_score >= 20:
        return "D"
    else:
        return "F"

def find_entry_points(codebase: Codebase) -> List[Dict[str, Any]]:
    """Find potential entry points in the codebase"""
    entry_points = []
    
    # Look for main functions, app initializations, etc.
    for func in codebase.functions:
        if func.name in ["main", "app", "init", "start", "run"]:
            entry_points.append({
                "type": "function",
                "name": func.name,
                "filepath": func.filepath,
                "complexity": calculate_cyclomatic_complexity(func)
            })
    
    # Look for classes that might be entry points
    for cls in codebase.classes:
        if any(name in cls.name.lower() for name in ["app", "service", "controller", "main"]):
            entry_points.append({
                "type": "class",
                "name": cls.name,
                "filepath": cls.filepath,
                "methods": len(cls.methods)
            })
    
    # Look for files that might be entry points
    for file in codebase.files:
        if any(name in file.name.lower() for name in ["main", "app", "index", "server"]):
            entry_points.append({
                "type": "file",
                "name": file.name,
                "filepath": file.filepath,
                "symbols": len(file.symbols)
            })
    
    return entry_points

def find_unused_imports(codebase: Codebase) -> List[Dict[str, Any]]:
    """Find unused imports in the codebase"""
    unused_imports = []
    
    for file in codebase.files:
        for import_stmt in file.import_statements:
            for imp in import_stmt.imports:
                if not imp.symbol_usages:
                    unused_imports.append({
                        "filepath": file.filepath,
                        "import": imp.name,
                        "line": import_stmt.start_point[0] + 1
                    })
    
    return unused_imports

def find_unused_functions(codebase: Codebase) -> List[Dict[str, Any]]:
    """Find unused functions in the codebase"""
    unused_functions = []
    
    for func in codebase.functions:
        if not func.call_sites and not func.name.startswith("_"):
            unused_functions.append({
                "filepath": func.filepath,
                "name": func.name,
                "line": func.start_point[0] + 1
            })
    
    return unused_functions

def find_unused_classes(codebase: Codebase) -> List[Dict[str, Any]]:
    """Find unused classes in the codebase"""
    unused_classes = []
    
    for cls in codebase.classes:
        if not cls.symbol_usages and not cls.name.startswith("_"):
            unused_classes.append({
                "filepath": cls.filepath,
                "name": cls.name,
                "line": cls.start_point[0] + 1
            })
    
    return unused_classes

def find_high_complexity_functions(codebase: Codebase, threshold: int = 10) -> List[Dict[str, Any]]:
    """Find functions with high cyclomatic complexity"""
    complex_functions = []
    
    for func in codebase.functions:
        complexity = calculate_cyclomatic_complexity(func)
        if complexity > threshold:
            complex_functions.append({
                "filepath": func.filepath,
                "name": func.name,
                "complexity": complexity,
                "rank": cc_rank(complexity),
                "line": func.start_point[0] + 1
            })
    
    # Sort by complexity (highest first)
    complex_functions.sort(key=lambda x: x["complexity"], reverse=True)
    return complex_functions

def build_project_tree(codebase: Codebase, max_depth: int = 3) -> Dict[str, Any]:
    """Build a hierarchical representation of the project structure"""
    root = {"name": Path(codebase.repo_path).name, "type": "directory", "children": []}
    
    # Group files by directory
    directories = defaultdict(list)
    for file in codebase.files:
        rel_path = Path(file.filepath)
        parent_dir = str(rel_path.parent)
        directories[parent_dir].append(file)
    
    # Build directory tree
    def add_directory(path, parent, current_depth=0):
        if current_depth > max_depth:
            return
        
        dir_name = Path(path).name or path
        dir_node = {"name": dir_name, "type": "directory", "children": []}
        parent["children"].append(dir_node)
        
        # Add files in this directory
        for file in directories.get(path, []):
            file_node = {
                "name": file.name,
                "type": "file",
                "language": file.language,
                "symbols": len(file.symbols),
                "classes": len(file.classes),
                "functions": len(file.functions),
                "lines": len(file.source.splitlines()) if file.source else 0
            }
            
            # Add detailed information about symbols if not too deep
            if current_depth < max_depth - 1:
                file_node["details"] = []
                
                # Add classes
                for cls in file.classes:
                    cls_node = {
                        "name": cls.name,
                        "type": "class",
                        "methods": len(cls.methods),
                        "attributes": len(cls.properties),
                        "line": cls.start_point[0] + 1
                    }
                    
                    # Add methods if not too deep
                    if current_depth < max_depth - 2:
                        cls_node["methods_details"] = []
                        for method in cls.methods:
                            method_node = {
                                "name": method.name,
                                "line": method.start_point[0] + 1,
                                "parameters": len(method.parameters) if hasattr(method, "parameters") else 0
                            }
                            cls_node["methods_details"].append(method_node)
                    
                    file_node["details"].append(cls_node)
                
                # Add functions
                for func in file.functions:
                    if not any(cls.methods for cls in file.classes if func in cls.methods):
                        func_node = {
                            "name": func.name,
                            "type": "function",
                            "line": func.start_point[0] + 1,
                            "parameters": len(func.parameters) if hasattr(func, "parameters") else 0
                        }
                        file_node["details"].append(func_node)
            
            dir_node["children"].append(file_node)
        
        # Add subdirectories
        subdirs = set()
        for d in directories.keys():
            if d.startswith(path + "/") and d != path:
                subdir = d.split("/")[len(path.split("/"))]
                subdirs.add(path + "/" + subdir if path else subdir)
        
        for subdir in sorted(subdirs):
            add_directory(subdir, dir_node, current_depth + 1)
    
    # Start with the root directory
    add_directory("", root)
    return root

def build_dependency_graph(codebase: Codebase) -> Dict[str, Any]:
    """Build a dependency graph of the codebase"""
    graph = nx.DiGraph()
    
    # Add nodes for each file
    for file in codebase.files:
        graph.add_node(file.filepath, type="file", name=file.name)
    
    # Add edges for imports
    for file in codebase.files:
        for import_stmt in file.import_statements:
            for imp in import_stmt.imports:
                if imp.symbol_definition and imp.symbol_definition.filepath:
                    graph.add_edge(file.filepath, imp.symbol_definition.filepath)
    
    # Convert to a serializable format
    nodes = []
    for node in graph.nodes:
        nodes.append({
            "id": node,
            "name": graph.nodes[node].get("name", Path(node).name),
            "type": graph.nodes[node].get("type", "file")
        })
    
    edges = []
    for source, target in graph.edges:
        edges.append({
            "source": source,
            "target": target
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "density": nx.density(graph) if len(nodes) > 1 else 0,
            "connected_components": nx.number_connected_components(graph.to_undirected()) if len(nodes) > 0 else 0
        }
    }

def build_call_graph(codebase: Codebase) -> Dict[str, Any]:
    """Build a call graph of the codebase"""
    graph = nx.DiGraph()
    
    # Add nodes for each function
    for func in codebase.functions:
        graph.add_node(f"{func.filepath}:{func.name}", type="function", name=func.name, filepath=func.filepath)
    
    # Add edges for function calls
    for func in codebase.functions:
        if hasattr(func, "code_block") and func.code_block:
            for stmt in func.code_block.statements:
                for call in stmt.function_calls:
                    if call.symbol_definition:
                        target_func = call.symbol_definition
                        graph.add_edge(
                            f"{func.filepath}:{func.name}",
                            f"{target_func.filepath}:{target_func.name}"
                        )
    
    # Convert to a serializable format
    nodes = []
    for node in graph.nodes:
        nodes.append({
            "id": node,
            "name": graph.nodes[node].get("name", node.split(":")[-1]),
            "filepath": graph.nodes[node].get("filepath", node.split(":")[0]),
            "type": graph.nodes[node].get("type", "function")
        })
    
    edges = []
    for source, target in graph.edges:
        edges.append({
            "source": source,
            "target": target
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "density": nx.density(graph) if len(nodes) > 1 else 0,
            "connected_components": nx.number_connected_components(graph.to_undirected()) if len(nodes) > 0 else 0
        }
    }

def analyze_codebase(codebase_path: str, language: LanguageType = LanguageType.AUTO, max_depth: int = 3) -> Dict[str, Any]:
    """Analyze a codebase and return comprehensive metrics"""
    start_time = time.time()
    
    # Initialize codebase
    codebase = Codebase(codebase_path)
    
    # Collect overall statistics
    file_count = len(codebase.files)
    files_by_language = Counter(file.language for file in codebase.files if file.language)
    total_lines = sum(len(file.source.splitlines()) if file.source else 0 for file in codebase.files)
    class_count = len(codebase.classes)
    function_count = len(codebase.functions)
    symbol_count = sum(len(file.symbols) for file in codebase.files)
    
    # Calculate average complexity
    complexities = [calculate_cyclomatic_complexity(func) for func in codebase.functions if hasattr(func, "code_block")]
    avg_complexity = sum(complexities) / len(complexities) if complexities else 0
    
    # Find important files and entry points
    entry_points = find_entry_points(codebase)
    
    # Build project structure tree
    project_structure = build_project_tree(codebase, max_depth)
    
    # Find code quality issues
    unused_imports = find_unused_imports(codebase)
    unused_functions = find_unused_functions(codebase)
    unused_classes = find_unused_classes(codebase)
    high_complexity_functions = find_high_complexity_functions(codebase)
    
    # Build dependency graphs
    dependency_graph = build_dependency_graph(codebase)
    call_graph = build_call_graph(codebase)
    
    # Detect circular dependencies
    circular_deps = []
    try:
        cycles = list(nx.simple_cycles(nx.DiGraph(dependency_graph["edges"])))
        for cycle in cycles:
            if len(cycle) > 1:
                circular_deps.append({
                    "files": cycle,
                    "length": len(cycle)
                })
    except nx.NetworkXNoCycle:
        pass
    
    # Compile results
    analysis_time = time.time() - start_time
    
    return {
        "overall_statistics": {
            "total_files": file_count,
            "files_by_language": dict(files_by_language),
            "total_lines_of_code": total_lines,
            "total_classes": class_count,
            "total_functions": function_count,
            "total_symbols": symbol_count,
            "average_cyclomatic_complexity": round(avg_complexity, 2)
        },
        "important_files": entry_points,
        "project_structure": project_structure,
        "code_quality_issues": {
            "unused_imports": {
                "count": len(unused_imports),
                "items": unused_imports[:10]  # Limit to avoid huge responses
            },
            "unused_functions": {
                "count": len(unused_functions),
                "items": unused_functions[:10]
            },
            "unused_classes": {
                "count": len(unused_classes),
                "items": unused_classes[:10]
            },
            "high_complexity_functions": {
                "count": len(high_complexity_functions),
                "items": high_complexity_functions[:10]
            },
            "circular_dependencies": {
                "count": len(circular_deps),
                "items": circular_deps[:10]
            }
        },
        "dependency_graph": dependency_graph,
        "call_graph": call_graph,
        "visualization_options": [v.value for v in VisualizationType],
        "analysis_time": round(analysis_time, 2)
    }

@app.get("/")
async def root():
    return {"message": "Welcome to the Codebase Analysis API", "version": "1.0.0"}

@app.get("/analyze/{repo_url:path}")
async def analyze_repo(
    repo_url: str,
    language: LanguageType = LanguageType.AUTO,
    include_visualizations: bool = False,
    max_depth: int = Query(default=3, ge=1, le=10),
    background_tasks: BackgroundTasks = None
):
    """Analyze a GitHub repository"""
    # Check cache
    cache_key = f"{repo_url}:{language}:{max_depth}"
    if cache_key in analysis_cache:
        return analysis_cache[cache_key]
    
    # Clone repository to temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Clone repository
            repo_name = repo_url.split("/")[-1]
            clone_dir = os.path.join(temp_dir, repo_name)
            
            # Use subprocess to clone
            import subprocess
            result = subprocess.run(
                ["git", "clone", f"https://github.com/{repo_url}", clone_dir, "--depth", "1"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise HTTPException(status_code=400, detail=f"Failed to clone repository: {result.stderr}")
            
            # Analyze codebase
            analysis_result = analyze_codebase(clone_dir, language, max_depth)
            
            # Remove large data if not requested
            if not include_visualizations:
                if "dependency_graph" in analysis_result:
                    del analysis_result["dependency_graph"]
                if "call_graph" in analysis_result:
                    del analysis_result["call_graph"]
            
            # Cache result
            analysis_cache[cache_key] = analysis_result
            
            return analysis_result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error analyzing repository: {str(e)}")

@app.post("/analyze/local")
async def analyze_local_repo(
    file: UploadFile = File(...),
    language: LanguageType = LanguageType.AUTO,
    include_visualizations: bool = False,
    max_depth: int = Query(default=3, ge=1, le=10)
):
    """Analyze a local codebase (uploaded as a zip file)"""
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Check file size
            file_size = 0
            chunk_size = 1024 * 1024  # 1MB
            zip_path = os.path.join(temp_dir, "repo.zip")
            
            with open(zip_path, "wb") as f:
                while chunk := await file.read(chunk_size):
                    file_size += len(chunk)
                    if file_size > MAX_REPO_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail=f"File too large. Maximum size is {MAX_REPO_SIZE / (1024 * 1024)}MB"
                        )
                    f.write(chunk)
            
            # Extract zip file
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Analyze codebase
            analysis_result = analyze_codebase(extract_dir, language, max_depth)
            
            # Remove large data if not requested
            if not include_visualizations:
                if "dependency_graph" in analysis_result:
                    del analysis_result["dependency_graph"]
                if "call_graph" in analysis_result:
                    del analysis_result["call_graph"]
            
            return analysis_result
            
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid zip file")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error analyzing codebase: {str(e)}")

@app.get("/visualize/{repo_url:path}/{visualization_type}")
async def visualize_repo(
    repo_url: str,
    visualization_type: VisualizationType,
    language: LanguageType = LanguageType.AUTO,
    format: str = Query(default="json", regex="^(json|html|svg)$")
):
    """Generate a visualization of the codebase"""
    # Check cache
    cache_key = f"{repo_url}:{language}:3"  # Use default depth
    
    if cache_key not in analysis_cache:
        # Analyze repository first
        await analyze_repo(repo_url, language, True, 3)
    
    analysis_result = analysis_cache[cache_key]
    
    if visualization_type == VisualizationType.DEPENDENCY_GRAPH:
        graph_data = analysis_result.get("dependency_graph", {})
    elif visualization_type == VisualizationType.CALL_GRAPH:
        graph_data = analysis_result.get("call_graph", {})
    else:
        # For other visualization types, we need to generate them
        raise HTTPException(status_code=501, detail=f"Visualization type {visualization_type} not implemented yet")
    
    if format == "json":
        return graph_data
    else:
        # For other formats, we would generate the appropriate visualization
        raise HTTPException(status_code=501, detail=f"Format {format} not implemented yet")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("api:app", host=HOST, port=PORT, reload=True)

