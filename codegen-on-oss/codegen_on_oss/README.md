# Codegen OSS Analysis System

A comprehensive system for analyzing codebases, tracking changes, and providing insights through a unified API.

## Architecture

The Codegen OSS Analysis System is built with a modular, service-oriented architecture that enables seamless data flow, storage, and retrieval. The system consists of the following components:

### Core Components

1. **Database Layer**
   - Unified schema for all analysis data
   - Support for PostgreSQL, SQLite, and other SQL databases
   - Efficient storage of snapshots, metrics, and analysis results

2. **Storage Service**
   - Pluggable storage backends (local, S3, memory)
   - Efficient incremental storage of file content
   - Content-addressable storage to minimize duplication

3. **Snapshot Service**
   - Create point-in-time snapshots of codebases
   - Track changes between snapshots
   - Efficient storage with deduplication

4. **Analysis Service**
   - Code quality analysis
   - Dependency analysis
   - Security analysis
   - File and symbol analysis

5. **API Layer**
   - RESTful API for all operations
   - GraphQL support for complex queries
   - WebSocket support for real-time updates

6. **Task Queue**
   - Background processing of long-running analyses
   - Scalable worker architecture
   - Progress tracking and notifications

## Getting Started

### Installation

```bash
# Install from PyPI
pip install codegen-on-oss

# Or install from source
git clone https://github.com/codegen-sh/codegen.git
cd codegen/codegen-on-oss
pip install -e .
```

### Configuration

Create a `.env` file with your configuration:

```env
# Database settings
DB_URL=sqlite:///./codegen_analysis.db
# DB_URL=postgresql://user:password@localhost:5432/codegen

# Storage settings
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./storage
# STORAGE_TYPE=s3
# S3_BUCKET=my-bucket
# S3_REGION=us-west-2

# API settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
ENABLE_GRAPHQL=true
ENABLE_WEBSOCKETS=true

# Task queue settings
REDIS_URL=redis://localhost:6379/0
MAX_WORKERS=4
```

### Initialize the Database

```bash
codegen-oss init
```

### Start the API Server

```bash
codegen-oss server
```

### Start Task Queue Workers

```bash
codegen-oss worker
```

## Usage

### Create a Snapshot

```bash
codegen-oss snapshot https://github.com/username/repo --branch main
```

### Analyze a Repository

```bash
codegen-oss analyze https://github.com/username/repo --branch main --types code_quality dependencies security
```

### API Examples

#### Create a Snapshot

```bash
curl -X POST http://localhost:8000/api/snapshots \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/username/repo", "branch": "main"}'
```

#### Request Analysis

```bash
curl -X POST http://localhost:8000/api/analysis/request \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/username/repo", "branch": "main", "analysis_types": ["code_quality", "dependencies", "security"]}'
```

#### Get Analysis Results

```bash
curl http://localhost:8000/api/snapshots/{snapshot_id}/analysis/code_quality
```

## GraphQL Support

If GraphQL is enabled, you can access the GraphQL playground at:

```
http://localhost:8000/graphql
```

Example query:

```graphql
query {
  snapshots(repository: "https://github.com/username/repo", limit: 5) {
    id
    repository
    commitSha
    branch
    createdAt
  }
}
```

## WebSocket Support

If WebSockets are enabled, you can subscribe to analysis job updates:

```javascript
const socket = new WebSocket('ws://localhost:8000/ws/analysis/{job_id}');

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Analysis progress:', data.progress);
};
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms of the MIT license.

