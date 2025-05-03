# Enhanced Code Analysis Server

The Enhanced Code Analysis Server is a backend server for analyzing repositories, commits, branches, and pull requests. It provides detailed analysis of code quality, functionality changes, and potential issues.

## Features

- **Repository Analysis**: Analyze entire repositories for code quality and structure
- **Commit Analysis**: Analyze specific commits to determine if they are properly implemented
- **Branch Comparison**: Compare two branches to identify differences and potential issues
- **PR Validation**: Analyze pull requests to validate changes and identify issues
- **Function Analysis**: Analyze specific functions for complexity, dependencies, and issues
- **Feature Analysis**: Analyze specific features (files or directories) for quality and issues
- **Project Management**: Register and manage projects for continuous analysis
- **Webhook Integration**: Register webhooks to receive notifications about analysis results
- **Caching**: Cache analysis results for improved performance
- **Background Cleanup**: Automatically clean up temporary directories after analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen

# Install dependencies
pip install -e .
```

## Usage

### Starting the Server

```bash
# Start the server on the default host and port (0.0.0.0:8000)
python -m codegen_on_oss.analysis.enhanced_server_example --start-server

# Start the server on a specific host and port
python -m codegen_on_oss.analysis.enhanced_server_example --start-server --host localhost --port 8080
```

### Project Management

```bash
# Register a project for analysis
python -m codegen_on_oss.analysis.enhanced_server_example --register-project https://github.com/owner/repo "My Project" --webhook-url https://example.com/webhook

# Register a webhook for a project
python -m codegen_on_oss.analysis.enhanced_server_example --register-webhook project-id https://example.com/webhook
```

### Repository Analysis

```bash
# Analyze a repository
python -m codegen_on_oss.analysis.enhanced_server_example --analyze-repo https://github.com/owner/repo
```

### Commit Analysis

```bash
# Analyze a commit
python -m codegen_on_oss.analysis.enhanced_server_example --analyze-commit https://github.com/owner/repo abc123
```

### Branch Comparison

```bash
# Compare two branches
python -m codegen_on_oss.analysis.enhanced_server_example --compare-branches https://github.com/owner/repo main feature-branch
```

### PR Validation

```bash
# Analyze a pull request
python -m codegen_on_oss.analysis.enhanced_server_example --analyze-pr https://github.com/owner/repo 123

# Run a complete PR validation workflow
python -m codegen_on_oss.analysis.enhanced_server_example --pr-validation https://github.com/owner/repo 123
```

### Function Analysis

```bash
# Analyze a specific function
python -m codegen_on_oss.analysis.enhanced_server_example --analyze-function https://github.com/owner/repo "module.submodule.function_name"

# Analyze a function in a specific branch or commit
python -m codegen_on_oss.analysis.enhanced_server_example --analyze-function https://github.com/owner/repo "module.submodule.function_name" --branch feature-branch
python -m codegen_on_oss.analysis.enhanced_server_example --analyze-function https://github.com/owner/repo "module.submodule.function_name" --commit abc123
```

### Feature Analysis

```bash
# Analyze a specific feature (file or directory)
python -m codegen_on_oss.analysis.enhanced_server_example --analyze-feature https://github.com/owner/repo "path/to/feature"

# Analyze a feature in a specific branch or commit
python -m codegen_on_oss.analysis.enhanced_server_example --analyze-feature https://github.com/owner/repo "path/to/feature" --branch feature-branch
python -m codegen_on_oss.analysis.enhanced_server_example --analyze-feature https://github.com/owner/repo "path/to/feature" --commit abc123
```

## API Endpoints

The server exposes the following API endpoints:

- `GET /`: Get information about the server and available endpoints
- `POST /analyze_repo`: Analyze a repository
- `POST /analyze_commit`: Analyze a commit in a repository
- `POST /compare_branches`: Compare two branches in a repository
- `POST /analyze_pr`: Analyze a pull request in a repository
- `POST /register_project`: Register a project for analysis
- `POST /register_webhook`: Register a webhook
- `POST /analyze_function`: Analyze a specific function
- `POST /analyze_feature`: Analyze a specific feature

## Webhook Integration

The server can send webhook notifications when analysis is complete. Webhooks can be registered for the following events:

- `pr`: Pull request analysis
- `commit`: Commit analysis
- `branch`: Branch comparison

Webhook payloads include the analysis results and metadata about the event.

## Using as a Backend Service

The Enhanced Code Analysis Server is designed to be used as a backend service for PR validation and codebase analysis. It can be integrated with other systems through its API endpoints and webhook notifications.

### Example: PR Validation Workflow

1. Register a project for analysis
2. Set up a webhook to receive notifications
3. When a PR is created or updated, analyze the PR
4. Analyze specific features and functions in the PR
5. Send the analysis results to the webhook
6. Display the results in your frontend application

### Example: Continuous Analysis

1. Register a project for analysis
2. Set up a webhook to receive notifications
3. Periodically analyze the repository and its branches
4. Send the analysis results to the webhook
5. Display the results in your dashboard

## Configuration

The server can be configured through environment variables:

- `ANALYSIS_SERVER_HOST`: Host to bind the server to (default: 0.0.0.0)
- `ANALYSIS_SERVER_PORT`: Port to bind the server to (default: 8000)
- `ANALYSIS_SERVER_DATA_DIR`: Directory to store project data (default: ~/.codegen_analysis)
- `ANALYSIS_SERVER_CACHE_SIZE`: Maximum number of cached analysis results (default: 100)
- `ANALYSIS_SERVER_CACHE_TTL`: Time-to-live for cached results in seconds (default: 3600)
- `ANALYSIS_SERVER_LOG_LEVEL`: Logging level (default: INFO)
- `GITHUB_TOKEN`: GitHub token for accessing private repositories

## Development

### Running Tests

```bash
# Run all tests
pytest codegen_on_oss/analysis/tests

# Run specific tests
pytest codegen_on_oss/analysis/tests/test_server.py
```

### Adding New Features

To add new features to the server:

1. Add new request and response models in `server.py`
2. Add new endpoints in `server.py`
3. Add new analysis functionality in the appropriate module
4. Update the documentation in `README_ENHANCED.md`
5. Add tests for the new functionality

## License

This project is licensed under the MIT License - see the LICENSE file for details.
