# Codegen-on-OSS

A comprehensive code analysis and metrics system for open-source repositories.

## Overview

Codegen-on-OSS is a powerful system for analyzing code repositories, commits, and pull requests. It provides detailed metrics, issue detection, and insights into code quality and structure. The system is designed to be extensible, allowing for easy integration with various code analysis tools and metrics.

## Features

- **Repository Analysis**: Analyze entire repositories to get comprehensive metrics and insights.
- **Commit Analysis**: Analyze specific commits to understand changes and their impact.
- **Pull Request Analysis**: Analyze pull requests to ensure code quality and proper implementation.
- **Symbol Analysis**: Analyze specific functions, classes, and variables to understand their complexity and dependencies.
- **Feature Analysis**: Analyze specific features (files or directories) to understand their structure and quality.
- **Metrics Collection**: Collect various code quality metrics, such as cyclomatic complexity, maintainability index, and lines of code.
- **Issue Detection**: Detect code quality issues, such as high complexity, low maintainability, and code smells.
- **Dependency Analysis**: Analyze dependencies between symbols, such as function calls, class inheritance, and imports.
- **Snapshot Management**: Create and compare snapshots of codebases at specific points in time.
- **API Integration**: Integrate with other tools and services through a comprehensive API.

## Architecture

Codegen-on-OSS has a modular architecture with the following components:

### Enhanced Database Architecture

The enhanced database architecture provides a comprehensive data model for storing and retrieving code analysis data:

- **Unified Data Model**: A comprehensive data model that connects all aspects of code analysis, including repositories, commits, files, symbols, snapshots, and analysis results.
- **Efficient Storage**: Properly designed database schema for efficient querying and storage of code analysis data.
- **Repository Pattern**: A clean repository pattern for database operations, making it easy to interact with the database.
- **Connection Management**: Efficient connection management with connection pooling and transaction support.

### Enhanced Analysis Architecture

The enhanced analysis architecture provides a comprehensive pipeline for analyzing code repositories, commits, symbols, and features:

- **Analysis Pipeline**: A structured pipeline for code analysis, with different analyzers for repositories, commits, symbols, and features.
- **Coordinator Pattern**: A coordinator that orchestrates the execution of different analyzers and collectors.
- **Metrics Collection**: Comprehensive metrics collection for code quality analysis.
- **Issue Detection**: Detection of code quality issues, such as high complexity, low maintainability, and code smells.
- **Dependency Analysis**: Analysis of dependencies between symbols, such as function calls, class inheritance, and imports.
- **Snapshot Generation**: Generation of snapshots of codebases at specific points in time, with support for differential snapshots.
- **API Integration**: Integration with the API server, providing endpoints for analyzing repositories, commits, symbols, and features.

### API Server

The API server provides a comprehensive API for interacting with the system:

- **Repository Analysis**: Analyze repositories and get comprehensive metrics.
- **Commit Analysis**: Analyze commits and understand their impact.
- **Pull Request Analysis**: Analyze pull requests to ensure code quality.
- **Symbol Analysis**: Analyze specific symbols to understand their complexity.
- **Feature Analysis**: Analyze specific features to understand their structure.
- **Snapshot Management**: Create and compare snapshots of codebases.
- **Metrics Retrieval**: Retrieve metrics for repositories, files, and symbols.
- **Issue Retrieval**: Retrieve issues for repositories, files, and symbols.

## Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/codegen-on-oss.git
   cd codegen-on-oss
   ```

2. Install the dependencies:
   ```bash
   pip install -e .
   ```

3. Set up the database:
   ```bash
   # Create a PostgreSQL database
   createdb codegen_oss

   # Set environment variables for database connection
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_USER=postgres
   export DB_PASSWORD=postgres
   export DB_DATABASE=codegen_oss
   ```

4. Run the server:
   ```bash
   python -m codegen_on_oss.analysis.server
   ```

## Usage

### API Endpoints

The API server provides the following endpoints:

- `POST /api/v1/analyze/repository`: Analyze a repository.
- `POST /api/v1/analyze/commit`: Analyze a commit.
- `POST /api/v1/analyze/symbol`: Analyze a symbol.
- `POST /api/v1/snapshots/create`: Create a snapshot.
- `POST /api/v1/snapshots/compare`: Compare snapshots.
- `GET /api/v1/repositories`: List repositories.
- `GET /api/v1/snapshots`: List snapshots.
- `GET /api/v1/analysis-results`: List analysis results.

### Example: Analyzing a Repository

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/repository" \
     -H "Content-Type: application/json" \
     -d '{"repo_url": "https://github.com/example/example-repo"}'
```

### Example: Analyzing a Commit

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/commit" \
     -H "Content-Type: application/json" \
     -d '{"repo_url": "https://github.com/example/example-repo", "commit_sha": "abc123"}'
```

### Example: Creating a Snapshot

```bash
curl -X POST "http://localhost:8000/api/v1/snapshots/create" \
     -H "Content-Type: application/json" \
     -d '{"repo_url": "https://github.com/example/example-repo", "description": "Initial snapshot"}'
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
