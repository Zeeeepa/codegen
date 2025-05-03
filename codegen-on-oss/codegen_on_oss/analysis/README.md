# Codegen Analysis Module

A comprehensive code analysis module for the Codegen-on-OSS project that provides a unified interface for analyzing codebases.

## Overview

The Analysis Module integrates various specialized analysis components into a cohesive system, allowing for:

- Code complexity analysis
- Import dependency analysis
- Documentation generation
- Symbol attribution
- Visualization of module dependencies
- Comprehensive code quality metrics
- Commit and PR analysis
- Codebase comparison and diff analysis

## Components

The module consists of the following key components:

- **CodeAnalyzer**: Central class that orchestrates all analysis functionality
- **DiffAnalyzer**: Class for analyzing differences between codebase snapshots
- **CommitAnalyzer**: Class for analyzing commits by comparing snapshots
- **SWEHarnessAgent**: Harness for a Software Engineering agent that analyzes commits and PRs
- **Metrics Integration**: Connection with the CodeMetrics class for comprehensive metrics
- **Import Analysis**: Tools for analyzing import relationships and cycles
- **Documentation Tools**: Functions for generating documentation for code
- **Visualization**: Tools for visualizing dependencies and relationships

## Usage

### Basic Usage

```python
from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.metrics import CodeMetrics

# Load a codebase
codebase = Codebase.from_repo("owner/repo")

# Create analyzer instance
analyzer = CodeAnalyzer(codebase)

# Get codebase summary
summary = analyzer.get_codebase_summary()
print(summary)

# Analyze complexity
complexity_results = analyzer.analyze_complexity()
print(f"Average cyclomatic complexity: {complexity_results['cyclomatic_complexity']['average']}")

# Analyze imports
import_analysis = analyzer.analyze_imports()
print(f"Found {len(import_analysis['import_cycles'])} import cycles")

# Create metrics instance
metrics = CodeMetrics(codebase)

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
analysis_results = analyzer.analyze_commit(
    base_commit="abc123",
    head_commit="def456",
    github_token="your_github_token"
)

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
analysis_results = analyzer.analyze_pull_request(
    pr_number=123,
    github_token="your_github_token"
)

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

The module also provides a FastAPI web interface for analyzing repositories:

```bash
# Run the API server
python -m codegen_on_oss.analysis.analysis
```

Then you can make POST requests to `/analyze_repo` with a JSON body:

```json
{
  "repo_url": "owner/repo"
}
```

## Key Features

### Code Complexity Analysis

- Cyclomatic complexity calculation
- Halstead complexity metrics
- Maintainability index
- Line metrics (LOC, LLOC, SLOC, comments)

### Import Analysis

- Detect import cycles
- Identify problematic import loops
- Visualize module dependencies

### Documentation Generation

- Generate documentation for functions
- Create MDX documentation for classes
- Extract context for symbols

### Symbol Attribution

- Track symbol authorship
- Analyze AI contribution

### Dependency Analysis

- Create dependency graphs
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

- Comprehensive code quality metrics
- Functions to find problematic code areas
- Dependency analysis
- Documentation generation

## Integration with Snapshot Module

The Analysis Module integrates with the Snapshot Module to:

- Create snapshots of codebases at specific commits
- Compare snapshots to analyze changes
- Track changes over time
- Analyze commits and PRs

## Example

See `example.py` for a demonstration of the basic analysis functionality and `swe_harness_example.py` for a demonstration of the commit and PR analysis functionality.
