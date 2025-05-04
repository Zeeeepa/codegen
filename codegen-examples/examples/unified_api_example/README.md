# Unified API Example

This example demonstrates how to use the unified API for codegen-on-oss to perform various code analysis tasks, including repository analysis, commit analysis, PR analysis, and code integrity validation.

## Overview

The unified API provides a consistent interface for interacting with the codegen-on-oss package, making it easier to use the various components for code analysis, snapshot management, and code integrity validation.

This example shows how to:

- Analyze a repository and get comprehensive metrics
- Analyze a commit and get quality assessment
- Analyze a pull request and get quality assessment
- Compare two branches and get the differences
- Create and compare snapshots
- Analyze code integrity and get issues
- Batch analyze multiple repositories

## Usage

```bash
# Analyze a repository
python run.py --repo https://github.com/username/repo --output-dir output --example repo

# Analyze a commit
python run.py --repo https://github.com/username/repo --commit abc123 --output-dir output --example commit

# Analyze a PR
python run.py --repo https://github.com/username/repo --pr 123 --github-token your-github-token --output-dir output --example pr

# Compare branches
python run.py --repo https://github.com/username/repo --base-branch main --head-branch feature --output-dir output --example branches

# Create and compare snapshots
python run.py --repo https://github.com/username/repo --output-dir output --example snapshot

# Analyze code integrity
python run.py --repo https://github.com/username/repo --output-dir output --example integrity

# Batch analyze repositories
python run.py --batch-repos https://github.com/username/repo1 https://github.com/username/repo2 --output-dir output --example batch
```

## Example Output

### Repository Analysis

```
Analyzing repository: https://github.com/username/repo

Repository Analysis Summary:
Files: 100
Functions: 500
Classes: 50
Average Complexity: 5.2
Issues Found: 25

Top Issues:
1. Function too complex - src/main.py:123
2. Line too long - src/utils.py:45
3. Too many parameters - src/api.py:67
4. Missing docstring - src/models.py:89
5. Unused import - src/views.py:12
```

### Commit Analysis

```
Analyzing commit: abc123

Commit Analysis Summary:
Is Properly Implemented: True
Score: 85
Overall Assessment: The commit is well-implemented with good test coverage.
Files Added: 2
Files Modified: 5
Files Removed: 1
Issues Found: 3

Top Issues:
1. Missing test for new function - src/utils.py:45
2. Unused variable - src/api.py:67
3. Inconsistent naming - src/models.py:89
```

### PR Analysis

```
Analyzing PR #123

PR Analysis Summary:
Is Properly Implemented: True
Score: 90
Overall Assessment: The PR is well-implemented with good test coverage and documentation.
Files Added: 3
Files Modified: 7
Files Removed: 2
Issues Found: 2

Top Issues:
1. Missing test for new function - src/utils.py:45
2. Unused variable - src/api.py:67
```

### Branch Comparison

```
Comparing branches: main -> feature

Branch Comparison Summary:
Summary: The feature branch adds 3 new files and modifies 7 existing files.
Files Added: 3
Files Modified: 7
Files Removed: 2
```

### Snapshot Comparison

```
Creating snapshots for repository: https://github.com/username/repo
Created snapshots: https://github.com/username/repo:main:latest:main-snapshot and https://github.com/username/repo:develop:latest:develop-snapshot

Snapshot Comparison Summary:
Summary: The develop snapshot adds 3 new files and modifies 7 existing files compared to the main snapshot.
Files Added: 3
Files Modified: 7
Files Removed: 2
```

### Code Integrity Analysis

```
Analyzing code integrity for repository: https://github.com/username/repo

Code Integrity Analysis Summary:
Issues Found: 25
Summary: The codebase has 25 issues, including 5 high-priority issues.

Top Issues:
1. Function too complex - src/main.py:123
2. Line too long - src/utils.py:45
3. Too many parameters - src/api.py:67
4. Missing docstring - src/models.py:89
5. Unused import - src/views.py:12
```

### Batch Analysis

```
Batch analyzing 3 repositories

Batch Analysis Summary:
https://github.com/username/repo1: 100 files, 500 functions
https://github.com/username/repo2: 50 files, 200 functions
https://github.com/username/repo3: Error - Failed to clone repository
```

## API Reference

For more information on the unified API, see the [API documentation](../../../codegen-on-oss/codegen_on_oss/api/README.md).

