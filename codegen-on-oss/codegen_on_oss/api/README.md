# Unified API for codegen-on-oss

This module provides a unified API for interacting with the codegen-on-oss package, making it easier to use the various components for code analysis, snapshot management, and code integrity validation.

## Overview

The Unified API simplifies the use of codegen-on-oss by providing:

- A consistent interface for all analysis operations
- Convenience functions for common tasks
- Simplified error handling and result formatting
- Integration with all codegen-on-oss components

## Usage

### Basic Repository Analysis

```python
from codegen_on_oss.api.unified_api import analyze_repository

# Analyze a repository
results = analyze_repository(
    repo_url="https://github.com/username/repo",
    output_path="results.json",
    include_integrity=True,
    github_token="your-github-token",  # Optional
)

# Print a summary of the results
print(f"Files: {results['summary']['file_count']}")
print(f"Functions: {results['summary']['function_count']}")
print(f"Classes: {results['summary']['class_count']}")
print(f"Average Complexity: {results['complexity']['average_complexity']}")
```

### Commit Analysis

```python
from codegen_on_oss.api.unified_api import analyze_commit

# Analyze a commit
results = analyze_commit(
    repo_url="https://github.com/username/repo",
    commit_hash="abc123",
    base_commit="def456",  # Optional
    output_path="commit_analysis.json",
    github_token="your-github-token",  # Optional
)

# Print a summary of the results
print(f"Is Properly Implemented: {results['quality_assessment']['is_properly_implemented']}")
print(f"Score: {results['quality_assessment']['score']}")
print(f"Overall Assessment: {results['quality_assessment']['overall_assessment']}")
```

### Pull Request Analysis

```python
from codegen_on_oss.api.unified_api import analyze_pull_request

# Analyze a pull request
results = analyze_pull_request(
    repo_url="https://github.com/username/repo",
    pr_number=123,
    output_path="pr_analysis.json",
    github_token="your-github-token",  # Required for PR analysis
)

# Print a summary of the results
print(f"Is Properly Implemented: {results['quality_assessment']['is_properly_implemented']}")
print(f"Score: {results['quality_assessment']['score']}")
print(f"Overall Assessment: {results['quality_assessment']['overall_assessment']}")
```

### Branch Comparison

```python
from codegen_on_oss.api.unified_api import compare_branches

# Compare two branches
results = compare_branches(
    repo_url="https://github.com/username/repo",
    base_branch="main",
    head_branch="feature",
    output_path="branch_comparison.json",
    github_token="your-github-token",  # Optional
)

# Print a summary of the results
print(f"Summary: {results['summary']}")
print(f"Files Added: {len(results['changes']['files_added'])}")
print(f"Files Modified: {len(results['changes']['files_modified'])}")
print(f"Files Removed: {len(results['changes']['files_removed'])}")
```

### Snapshot Management

```python
from codegen_on_oss.api.unified_api import create_snapshot, compare_snapshots

# Create snapshots
snapshot_id_1 = create_snapshot(
    repo_url="https://github.com/username/repo",
    branch="main",
    snapshot_name="main-snapshot",
    output_path="main_snapshot.json",
    github_token="your-github-token",  # Optional
)

snapshot_id_2 = create_snapshot(
    repo_url="https://github.com/username/repo",
    branch="feature",
    snapshot_name="feature-snapshot",
    output_path="feature_snapshot.json",
    github_token="your-github-token",  # Optional
)

# Compare snapshots
results = compare_snapshots(
    snapshot_id_1="main_snapshot.json",
    snapshot_id_2="feature_snapshot.json",
    output_path="snapshot_comparison.json",
    github_token="your-github-token",  # Optional
)
```

### Code Integrity Analysis

```python
from codegen_on_oss.api.unified_api import analyze_code_integrity

# Define custom rules
rules = [
    {"type": "complexity", "max_value": 10},
    {"type": "line_length", "max_value": 100},
    {"type": "function_length", "max_value": 50},
]

# Analyze code integrity
results = analyze_code_integrity(
    repo_url="https://github.com/username/repo",
    rules=rules,
    output_path="code_integrity.json",
    github_token="your-github-token",  # Optional
)

# Print a summary of the results
print(f"Issues Found: {len(results['issues'])}")
print(f"Summary: {results['summary']}")
```

### Batch Analysis

```python
from codegen_on_oss.api.unified_api import batch_analyze_repositories

# Analyze multiple repositories
results = batch_analyze_repositories(
    repo_urls=[
        "https://github.com/username/repo1",
        "https://github.com/username/repo2",
        "https://github.com/username/repo3",
    ],
    output_dir="analysis_results",
    include_integrity=True,
    github_token="your-github-token",  # Optional
)

# Print a summary of the results
for repo_url, result in results.items():
    if "error" in result:
        print(f"{repo_url}: Error - {result['error']}")
    else:
        print(f"{repo_url}: {result['summary']['file_count']} files, {result['summary']['function_count']} functions")
```

## Using the UnifiedAPI Class

For more control, you can use the `UnifiedAPI` class directly:

```python
from codegen_on_oss.api.unified_api import UnifiedAPI

# Initialize the API
api = UnifiedAPI(github_token="your-github-token")  # Optional

# Analyze a repository
repo_results = api.analyze_repository(
    repo_url="https://github.com/username/repo",
    output_path="results.json",
    include_integrity=True,
)

# Analyze a commit
commit_results = api.analyze_commit(
    repo_url="https://github.com/username/repo",
    commit_hash="abc123",
    base_commit="def456",  # Optional
    output_path="commit_analysis.json",
)

# Analyze a pull request
pr_results = api.analyze_pull_request(
    repo_url="https://github.com/username/repo",
    pr_number=123,
    output_path="pr_analysis.json",
)
```

## API Reference

### Convenience Functions

- `analyze_repository(repo_url, branch=None, commit=None, output_path=None, include_integrity=False, github_token=None)`
- `analyze_commit(repo_url, commit_hash, base_commit=None, output_path=None, github_token=None)`
- `analyze_pull_request(repo_url, pr_number, output_path=None, github_token=None)`
- `compare_branches(repo_url, base_branch, head_branch, output_path=None, github_token=None)`
- `create_snapshot(repo_url, branch=None, commit=None, snapshot_name=None, output_path=None, github_token=None)`
- `compare_snapshots(snapshot_id_1, snapshot_id_2, output_path=None, github_token=None)`
- `analyze_code_integrity(repo_url, branch=None, commit=None, rules=None, output_path=None, github_token=None)`
- `batch_analyze_repositories(repo_urls, output_dir=None, include_integrity=False, github_token=None)`

### UnifiedAPI Class

- `__init__(github_token=None)`
- `analyze_repository(repo_url, branch=None, commit=None, output_path=None, include_integrity=False)`
- `analyze_commit(repo_url, commit_hash, base_commit=None, output_path=None)`
- `analyze_pull_request(repo_url, pr_number, output_path=None)`
- `compare_branches(repo_url, base_branch, head_branch, output_path=None)`
- `create_snapshot(repo_url, branch=None, commit=None, snapshot_name=None, output_path=None)`
- `compare_snapshots(snapshot_id_1, snapshot_id_2, output_path=None)`
- `analyze_code_integrity(repo_url, branch=None, commit=None, rules=None, output_path=None)`
- `batch_analyze_repositories(repo_urls, output_dir=None, include_integrity=False)`

