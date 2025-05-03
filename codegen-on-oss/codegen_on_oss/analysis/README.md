# Enhanced Analysis Architecture for Codegen-on-OSS

This directory contains the enhanced analysis architecture for Codegen-on-OSS, which provides a comprehensive pipeline for analyzing code repositories, commits, symbols, and features.

## Overview

The enhanced analysis architecture provides:

1. **Analysis Pipeline**: A structured pipeline for code analysis, with different analyzers for repositories, commits, symbols, and features.

2. **Coordinator Pattern**: A coordinator that orchestrates the execution of different analyzers and collectors.

3. **Metrics Collection**: Comprehensive metrics collection for code quality analysis.

4. **Issue Detection**: Detection of code quality issues, such as high complexity, low maintainability, and code smells.

5. **Dependency Analysis**: Analysis of dependencies between symbols, such as function calls, class inheritance, and imports.

6. **Snapshot Generation**: Generation of snapshots of codebases at specific points in time, with support for differential snapshots.

7. **API Integration**: Integration with the API server, providing endpoints for analyzing repositories, commits, symbols, and features.

## Components

### Coordinator

The `coordinator.py` file provides a coordinator for the analysis pipeline:

- **AnalysisCoordinator**: Orchestrates the execution of different analyzers and collectors.
- **AnalysisContext**: Context for an analysis run, containing state and results.

### Analyzers

The analysis architecture includes several analyzers:

- **RepositoryAnalyzer**: Analyzes repositories and extracts metadata about them.
- **CommitAnalyzer**: Analyzes commits and extracts metadata about them.
- **SymbolAnalyzer**: Analyzes symbols (functions, classes, variables) and extracts metadata about them.
- **FeatureAnalyzer**: Analyzes features (files or directories) and extracts metadata about them.
- **DependencyAnalyzer**: Analyzes dependencies between symbols.

### Collectors

The analysis architecture includes several collectors:

- **MetricsCollector**: Collects code quality metrics for repositories, files, and symbols.
- **IssueDetector**: Detects code quality issues in repositories, files, and symbols.

### Snapshot Generator

The `snapshot_generator.py` file provides a snapshot generator:

- **SnapshotGenerator**: Creates snapshots of codebases at specific points in time, with support for differential snapshots.

### API Endpoints

The `api_endpoints.py` file provides API endpoints for the analysis architecture:

- **analyze_repository**: Analyzes a repository and returns comprehensive metrics.
- **analyze_commit**: Analyzes a commit in a repository.
- **create_snapshot**: Creates a snapshot of a repository.
- **compare_snapshots**: Compares two snapshots.
- **analyze_symbol**: Analyzes a specific symbol in a repository.

## Usage

### Analyzing a Repository

```python
from codegen import Codebase
from codegen_on_oss.analysis.coordinator import AnalysisCoordinator

# Create a Codebase instance
codebase = Codebase.from_repo("https://github.com/example/example-repo")

# Create an AnalysisCoordinator instance
coordinator = AnalysisCoordinator()

# Analyze the repository
result = await coordinator.analyze_repository(
    repo_url="https://github.com/example/example-repo",
    codebase=codebase
)

# Access the results
repository_data = result.get("repository", {})
commit_data = result.get("commit", {})
symbols_data = result.get("symbols", {})
metrics_data = result.get("metrics", {})
issues_data = result.get("issues", {})
snapshot_data = result.get("snapshot", {})
dependencies_data = result.get("dependencies", {})
```

### Creating a Snapshot

```python
from codegen import Codebase
from codegen_on_oss.analysis.coordinator import AnalysisCoordinator

# Create a Codebase instance
codebase = Codebase.from_repo("https://github.com/example/example-repo")

# Create an AnalysisCoordinator instance
coordinator = AnalysisCoordinator()

# Analyze the repository and create a snapshot
result = await coordinator.analyze_repository(
    repo_url="https://github.com/example/example-repo",
    codebase=codebase
)

# Access the snapshot data
snapshot_data = result.get("snapshot", {})
snapshot_id = snapshot_data.get("id")
snapshot_hash = snapshot_data.get("snapshot_hash")
```

### Analyzing a Symbol

```python
from codegen import Codebase
from codegen_on_oss.analysis.coordinator import AnalysisCoordinator

# Create a Codebase instance
codebase = Codebase.from_repo("https://github.com/example/example-repo")

# Create an AnalysisCoordinator instance
coordinator = AnalysisCoordinator()

# Analyze the repository
result = await coordinator.analyze_repository(
    repo_url="https://github.com/example/example-repo",
    codebase=codebase
)

# Access the symbol data
symbols_data = result.get("symbols", {})
symbol_list = symbols_data.get("symbols", {}).get("functions", [])
for symbol in symbol_list:
    if symbol["name"] == "example_function":
        # Found the symbol
        print(f"Symbol: {symbol['name']}")
        print(f"File: {symbol['file_path']}")
        print(f"Lines: {symbol['line_start']}-{symbol['line_end']}")
```

## Analysis Pipeline

The analysis pipeline consists of the following stages:

1. **Repository Analysis**: Analyzes the repository and extracts metadata about it.
2. **Commit Analysis**: Analyzes the commit and extracts metadata about it.
3. **Symbol Analysis**: Analyzes symbols (functions, classes, variables) and extracts metadata about them.
4. **Feature Analysis**: Analyzes features (files or directories) and extracts metadata about them.
5. **Metrics Collection**: Collects code quality metrics for repositories, files, and symbols.
6. **Issue Detection**: Detects code quality issues in repositories, files, and symbols.
7. **Dependency Analysis**: Analyzes dependencies between symbols.
8. **Snapshot Generation**: Creates a snapshot of the codebase.

## Metrics

The analysis architecture collects the following metrics:

- **Cyclomatic Complexity**: Measures the complexity of a function or method.
- **Maintainability Index**: Measures how maintainable the code is.
- **Halstead Volume**: Measures the size of the code in terms of operators and operands.
- **Lines of Code**: Counts the number of lines of code.
- **Comment Ratio**: Measures the ratio of comment lines to code lines.
- **Method Count**: Counts the number of methods in a class.
- **Degree of Interest**: Measures how interesting a symbol is based on complexity, volume, and size.

## Issues

The analysis architecture detects the following issues:

- **High Complexity**: Functions or methods with high cyclomatic complexity.
- **Low Maintainability**: Code with low maintainability index.
- **Large Files**: Files with too many lines of code.
- **Large Functions**: Functions with too many lines of code.
- **Large Classes**: Classes with too many methods or lines of code.
- **Low Comment Ratio**: Code with too few comments.
- **Duplicate Code**: Code that is duplicated across multiple files.
- **Long Parameter Lists**: Functions with too many parameters.

## Dependencies

The analysis architecture analyzes the following dependencies:

- **Function Calls**: Functions that call other functions.
- **Class Inheritance**: Classes that inherit from other classes.
- **Imports**: Modules that import other modules.

## Snapshots

The analysis architecture supports differential snapshots to reduce storage requirements. When creating a snapshot, the system checks if a file has changed since the previous snapshot. If not, the file is referenced from the previous snapshot instead of being stored again.

## API Integration

The analysis architecture is integrated with the API server, providing endpoints for:

- Analyzing repositories and commits.
- Creating and comparing snapshots.
- Analyzing symbols and features.
- Retrieving metrics and issues.

## Future Enhancements

Future enhancements to the analysis architecture may include:

- Support for more programming languages.
- More advanced code quality metrics and issue detection.
- Integration with more code analysis tools.
- Support for distributed analysis for large codebases.
- Real-time analysis with WebSocket support.

