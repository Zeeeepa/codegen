# Codegen on OSS

The **Codegen on OSS** package provides a modular pipeline that:

- **Parses repositories** using the codegen tool.
- **Profiles performance** and logs metrics for each parsing run.
- **Logs errors** to help pinpoint parsing failures or performance bottlenecks.
- **Analyzes codebases** with comprehensive static analysis.
- **Compares codebases** to identify differences between repositories or branches.

______________________________________________________________________

## Installation

```bash
# Install from PyPI
pip install codegen-on-oss

# Install from source
git clone https://github.com/username/codegen-on-oss.git
cd codegen-on-oss
pip install -e .
```

## Package Structure

The package is composed of several modules:

- `cli`

  - Command-line interface for the package
  - Supports parsing repositories, analyzing codebases, and comparing codebases

- `codebase_analyzer`

  - Comprehensive static code analysis for a single codebase
  - Analyzes code structure, dependencies, quality, and more

- `codebase_comparator`

  - Compares two codebases and identifies differences
  - Can compare different repositories or different branches of the same repository

- `analysis_viewer_cli`

  - Interactive command-line interface for codebase analysis
  - Provides a user-friendly way to analyze and compare codebases

- `analysis_viewer_web`

  - Web-based interface for codebase analysis
  - Allows users to analyze and compare codebases through a browser

## Usage

### Parsing Repositories

```bash
# Parse repositories from a CSV file
codegen-on-oss parse --source csv

# Parse repositories from GitHub
codegen-on-oss parse --source github --limit 10
```

### Analyzing a Codebase

```bash
# Analyze a repository by URL
codegen-on-oss analyze --repo-url https://github.com/username/repo

# Analyze a local repository
codegen-on-oss analyze --repo-path /path/to/local/repo

# Specify output format and file
codegen-on-oss analyze --repo-url https://github.com/username/repo --output-format html --output-file report.html
```

### Comparing Codebases

```bash
# Compare two repositories
codegen-on-oss compare --base-repo-url https://github.com/username/repo1 --compare-repo-url https://github.com/username/repo2

# Compare two branches of the same repository
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch main --compare-branch feature-branch

# Specify output format and file
codegen-on-oss compare --base-repo-url https://github.com/username/repo1 --compare-repo-url https://github.com/username/repo2 --output-format html --output-file comparison.html
```

### Interactive Mode

```bash
# Run in interactive mode
codegen-on-oss interactive
```

### Web Interface

```bash
# Launch the web interface
codegen-on-oss web

# Create a shareable link
codegen-on-oss web --share

# Don't open the browser automatically
codegen-on-oss web --no-browser
```

## Analysis Categories

The codebase analyzer and comparator support the following categories of analysis:

- **Codebase Structure**: File counts, language distribution, directory structure, etc.
- **Symbol Level**: Function parameters, return types, complexity metrics, etc.
- **Dependency Flow**: Function call relationships, entry point analysis, etc.
- **Code Quality**: Unused functions, repeated code patterns, refactoring opportunities, etc.
- **Visualization**: Module dependencies, symbol dependencies, call hierarchies, etc.
- **Language Specific**: Decorator usage, type hint coverage, etc.
- **Code Metrics**: Cyclomatic complexity, Halstead volume, maintainability index, etc.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
black .
isort .
mypy .
ruff .
```
