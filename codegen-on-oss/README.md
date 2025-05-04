# Codegen-on-OSS

Codegen-on-OSS is a Python SDK for interacting with intelligent code generation agents. This project provides tools for code analysis, validation, and comparison.

## Project Structure

```
codegen-on-oss/
├── codegen_on_oss/           # Main package
│   ├── analysis/             # Code analysis modules
│   │   ├── code_integrity_analyzer.py
│   │   ├── diff_analyzer.py
│   │   ├── wsl_client.py     # Client for WSL2 server
│   │   ├── wsl_deployment.py # Deployment utilities for WSL2 server
│   │   ├── wsl_integration.py # Integration with external tools
│   │   ├── wsl_server.py     # FastAPI server for code validation
│   │   └── ...
│   ├── scripts/              # Utility scripts
│   │   ├── analyze_code_integrity.py
│   │   ├── create_db.py
│   │   ├── wsl_server_cli.py # CLI for WSL2 server
│   │   └── ...
│   ├── snapshot/             # Codebase snapshot modules
│   │   ├── codebase_snapshot.py
│   │   └── ...
│   └── ...
├── scripts/                  # Legacy scripts (moved to codegen_on_oss/scripts)
└── ...
```

## WSL2 Server

The WSL2 server provides a robust backend for code validation, repository comparison, and PR analysis. It can be deployed using Docker, ctrlplane, or directly on WSL2.

### Features

- **Code Validation**: Analyze a repository for code quality, security, and maintainability issues
- **Repository Comparison**: Compare two repositories or branches and identify differences
- **PR Analysis**: Analyze a pull request and provide feedback on code quality and potential issues
- **Error Handling**: Robust error handling with detailed error messages
- **Logging**: Comprehensive logging for debugging and monitoring
- **API Key Authentication**: Secure API key authentication for protected endpoints
- **Docker Support**: Deploy the server using Docker for easy setup and management
- **ctrlplane Integration**: Deploy the server using ctrlplane for orchestration
- **Systemd Integration**: Deploy the server as a systemd service for reliable operation

### Deployment

The WSL2 server can be deployed using the `wsl_server_cli.py` script:

```bash
python -m codegen_on_oss.scripts.wsl_server_cli deploy
```

### Usage

The WSL2 server can be used via the `wsl_client.py` module or the `wsl_server_cli.py` script:

```python
from codegen_on_oss.analysis.wsl_client import WSLClient

client = WSLClient()
results = client.validate_codebase("https://github.com/user/repo")
```

```bash
python -m codegen_on_oss.scripts.wsl_server_cli validate --repo https://github.com/user/repo
```

## Code Analysis

The code analysis modules provide tools for analyzing code integrity, comparing repositories, and analyzing pull requests.

### Features

- **Code Integrity Analysis**: Find errors in functions and classes, detect improper parameter usage, and more
- **Diff Analysis**: Compare two repositories or branches and identify differences
- **PR Analysis**: Analyze a pull request and provide feedback on code quality and potential issues

### Usage

```python
from codegen_on_oss.analysis.code_integrity_analyzer import CodeIntegrityAnalyzer
from codegen import Codebase

codebase = Codebase.from_repo("/path/to/repo")
analyzer = CodeIntegrityAnalyzer(codebase)
results = analyzer.analyze()
```

## Scripts

The `scripts` directory contains utility scripts for the Codegen-on-OSS project. See the [scripts README](codegen_on_oss/scripts/README.md) for more information.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

