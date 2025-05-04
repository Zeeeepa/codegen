# Codegen on OSS

The **Codegen on OSS** package provides a comprehensive set of tools for analyzing codebases, comparing code changes, and evaluating pull requests. It includes:

1. **Codebase Analysis**: Analyze repositories to extract metrics, structure, and quality indicators
2. **Diff Analysis**: Compare different versions of a codebase to identify changes and potential issues
3. **PR Analysis**: Evaluate pull requests to determine if they're properly implemented
4. **Snapshot Management**: Create and manage snapshots of codebases at specific points in time

## Key Features

- **Codebase Snapshots**: Capture the state of a codebase at a specific point in time
- **Diff Analysis**: Compare snapshots to identify changes, including high-risk modifications
- **PR Evaluation**: Analyze pull requests to determine quality and implementation correctness
- **CLI Interface**: Easy-to-use command-line tools for all functionality
- **GitHub Integration**: Seamless integration with GitHub repositories and pull requests

## Package Structure

The package is organized into several modules:

- **`snapshot`**: Tools for creating and managing codebase snapshots
  - `codebase_snapshot.py`: Core classes for creating and managing snapshots
  - `enhanced_snapshot_manager.py`: Advanced snapshot management capabilities

- **`analysis`**: Tools for analyzing codebases and changes
  - `diff_analyzer.py`: Compare snapshots to identify changes
  - `swe_harness_agent.py`: Analyze commits and PRs for quality and correctness
  - `swe_harness_cli.py`: Command-line interface for analysis tools
  - `code_integrity_analyzer.py`: Analyze code for integrity and quality issues

- **`sources`**: Repository source definitions
  - `github_source.py`: Fetch repositories from GitHub
  - `csv_source.py`: Read repository URLs from CSV files

- **`outputs`**: Output formatting and storage
  - `csv_output.py`: Write results to CSV files
  - `sql_output.py`: Store results in SQL databases

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/codegen-on-oss

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

### Basic Usage

#### Analyzing a Pull Request

```bash
# Analyze a pull request and post a comment with the results
python -m codegen_on_oss.analysis.swe_harness_cli analyze-pr \
  --token YOUR_GITHUB_TOKEN \
  --comment \
  username/repo 123
```

#### Comparing Commits

```bash
# Compare two commits in a repository
python -m codegen_on_oss.analysis.swe_harness_cli analyze-commit \
  --token YOUR_GITHUB_TOKEN \
  username/repo base_commit_sha head_commit_sha
```

#### Creating a Snapshot

```bash
# Create a snapshot of a repository at a specific commit
python -m codegen_on_oss.analysis.swe_harness_cli create-snapshot \
  --token YOUR_GITHUB_TOKEN \
  --commit commit_sha \
  username/repo
```

#### Comparing Branches

```bash
# Compare two branches and output the results as formatted text
python -m codegen_on_oss.analysis.swe_harness_cli compare-branches \
  --token YOUR_GITHUB_TOKEN \
  --text \
  --high-risk \
  username/repo main feature-branch
```

## Advanced Usage

### Creating and Comparing Snapshots Programmatically

```python
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot, SnapshotManager
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer

# Create snapshots of the original and modified codebases
original_snapshot = CodebaseSnapshot.create_from_repo(
    "username/repo", 
    commit_sha="base_commit_sha", 
    github_token="YOUR_GITHUB_TOKEN"
)

modified_snapshot = CodebaseSnapshot.create_from_repo(
    "username/repo", 
    commit_sha="head_commit_sha", 
    github_token="YOUR_GITHUB_TOKEN"
)

# Analyze the differences
diff_analyzer = DiffAnalyzer(original_snapshot, modified_snapshot)

# Get a summary of the changes
summary = diff_analyzer.get_summary()
print(diff_analyzer.format_summary_text())

# Identify high-risk changes
high_risk_changes = diff_analyzer.get_high_risk_changes()
```

### Analyzing a PR and Posting Comments

```python
from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent

# Initialize the agent
agent = SWEHarnessAgent(github_token="YOUR_GITHUB_TOKEN")

# Analyze a PR and post a comment with the results
results = agent.analyze_and_comment_on_pr(
    repo_url="username/repo",
    pr_number=123,
    post_comment=True,
    detailed=True
)

# Print the analysis results
print(f"PR Quality Score: {results['quality_score']}/10.0")
print(f"Overall Assessment: {results['overall_assessment']}")
```

## CLI Reference

The package provides a comprehensive command-line interface for all functionality:

```
usage: swe_harness_cli.py [-h] [--verbose] [--token TOKEN] [--snapshot-dir SNAPSHOT_DIR] [--output OUTPUT]
                          {analyze-pr,analyze-commit,compare-branches,create-snapshot} ...

SWE Harness CLI for analyzing commits and pull requests

options:
  -h, --help            show this help message and exit
  --verbose, -v         Enable verbose logging
  --token TOKEN         GitHub token for private repositories
  --snapshot-dir SNAPSHOT_DIR
                        Directory to store snapshots
  --output OUTPUT, -o OUTPUT
                        Output file for results (default: stdout)

command:
  {analyze-pr,analyze-commit,compare-branches,create-snapshot}
                        Command to run
    analyze-pr          Analyze a pull request
    analyze-commit      Analyze a commit
    compare-branches    Compare two branches
    create-snapshot     Create a snapshot of a repository
```

## Contributing

Contributions are welcome! Here are some ways you can contribute:

- Report bugs and request features by creating issues
- Submit pull requests to fix bugs or add new features
- Improve documentation
- Share your experiences and use cases

## License

This project is licensed under the MIT License - see the LICENSE file for details.

