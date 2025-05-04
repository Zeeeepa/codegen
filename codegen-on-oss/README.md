# Codegen on OSS

The **Codegen on OSS** package provides a modular pipeline for analyzing and processing open-source repositories. It offers comprehensive tools for repository parsing, code analysis, snapshot management, and quality assessment.

## Table of Contents
- [Core Features](#core-features)
- [Package Structure](#package-structure)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Running on Modal](#running-on-modal)
- [Code Analysis Usage](#code-analysis-usage)
- [Snapshot Usage](#snapshot-usage)
- [Code Integrity Analysis](#code-integrity-analysis)
- [Extensibility](#extensibility)
- [License](#license)

## Core Features

- **Repository Collection & Parsing**: Collect repository URLs from different sources and parse them using the Codegen tool
- **Performance Profiling**: Profile performance and log metrics for each parsing run
- **Code Analysis**: Analyze code quality, complexity, and structure
- **Snapshot Management**: Create, store, and compare snapshots of codebases
- **PR & Commit Analysis**: Analyze pull requests and commits for quality assessment
- **Server Backend**: Provide a WSL2 server backend for code validation, repository comparison, and PR analysis

## Package Structure

The package is composed of several modules:

### Sources Module

Defines the Repository source classes and settings:

- **Github Source**: Query repositories from GitHub based on language and heuristic
- **CSV Source**: Read repository URLs from CSV files

### Cache Module

Specifies the cache directory for storing repositories.

### CLI Module

Built with Click, provides commands for parsing repositories:

- `run-one`: Parse a single repository specified by URL
- `run`: Iterate over repositories from a selected source and parse each one

### Metrics Module

Provides profiling tools to measure performance during parsing:

- `MetricsProfiler`: Context manager for profiling sessions
- `MetricsProfile`: Records step-by-step metrics (clock duration, CPU time, memory usage)

### Parser Module

Contains the `CodegenParser` class that orchestrates the parsing process:

- Clone repositories or force pull if specified
- Initialize a `Codebase` from the Codegen tool
- Run post-initialization validation
- Integrate with the `MetricsProfiler` to log measurements

### Analysis Module

Provides comprehensive code analysis capabilities:

- **CodeAnalyzer**: Central class for orchestrating analysis functionality
- **DiffAnalyzer**: Analyze differences between codebase snapshots
- **CommitAnalyzer**: Analyze commits by comparing snapshots
- **SWEHarnessAgent**: Analyze commits and PRs
- **Code Integrity Analysis**: Detect code quality issues and potential errors
- **Server**: FastAPI server for analyzing repositories, commits, branches, and PRs ([WSL Server details](./codegen_on_oss/analysis/WSL_README.md))

### Snapshot Module

Enables capturing the state of a codebase at specific points in time:

- **CodebaseSnapshot**: Capture and store codebase state
- **SnapshotManager**: Manage creation, storage, and retrieval of snapshots
- **Event Handlers**: Integrate with GitHub events for automatic snapshot creation

## Installation

1. **Install the Package**

   You can install the package using pip:

   ```bash
   pip install codegen-on-oss
   ```

   Alternatively, you can install from source:

   ```bash
   git clone https://github.com/your-org/codegen-on-oss.git
   cd codegen-on-oss
   pip install -e .
   ```

2. **Configure the Repository Source**

   Decide whether you want to read from a CSV file or query GitHub:

   - For CSV, ensure your CSV file (default: `input.csv`) contains repository URLs in its first column and commit hash in the second column
   - For GitHub, configure settings via environment variables (`GITHUB_` prefix)

## Getting Started

1. **Run the Parser**

   Use the CLI to start parsing:

   ```bash
   # Parse one repository
   uv run cgparse run-one --help

   # Parse multiple repositories from a source
   uv run cgparse run --help
   ```

2. **Review Metrics and Logs**

   After parsing, check the CSV (default: `metrics.csv`) to review performance measurements per repository. Error logs are written to the specified error output file (default: `errors.log`)

## Running on Modal

```shell
$ uv run modal run modal_run.py
```

Codegen runs this parser on modal using the CSV source file `input.csv` tracked in this repository.

### Modal Configuration

- **Compute Resources**: Allocates 4 CPUs and 16GB of memory
- **Secrets & Volumes**: Uses secrets for bucket credentials and mounts a volume for caching repositories
- **Image Setup**: Builds on a Debian slim image with Python 3.12, installs required packages
- **Environment Configuration**: Environment variables are injected at runtime

### Bucket Storage

**Bucket (public):** [codegen-oss-parse](https://s3.amazonaws.com/codegen-oss-parse/)

The results of each run are saved under the version of `codegen` lib that the run installed and the source type it was run with.

## Code Analysis Usage

### Basic Analysis

```python
from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer

# Create a codebase from a directory
# This loads all files and parses them into a structured representation
codebase = Codebase.from_directory("/path/to/repo")

# Create an analyzer instance with the loaded codebase
# The analyzer provides various methods for code analysis
analyzer = CodeAnalyzer(codebase)

# Get a summary of the codebase
# This includes file counts, language distribution, and overall metrics
summary = analyzer.get_codebase_summary()
print(summary)

# Analyze code complexity
# This calculates cyclomatic complexity, cognitive complexity, and other metrics
complexity = analyzer.analyze_complexity()
print(complexity)

# Analyze imports and dependencies
# This identifies all imports and their relationships across the codebase
imports = analyzer.analyze_imports()
print(imports)
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

## Snapshot Usage

### Creating and Comparing Snapshots

```python
from codegen import Codebase
from codegen.configs.models.secrets import SecretsConfig
from codegen_on_oss.snapshot.codebase_snapshot import SnapshotManager, CodebaseSnapshot
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer

# Create a snapshot manager
snapshot_manager = SnapshotManager()

# Create a codebase from a repository
github_token = "your_github_token"
secrets = SecretsConfig(github_token=github_token)
codebase = Codebase.from_repo("owner/repo", secrets=secrets)

# Create a snapshot
snapshot = snapshot_manager.create_snapshot(codebase, commit_sha="abc123")

# Save the snapshot to a file
snapshot.save_to_file("snapshot.json")

# Load a snapshot from a file
loaded_snapshot = CodebaseSnapshot.load_from_file("snapshot.json")

# Create a diff analyzer to compare two snapshots
diff_analyzer = DiffAnalyzer(original_snapshot, modified_snapshot)

# Get a summary of the changes
summary = diff_analyzer.get_summary()
print(summary)
```

## Code Integrity Analysis

### Command Line Interface

```bash
# Basic analysis
python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --output results.json --html report.html

# Analysis with custom configuration
python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --config config.json --output results.json --html report.html

# Branch comparison
python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --mode compare --main-branch main --feature-branch feature --output comparison.json --html report.html

# PR analysis
python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --mode pr --main-branch main --feature-branch pr-branch --output pr_analysis.json --html report.html
```

## Extensibility

### Adding New Sources

You can define additional repository sources by subclassing `RepoSource` and providing a corresponding settings class. Make sure to set the `source_type` and register your new source by following the pattern established in `CSVInputSource` or `GithubSource`.

### Improving Testing

The detailed metrics collected can help you understand where parsing failures occur or where performance lags. Use these insights to improve error handling and optimize the codegen parsing logic.

### Containerization and Automation

There is a Dockerfile that can be used to create an image capable of running the parse tests. Runtime environment variables can be used to configure the run and output.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
