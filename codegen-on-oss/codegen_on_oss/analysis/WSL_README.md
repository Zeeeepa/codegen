# WSL2 Server for Code Validation

This module provides a complete solution for running codegen on a WSL2 server backend for code validation, with integration for ctrlplane, ctrlcli, weave, probot, pkg.pr.new, and tldr.

## Overview

The WSL2 server implementation consists of the following components:

1. **WSL Server** (`wsl_server.py`): A FastAPI server that provides endpoints for code validation, repository comparison, and PR analysis.
2. **WSL Client** (`wsl_client.py`): A Python client for interacting with the WSL2 server.
3. **WSL Deployment** (`wsl_deployment.py`): Utilities for deploying the WSL2 server, with support for Docker and ctrlplane.
4. **WSL CLI** (`wsl_cli.py`): A command-line interface for deploying the server and interacting with it.
5. **WSL Integration** (`wsl_integration.py`): Integration with external tools like ctrlplane, weave, probot, pkg.pr.new, and tldr.

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
    use_docker=True,
    use_ctrlplane=False,
)

# Check if WSL is installed
if not deployment.check_wsl_installed():
    print("WSL is not installed")
    exit(1)

# Check if the distribution is installed
if not deployment.check_distro_installed():
    print(f"Distribution {deployment.wsl_distro} is not installed")
    exit(1)

# Install dependencies
deployment.install_dependencies()

# Deploy server
deployment.deploy_server()
```

## Usage

### Using the CLI

Once the server is deployed, you can use the CLI to interact with it:

```bash
# Validate a codebase
python -m codegen_on_oss.analysis.wsl_cli validate https://github.com/username/repo

# Validate a specific branch
python -m codegen_on_oss.analysis.wsl_cli validate https://github.com/username/repo --branch develop

# Validate specific categories
python -m codegen_on_oss.analysis.wsl_cli validate https://github.com/username/repo --categories code_quality,security

# Compare two repositories
python -m codegen_on_oss.analysis.wsl_cli compare https://github.com/username/repo1 https://github.com/username/repo2

# Compare two branches
python -m codegen_on_oss.analysis.wsl_cli compare https://github.com/username/repo https://github.com/username/repo --base-branch main --head-branch develop

# Analyze a pull request
python -m codegen_on_oss.analysis.wsl_cli analyze-pr https://github.com/username/repo 123

# Analyze a pull request and post a comment
python -m codegen_on_oss.analysis.wsl_cli analyze-pr https://github.com/username/repo 123 --post-comment

# Format output as JSON
python -m codegen_on_oss.analysis.wsl_cli validate https://github.com/username/repo --format json

# Format output as Markdown
python -m codegen_on_oss.analysis.wsl_cli validate https://github.com/username/repo --format markdown

# Save output to a file
python -m codegen_on_oss.analysis.wsl_cli validate https://github.com/username/repo --output results.json
```

### Using the Client API

You can also use the client API to interact with the server programmatically:

```python
from codegen_on_oss.analysis.wsl_client import WSLClient

# Initialize client
client = WSLClient(
    base_url="http://localhost:8000",
    api_key="your-api-key",
)

# Check server health
health = client.health_check()
print(f"Server health: {health['status']}")

# Validate a codebase
results = client.validate_codebase(
    repo_url="https://github.com/username/repo",
    branch="main",
    categories=["code_quality", "security", "maintainability"],
    github_token="your-github-token",
)

# Format results as Markdown
markdown = client.format_validation_results_markdown(results)
print(markdown)

# Save results to a file
client.save_results_to_file(results, "results.json")

# Compare two repositories
comparison = client.compare_repositories(
    base_repo_url="https://github.com/username/repo1",
    head_repo_url="https://github.com/username/repo2",
    base_branch="main",
    head_branch="main",
    github_token="your-github-token",
)

# Analyze a pull request
pr_analysis = client.analyze_pr(
    repo_url="https://github.com/username/repo",
    pr_number=123,
    github_token="your-github-token",
    detailed=True,
    post_comment=False,
)
```

### Integration with External Tools

The WSL2 server implementation includes integration with several external tools:

#### ctrlplane

```python
from codegen_on_oss.analysis.wsl_integration import CtrlplaneIntegration

# Initialize integration
ctrlplane = CtrlplaneIntegration(api_key="your-ctrlplane-api-key")

# Deploy a service
ctrlplane.deploy_service(
    name="codegen-wsl-server",
    command="python -m codegen_on_oss.analysis.wsl_server",
    environment={"CODEGEN_API_KEY": "your-api-key"},
    ports=[{"internal": 8000, "external": 8000}],
)

# Stop a service
ctrlplane.stop_service("codegen-wsl-server")
```

#### weave

```python
from codegen_on_oss.analysis.wsl_integration import WeaveIntegration

# Initialize integration
weave = WeaveIntegration(api_key="your-weave-api-key")

# Create a visualization
url = weave.create_visualization(
    data=results,
    title="Code Validation Results",
    description="Results of code validation for repository",
)
```

#### probot

```python
from codegen_on_oss.analysis.wsl_integration import ProbotIntegration

# Initialize integration
probot = ProbotIntegration(github_token="your-github-token")

# Register a webhook
probot.register_webhook(
    repo="username/repo",
    events=["pull_request", "push"],
    webhook_url="https://your-webhook-url.com",
    secret="your-webhook-secret",
)
```

#### pkg.pr.new

```python
from codegen_on_oss.analysis.wsl_integration import PkgPrNewIntegration

# Initialize integration
pkg_pr_new = PkgPrNewIntegration(api_key="your-pkg-pr-new-api-key")

# Create a preview release
url = pkg_pr_new.create_preview_release(
    repo="username/repo",
    branch="feature-branch",
    version="0.1.0-preview",
    package_name="your-package",
)
```

#### tldr

```python
from codegen_on_oss.analysis.wsl_integration import TldrIntegration

# Initialize integration
tldr = TldrIntegration(github_token="your-github-token")

# Summarize a pull request
summary = tldr.summarize_pr(
    repo="username/repo",
    pr_number=123,
    post_comment=True,
)
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

