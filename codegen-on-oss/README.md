# Codegen on OSS

The **Codegen on OSS** package provides a comprehensive toolkit for codebase analysis, context management, and agent execution. It integrates the functionality from the original harness.py with enhanced capabilities for codebase analysis and context saving.

## New Features

### 1. Comprehensive Codebase Analysis

The package now includes powerful tools for analyzing codebases:

- **CodebaseAnalysisHarness**: Integrates core functionality from harness.py to provide detailed codebase analysis
- **Diff Generation**: Track file changes and generate diffs between commits
- **File Statistics**: Get comprehensive metrics about files, classes, functions, and their relationships

### 2. Context Saving and Retrieval

Save and restore codebase state for later use:

- **CodebaseContextSnapshot**: Save and restore codebase state and analysis results
- **S3 Integration**: Store snapshots in S3-compatible storage via BucketStore
- **Local Storage**: Save snapshots locally for easy access

### 3. CodeContextRetrievalServer

A FastAPI server that provides a REST API for accessing all functionality:

- **Repository Analysis**: Analyze repositories and get detailed metrics
- **Snapshot Management**: Create, list, and load snapshots
- **Agent Execution**: Run AI agents with saved context for code analysis and modification

## Getting Started

### Installation

```bash
pip install codegen-on-oss
```

### Basic Usage

#### Analyzing a Repository

```python
from codegen_on_oss.analysis import CodebaseAnalysisHarness
from codegen_on_oss.snapshot import CodebaseContextSnapshot

# Create a harness and analyze a codebase
harness = CodebaseAnalysisHarness.from_repo("owner/repo")
results = harness.analyze_codebase()

# Save the state for later
snapshot = CodebaseContextSnapshot(harness)
snapshot_id = snapshot.create_snapshot()
```

#### Starting the Server

```bash
cgparse serve --host 0.0.0.0 --port 8000
```

## Package Structure

The package is composed of several modules:

- **analysis**: Codebase analysis tools

  - `harness_integration.py`: Integration of harness.py functionality
  - Other analysis modules for parsing and metrics

- **snapshot**: Context saving and retrieval

  - `context_snapshot.py`: Save and restore codebase state
  - Other snapshot-related modules

- **context_server**: FastAPI server for accessing functionality

  - `server.py`: REST API for codebase analysis and context management

- **sources**: Repository source definitions

  - Defines the Repository source classes and settings

- **cli**: Command-line interface

  - Built with Click, provides commands for parsing, analysis, and serving

## CLI Commands

The CLI provides several commands:

- `run-one`: Parse a single repository specified by URL
- `run`: Iterate over repositories from a source and parse each one
- `serve`: Start the CodeContextRetrievalServer

### Example: Starting the Server

```bash
cgparse serve --host 0.0.0.0 --port 8000
```

### Example: Analyzing a Repository

```bash
cgparse run-one https://github.com/owner/repo
```

## API Endpoints

When running the server, the following endpoints are available:

- `/analyze/repository`: Analyze a repository and return results
- `/analyze/file_stats`: Get file statistics for an analyzed repository
- `/snapshot/create`: Create a snapshot of the current state
- `/snapshot/list`: List all available snapshots
- `/snapshot/load/{snapshot_id}`: Load a snapshot by ID
- `/agent/run`: Run an agent on the codebase

## Example Scripts

Check the `scripts` directory for example usage:

- `example_usage.py`: Demonstrates how to use the CodebaseAnalysisHarness and CodebaseContextSnapshot

## Original Functionality

The package still includes all the original functionality:

- **Repository Sources**: Collect repository URLs from different sources
- **Repository Parsing**: Parse repositories using the codegen tool
- **Performance Profiling**: Log metrics for each parsing run
- **Error Logging**: Log errors to help pinpoint parsing failures

For more details on the original functionality, see the "Package Structure" and "Getting Started" sections below.

______________________________________________________________________

## Original Package Structure

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

  - Built with Click, the CLI provides two main commands:
    - `run-one`: Parses a single repository specified by URL.
    - `run`: Iterates over repositories obtained from a selected source and parses each one.

- **`metrics`**

  - Provides profiling tools to measure performance during the parse:
    - `MetricsProfiler`: A context manager that creates a profiling session.
    - `MetricsProfile`: Represents a "span" or a "run" of a specific repository. Records step-by-step metrics (clock duration, CPU time, memory usage) and writes them to a CSV file specified by `--output-path`

- **`parser`**

  Contains the `CodegenParser` class that orchestrates the parsing process:

  - Clones the repository (or forces a pull if specified).
  - Initializes a `Codebase` (from the codegen tool).
  - Runs post-initialization validation.
  - Integrates with the `MetricsProfiler` to log measurements at key steps.

______________________________________________________________________

## Getting Started

1. **Configure the Repository Source**

   Decide whether you want to read from a CSV file or query GitHub:

   - For CSV, ensure that your CSV file (default: `input.csv`) exists and contains repository URLs in its first column \[`repo_url`\] and commit hash \[`commit_hash`\] (or empty) in the second column.
   - For GitHub, configure your desired settings (e.g., `language`, `heuristic`, and optionally a GitHub token) via environment variables (`GITHUB_` prefix)

1. **Run the Parser**

   Use the CLI to start parsing:

   - To parse one repository:

     ```bash
     uv run cgparse run-one --help
     ```

   - To parse multiple repositories from a source:

     ```bash
     uv run cgparse run --help
     ```

1. **Review Metrics and Logs**

   After parsing, check the CSV (default: `metrics.csv` ) to review performance measurements per repository. Error logs are written to the specified error output file (default: `errors.log`)

______________________________________________________________________

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

______________________________________________________________________

### Running it yourself

You can also run `modal_run.py` yourself. It is designed to be run via Modal for cloud-based parsing. It offers additional configuration methods:

```shell
$ uv run modal run modal_run.py
```

- **CSV and Repository Volumes:**
  The script defines two Modal volumes:

  - `codegen-oss-input-volume`: For uploading and reloading CSV inputs.
  - `codegen-oss-repo-volume`: For caching repository data during parsing.
    The repository and input volume names are configurable via environment variables (`CODEGEN_MODAL_REPO_VOLUME` and `CODEGEN_MODAL_INPUT_VOLUME`).

- **Secrets Handling:**
  The script loads various credentials via Modal secrets. It first checks for a pre-configured Modal secret (`codegen-oss-bucket-credentials` configurable via environment variable `CODEGEN_MODAL_SECRET_NAME`) and falls back to dynamically created Modal secret from local `.env` or environment variables if not found.

- **Entrypoint Parameters:**
  The main function supports multiple source types:

  - **csv:** Uploads a CSV file (`--csv-file input.csv`) for batch processing.
  - **single:** Parses a single repository specified by its URL (`--single-url "https://github.com/codegen-sh/codegen-sdk.git"`) and an optional commit hash (`--single-commit ...`)
  - **github:** Uses GitHub settings, language (`--github-language python`) and heuristic (`--github-heuristic stars`) to query for top repositories.

- **Result Storage:**
  Upon completion, logs and metrics are automatically uploaded to the S3 bucket specified by the environment variable `BUCKET_NAME` (default: `codegen-oss-parse`). This allows for centralized storage and easy retrieval of run outputs. The AWS Credentials provided in the secret are used for this operation.

______________________________________________________________________

## Extensibility

**Adding New Sources:**

You can define additional repository sources by subclassing `RepoSource` and providing a corresponding settings class. Make sure to set the `source_type` and register your new source by following the pattern established in `CSVInputSource` or `GithubSource`.

**Improving Testing:**

The detailed metrics collected can help you understand where parsing failures occur or where performance lags. Use these insights to improve error handling and optimize the codegen parsing logic.

**Containerization and Automation:**

There is a Dockerfile that can be used to create an image capable of running the parse tests. Runtime environment variables can be used to configure the run and output.

**Input & Configuration**

Explore a better CLI for providing options to the Modal run.
