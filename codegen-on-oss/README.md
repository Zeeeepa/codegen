# Codegen-on-OSS: Enhanced Analysis System

The **Codegen on OSS** package provides a comprehensive system for code analysis, snapshotting, and visualization. The enhanced system includes:

- **Unified Database Integration**: Centralized storage for analysis results, snapshots, and metrics
- **Enhanced Analysis System**: Orchestrated analysis with dependency management and caching
- **Advanced Snapshotting**: Differential snapshots with rich metadata and comparison capabilities
- **GraphQL API**: Flexible API for frontend integration with real-time updates

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Analysis Orchestrator                           │
├─────────────────────────────────────────────────────────────────────┤
│ - Coordinates multiple analyzers                                    │
│ - Manages analysis dependencies                                     │
│ - Handles caching and invalidation                                  │
│ - Provides unified API for all analysis operations                  │
└─────────────────────────┬─────────────────────────────────────┬─────┘
                          │                                     │
    ┌─────────────────────▼───────────────────┐         ┌───────▼───────────────────┐
    │   AnalysisRegistry                      │         │   AnalysisScheduler       │
    ├─────────────────────────────────────────┤         ├───────────────────────────┤
    │ - Registers analyzers                   │         │ - Schedules analyses      │
    │ - Manages dependencies                  │         │ - Handles parallelism     │
    │ - Provides discovery                    │         │ - Manages resources       │
    └─────────────────────────────────────────┘         └───────────────────────────┘
```

### Database Schema

```
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ CodebaseSnapshot        │      │ AnalysisResult          │      │ CodeMetrics             │
├─────────────────────────┤      ├─────────────────────────┤      ├─────────────────────────┤
│ id                      │      │ id                      │      │ id                      │
│ snapshot_id             │◄─────┤ snapshot_id             │      │ analysis_id             │◄─┐
│ commit_sha              │      │ analyzer_type           │      │ complexity              │  │
│ timestamp               │      │ status                  │      │ maintainability         │  │
│ metadata                │      │ created_at              │      │ halstead_metrics        │  │
│ storage_path            │      │ completed_at            │      │ doi_metrics             │  │
└─────────────────────────┘      │ result_data             │      │ lines_of_code           │  │
                                 └─────────────────────────┘      └─────────────────────────┘  │
                                   ▲                                                           │
                                   │                                                           │
                                   │                                                           │
┌─────────────────────────┐      ┌┴────────────────────────┐                                  │
│ SymbolAnalysis          │      │ DependencyGraph         │                                  │
├─────────────────────────┤      ├─────────────────────────┤                                  │
│ id                      │      │ id                      │                                  │
│ analysis_id             │◄─┐   │ analysis_id             │◄────────────────────────────────┘
│ symbol_type             │  │   │ graph_data              │
│ symbol_name             │  │   │ node_count              │
│ file_path               │  │   │ edge_count              │
│ line_number             │  │   │ clusters                │
│ complexity              │  │   │ central_nodes           │
│ dependencies            │  │   └─────────────────────────┘
└─────────────────────────┘  │
                             │
                             └───────────────────────────────────────────────────────────────┘
```

## Package Structure

The package is composed of several modules:

- **`database`**: Database models and management
  - `models.py`: SQLAlchemy ORM models
  - `manager.py`: Database connection and operations

- **`snapshot`**: Enhanced snapshotting system
  - `enhanced_snapshot.py`: Differential snapshots with rich metadata
  - `codebase_snapshot.py`: Original snapshot implementation

- **`analysis`**: Code analysis components
  - `orchestrator.py`: Analysis orchestration and scheduling
  - `code_analyzer.py`: Code complexity analysis
  - `diff_analyzer.py`: Code diff analysis
  - `feature_analyzer.py`: Feature detection and analysis

- **`api`**: API for frontend integration
  - `server.py`: FastAPI server
  - `graphql_schema.py`: GraphQL schema

- **`sources`**: Repository source definitions
  - `github_source.py`: GitHub repository source
  - `csv_source.py`: CSV file repository source

- **`outputs`**: Output formats for analysis results
  - `sql_output.py`: SQL database output
  - `csv_output.py`: CSV file output

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/codegen-on-oss

# Install dependencies
pip install -r requirements.txt
```

### Database Setup

```bash
# Set up the database
python -m codegen_on_oss.main setup-db

# Or with a custom database URL
python -m codegen_on_oss.main setup-db --db-url postgresql://user:password@localhost:5432/codegen_oss
```

### Running the API Server

```bash
# Start the API server
python -m codegen_on_oss.main server

# With custom host and port
python -m codegen_on_oss.main server --host 127.0.0.1 --port 8080
```

## API Usage

### GraphQL API

The GraphQL API is available at `/graphql` and provides the following operations:

#### Queries

- `snapshot(id: ID!)`: Get a snapshot by ID
- `snapshots(filter: SnapshotFilter)`: Get snapshots with filtering
- `analysis(id: ID!)`: Get an analysis by ID
- `analyses(filter: AnalysisFilter)`: Get analyses with filtering
- `symbol(id: ID!)`: Get a symbol by ID
- `symbols(filter: SymbolFilter)`: Get symbols with filtering
- `metrics(analysisId: ID!)`: Get metrics for an analysis

#### Mutations

- `createSnapshot(repoUrl: String!, commitSha: String, metadata: JSONString)`: Create a new snapshot
- `runAnalysis(snapshotId: String!, analyzerType: String!, params: JSONString)`: Run an analysis
- `compareSnapshots(baseSnapshotId: String!, compareSnapshotId: String!)`: Compare two snapshots

#### Subscriptions

- `analysisProgress(id: ID!)`: Get real-time updates on analysis progress
- `snapshotCreated`: Get notified when a new snapshot is created

### REST API

The REST API provides the following endpoints:

- `POST /api/snapshots`: Create a new snapshot
- `POST /api/analyses`: Run an analysis
- `GET /api/analyses/{analysis_id}`: Get analysis results
- `GET /api/analyses/{analysis_id}/status`: Get analysis status
- `POST /api/snapshots/compare`: Compare two snapshots

## Example Usage

### Creating a Snapshot

```python
import requests

response = requests.post(
    "http://localhost:8000/api/snapshots",
    json={
        "repo_url": "https://github.com/Zeeeepa/codegen.git",
        "commit_sha": "main",
        "metadata": {
            "description": "Codegen repository snapshot"
        }
    }
)

snapshot_id = response.json()["id"]
print(f"Created snapshot with ID: {snapshot_id}")
```

### Running an Analysis

```python
import requests

response = requests.post(
    "http://localhost:8000/api/analyses",
    json={
        "snapshot_id": "snapshot_id_here",
        "analyzer_type": "CodeComplexityAnalyzer",
        "params": {
            "max_complexity": 20
        }
    }
)

analysis_id = response.json()["id"]
print(f"Started analysis with ID: {analysis_id}")
```

### Getting Analysis Results

```python
import requests

response = requests.get(
    f"http://localhost:8000/api/analyses/{analysis_id}"
)

results = response.json()
print(f"Analysis results: {results}")
```

## Contributing

Contributions are welcome! Here are some ways you can contribute:

- Implement new analyzers by subclassing `BaseAnalyzer`
- Improve the database schema and models
- Enhance the GraphQL API with new queries and mutations
- Add new frontend components for visualization

## License

This project is licensed under the MIT License - see the LICENSE file for details.

