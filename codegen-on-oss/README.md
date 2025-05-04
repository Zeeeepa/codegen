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

## Public API

Codegen-on-OSS provides a clean, well-documented public API for interacting with the component. The main entry point is the `CodegenOnOSS` class:

```python
from codegen_on_oss.api import CodegenOnOSS

# Initialize the API
codegen = CodegenOnOSS()

# Parse a repository
repo_data = codegen.parse_repository("https://github.com/org/repo")

# Analyze the codebase
analysis = codegen.analyze_codebase(repo_data)

# Create a snapshot
snapshot_id = codegen.create_snapshot(repo_data)
```

For convenience, you can also import individual functions:

```python
from codegen_on_oss.api import parse_repository, analyze_codebase

# Parse a repository
repo_data = parse_repository("https://github.com/org/repo")

# Analyze the codebase
analysis = analyze_codebase(repo_data)
```

### Helper Functions

The component also provides helper functions for common tasks:

```python
from codegen_on_oss.helpers import analyze_repository, batch_analyze_repositories

# Analyze a single repository
results = analyze_repository(
    "https://github.com/org/repo",
    output_path="results.json",
    include_integrity=True
)

# Analyze multiple repositories
batch_results = batch_analyze_repositories(
    ["https://github.com/org/repo1", "https://github.com/org/repo2"],
    output_dir="results",
    include_integrity=True
)
```

## Key Features

### Repository Parsing

Parse repositories to extract their structure, including files, directories, and language information:

```python
repo_data = codegen.parse_repository(
    "https://github.com/org/repo",
    branch="main",
    include_patterns=["*.py", "*.js"],
    exclude_patterns=["node_modules/*", "venv/*"]
)
```

### Codebase Analysis

Analyze codebases to extract insights about their structure, dependencies, and quality:

```python
analysis = codegen.analyze_codebase(
    repo_data,
    analysis_type="full"  # Options: "full", "quick", "dependencies"
)
```

### Code Integrity Analysis

Analyze code integrity based on predefined or custom rules:

```python
integrity_results = codegen.analyze_code_integrity(
    repo_data,
    rules=[
        {"type": "complexity", "max_value": 10},
        {"type": "line_length", "max_value": 100}
    ]
)
```

### Commit Analysis

Analyze specific commits to understand their impact:

```python
commit_analysis = codegen.analyze_commit(
    "https://github.com/org/repo",
    commit_hash="abc123..."
)
```

### Diff Analysis

Analyze the differences between two references (commits, branches, tags):

```python
diff_analysis = codegen.analyze_diff(
    "https://github.com/org/repo",
    base_ref="main",
    head_ref="feature-branch"
)
```

### Snapshots

Create and compare snapshots of repositories:

```python
# Create snapshots
snapshot_id_1 = codegen.create_snapshot(repo_data_1, snapshot_name="before")
snapshot_id_2 = codegen.create_snapshot(repo_data_2, snapshot_name="after")

# Compare snapshots
comparison = codegen.compare_snapshots(snapshot_id_1, snapshot_id_2)
```

## Examples

For more detailed examples, see the [codegen-examples](https://github.com/Zeeeepa/codegen/tree/develop/codegen-examples) directory, which includes:

- Repository analysis examples
- Code integrity checking
- Dependency analysis
- Snapshot comparison

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](https://github.com/Zeeeepa/codegen/blob/develop/CONTRIBUTING.md) for details.

## License

This project is licensed under the terms of the license included in the [LICENSE](https://github.com/Zeeeepa/codegen/blob/develop/LICENSE) file.
