# Overview

The **Codegen on OSS** package provides a modular pipeline that:

- **Collects repository URLs** from different sources (e.g., CSV files or GitHub searches).
- **Parses repositories** using the codegen tool.
- **Profiles performance** and logs metrics for each parsing run.
- **Logs errors** to help pinpoint parsing failures or performance bottlenecks.
- **Analyzes codebases** with comprehensive static analysis.
- **Compares codebases** to identify differences between repositories or branches.

______________________________________________________________________

## Package Structure

The package is composed of several modules:

- `sources`

  - Defines the Repository source classes and settings. Settings are all configurable via environment variables

  - Github Source

    ```python
    class GithubSettings(SourceSettings):
        language: Literal["python", "typescript"] = "python"
        heuristic: Literal[
            "stars",
            "forks",
            "updated",
            # "watchers",
            # "contributors",
            # "commit_activity",
            # "issues",
            # "dependency",
        ] = "stars"
        github_token: str | None = None
    ```

    - The three options available now are the three supported by the Github API.
      - Future Work Additional options will require different strategies

  - CSV Source

    - Simply reads repo URLs from CSV

- `cache`

  - Currently only specifies the cache directory. It is used for caching git repositories pulled by the pipeline `--force-pull` can be used to re-pull from the remote.

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

## Installation

```bash
# Install from PyPI
pip install codegen-on-oss

# Install from source
git clone https://github.com/username/codegen-on-oss.git
cd codegen-on-oss
pip install -e .
```

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

## Documentation

For comprehensive documentation, see the [docs](docs/) directory:

- [Components](docs/components/): Documentation for each component
- [Examples](docs/examples/): Usage examples
- [Tutorials](docs/tutorials/): Step-by-step tutorials
- [Analysis Categories and Metrics](docs/analysis_categories_and_metrics.md): Detailed information about analysis categories and metrics
- [Comparison Report Examples](docs/comparison_report_examples.md): Examples of comparison reports
- [Troubleshooting](docs/troubleshooting.md): Solutions to common issues

## Running on Modal

```shell
$ uv run modal run modal_run.py
```

Codegen runs this parser on modal using the CSV source file `input.csv` tracked in this repository.

### Modal Configuration

- **Compute Resources**: Allocates 4 CPUs and 16GB of memory.
- **Secrets & Volumes**: Uses secrets (for bucket credentials) and mounts a volume for caching repositories.
- **Image Setup**: Builds on a Debian slim image with Python 3.12, installs required packages (`uv` and `git` )
- **Environment Configuration**: Environment variables (e.g., GitHub settings) are injected at runtime.

The function `parse_repo_on_modal` performs the following steps:

1. **Environment Setup**: Updates environment variables and configures logging using Loguru.
1. **Source Initialization**: Creates a repository source based on the provided type (e.g., GitHub).
1. **Metrics Profiling**: Instantiates `MetricsProfiler` to capture and log performance data.
1. **Repository Parsing**: Iterates over repository URLs and parses each using the `CodegenParser`.
1. **Error Handling**: Logs any exceptions encountered during parsing.
1. **Result Upload**: Uses the `BucketStore` class to upload the configuration, logs, and metrics to an S3 bucket.

### Bucket Storage

**Bucket (public):** [codegen-oss-parse](https://s3.amazonaws.com/codegen-oss-parse/)

The results of each run are saved under the version of `codegen` lib that the run installed and the source type it was run with. Within this prefix:

- Source Settings
  - `https://s3.amazonaws.com/codegen-oss-parse/{version}/{source}/config.json`
- Metrics
  - `https://s3.amazonaws.com/codegen-oss-parse/{version}/{source}/metrics.csv`
- Logs
  - `https://s3.amazonaws.com/codegen-oss-parse/{version}/{source}/output.logs`

## Extensibility

**Adding New Sources:**

You can define additional repository sources by subclassing `RepoSource` and providing a corresponding settings class. Make sure to set the `source_type` and register your new source by following the pattern established in `CSVInputSource` or `GithubSource`.

**Improving Testing:**

The detailed metrics collected can help you understand where parsing failures occur or where performance lags. Use these insights to improve error handling and optimize the codegen parsing logic.

**Containerization and Automation:**

There is a Dockerfile that can be used to create an image capable of running the parse tests. Runtime environment variables can be used to configure the run and output.

