# Codebase Analysis API

This example demonstrates how to create a comprehensive API for codebase analysis using the Codegen SDK. The API provides detailed insights into your codebase structure, quality, and dependencies.

## Features

- **Comprehensive Analysis**: Get detailed metrics about your codebase including file statistics, symbol analysis, complexity metrics, and more.
- **Visualization Support**: Generate visual representations of your codebase structure, dependencies, and call graphs.
- **Issue Detection**: Identify potential issues like unused code, circular dependencies, and high complexity functions.
- **Language-Specific Analysis**: Get specialized insights for Python and TypeScript codebases.

## Usage

### Running the API Server

```bash
python api.py
```

This will start a FastAPI server on port 8000 by default.

### API Endpoints

- `GET /analyze/{repo_url}`: Analyze a GitHub repository
- `POST /analyze/local`: Analyze a local codebase (requires uploading a zip file)
- `GET /visualize/{repo_url}/{visualization_type}`: Generate a visualization of the codebase

## Example Request

```bash
curl -X GET "http://localhost:8000/analyze/github.com/username/repo"
```

## Example Response

The API returns a comprehensive JSON response with detailed analysis of the codebase, including:

- Overall statistics (file count, language breakdown, etc.)
- Important entry points and main files
- Project structure with detailed information
- Code quality issues (unused imports, functions, classes, etc.)
- Visualization options

## Configuration

You can configure the API by setting environment variables:

- `PORT`: The port to run the server on (default: 8000)
- `HOST`: The host to bind to (default: 0.0.0.0)
- `MAX_REPO_SIZE`: Maximum repository size in MB (default: 100)
- `ANALYSIS_TIMEOUT`: Maximum time in seconds for analysis (default: 300)

## Dependencies

- Codegen SDK
- FastAPI
- Uvicorn
- NetworkX
- Plotly

