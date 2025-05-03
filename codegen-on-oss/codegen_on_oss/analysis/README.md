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

- **DiffAnalyzer**: Class for analyzing differences between codebase snapshots

- **CommitAnalyzer**: Class for analyzing commits by comparing snapshots

- **SWEHarnessAgent**: Harness for a Software Engineering agent that analyzes commits and PRs

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

```python
from codegen_on_oss.analysis.analysis import CodeAnalyzer

# Create analyzer instance
analyzer = CodeAnalyzer(codebase)

# Analyze a commit
analysis_results = analyzer.analyze_commit(base_commit="abc123", head_commit="def456", github_token="your_github_token")

# Print the results
print(f"Is properly implemented: {analysis_results['quality_assessment']['is_properly_implemented']}")
print(f"Quality score: {analysis_results['quality_assessment']['score']}")
print(f"Overall assessment: {analysis_results['quality_assessment']['overall_assessment']}")
```

### PR Analysis

```python
from codegen_on_oss.analysis.analysis import CodeAnalyzer

# Create analyzer instance
analyzer = CodeAnalyzer(codebase)

# Analyze a PR
analysis_results = analyzer.analyze_pull_request(pr_number=123, github_token="your_github_token")

# Print the results
print(f"Is properly implemented: {analysis_results['quality_assessment']['is_properly_implemented']}")
print(f"Quality score: {analysis_results['quality_assessment']['score']}")
print(f"Overall assessment: {analysis_results['quality_assessment']['overall_assessment']}")
```

### SWE Harness Agent

```python
from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent

# Create a SWE harness agent
swe_agent = SWEHarnessAgent(github_token="your_github_token")

# Analyze a PR
results = swe_agent.analyze_pull_request("owner/repo", pr_number=123)
print(results)

# Analyze a commit
results = swe_agent.analyze_commit("owner/repo", base_commit="abc123", head_commit="def456")
print(results)

# Analyze and comment on a PR
results = swe_agent.analyze_and_comment_on_pr("owner/repo", pr_number=123, post_comment=True)
print(results)
```

### Web API

The module provides functionality for analyzing and comparing commits:

```python
from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.analysis.commit_analysis import CommitAnalyzer

# Method 1: Analyze a commit from a repository URL and commit hash
result = CodeAnalyzer.analyze_commit_from_repo_and_commit(repo_url="https://github.com/owner/repo", commit_hash="abc123")
print(result.get_summary())

# Method 2: Analyze a commit by comparing two local repository paths
analyzer = CommitAnalyzer.from_paths(original_path="/path/to/original/repo", commit_path="/path/to/commit/repo")
result = analyzer.analyze_commit()
print(result.get_summary())

# Method 3: Analyze a commit by comparing two codebases
original_codebase = Codebase.from_directory("/path/to/original/repo")
commit_codebase = Codebase.from_directory("/path/to/commit/repo")

analyzer = CommitAnalyzer(original_codebase=original_codebase, commit_codebase=commit_codebase)
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

### Commit and PR Analysis

- Compare codebases before and after changes
- Analyze file, function, and class changes
- Identify high-risk changes
- Evaluate commit quality
- Determine if a commit is properly implemented

### Snapshot Integration

- Create and compare codebase snapshots
- Analyze differences between snapshots
- Track changes over time

## Integration with Metrics

The Analysis Module is fully integrated with the CodeMetrics class, which provides:

- Cyclomatic complexity metrics
- Line-based metrics (LOC, LLOC, SLOC, comments)
- Maintainability index metrics
- Inheritance depth metrics
- Halstead complexity metrics

## Integration with Snapshot Module

The Analysis Module integrates with the Snapshot Module to:

- Create snapshots of codebases at specific commits
- Compare snapshots to analyze changes
- Track changes over time
- Analyze commits and PRs

## Example

See `example.py` for a demonstration of the basic analysis functionality and `swe_harness_example.py` for a demonstration of the commit and PR analysis functionality.
