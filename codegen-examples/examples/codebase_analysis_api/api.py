import os
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import tempfile
import shutil
import zipfile
import networkx as nx
import plotly.graph_objects as go
from pathlib import Path
import time
import json
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
from codegen.sdk.codebase.codebase_analysis import get_codebase_summary, get_file_summary, get_class_summary, get_function_summary

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
            if not re.search(r'["\'].*#.*["\']', line[:comment_start]):
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
            file_stats = {
                "name": file.name,
                "type": "file",
                "language": file.language.name.lower() if hasattr(file, "language") else "unknown",
                "symbols": len(file.symbols),
                "classes": len(file.classes),
                "functions": len(file.functions),
                "lines": len(file.source.splitlines()) if hasattr(file, "source") else 0
            }
            
            # Add detailed class and function info for important files
            if file_stats["classes"] > 0 or file_stats["functions"] > 0:
                file_stats["details"] = []
                
                for cls in file.classes:
                    cls_info = {
                        "name": cls.name,
                        "type": "class",
                        "methods": len(cls.methods),
                        "attributes": len(cls.attributes),
                        "line": cls.start_point[0] + 1
                    }
                    
                    # Add method details
                    if cls.methods and current_depth < max_depth - 1:
                        cls_info["methods_details"] = []
                        for method in cls.methods:
                            method_info = {
                                "name": method.name,
                                "line": method.start_point[0] + 1,
                                "parameters": len(method.parameters)
                            }
                            cls_info["methods_details"].append(method_info)
                    
                    file_stats["details"].append(cls_info)
                
                for func in file.functions:
                    if not func.is_method:  # Skip methods as they're already covered in classes
                        func_info = {
                            "name": func.name,
                            "type": "function",
                            "line": func.start_point[0] + 1,
                            "parameters": len(func.parameters)
                        }
                        file_stats["details"].append(func_info)
            
            dir_node["children"].append(file_stats)
        
        # Recursively add subdirectories
        subdirs = [d for d in directories.keys() if Path(d).parent == Path(path) and d != path]
        for subdir in subdirs:
            add_directory(subdir, dir_node, current_depth + 1)
    
    # Start with root directories
    root_dirs = [d for d in directories.keys() if d == "." or "/" not in d and "\\" not in d]
    for root_dir in root_dirs:
        add_directory(root_dir, root)
    
    return root

def analyze_codebase(repo_url: str, language: LanguageType = LanguageType.AUTO) -> Dict[str, Any]:
    """Perform comprehensive analysis of a codebase"""
    start_time = time.time()
    
    # Determine language if AUTO
    lang = None
    if language != LanguageType.AUTO:
        lang = language
    
    # Load the codebase
    codebase = Codebase.from_repo(repo_url, language=lang)
    
    # Calculate overall statistics
    file_count = len(codebase.files)
    file_by_language = Counter([f.language.name.lower() if hasattr(f, "language") else "unknown" for f in codebase.files])
    total_lines = sum(len(f.source.splitlines()) if hasattr(f, "source") else 0 for f in codebase.files)
    
    # Find entry points
    entry_points = find_entry_points(codebase)
    
    # Build project tree
    project_tree = build_project_tree(codebase)
    
    # Find code quality issues
    unused_imports = find_unused_imports(codebase)
    unused_functions = find_unused_functions(codebase)
    unused_classes = find_unused_classes(codebase)
    complex_functions = find_high_complexity_functions(codebase)
    
    # Calculate complexity metrics
    callables = codebase.functions + [m for c in codebase.classes for m in c.methods]
    total_complexity = sum(calculate_cyclomatic_complexity(func) for func in callables if hasattr(func, "code_block"))
    avg_complexity = total_complexity / len(callables) if callables else 0
    
    # Prepare visualization options
    visualization_options = [v.value for v in VisualizationType]
    
    # Compile results
    results = {
        "overall_statistics": {
            "total_files": file_count,
            "files_by_language": dict(file_by_language),
            "total_lines_of_code": total_lines,
            "total_classes": len(codebase.classes),
            "total_functions": len(codebase.functions),
            "total_symbols": len(codebase.symbols),
            "average_cyclomatic_complexity": round(avg_complexity, 2)
        },
        "important_files": entry_points,
        "project_structure": project_tree,
        "code_quality_issues": {
            "unused_imports": {
                "count": len(unused_imports),
                "items": unused_imports[:100]  # Limit to 100 items
            },
            "unused_functions": {
                "count": len(unused_functions),
                "items": unused_functions[:100]
            },
            "unused_classes": {
                "count": len(unused_classes),
                "items": unused_classes[:100]
            },
            "high_complexity_functions": {
                "count": len(complex_functions),
                "items": complex_functions[:100]
            }
        },
        "visualization_options": visualization_options,
        "analysis_time": time.time() - start_time
    }
    
    return results

def generate_visualization(codebase: Codebase, viz_type: VisualizationType, target: Optional[str] = None) -> Dict[str, Any]:
    """Generate visualization data for the codebase"""
    if viz_type == VisualizationType.CALL_GRAPH:
        # Create call graph
        G = nx.DiGraph()
        
        # If target is specified, use it as the root node
        if target:
            parts = target.split(".")
            if len(parts) == 1:
                # Just a function name
                func = codebase.get_function(target)
            else:
                # Class.method
                cls = codebase.get_class(parts[0])
                func = cls.get_method(parts[1]) if cls else None
        else:
            # Use the first function with call sites as root
            funcs_with_calls = [f for f in codebase.functions if f.function_calls]
            func = funcs_with_calls[0] if funcs_with_calls else None
        
        if not func:
            return {"error": "No suitable function found for call graph"}
        
        # Build call graph
        def add_calls(function, depth=0, max_depth=3):
            if depth >= max_depth:
                return
            
            for call in function.function_calls:
                called_func = call.function_definition
                if called_func and isinstance(called_func, codegen.sdk.core.function.Function):
                    G.add_node(called_func.name, type="function")
                    G.add_edge(function.name, called_func.name)
                    add_calls(called_func, depth + 1, max_depth)
        
        G.add_node(func.name, type="function", root=True)
        add_calls(func)
        
        # Convert to JSON-serializable format
        return {
            "nodes": [{"id": n, "type": G.nodes[n].get("type", "function"), "root": G.nodes[n].get("root", False)} for n in G.nodes],
            "edges": [{"source": u, "target": v} for u, v in G.edges]
        }
    
    elif viz_type == VisualizationType.DEPENDENCY_GRAPH:
        # Create module dependency graph
        G = nx.DiGraph()
        
        # Group files by directory
        modules = defaultdict(list)
        for file in codebase.files:
            module_path = str(Path(file.filepath).parent)
            modules[module_path].append(file)
        
        # Add nodes for each module
        for module, files in modules.items():
            G.add_node(module, type="module", files=len(files))
        
        # Add edges based on imports
        for file in codebase.files:
            source_module = str(Path(file.filepath).parent)
            for import_stmt in file.import_statements:
                for imp in import_stmt.imports:
                    if hasattr(imp, "imported_symbol") and hasattr(imp.imported_symbol, "filepath"):
                        target_module = str(Path(imp.imported_symbol.filepath).parent)
                        if source_module != target_module and G.has_node(target_module):
                            G.add_edge(source_module, target_module)
        
        # Convert to JSON-serializable format
        return {
            "nodes": [{"id": n, "type": "module", "files": G.nodes[n].get("files", 0)} for n in G.nodes],
            "edges": [{"source": u, "target": v} for u, v in G.edges]
        }
    
    elif viz_type == VisualizationType.SYMBOL_TREE:
        # Create symbol hierarchy tree
        root = {"name": Path(codebase.repo_path).name, "type": "root", "children": []}
        
        # Add classes
        classes_node = {"name": "Classes", "type": "category", "children": []}
        for cls in codebase.classes:
            class_node = {
                "name": cls.name,
                "type": "class",
                "filepath": cls.filepath,
                "children": []
            }
            
            # Add methods
            for method in cls.methods:
                method_node = {
                    "name": method.name,
                    "type": "method",
                    "parameters": len(method.parameters)
                }
                class_node["children"].append(method_node)
            
            classes_node["children"].append(class_node)
        
        # Add functions
        functions_node = {"name": "Functions", "type": "category", "children": []}
        for func in codebase.functions:
            if not func.is_method:  # Skip methods as they're already covered in classes
                func_node = {
                    "name": func.name,
                    "type": "function",
                    "filepath": func.filepath,
                    "parameters": len(func.parameters)
                }
                functions_node["children"].append(func_node)
        
        root["children"].append(classes_node)
        root["children"].append(functions_node)
        
        return root
    
    elif viz_type == VisualizationType.INHERITANCE_HIERARCHY:
        # Create class inheritance hierarchy
        root = {"name": "Class Hierarchy", "type": "root", "children": []}
        
        # Find base classes (those without superclasses)
        base_classes = [cls for cls in codebase.classes if not cls.superclasses]
        
        # Build inheritance tree
        def add_subclasses(parent_node, parent_class):
            # Find all classes that inherit from this class
            subclasses = [cls for cls in codebase.classes if parent_class.name in cls.parent_class_names]
            
            for subcls in subclasses:
                subcls_node = {
                    "name": subcls.name,
                    "type": "class",
                    "filepath": subcls.filepath,
                    "methods": len(subcls.methods),
                    "children": []
                }
                parent_node["children"].append(subcls_node)
                add_subclasses(subcls_node, subcls)
        
        # Add each base class and its descendants
        for base_cls in base_classes:
            base_node = {
                "name": base_cls.name,
                "type": "class",
                "filepath": base_cls.filepath,
                "methods": len(base_cls.methods),
                "children": []
            }
            root["children"].append(base_node)
            add_subclasses(base_node, base_cls)
        
        return root
    
    else:
        return {"error": f"Visualization type {viz_type} not implemented"}

# API endpoints
@app.get("/analyze/{repo_url:path}")
async def analyze_repo(
    repo_url: str,
    language: LanguageType = LanguageType.AUTO,
    background_tasks: BackgroundTasks = None
):
    """Analyze a GitHub repository"""
    # Check cache
    cache_key = f"{repo_url}_{language}"
    if cache_key in analysis_cache:
        return JSONResponse(content=analysis_cache[cache_key])
    
    try:
        # Run analysis with timeout
        results = analyze_codebase(repo_url, language)
        
        # Cache results
        analysis_cache[cache_key] = results
        
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze/local")
async def analyze_local_repo(
    language: LanguageType = LanguageType.AUTO,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Analyze a local repository (uploaded as zip)"""
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Check file size
        file.file.seek(0, 2)  # Go to end of file
        file_size = file.file.tell()
        if file_size > MAX_REPO_SIZE:
            raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {MAX_REPO_SIZE/1024/1024}MB")
        file.file.seek(0)  # Go back to start
        
        # Save zip file
        zip_path = os.path.join(temp_dir, "repo.zip")
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Extract zip
        repo_dir = os.path.join(temp_dir, "repo")
        os.makedirs(repo_dir)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(repo_dir)
        
        # Run analysis
        codebase = Codebase(repo_dir, language=language)
        results = analyze_codebase(codebase)
        
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        # Clean up temp directory in background
        if background_tasks:
            background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)

@app.get("/visualize/{repo_url:path}/{visualization_type}")
async def visualize_repo(
    repo_url: str,
    visualization_type: VisualizationType,
    target: Optional[str] = Query(None, description="Target symbol for visualization (e.g., function name or Class.method)"),
    language: LanguageType = LanguageType.AUTO
):
    """Generate visualization for a repository"""
    try:
        # Load codebase
        codebase = Codebase.from_repo(repo_url, language=language)
        
        # Generate visualization
        viz_data = generate_visualization(codebase, visualization_type, target)
        
        return JSONResponse(content=viz_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("api:app", host=HOST, port=PORT, reload=True)

