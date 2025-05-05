# WSL2 Server for Code Validation

This module provides a complete solution for running codegen on a WSL2 server backend for code validation, with integration for ctrlplane, ctrlcli, weave, probot, pkg.pr.new, and tldr.

## Overview

The WSL2 server implementation consists of the following components:

1. **WSL Server** (`wsl_server.py`): A FastAPI server that provides endpoints for code validation, repository comparison, and PR analysis.
1. **WSL Client** (`wsl_client.py`): A Python client for interacting with the WSL2 server.
1. **WSL Deployment** (`wsl_deployment.py`): Utilities for deploying the WSL2 server, with support for Docker and ctrlplane.
1. **WSL CLI** (`wsl_cli.py`): A command-line interface for deploying the server and interacting with it.
1. **WSL Integration** (`wsl_integration.py`): Integration with external tools like ctrlplane, weave, probot, pkg.pr.new, and tldr.

## Installation

### Prerequisites

- Windows 10/11 with WSL2 installed
- Ubuntu or another Linux distribution installed in WSL2
- Python 3.8 or higher
- Git

### Installing the Package

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen

# Install the package
pip install -e .
```

## Deployment

### Using the CLI

The easiest way to deploy the WSL2 server is using the CLI:

```bash
# Deploy the server
python -m codegen_on_oss.analysis.wsl_cli deploy

# Deploy with Docker
python -m codegen_on_oss.analysis.wsl_cli deploy --docker

# Deploy with ctrlplane
python -m codegen_on_oss.analysis.wsl_cli deploy --ctrlplane

# Deploy with a custom API key
python -m codegen_on_oss.analysis.wsl_cli deploy --api-key your-api-key

# Deploy on a custom port
python -m codegen_on_oss.analysis.wsl_cli deploy --port 8080

# Deploy on a specific WSL distribution
python -m codegen_on_oss.analysis.wsl_cli deploy --distro Ubuntu-20.04
```

### Using the Deployment API

You can also deploy the server programmatically:

```python
from codegen_on_oss.analysis.wsl_deployment import WSLDeployment

# Initialize deployment
deployment = WSLDeployment(
    wsl_distro="Ubuntu",
    port=8000,
    api_key="your-api-key",
    use_docker=False,
    use_ctrlplane=False,
)

# Check if WSL is installed
if not deployment.check_wsl_installed():
    print("WSL is not installed. Please install WSL first.")
    exit(1)

# Check if the specified distribution is installed
if not deployment.check_distro_installed():
    print(f"WSL distribution '{deployment.wsl_distro}' is not installed.")
    print(f"Please install it using: wsl --install -d {deployment.wsl_distro}")
    exit(1)

# Install dependencies
print("Installing dependencies...")
if not deployment.install_dependencies():
    print("Failed to install dependencies.")
    exit(1)

# Deploy server
print("Deploying server...")
if not deployment.deploy_server():
    print("Failed to deploy server.")
    exit(1)

print(f"Server deployed successfully on port {deployment.port}.")
print(f"You can access the server at: http://localhost:{deployment.port}")
```

## Usage

### Deployment

The `WSLDeployment` class provides utilities for deploying the WSL2 server:

```python
from codegen_on_oss.server.wsl.deployment import WSLDeployment

# Initialize deployment
deployment = WSLDeployment(
    wsl_distro="Ubuntu",
    port=8000,
    api_key="your-api-key",
    use_docker=False,
    use_ctrlplane=False,
)

# Check if WSL is installed
if not deployment.check_wsl_installed():
    print("WSL is not installed. Please install WSL first.")
    exit(1)

# Check if the specified distribution is installed
if not deployment.check_distro_installed():
    print(f"WSL distribution '{deployment.wsl_distro}' is not installed.")
    print(f"Please install it using: wsl --install -d {deployment.wsl_distro}")
    exit(1)

# Install dependencies
print("Installing dependencies...")
if not deployment.install_dependencies():
    print("Failed to install dependencies.")
    exit(1)

# Deploy server
print("Deploying server...")
if not deployment.deploy_server():
    print("Failed to deploy server.")
    exit(1)

print(f"Server deployed successfully on port {deployment.port}.")
print(f"You can access the server at: http://localhost:{deployment.port}")
```

### Client

The `WSLClient` class provides a client for interacting with the WSL2 server:

```python
from codegen_on_oss.server.wsl.client import WSLClient

# Initialize client
client = WSLClient(
    base_url="http://localhost:8000",
    api_key="your-api-key",
)

# Check server health
health = client.health_check()
print(f"Server health: {health['status']}")

# Validate codebase
results = client.validate_codebase(
    repo_url="https://github.com/username/repo",
    branch="main",
    categories=["code_quality", "security", "maintainability"],
    github_token="your-github-token",
)

# Format results as Markdown
markdown = client.format_validation_results_markdown(results)
print(markdown)

# Save results to file
client.save_results_to_file(results, "validation_results.json")
```

### Integration

The WSL2 server can be integrated with various external tools:

#### ctrlplane

```python
from codegen_on_oss.server.wsl.integration import CtrlplaneIntegration

# Initialize integration
integration = CtrlplaneIntegration(
    api_key="your-ctrlplane-api-key",
    project_id="your-project-id",
)

# Deploy server using ctrlplane
integration.deploy_server(
    wsl_distro="Ubuntu",
    port=8000,
    api_key="your-api-key",
)
```

#### weave

```python
from codegen_on_oss.server.wsl.integration import WeaveIntegration

# Initialize integration
integration = WeaveIntegration(
    api_key="your-weave-api-key",
    project_id="your-project-id",
)

# Visualize validation results
integration.visualize_results(results)
```

#### probot

```python
from codegen_on_oss.server.wsl.integration import ProbotIntegration

# Initialize integration
integration = ProbotIntegration(
    api_key="your-probot-api-key",
    repo_url="https://github.com/username/repo",
)

# Automate PR validation
integration.validate_pr(pr_number=123)
```

#### pkg.pr.new

```python
from codegen_on_oss.server.wsl.integration import PkgPrNewIntegration

# Initialize integration
integration = PkgPrNewIntegration(
    api_key="your-pkg-pr-new-api-key",
    repo_url="https://github.com/username/repo",
)

# Create preview release
integration.create_preview_release(version="1.0.0")
```

#### tldr

```python
from codegen_on_oss.server.wsl.integration import TldrIntegration

# Initialize integration
integration = TldrIntegration(
    api_key="your-tldr-api-key",
    repo_url="https://github.com/username/repo",
)

# Summarize PR
integration.summarize_pr(pr_number=123)
```

## API Reference

### WSL Server API

The WSL2 server provides the following endpoints:

- `GET /`: Root endpoint that returns information about the server.
- `GET /health`: Health check endpoint.
- `POST /validate`: Validate a codebase.
- `POST /compare`: Compare two repositories or branches.
- `POST /analyze-pr`: Analyze a pull request.

### WSL Client API

The WSL client provides the following methods:

- `health_check()`: Check the health of the WSL2 server.
- `validate_codebase()`: Validate a codebase.
- `compare_repositories()`: Compare two repositories or branches.
- `analyze_pr()`: Analyze a pull request.
- `format_validation_results_markdown()`: Format validation results as Markdown.
- `format_comparison_results_markdown()`: Format comparison results as Markdown.
- `format_pr_analysis_markdown()`: Format PR analysis results as Markdown.
- `save_results_to_file()`: Save results to a file.
- `load_results_from_file()`: Load results from a file.

### WSL Deployment API

The WSL deployment provides the following methods:

- `check_wsl_installed()`: Check if WSL is installed.
- `check_distro_installed()`: Check if the specified WSL distribution is installed.
- `install_dependencies()`: Install dependencies in the WSL distribution.
- `deploy_server()`: Deploy the WSL2 server.
- `stop_server()`: Stop the WSL2 server.

### WSL Integration API

The WSL integration provides the following classes and methods:

- `CtrlplaneIntegration`: Integration with ctrlplane for deployment orchestration.
  - `deploy_service()`: Deploy a service using ctrlplane.
  - `stop_service()`: Stop a service using ctrlplane.
- `WeaveIntegration`: Integration with weave for visualization.
  - `create_visualization()`: Create a visualization using weave.
- `ProbotIntegration`: Integration with probot for GitHub automation.
  - `register_webhook()`: Register a webhook for a repository.
- `PkgPrNewIntegration`: Integration with pkg.pr.new for continuous preview releases.
  - `create_preview_release()`: Create a preview release.
- `TldrIntegration`: Integration with tldr for PR summarization.
  - `summarize_pr()`: Summarize a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
