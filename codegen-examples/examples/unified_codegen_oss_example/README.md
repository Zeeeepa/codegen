# Unified Codegen-on-OSS Example

This example demonstrates a comprehensive integration of all the codegen-on-oss features, including repository analysis, commit analysis, PR analysis, code integrity validation, and snapshot management.

## Overview

The unified example provides a complete workflow for analyzing a codebase, from initial repository analysis to detailed commit and PR analysis, with code integrity validation and snapshot management.

## Features

- **Repository Analysis**: Analyze a repository and get comprehensive metrics
- **Commit Analysis**: Analyze commits and get quality assessment
- **PR Analysis**: Analyze pull requests and get quality assessment
- **Branch Comparison**: Compare two branches and get the differences
- **Snapshot Management**: Create and compare snapshots of codebases
- **Code Integrity Validation**: Validate code integrity and get issues
- **Visualization**: Generate visualizations of the analysis results
- **Report Generation**: Generate comprehensive reports of the analysis results

## Usage

```bash
# Run the unified example
python run.py --repo https://github.com/username/repo --output-dir output
```

## Example Output

The example generates a comprehensive report of the analysis results, including:

- Repository summary
- Code complexity metrics
- Dependency analysis
- Code quality assessment
- Commit analysis
- PR analysis
- Branch comparison
- Snapshot comparison
- Code integrity validation

## Implementation

The example uses the unified API provided by codegen-on-oss to perform all the analysis tasks:

```python
from codegen_on_oss.api import (
    UnifiedAPI,
    analyze_repository,
    analyze_commit,
    analyze_pull_request,
    compare_branches,
    create_snapshot,
    compare_snapshots,
    analyze_code_integrity,
)

# Initialize the API
api = UnifiedAPI(github_token="your-github-token")

# Analyze a repository
repo_results = api.analyze_repository(
    repo_url="https://github.com/username/repo",
    output_path="output/repo_analysis.json",
    include_integrity=True,
)

# Analyze a commit
commit_results = api.analyze_commit(
    repo_url="https://github.com/username/repo",
    commit_hash="abc123",
    output_path="output/commit_analysis.json",
)

# Analyze a PR
pr_results = api.analyze_pull_request(
    repo_url="https://github.com/username/repo",
    pr_number=123,
    output_path="output/pr_analysis.json",
)

# Compare branches
branch_results = api.compare_branches(
    repo_url="https://github.com/username/repo",
    base_branch="main",
    head_branch="feature",
    output_path="output/branch_comparison.json",
)

# Create and compare snapshots
snapshot_id_1 = api.create_snapshot(
    repo_url="https://github.com/username/repo",
    branch="main",
    snapshot_name="main-snapshot",
    output_path="output/main_snapshot.json",
)

snapshot_id_2 = api.create_snapshot(
    repo_url="https://github.com/username/repo",
    branch="feature",
    snapshot_name="feature-snapshot",
    output_path="output/feature_snapshot.json",
)

snapshot_results = api.compare_snapshots(
    snapshot_id_1="output/main_snapshot.json",
    snapshot_id_2="output/feature_snapshot.json",
    output_path="output/snapshot_comparison.json",
)

# Analyze code integrity
integrity_results = api.analyze_code_integrity(
    repo_url="https://github.com/username/repo",
    output_path="output/code_integrity.json",
)

# Generate a comprehensive report
generate_report(
    repo_results=repo_results,
    commit_results=commit_results,
    pr_results=pr_results,
    branch_results=branch_results,
    snapshot_results=snapshot_results,
    integrity_results=integrity_results,
    output_path="output/comprehensive_report.html",
)
```

## Integration with Other Tools

The example also demonstrates integration with other tools:

- **GitHub**: Integration with GitHub for PR analysis and commit analysis
- **Linear**: Integration with Linear for issue tracking
- **Slack**: Integration with Slack for notifications
- **Modal**: Integration with Modal for cloud-based analysis
- **WSL2 Server**: Integration with the WSL2 server for code validation

## Customization

The example can be customized to fit your specific needs:

- **Custom Rules**: Define custom rules for code integrity validation
- **Custom Metrics**: Define custom metrics for code analysis
- **Custom Visualizations**: Define custom visualizations for the analysis results
- **Custom Reports**: Define custom reports for the analysis results

## License

This project is licensed under the MIT License - see the LICENSE file for details.

