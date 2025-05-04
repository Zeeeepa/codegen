# Codegen-on-OSS

A comprehensive code analysis and management system built on the Codegen SDK.

## Overview

Codegen-on-OSS provides a suite of tools for code analysis, codebase snapshots, PR review, and WSL integration. It is designed to help developers understand, analyze, and improve their codebases.

## Features

- **Code Analysis**: Analyze code complexity, features, and integrity
- **Codebase Snapshots**: Create and compare snapshots of codebases
- **PR Review**: Automatically review pull requests
- **WSL Integration**: Run code analysis in WSL environments
- **API**: REST and WebSocket APIs for integration with other tools

## Architecture

The system is organized into the following modules:

- **analysis**: Code analysis functionality
- **snapshot**: Codebase snapshot and PR review functionality
- **wsl**: WSL integration functionality
- **api**: REST and WebSocket APIs
- **database**: Database management
- **events**: Event-driven architecture
- **outputs**: Output generation
- **sources**: Data sources

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/codegen-on-oss.git
cd codegen-on-oss

# Install dependencies
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Run the CLI
python -m codegen_on_oss.cli --help

# Analyze a repository
python -m codegen_on_oss.cli analyze --repo-path /path/to/repo

# Create a snapshot
python -m codegen_on_oss.cli snapshot create --repo-path /path/to/repo

# Review a PR
python -m codegen_on_oss.cli pr review --repo-url https://github.com/user/repo --pr-number 123

# Run the WSL server
python -m codegen_on_oss.scripts.run_wsl_server
```

### API

```bash
# Run the API server
python -m codegen_on_oss.app
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

