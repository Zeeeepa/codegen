# Codegen Snapshot Module

A comprehensive snapshot module for the Codegen-on-OSS project that provides functionality for creating, storing, and comparing snapshots of codebases.

## Overview

The Snapshot Module enables capturing the state of a codebase at specific points in time, allowing for:

- Creating snapshots of codebases at specific commits
- Storing and retrieving snapshots
- Comparing snapshots to analyze changes
- Integrating with event handlers to automatically create snapshots on PR events

## Components

The module consists of the following key components:

- **CodebaseSnapshot**: Class for capturing and storing the state of a codebase
- **SnapshotManager**: Class for managing the creation, storage, and retrieval of snapshots
- **Event Handlers**: Integration with GitHub events to automatically create snapshots
- **Analysis Integration**: Integration with the Analysis Module for analyzing changes between snapshots

## Usage

### Basic Usage

```python
from codegen import Codebase
from codegen.configs.models.secrets import SecretsConfig
from codegen_on_oss.snapshot.codebase_snapshot import SnapshotManager, CodebaseSnapshot

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

# Get a summary of the snapshot
print(snapshot.get_summary())
```

### Creating Snapshots from a Repository

```python
from codegen_on_oss.snapshot.codebase_snapshot import SnapshotManager

# Create a snapshot manager
snapshot_manager = SnapshotManager()

# Create a snapshot directly from a repository
snapshot = snapshot_manager.snapshot_repo(repo_url="owner/repo", commit_sha="abc123", github_token="your_github_token")
```

### Comparing Snapshots

```python
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer

# Create a diff analyzer to compare two snapshots
diff_analyzer = DiffAnalyzer(original_snapshot, modified_snapshot)

# Get a summary of the changes
summary = diff_analyzer.get_summary()
print(summary)

# Get a formatted summary text
formatted_summary = diff_analyzer.format_summary_text()
print(formatted_summary)

# Get high-risk changes
high_risk_changes = diff_analyzer.get_high_risk_changes()
print(high_risk_changes)
```

## Integration with SWE Harness Agent

The Snapshot Module integrates with the SWE Harness Agent to analyze commits and pull requests:

```python
from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent

# Create a SWE harness agent
swe_agent = SWEHarnessAgent(github_token="your_github_token")

# Analyze a pull request
results = swe_agent.analyze_pull_request("owner/repo", pr_number=123)
print(results)

# Analyze a commit
results = swe_agent.analyze_commit("owner/repo", base_commit="abc123", head_commit="def456")
print(results)
```

## Event Handlers

The module includes event handlers for automatically creating snapshots on GitHub events:

- **PR Labeled**: Creates a snapshot when a PR is labeled
- **PR Closed**: Creates a snapshot when a PR is merged
- **Web Endpoints**: Provides web endpoints for analyzing PRs and commits

## Key Features

### Snapshot Creation and Storage

- Create snapshots of codebases at specific commits
- Store snapshots in memory or on disk
- Serialize and deserialize snapshots to/from JSON

### Snapshot Analysis

- Compare snapshots to identify changes
- Analyze file, function, and class changes
- Identify high-risk changes
- Calculate complexity changes

### Integration with GitHub Events

- Automatically create snapshots on PR events
- Analyze PRs and commits on demand
- Post analysis results as comments on PRs

## Example

See `swe_harness_example.py` in the analysis module for a complete demonstration of the snapshot module's capabilities.
