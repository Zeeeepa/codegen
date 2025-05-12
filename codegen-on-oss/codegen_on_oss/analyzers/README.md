# Analyzers Package

This package provides tools for analyzing and modifying code during analysis.

## Transaction Manager

The `transaction_manager.py` module provides a transaction manager for handling code modifications during analysis. It's responsible for queuing, sorting, and committing transactions in a controlled manner.

### Key Features

- **Transaction Queuing**: Queue up code modifications to be applied later
- **Transaction Sorting**: Sort transactions by priority and position
- **Conflict Resolution**: Detect and resolve conflicts between transactions
- **Transaction Limits**: Set limits on the number of transactions and execution time
- **Bulk Commits**: Commit multiple transactions at once
- **Undo Support**: Revert transactions if needed

### Usage Example

```python
from codegen_on_oss.analyzers.transaction_manager import TransactionManager
from codegen_on_oss.analyzers.transactions import EditTransaction

# Create a transaction manager
manager = TransactionManager()

# Set limits
manager.set_max_transactions(100)  # Limit to 100 transactions
manager.reset_stopwatch(5)  # Limit to 5 seconds

# Create a transaction
transaction = EditTransaction(start_byte=10, end_byte=20, file=file_obj, new_content="new code")

# Add the transaction to the queue
manager.add_transaction(transaction)

# Commit all transactions
files_to_commit = manager.to_commit()
diffs = manager.commit(files_to_commit)

# Or apply a single transaction immediately
manager.apply(transaction)

# Or apply all transactions at once
diffs = manager.apply_all()

# Revert all transactions
manager.revert_all()
```

### Transaction Types

The following transaction types are supported:

- **EditTransaction**: Replace content in a file
- **InsertTransaction**: Insert content at a specific position
- **RemoveTransaction**: Remove content from a file
- **FileAddTransaction**: Add a new file
- **FileRenameTransaction**: Rename a file
- **FileRemoveTransaction**: Remove a file

### Error Handling

The transaction manager can raise the following exceptions:

- **MaxTransactionsExceeded**: Raised when the number of transactions exceeds the limit
- **MaxPreviewTimeExceeded**: Raised when the execution time exceeds the limit
- **TransactionError**: Raised when there's a conflict between transactions

### Integration with Analyzers

The transaction manager is designed to be used with the analyzers package to provide a consistent way to modify code during analysis. It can be integrated with other components of the analyzers package to provide a complete code analysis and modification solution.

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
call_graph = api.get_function_call_graph(function_name="main", depth=3, format="json")

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
from codegen_on_oss.analyzers.api import api_analyze_codebase, api_analyze_pr, api_get_visualization, api_get_static_errors

app = Flask(__name__)


@app.route("/api/analyze/codebase", methods=["POST"])
def analyze_codebase():
    data = request.json
    result = api_analyze_codebase(repo_path=data.get("repo_path"), analysis_types=data.get("analysis_types"))
    return jsonify(result)


@app.route("/api/analyze/pr", methods=["POST"])
def analyze_pr():
    data = request.json
    result = api_analyze_pr(repo_path=data.get("repo_path"), pr_number=data.get("pr_number"))
    return jsonify(result)


@app.route("/api/visualize", methods=["POST"])
def visualize():
    data = request.json
    result = api_get_visualization(repo_path=data.get("repo_path"), viz_type=data.get("viz_type"), params=data.get("params", {}))
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

