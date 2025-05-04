# WSL2 Server for Code Analysis

The WSL2 Server provides a robust backend for code validation, repository comparison, and PR analysis. It is designed to run on Windows Subsystem for Linux (WSL2) and provides a RESTful API for interacting with the code analysis tools.

## Features

- **Code Validation**: Analyze a repository for code quality, security, and maintainability issues
- **Repository Comparison**: Compare two repositories or branches to identify changes and assess risk
- **PR Analysis**: Analyze pull requests for code quality, issues, and provide recommendations
- **Error Handling**: Robust error handling with detailed error messages and traceback information
- **Retry Logic**: Automatic retry for failed requests with configurable retry parameters
- **Integration with External Tools**: Integration with ctrlplane, weave, probot, pkg.pr.new, and tldr

## Components

### Server (wsl_server.py)

The server component provides a FastAPI-based RESTful API with the following endpoints:

- **GET /**: Root endpoint providing information about available endpoints
- **GET /health**: Health check endpoint
- **POST /validate**: Validate a repository for code quality, security, and maintainability
- **POST /compare**: Compare two repositories or branches
- **POST /analyze-pr**: Analyze a pull request

### Client (wsl_client.py)

The client component provides a Python client for interacting with the WSL2 server:

- **WSLClient**: Client for interacting with the WSL2 server
  - **health_check()**: Check the health of the WSL2 server
  - **validate_codebase()**: Validate a codebase
  - **compare_repositories()**: Compare two repositories or branches
  - **analyze_pr()**: Analyze a pull request
  - **format_*_markdown()**: Format results as Markdown
  - **save_results_to_file()**: Save results to a file
  - **load_results_from_file()**: Load results from a file

### Deployment (wsl_deployment.py)

The deployment component provides utilities for deploying the WSL2 server:

- **WSLDeployment**: Utilities for deploying the WSL2 server
  - **check_wsl_installed()**: Check if WSL is installed
  - **check_distro_installed()**: Check if the specified WSL distribution is installed
  - **install_dependencies()**: Install dependencies in the WSL distribution
  - **deploy_server()**: Deploy the WSL2 server
  - **stop_server()**: Stop the WSL2 server

### CLI (wsl_cli.py)

The CLI component provides a command-line interface for deploying the WSL2 server and interacting with it:

- **deploy**: Deploy the WSL2 server
- **stop**: Stop the WSL2 server
- **validate**: Validate a codebase
- **compare**: Compare two repositories or branches
- **analyze-pr**: Analyze a pull request

### Integration (wsl_integration.py)

The integration component provides integration with external tools:

- **CtrlplaneIntegration**: Integration with ctrlplane for deployment orchestration
- **WeaveIntegration**: Integration with weave for visualization
- **ProbotIntegration**: Integration with probot for GitHub automation
- **PkgPrNewIntegration**: Integration with pkg.pr.new for continuous preview releases
- **TldrIntegration**: Integration with tldr for PR summarization

## Scripts

The scripts directory contains several scripts for analyzing codebases:

- **analyze_code_integrity.py**: Analyze code integrity in a repository
- **analyze_code_integrity_example.py**: Example script for analyzing code integrity
- **compare_pr_codebase.py**: Compare a PR version of a codebase with the base branch
- **error_analyzer.py**: Analyze and report errors in a codebase
- **codebase_analyzer.py**: Analyze a codebase for structure, dependencies, complexity, and more

## Getting Started

### Prerequisites

- Windows 10 or later with WSL2 installed
- A WSL2 distribution (e.g., Ubuntu)
- Python 3.8 or later

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/codegen-on-oss
```

2. Install the package:

```bash
pip install -e .
```

### Deploying the Server

Deploy the WSL2 server using the CLI:

```bash
python -m codegen_on_oss.analysis.wsl_cli deploy
```

This will:
- Check if WSL is installed
- Check if the specified distribution is installed
- Install dependencies
- Deploy the server

### Using the Client

Use the WSLClient to interact with the server:

```python
from codegen_on_oss.analysis.wsl_client import WSLClient

# Initialize client
client = WSLClient(base_url="http://localhost:8000")

# Check server health
health = client.health_check()
print(f"Server health: {health['status']}")

# Validate a codebase
results = client.validate_codebase(
    repo_url="https://github.com/example/repo.git",
    branch="main",
    categories=["code_quality", "security", "maintainability"],
)

# Format results as Markdown
markdown = client.format_validation_results_markdown(results)
print(markdown)

# Save results to file
client.save_results_to_file(results, "validation_results.json")
```

### Using the Scripts

Use the scripts to analyze codebases:

```bash
# Analyze code integrity
python -m codegen_on_oss.scripts.analyze_code_integrity --repo /path/to/repo --output results.json

# Compare PR codebase
python -m codegen_on_oss.scripts.compare_pr_codebase https://github.com/example/repo.git 123 --output pr_comparison.json

# Analyze errors
python -m codegen_on_oss.scripts.error_analyzer /path/to/repo --output errors.json

# Analyze codebase
python -m codegen_on_oss.scripts.codebase_analyzer /path/to/repo --output codebase_analysis.json
```

## Error Handling

The WSL2 server and client include robust error handling:

- **Server-side**: The server catches and logs all exceptions, returning structured error responses
- **Client-side**: The client includes retry logic for transient errors and provides structured error responses

## Customization

The WSL2 server and client can be customized through various parameters:

- **Server**: Configure the server through environment variables (e.g., `CODEGEN_API_KEY`)
- **Client**: Configure the client through constructor parameters (e.g., `timeout`, `max_retries`, `retry_delay`)
- **Deployment**: Configure the deployment through constructor parameters (e.g., `wsl_distro`, `port`, `use_docker`, `use_ctrlplane`)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

