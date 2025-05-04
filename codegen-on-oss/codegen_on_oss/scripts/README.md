# Codegen-on-OSS Scripts

This directory contains utility scripts for the Codegen-on-OSS project.

## Scripts Overview

### analyze_code_integrity.py

A script for analyzing code integrity in a repository. It can:
- Find all functions and classes
- Identify errors in functions and classes
- Detect improper parameter usage
- Find incorrect function callback points
- Compare error counts between branches
- Analyze code complexity and duplication
- Check for type hint usage
- Detect unused imports

Usage:
```bash
python -m codegen_on_oss.scripts.analyze_code_integrity --repo /path/to/repo --output results.json --html report.html
```

### analyze_code_integrity_example.py

An example script demonstrating how to use the CodeIntegrityAnalyzer to analyze code integrity for a repository.

Usage:
```bash
python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --output results.json --html report.html
```

### create_db.py

A script for creating the database schema for the Codegen-on-OSS project.

Usage:
```bash
python -m codegen_on_oss.scripts.create_db
```

### wsl_server_cli.py

A comprehensive command-line interface for deploying, managing, and interacting with the WSL2 server for code validation.

Usage:
```bash
# Deploy the server
python -m codegen_on_oss.scripts.wsl_server_cli deploy

# Check server status
python -m codegen_on_oss.scripts.wsl_server_cli status

# Stop the server
python -m codegen_on_oss.scripts.wsl_server_cli stop

# Validate a codebase
python -m codegen_on_oss.scripts.wsl_server_cli validate --repo https://github.com/user/repo

# Compare repositories
python -m codegen_on_oss.scripts.wsl_server_cli compare --base-repo https://github.com/user/repo1 --head-repo https://github.com/user/repo2

# Analyze a PR
python -m codegen_on_oss.scripts.wsl_server_cli analyze-pr --repo https://github.com/user/repo --pr-number 123
```

## Adding New Scripts

When adding new scripts to this directory, please follow these guidelines:
1. Include a docstring at the top of the script explaining its purpose
2. Add proper error handling
3. Use logging instead of print statements
4. Update this README with information about the new script
