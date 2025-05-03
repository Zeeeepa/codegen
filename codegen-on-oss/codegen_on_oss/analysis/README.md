# Analysis Module

The Analysis Module integrates various specialized analysis components into a comprehensive system for analyzing codebases.

## Features

- Comprehensive code analysis
- Code quality metrics
- Import analysis
- Symbol attribution
- Visualization of module dependencies
- Comprehensive code quality metrics
- Commit analysis and comparison
- Repository and PR/Branch/Commit comparison

## Components

The module consists of the following key components:

- **CodeAnalyzer**: Central class that orchestrates all analysis functionality
- **CommitAnalyzer**: Class for analyzing and comparing commits
- **Metrics Integration**: Connection with the CodeMetrics class for comprehensive metrics
- **Import Analysis**: Tools for analyzing import relationships and cycles
- **Documentation Tools**: Functions for generating documentation for code
- **Server**: FastAPI server for analyzing repositories, commits, branches, and PRs

## Usage

### Basic Analysis

```python
from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer

# Create a codebase from a directory
codebase = Codebase.from_directory("/path/to/repo")

# Create an analyzer
analyzer = CodeAnalyzer(codebase)

# Get a summary of the codebase
summary = analyzer.get_codebase_summary()
print(summary)

# Analyze complexity
complexity = analyzer.analyze_complexity()
print(complexity)

# Analyze imports
imports = analyzer.analyze_imports()
print(imports)
```

### Metrics

```python
from codegen import Codebase
from codegen_on_oss.analysis.metrics import CodeMetrics

# Create a codebase from a directory
codebase = Codebase.from_directory("/path/to/repo")

# Create a metrics instance
metrics = CodeMetrics(codebase)

# Calculate all metrics
all_metrics = metrics.calculate_all_metrics()
print(all_metrics)

# Get code quality summary
quality_summary = metrics.get_code_quality_summary()
print(quality_summary)
```

### Commit Analysis

The module provides functionality for analyzing and comparing commits:

```python
from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.analysis.commit_analysis import CommitAnalyzer

# Method 1: Analyze a commit from a repository URL and commit hash
result = CodeAnalyzer.analyze_commit_from_repo_and_commit(
    repo_url="https://github.com/owner/repo",
    commit_hash="abc123"
)
print(result.get_summary())

# Method 2: Analyze a commit by comparing two local repository paths
analyzer = CommitAnalyzer.from_paths(
    original_path="/path/to/original/repo",
    commit_path="/path/to/commit/repo"
)
result = analyzer.analyze_commit()
print(result.get_summary())

# Method 3: Analyze a commit by comparing two codebases
original_codebase = Codebase.from_directory("/path/to/original/repo")
commit_codebase = Codebase.from_directory("/path/to/commit/repo")

analyzer = CommitAnalyzer(
    original_codebase=original_codebase,
    commit_codebase=commit_codebase
)
result = analyzer.analyze_commit()
print(result.get_summary())
```

### Analysis Server

The module provides a FastAPI server for analyzing repositories, commits, branches, and PRs:

```python
from codegen_on_oss.analysis.server import run_server

# Start the server
run_server(host="0.0.0.0", port=8000)
```

You can then make requests to the server:

```bash
# Analyze a repository
curl -X POST http://localhost:8000/analyze_repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/owner/repo"}'

# Analyze a commit
curl -X POST http://localhost:8000/analyze_commit \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/owner/repo", "commit_hash": "abc123"}'

# Compare branches
curl -X POST http://localhost:8000/compare_branches \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/owner/repo", "base_branch": "main", "compare_branch": "feature"}'

# Analyze a PR
curl -X POST http://localhost:8000/analyze_pr \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/owner/repo", "pr_number": 123}'
```

### Web API

The module also provides a FastAPI web interface for analyzing repositories:

```python
from codegen_on_oss.analysis.analysis import app
import uvicorn

# Run the FastAPI app
uvicorn.run(app, host="0.0.0.0", port=8000)
```

Then you can make POST requests to `/analyze_repo` with a JSON body:

```json
{
  "repo_url": "https://github.com/owner/repo"
}
```

## Capabilities

### Code Analysis

- Analyze code complexity
- Identify complex functions
- Find import cycles
- Find central files
- Identify dependency cycles

### Commit Analysis

- Compare two versions of a codebase
- Identify added, modified, and removed files
- Analyze code complexity changes
- Detect potential issues in commits
- Generate detailed reports on commit quality

### Repository and PR Analysis

- Compare branches in a repository
- Analyze pull requests
- Determine if a PR/commit is properly implemented
- Identify issues in PRs/commits
- Generate detailed reports on PR/commit quality

## Integration with Metrics

The Analysis Module is fully integrated with the CodeMetrics class, which provides:

- Cyclomatic complexity metrics
- Line-based metrics (LOC, LLOC, SLOC, comments)
- Maintainability index metrics
- Inheritance depth metrics
- Halstead complexity metrics

## Examples

See `example.py` for a complete demonstration of the analysis module's capabilities.

For commit analysis examples, see `commit_example.py`.

For server examples, see `server_example.py`.
