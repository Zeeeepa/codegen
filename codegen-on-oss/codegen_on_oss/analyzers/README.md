# CodeGen Analyzer

The CodeGen Analyzer module provides comprehensive static analysis capabilities for codebases, focusing on code quality, dependencies, structure, and visualization. It serves as a backend API that can be used by frontend applications to analyze repositories.

## Architecture

The analyzer system is built with a modular plugin-based architecture:

```
analyzers/
├── api.py                  # Main API endpoints for frontend integration
├── analyzer.py             # Plugin-based analyzer system
├── issues.py               # Issue tracking and management
├── code_quality.py         # Code quality analysis
├── dependencies.py         # Dependency analysis
├── models/
│   └── analysis_result.py  # Data models for analysis results
├── context/                # Code context management
├── visualization/          # Visualization support
└── resolution/             # Issue resolution tools
```

## Core Components

### 1. API Interface (`api.py`)

The main entry point for frontend applications. Provides REST-like endpoints for:
- Codebase analysis
- PR analysis
- Dependency visualization
- Issue reporting
- Code quality assessment

### 2. Analyzer System (`analyzer.py`)

Plugin-based system that coordinates different types of analysis:
- Code quality analysis (complexity, maintainability)
- Dependency analysis (imports, cycles, coupling)
- PR impact analysis
- Type checking and error detection

### 3. Issue Tracking (`issues.py`)

Comprehensive issue model with:
- Severity levels (critical, error, warning, info)
- Categories (dead code, complexity, dependency, etc.)
- Location information and suggestions
- Filtering and grouping capabilities

### 4. Dependency Analysis (`dependencies.py`)

Analysis of codebase dependencies:
- Import dependencies between modules
- Circular dependency detection
- Module coupling analysis
- External dependencies tracking
- Call graphs and class hierarchies

### 5. Code Quality Analysis (`code_quality.py`)

Analysis of code quality aspects:
- Dead code detection (unused functions, variables)
- Complexity metrics (cyclomatic, cognitive)
- Parameter checking (types, usage)
- Style issues and maintainability

## Using the API

### Setup

```python
from codegen_on_oss.analyzers.api import CodegenAnalyzerAPI

# Create API instance with repository
api = CodegenAnalyzerAPI(repo_path="/path/to/repo")
# OR
api = CodegenAnalyzerAPI(repo_url="https://github.com/owner/repo")
```

### Analyzing a Codebase

```python
# Run comprehensive analysis
results = api.analyze_codebase()

# Run specific analysis types
results = api.analyze_codebase(analysis_types=["code_quality", "dependency"])

# Force refresh of cached analysis
results = api.analyze_codebase(force_refresh=True)
```

### Analyzing a PR

```python
# Analyze a specific PR
pr_results = api.analyze_pr(pr_number=123)

# Get PR impact visualization
impact_viz = api.get_pr_impact(pr_number=123, format="json")
```

### Getting Issues

```python
# Get all issues
all_issues = api.get_issues()

# Get issues by severity
critical_issues = api.get_issues(severity="critical")
error_issues = api.get_issues(severity="error")

# Get issues by category
dependency_issues = api.get_issues(category="dependency_cycle")
```

### Getting Visualizations

```python
# Get module dependency graph
module_deps = api.get_module_dependencies(format="json")

# Get function call graph
call_graph = api.get_function_call_graph(
    function_name="main", 
    depth=3,
    format="json"
)

# Export visualization to file
api.export_visualization(call_graph, format="html", filename="call_graph.html")
```

### Common Analysis Patterns

```python
# Find dead code
api.analyze_codebase(analysis_types=["code_quality"])
dead_code = api.get_issues(category="dead_code")

# Find circular dependencies
api.analyze_codebase(analysis_types=["dependency"])
circular_deps = api.get_circular_dependencies()

# Find parameter issues
api.analyze_codebase(analysis_types=["code_quality"])
param_issues = api.get_parameter_issues()
```

## REST API Endpoints

The analyzer can be exposed as REST API endpoints for integration with frontend applications:

### Codebase Analysis

```
POST /api/analyze/codebase
{
  "repo_path": "/path/to/repo",
  "analysis_types": ["code_quality", "dependency"]
}
```

### PR Analysis

```
POST /api/analyze/pr
{
  "repo_path": "/path/to/repo",
  "pr_number": 123
}
```

### Visualization

```
POST /api/visualize
{
  "repo_path": "/path/to/repo",
  "viz_type": "module_dependencies",
  "params": {
    "layout": "hierarchical",
    "format": "json"
  }
}
```

### Issues

```
GET /api/issues?severity=error&category=dependency_cycle
```

## Implementation Example

For a web application exposing these endpoints with Flask:

```python
from flask import Flask, request, jsonify
from codegen_on_oss.analyzers.api import (
    api_analyze_codebase,
    api_analyze_pr,
    api_get_visualization,
    api_get_static_errors
)

app = Flask(__name__)

@app.route("/api/analyze/codebase", methods=["POST"])
def analyze_codebase():
    data = request.json
    result = api_analyze_codebase(
        repo_path=data.get("repo_path"),
        analysis_types=data.get("analysis_types")
    )
    return jsonify(result)

@app.route("/api/analyze/pr", methods=["POST"])
def analyze_pr():
    data = request.json
    result = api_analyze_pr(
        repo_path=data.get("repo_path"),
        pr_number=data.get("pr_number")
    )
    return jsonify(result)

@app.route("/api/visualize", methods=["POST"])
def visualize():
    data = request.json
    result = api_get_visualization(
        repo_path=data.get("repo_path"),
        viz_type=data.get("viz_type"),
        params=data.get("params", {})
    )
    return jsonify(result)

@app.route("/api/issues", methods=["GET"])
def get_issues():
    repo_path = request.args.get("repo_path")
    severity = request.args.get("severity")
    category = request.args.get("category")
    
    api = create_api(repo_path=repo_path)
    return jsonify(api.get_issues(severity=severity, category=category))

if __name__ == "__main__":
    app.run(debug=True)
```