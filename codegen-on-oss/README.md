# Codegen-on-OSS

A modular pipeline for collecting, parsing, and analyzing code repositories.

## Overview

Codegen-on-OSS is a component that provides tools for:

- Collecting repository URLs from different sources
- Parsing repositories using the Codegen tool
- Profiling performance and logging metrics
- Providing analysis capabilities for code validation and PR analysis
- Including snapshot functionality for comparing codebases

## Installation

```bash
pip install codegen-on-oss
```

Or install from source:

```bash
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/codegen-on-oss
pip install -e .
```

## Unified API

Codegen-on-OSS provides a clean, well-documented unified API for interacting with the component:

```python
from codegen_on_oss.api import analyze_repository, analyze_commit, analyze_pull_request

# Analyze a repository
repo_results = analyze_repository(
    repo_url="https://github.com/org/repo",
    include_integrity=True
)

# Analyze a commit
commit_results = analyze_commit(
    repo_url="https://github.com/org/repo",
    commit_hash="abc123..."
)

# Analyze a PR
pr_results = analyze_pull_request(
    repo_url="https://github.com/org/repo",
    pr_number=123,
    github_token="your_github_token"
)
```

For more details, see the [API documentation](./codegen_on_oss/api/README.md).

## Key Features

### Repository Parsing

Parse repositories to extract their structure, including files, directories, and language information:

```python
from codegen_on_oss.api import analyze_repository

repo_data = analyze_repository(
    "https://github.com/org/repo",
    branch="main",
    include_integrity=True
)
```

### Codebase Analysis

Analyze codebases to extract insights about their structure, dependencies, and quality:

```python
from codegen_on_oss.api import analyze_repository

analysis = analyze_repository(
    "https://github.com/org/repo",
    include_integrity=True
)

print(f"Files: {analysis['summary']['file_count']}")
print(f"Functions: {analysis['summary']['function_count']}")
print(f"Classes: {analysis['summary']['class_count']}")
print(f"Average Complexity: {analysis['complexity']['average_complexity']}")
```

### Code Integrity Analysis

Analyze code integrity based on predefined or custom rules:

```python
from codegen_on_oss.api import analyze_code_integrity

integrity_results = analyze_code_integrity(
    "https://github.com/org/repo",
    rules=[
        {"type": "complexity", "max_value": 10},
        {"type": "line_length", "max_value": 100}
    ]
)

print(f"Issues Found: {len(integrity_results['issues'])}")
```

### Commit Analysis

Analyze specific commits to understand their impact:

```python
from codegen_on_oss.api import analyze_commit

commit_analysis = analyze_commit(
    "https://github.com/org/repo",
    commit_hash="abc123..."
)

print(f"Is properly implemented: {commit_analysis['quality_assessment']['is_properly_implemented']}")
print(f"Quality score: {commit_analysis['quality_assessment']['score']}")
```

### Diff Analysis

Analyze the differences between two references (commits, branches, tags):

```python
from codegen_on_oss.api import compare_branches

diff_analysis = compare_branches(
    "https://github.com/org/repo",
    base_branch="main",
    head_branch="feature-branch"
)

print(f"Files added: {len(diff_analysis['changes']['files_added'])}")
print(f"Files modified: {len(diff_analysis['changes']['files_modified'])}")
```

### Snapshots

Create and compare snapshots of repositories:

```python
from codegen_on_oss.api import create_snapshot, compare_snapshots

# Create snapshots
snapshot_id_1 = create_snapshot(
    "https://github.com/org/repo",
    branch="main",
    snapshot_name="before"
)

snapshot_id_2 = create_snapshot(
    "https://github.com/org/repo",
    branch="feature",
    snapshot_name="after"
)

# Compare snapshots
comparison = compare_snapshots(snapshot_id_1, snapshot_id_2)
```

## Examples

For more detailed examples, see the [codegen-examples](https://github.com/Zeeeepa/codegen/tree/develop/codegen-examples) directory, which includes:

- Repository analysis examples
- Code integrity checking
- Dependency analysis
- Snapshot comparison

## CLI Usage

The package also provides a command-line interface for parsing repositories:

```bash
# Parse one repository
cgparse run-one --repo-url https://github.com/org/repo

# Parse multiple repositories from a source
cgparse run --source csv --csv-file repos.csv
```

## Running on Modal

For cloud-based parsing, you can use the Modal integration:

```bash
# Run on Modal with CSV input
modal run codegen_modal_run.py --source csv --csv-file input.csv

# Run on Modal with a single repository
modal run codegen_modal_run.py --source single --single-url https://github.com/org/repo
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
