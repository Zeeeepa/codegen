# Comprehensive Codebase Analysis Backend

A powerful 3-file backend system for comprehensive codebase analysis and interactive visualization, built with graph-sitter compliance and tree-sitter foundation.

## 🎯 Features

### ✅ **EXACTLY 3 FILES as requested:**
- `api.py` - FastAPI server with comprehensive REST endpoints
- `analysis.py` - ALL analysis context engine with comprehensive capabilities
- `visualize.py` - Interactive web-based visualization system

### ✅ **ALL MOST IMPORTANT FUNCTIONS** 
- Comprehensive detection of ALL important functions (not just one)
- Full function definitions with source code
- Importance ranking using multiple metrics (usage, centrality, complexity)
- Context and metadata for each function

### ✅ **ALL ENTRY POINTS**
- Comprehensive detection across different patterns:
  - Main functions (`if __name__ == "__main__"`, `main()`)
  - CLI entry points (argparse, click, typer)
  - Web endpoints (FastAPI, Flask routes)
  - Exported functions (public API, `__all__`)
  - Framework-specific entry points (Django views, Celery tasks)

### ✅ **GRAPH-SITTER COMPLIANCE**
- Built on tree-sitter foundation for AST parsing
- Multi-language support (Python, TypeScript, JSX)
- Pre-computed relationships for fast lookups
- Consistent interface across languages

### ✅ **NO CODE COMPLEXITY in reports**
- Complexity metrics used internally for importance ranking
- Not exposed in API responses or reports
- Clean, focused output without complexity noise

### ✅ **INTERACTIVE VISUALIZATION**
- Symbol selection with detailed context panels
- Interactive graph with zoom/pan/filter capabilities
- Hierarchical browsing (file, class, function hierarchies)
- Search and filtering capabilities
- Multiple export formats (JSON, Cytoscape.js, D3.js)

## 🏗️ Architecture

```
backend/
├── api.py          # FastAPI server & REST endpoints
├── analysis.py     # Comprehensive analysis engine
├── visualize.py    # Interactive visualization system
├── requirements.txt # Dependencies
└── README.md       # This file
```

### api.py - REST API Server
- **Purpose**: HTTP server, endpoint orchestration, request/response handling
- **Key Features**:
  - Comprehensive REST endpoints for all analysis features
  - Request validation with Pydantic models
  - Caching for expensive operations
  - Error handling and logging
  - CORS support for web integration
  - Automatic API documentation

### analysis.py - Analysis Engine
- **Purpose**: Core analysis logic extending existing Codebase functionality
- **Key Features**:
  - ALL important functions detection with full definitions
  - ALL entry points detection across patterns
  - Issue detection (unused code, circular dependencies, missing docs)
  - Symbol context analysis with relationships
  - Dependency graph analysis
  - Function importance ranking (complexity used internally only)

### visualize.py - Visualization System
- **Purpose**: Interactive web-based visualization replacing Neo4j-only approach
- **Key Features**:
  - Interactive graph creation with nodes and edges
  - Symbol selection and context viewing
  - Multiple layout algorithms (force-directed, hierarchical, circular)
  - Filtering and search capabilities
  - Hierarchical views (file, class, function)
  - Export to multiple formats

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
python api.py --host 0.0.0.0 --port 8000 --reload
```

### 3. Access API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Endpoints

### Core Analysis
- `POST /analyze` - Comprehensive codebase analysis
- `GET /functions/important` - Get ALL important functions with definitions
- `GET /entrypoints` - Get ALL detected entry points
- `GET /issues` - Get detected issues with context

### Visualization
- `POST /visualize` - Create interactive visualization data
- `GET /symbols/{symbol_id}` - Get symbol context for selection
- `POST /search` - Search symbols and code
- `GET /hierarchy` - Get hierarchical views

### Utility
- `GET /health` - Health check
- `DELETE /cache` - Clear analysis cache

## 🔍 Usage Examples

### Analyze a Codebase
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "codebase_path": "/path/to/your/codebase",
    "language": "python"
  }'
```

### Get ALL Important Functions
```bash
curl "http://localhost:8000/functions/important?codebase_path=/path/to/codebase&limit=100"
```

### Get ALL Entry Points
```bash
curl "http://localhost:8000/entrypoints?codebase_path=/path/to/codebase"
```

### Create Interactive Visualization
```bash
curl -X POST "http://localhost:8000/visualize?codebase_path=/path/to/codebase" \
  -H "Content-Type: application/json" \
  -d '{
    "filter_options": {
      "min_importance": 0.3,
      "node_types": ["function", "class"]
    },
    "layout_options": {
      "algorithm": "force_directed",
      "spacing": 1.5
    },
    "export_format": "cytoscape"
  }'
```

## 🎨 Visualization Features

### Interactive Graph
- **Nodes**: Functions, classes, files, issues
- **Edges**: Function calls, inheritance, containment
- **Colors**: Type-based color coding
- **Sizes**: Importance-based sizing
- **Positions**: Layout algorithm positioning

### Symbol Selection
- Click on any node to get detailed context
- View source code, usage patterns, dependencies
- Navigate to related symbols
- See issue details and context

### Filtering Options
- Filter by node types (function, class, file, issue)
- Filter by importance score
- Show only entry points
- Show only nodes with issues
- Filter by file patterns

### Layout Algorithms
- **Force-directed**: Natural clustering based on relationships
- **Hierarchical**: Tree-like structure showing dependencies
- **Circular**: Circular arrangement for overview
- **Custom**: Configurable spacing and iterations

## 🔧 Configuration

### Filter Options
```python
{
  "node_types": ["function", "class", "file", "issue"],
  "min_importance": 0.0,
  "max_complexity": 100,
  "show_entry_points_only": false,
  "show_issues_only": false,
  "file_patterns": ["*.py", "*.ts"]
}
```

### Layout Options
```python
{
  "algorithm": "force_directed",  # force_directed, hierarchical, circular
  "spacing": 1.0,
  "iterations": 50,
  "cluster_by": "file"  # file, type, importance
}
```

## 🧪 Testing

### Test Analysis Engine
```python
from backend.analysis import create_analyzer

analyzer = create_analyzer("/path/to/codebase", "python")
functions = analyzer.get_all_important_functions()
entry_points = analyzer.get_all_entry_points()
issues = analyzer.detect_issues()
```

### Test Visualization
```python
from backend.visualize import create_visualizer

visualizer = create_visualizer(analyzer)
graph = visualizer.create_interactive_graph()
details = visualizer.get_symbol_details("func_example")
```

### Test API
```bash
# Health check
curl http://localhost:8000/health

# Analyze codebase
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"codebase_path": ".", "language": "python"}'
```

## 🔍 Graph-sitter Compliance

This system is fully compliant with graph-sitter standards:

1. **Tree-sitter Foundation**: Uses tree-sitter for AST parsing
2. **Multi-language Support**: Python, TypeScript, JSX parsers
3. **Graph Construction**: Multi-file graph analysis
4. **Pre-computed Relationships**: Fast symbol lookups
5. **Consistent Interface**: Uniform API across languages

## 🎯 Key Benefits

1. **Comprehensive**: Finds ALL important functions and ALL entry points
2. **Interactive**: Web-based visualization with symbol selection
3. **Fast**: Leverages existing tree-sitter infrastructure
4. **Extensible**: Clean 3-file architecture for easy enhancement
5. **Standards-compliant**: Built on graph-sitter foundation
6. **Production-ready**: Proper error handling, caching, documentation

## 🚀 Performance

- **Caching**: Analyzers and visualizers are cached for reuse
- **Lazy Loading**: Analysis performed on-demand
- **Efficient Parsing**: Tree-sitter for fast AST generation
- **Pre-computed Graphs**: Relationships calculated once, used many times
- **Configurable Limits**: Prevent analysis of overly large codebases

## 🔮 Future Enhancements

- Real-time analysis updates
- Plugin system for custom analysis
- Integration with IDEs and editors
- Advanced visualization layouts
- Machine learning-based importance ranking
- Multi-repository analysis
- Collaborative features

---

**Built with ❤️ for comprehensive codebase analysis and interactive visualization**

