# Codegen On OSS

The **Codegen on OSS** package provides a modular pipeline that:

- **Collects repository URLs** from different sources (e.g., CSV files or GitHub searches).
- **Parses repositories** using the codegen tool.
- **Profiles performance** and logs metrics for each parsing run.
- **Logs errors** to help pinpoint parsing failures or performance bottlenecks.
- **Analyzes codebases** with comprehensive metrics and context management.
- **Saves and retrieves context** for later use.
- **Provides a server** for accessing functionality via API.

## New Features

### CodebaseAnalysisHarness

The `CodebaseAnalysisHarness` integrates functionality from the `harness.py` file in the `swebench` extension to provide comprehensive codebase analysis:

- **Codebase Analysis**: Generate detailed metrics about files, classes, functions, and their relationships.
- **Diff Generation**: Compare the current state with a base commit.
- **File Tracking**: Track which files have been modified.
- **Agent Integration**: Run AI agents with context for code analysis and modification.

### CodebaseContextSnapshot

The `CodebaseContextSnapshot` allows saving and restoring codebase state:

- **Context Saving**: Save the current state of a codebase for later use.
- **S3 Integration**: Store snapshots in S3-compatible storage.
- **Metadata Management**: Track snapshot metadata for easy retrieval.

### CodeContextRetrievalServer

The `CodeContextRetrievalServer` provides a FastAPI server for accessing functionality:

- **API Access**: Access all functionality through a REST API.
- **Analysis Endpoints**: Analyze codebases via API.
- **Snapshot Management**: Create and load snapshots via API.
- **Agent Execution**: Run agents on codebases via API.

## Getting Started with New Features

### Using the CodebaseAnalysisHarness

```python
from codegen_on_oss.analysis import CodebaseAnalysisHarness

# Create a harness from a repository
harness = CodebaseAnalysisHarness.from_repo("owner/repo")

# Analyze the codebase
results = harness.analyze_codebase()

# Get a diff
diff = harness.get_diff()

# Run an agent
agent_result = harness.run_agent("Analyze this codebase and summarize its structure.")
```

### Using the CodebaseContextSnapshot

```python
from codegen_on_oss.analysis import CodebaseAnalysisHarness
from codegen_on_oss.snapshot import CodebaseContextSnapshot

# Create a harness
harness = CodebaseAnalysisHarness.from_repo("owner/repo")

# Create a snapshot
snapshot = CodebaseContextSnapshot(harness)
snapshot_id = snapshot.create_snapshot()

# Load a snapshot
snapshot_data = CodebaseContextSnapshot.load_snapshot(snapshot_id)
```

### Using the CodeContextRetrievalServer

Start the server:

```bash
cgparse serve --host 0.0.0.0 --port 8000
```

Make API requests:

```python
import requests

# Analyze a repository
response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "repo_full_name": "owner/repo",
    },
)
analysis_results = response.json()

# Create a snapshot
response = requests.post(
    "http://localhost:8000/snapshot/create",
    json={
        "repo_full_name": "owner/repo",
    },
)
snapshot_id = response.json()["snapshot_id"]

# Run an agent
response = requests.post(
    "http://localhost:8000/agent/run",
    json={
        "repo_full_name": "owner/repo",
        "prompt": "Analyze this codebase and summarize its structure.",
    },
)
agent_result = response.json()
```

## Package Structure

The package is composed of several modules:

- `sources`: Defines the Repository source classes and settings.
- `cache`: Specifies the cache directory for repositories.
- `cli`: Provides CLI commands for running the pipeline.
- `metrics`: Provides profiling tools to measure performance.
- `parser`: Contains the `CodegenParser` class that orchestrates the parsing process.
- `analysis`: Contains the `CodebaseAnalysisHarness` for comprehensive codebase analysis.
- `snapshot`: Contains the `CodebaseContextSnapshot` for saving and restoring codebase state.
- `context_server`: Contains the `CodeContextRetrievalServer` for accessing functionality via API.

______________________________________________________________________

## Original Functionality

### Running on Modal

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
  - **single:** Parses a single repository specified by its URL (`--single-url \"https://github.com/codegen-sh/codegen-sdk.git\"`) and an optional commit hash (`--single-commit ...`).
  - **github:** Uses GitHub settings, language (`--github-language python`) and heuristic (`--github-heuristic stars`) to query for top repositories.

- **Result Storage:**
  Upon completion, logs and metrics are automatically uploaded to the S3 bucket specified by the environment variable `BUCKET_NAME` (default: `codegen-oss-parse`). The AWS Credentials provided in the secret are used for this operation.

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

