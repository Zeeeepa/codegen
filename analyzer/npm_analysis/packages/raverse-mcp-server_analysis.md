# NPM Package Analysis: raverse-mcp-server

## Package Overview

**Package Name:** `raverse-mcp-server`  
**Version:** 1.0.14  
**NPM URL:** https://www.npmjs.com/package/raverse-mcp-server  
**Registry URL:** https://registry.npmjs.org/raverse-mcp-server  
**Published Size:** 316.7 KB (unpacked: 667.9 KB)  
**Total Files:** 61  

**Description:** MCP Server for RAVERSE - AI Multi-Agent Binary Patching System with 35 tools, NPX/NPM/PyPI support, and 20+ client configurations

**Author:** RAVERSE Team (team@raverse.ai)  
**License:** MIT  
**Repository:** https://github.com/usemanusai/jaegis-RAVERSE  

---

## Package Architecture

### Hybrid Package Structure

This package uniquely combines **Node.js** and **Python** in a hybrid architecture:

- **Node.js Entry Point:** `bin/raverse-mcp-server.js` - CLI wrapper
- **Python Backend:** `jaegis_raverse_mcp_server/` - Core MCP server implementation
- **Distribution:** Published to both NPM and PyPI (`jaegis-raverse-mcp-server`)

### Design Pattern

The package follows a **wrapper pattern**:
1. NPX/NPM provides easy distribution and CLI interface
2. Node.js binary checks Python availability
3. Automatically installs matching Python package version
4. Spawns Python MCP server process
5. Handles lifecycle and signal forwarding

---

## Package.json Analysis

### Key Configuration

```json
{
  "name": "raverse-mcp-server",
  "version": "1.0.14",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "bin": {
    "raverse-mcp-server": "bin/raverse-mcp-server.js"
  }
}
```

### Dependencies

**Runtime:**
- `raverse-mcp-server`: ^1.0.13 (self-dependency for updates)

**Dev Dependencies:**
- `@types/node`: ^20.0.0

**Python Dependencies (managed separately):**
- Listed in `requirements.txt` and `pyproject.toml`

### Scripts

**Core Commands:**
```bash
npm run start           # Start server
npm run dev             # Development mode with debug logging
npm run install:auto    # Auto-install Python dependencies
npm run setup           # Complete setup (Python + env)
```

**Development:**
```bash
npm run test            # Run pytest tests
npm run test:coverage   # Coverage reports
npm run lint            # Ruff + Black linting
npm run format          # Auto-format code
npm run type-check      # MyPy type checking
```

**Publishing:**
```bash
npm run build           # Build Python wheel
npm run publish:npm     # Publish to NPM
npm run publish:pypi    # Publish to PyPI
npm run clean           # Clean build artifacts
```

### Keywords

Comprehensive keyword coverage for discoverability:
- MCP: `mcp`, `model-context-protocol`
- Domain: `binary-analysis`, `reverse-engineering`, `security-analysis`
- AI: `ai-agents`, `multi-agent`, `rag`, `code-embedding`, `semantic-search`
- Integration: `claude-desktop`, `cursor-ide`, `vscode-extension`
- Tools: `binary-patching`, `web-analysis`, `api-reverse-engineering`

---

## Directory Structure

```
package/
├── bin/
│   └── raverse-mcp-server.js          # Node.js CLI entry point (10.2 KB)
├── dist/
│   ├── jaegis_raverse_mcp_server-1.0.13.tar.gz
│   ├── jaegis_raverse_mcp_server-1.0.13-py3-none-any.whl
│   ├── jaegis_raverse_mcp_server-1.0.14.tar.gz
│   └── jaegis_raverse_mcp_server-1.0.14-py3-none-any.whl
├── jaegis_raverse_mcp_server/         # Python source code
│   ├── __init__.py
│   ├── server.py                      # Main MCP server (45.7 KB)
│   ├── auto_installer.py              # Dependency auto-installer
│   ├── cache.py                       # Redis cache manager
│   ├── config.py                      # Configuration management
│   ├── database.py                    # PostgreSQL + pgvector
│   ├── errors.py                      # Custom exceptions
│   ├── logging_config.py              # Structured logging
│   ├── setup_guide.py                 # Setup instructions
│   ├── setup_wizard.py                # Interactive setup
│   ├── types.py                       # Type definitions
│   ├── tools_analysis_advanced.py     # Advanced analysis (5 tools)
│   ├── tools_binary_analysis.py       # Binary tools (4 tools)
│   ├── tools_infrastructure.py        # Infrastructure (5 tools)
│   ├── tools_knowledge_base.py        # RAG/KB tools (4 tools)
│   ├── tools_management.py            # Management (4 tools)
│   ├── tools_nlp_validation.py        # NLP/validation (2 tools)
│   ├── tools_system.py                # System tools (4 tools)
│   ├── tools_utilities.py             # Utilities (5 tools)
│   └── tools_web_analysis.py          # Web analysis (5 tools)
├── tests/
│   ├── __init__.py
│   └── test_tools.py                  # Tool tests
├── .env.example                       # Environment template
├── package.json                       # NPM configuration
├── pyproject.toml                     # Python build config
├── requirements.txt                   # Python dependencies
├── MANIFEST.in                        # Python package manifest
├── LICENSE                            # MIT License
└── Documentation/
    ├── README.md                      # Main documentation (18.3 KB)
    ├── INSTALLATION.md                # Installation guide (12.3 KB)
    ├── MCP_CLIENT_SETUP.md            # Client configs (24.5 KB)
    ├── QUICKSTART.md                  # Quick start (5.9 KB)
    ├── INTEGRATION_GUIDE.md           # Integration guide (6.7 KB)
    ├── DEPLOYMENT.md                  # Deployment guide (7.0 KB)
    └── TOOLS_REGISTRY_COMPLETE.md     # Tools reference (11.1 KB)
```

---

## Code Architecture

### 1. Entry Point (`bin/raverse-mcp-server.js`)

**Purpose:** Node.js wrapper and CLI interface

**Key Features:**
- Command-line argument parsing (`--dev`, `--help`, `--version`, `--list-tools`)
- Python availability detection
- Automatic Python package version alignment
- Process lifecycle management
- Signal forwarding (SIGINT, SIGTERM)
- MCP JSON-RPC protocol for `--list-tools` mode

**Code Highlights:**
```javascript
// Version synchronization between NPM and Python package
const VERSION = '1.0.14';
ensurePythonPackageVersion() // Installs jaegis-raverse-mcp-server==${VERSION}

// Spawns Python server
spawn(python, ['-m', 'jaegis_raverse_mcp_server.server'], {
  env: env,
  stdio: 'inherit'
});
```

### 2. Main Server (`server.py`)

**Architecture:** MCP Protocol Server using official MCP SDK

**Size:** 45.7 KB (7,711 tokens - largest file)

**Core Components:**

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

class MCPServer:
    def __init__(self, config):
        # Lazy initialization - no heavy connections on startup
        self.db_manager = None
        self.cache_manager = None
        # Tool managers initialized to None
        
    async def initialize(self):
        # Async initialization of connections
        self.db_manager = DatabaseManager(self.config)
        self.cache_manager = CacheManager(self.config)
        # Initialize all tool modules
```

**Tool Registration Pattern:**
- Each tool module provides static methods
- Tools registered dynamically via `list_tools()`
- Request routing via `call_tool(name, arguments)`
- Standardized error handling with `RAVERSEMCPError`

### 3. Tool Modules (9 Categories, 35 Tools)

#### Binary Analysis Tools (`tools_binary_analysis.py`)
1. **disassemble_binary** - Convert machine code to assembly
2. **generate_code_embedding** - Create semantic code vectors
3. **apply_patch** - Modify binary programmatically
4. **verify_patch** - Validate patch integrity

#### Knowledge Base & RAG (`tools_knowledge_base.py`)
1. **ingest_content** - Add content to knowledge base
2. **search_knowledge_base** - Semantic search
3. **retrieve_entry** - Get specific entries
4. **delete_entry** - Remove entries

#### Web Analysis (`tools_web_analysis.py`)
1. **reconnaissance** - Web target intelligence
2. **analyze_javascript** - Extract JS logic/API calls
3. **reverse_engineer_api** - Generate OpenAPI specs
4. **analyze_wasm** - Decompile WebAssembly
5. **security_analysis** - Identify vulnerabilities

#### Infrastructure (`tools_infrastructure.py`)
1. **database_query** - Parameterized DB queries
2. **cache_operation** - Redis cache management
3. **publish_message** - A2A protocol messages
4. **fetch_content** - HTTP with retry logic
5. **record_metric** - Performance tracking

#### Advanced Analysis (`tools_analysis_advanced.py`)
1. **logic_identification** - Pattern recognition
2. **traffic_interception** - Network analysis
3. **generate_report** - Comprehensive reports
4. **rag_orchestration** - RAG workflows
5. **deep_research** - Topic research

#### Management (`tools_management.py`)
1. **version_management** - Component versions
2. **quality_gate** - Quality enforcement
3. **governance_check** - Rule compliance
4. **generate_document** - Document generation

#### Utilities (`tools_utilities.py`)
1. **url_frontier_operation** - Crawl queue management
2. **api_pattern_matcher** - API pattern detection
3. **response_classifier** - HTTP response classification
4. **websocket_analyzer** - WebSocket analysis
5. **crawl_scheduler** - Job scheduling

#### System (`tools_system.py`)
1. **metrics_collector** - Performance metrics
2. **multi_level_cache** - Cache hierarchy
3. **configuration_service** - Config access
4. **llm_interface** - LLM provider interface

#### NLP & Validation (`tools_nlp_validation.py`)
1. **natural_language_interface** - NLP command processing
2. **poc_validation** - Vulnerability PoC validation

### 4. Supporting Infrastructure

#### Database Manager (`database.py`)
- **Technology:** PostgreSQL 17 + pgvector extension
- **Features:**
  - Connection pooling
  - Vector similarity search
  - Prepared statements
  - Migration support
- **Vector Operations:** Cosine similarity for code embeddings

#### Cache Manager (`cache.py`)
- **Technology:** Redis 8.2
- **Operations:**
  - Get/Set/Delete
  - TTL management
  - Atomic operations
  - Pipeline support

#### Configuration (`config.py`)
- **Pattern:** Pydantic Settings with environment variables
- **Sources:** .env files, environment variables
- **Validation:** Type-safe configuration with defaults

**Key Config Items:**
```python
DATABASE_URL: str = "postgresql://localhost/raverse"
REDIS_URL: str = "redis://localhost:6379"
OPENROUTER_API_KEY: str  # Required for LLM features
LOG_LEVEL: str = "INFO"
SERVER_HOST: str = "127.0.0.1"
SERVER_PORT: int = 8000
```

#### Error Handling (`errors.py`)
Custom exception hierarchy:
```python
RAVERSEMCPError (base)
├── ValidationError
├── DatabaseError
├── CacheError
├── BinaryAnalysisError
└── WebAnalysisError
```

#### Logging (`logging_config.py`)
- **Framework:** structlog
- **Features:** Structured logging with context
- **Levels:** DEBUG, INFO, WARNING, ERROR
- **Output:** JSON format for machine parsing

---

## Python Dependencies

### Core MCP Framework
```python
mcp>=0.1.0                      # Official MCP SDK
pydantic>=2.5.0                 # Data validation
pydantic-settings>=2.1.0        # Settings management
```

### Database & Caching
```python
psycopg2-binary>=2.9.9          # PostgreSQL driver
redis>=5.0.0                    # Redis client
pgvector>=0.2.4                 # Vector operations
```

### AI/ML
```python
sentence-transformers>=2.2.2    # Code embeddings
```

### Infrastructure
```python
python-dotenv>=1.0.0            # Environment config
requests>=2.31.0                # HTTP client
structlog>=24.1.0               # Structured logging
prometheus-client>=0.19.0       # Metrics
colorama>=0.4.6                 # Terminal colors
```

### Development
```python
pytest>=7.4.0                   # Testing
pytest-cov>=4.1.0               # Coverage
pytest-asyncio>=0.21.0          # Async testing
mypy>=1.7.0                     # Type checking
ruff>=0.1.0                     # Fast linter
black>=23.11.0                  # Code formatter
```

---

## Installation Methods

### 1. NPX (Zero Installation)
```bash
# Latest version
npx -y raverse-mcp-server@latest

# Specific version
npx -y raverse-mcp-server@1.0.14

# With arguments
npx -y raverse-mcp-server@latest -- --help
```

### 2. NPM Global
```bash
npm install -g raverse-mcp-server
raverse-mcp-server --version
```

### 3. NPM Local
```bash
npm install raverse-mcp-server
npx raverse-mcp-server
```

### 4. Python PyPI
```bash
pip install jaegis-raverse-mcp-server
python -m jaegis_raverse_mcp_server.server
```

---

## MCP Client Integration

The package provides **20+ MCP client configurations** in `MCP_CLIENT_SETUP.md`:

### Supported Clients
- Claude Desktop (macOS/Windows)
- Cursor IDE
- VSCode with Continue extension
- Zed Editor
- Windsurf Editor
- Claude Code CLI
- Cline (VSCode)
- Roo Code
- Amp Code
- MCPHub
- General stdio/SSE servers

### Configuration Pattern
```json
{
  "mcpServers": {
    "raverse": {
      "command": "npx",
      "args": ["-y", "raverse-mcp-server@latest"],
      "env": {
        "DATABASE_URL": "postgresql://...",
        "REDIS_URL": "redis://...",
        "OPENROUTER_API_KEY": "..."
      }
    }
  }
}
```

---

## Notable Features & Patterns

### 1. **Automatic Dependency Management**
The CLI wrapper automatically installs and synchronizes the Python package version:
```javascript
ensurePythonPackageVersion() // Ensures Python package matches NPM version
```

### 2. **Lazy Initialization**
Heavy resources (DB, cache, models) are initialized asynchronously after server start:
```python
def __init__(self):
    self.db_manager = None  # Not connected yet
    
async def initialize(self):
    self.db_manager = DatabaseManager()  # Connect on first use
```

### 3. **Setup Wizard**
Interactive setup wizard (`setup_wizard.py`) guides users through:
- Database configuration
- Redis setup
- API key configuration
- Environment file creation

### 4. **Tool Discovery**
MCP protocol support for tool discovery:
```bash
raverse-mcp-server --list-tools        # Human-readable
raverse-mcp-server --list-tools --json # Machine-readable
```

### 5. **Dual Publishing**
Simultaneous NPM and PyPI distribution:
```bash
npm run publish:npm    # NPM package
npm run publish:pypi   # PyPI package (same code)
```

### 6. **Comprehensive Documentation**
95+ KB of documentation across 7 files:
- Installation guide with troubleshooting
- 20+ client configuration examples
- Quick start tutorials
- Integration patterns
- Deployment strategies
- Complete tool registry

---

## Security Considerations

### Detected Potential Issues (from Repomix Security Scan)
The security scanner detected 10 files with potential sensitive information patterns:

**Files with Security Markers:**
1. `auto_installer.py` - Likely contains installation keys/URLs
2. `config.py` - Configuration with default values
3. `setup_guide.py` - Setup instructions with example credentials
4. `setup_wizard.py` - Interactive setup with input validation
5. `.env.example` - Environment template (safe - example only)
6. `DEPLOYMENT.md` - Deployment credentials examples
7. `INSTALLATION.md` - Installation examples
8. `INTEGRATION_GUIDE.md` - Integration examples
9. `QUICKSTART.md` - Quick start with examples
10. `README.md` - Documentation with usage examples

**Note:** These are mostly documentation and example files. Actual sensitive data should be in `.env` (not distributed in package).

### Security Best Practices
✅ Environment variables for secrets  
✅ `.env.example` provided (no real credentials)  
✅ Parameterized database queries  
✅ Input validation via Pydantic  
✅ Error sanitization in responses  
✅ MIT License (permissive, no liability)

### Recommendations
1. **Never commit `.env` file** - already in `.gitignore`
2. **Rotate API keys regularly** - especially OPENROUTER_API_KEY
3. **Use read-only database credentials** where possible
4. **Enable Redis AUTH** in production
5. **Review tool permissions** before exposing to untrusted clients

---

## Code Quality Metrics

### From Repomix Analysis

**Top 5 Files by Token Count:**
1. `server.py` - 7,711 tokens (19.3% of codebase)
2. `MCP_CLIENT_SETUP.md` - 6,901 tokens (17.3%)
3. `TOOLS_REGISTRY_COMPLETE.md` - 2,874 tokens (7.2%)
4. `bin/raverse-mcp-server.js` - 2,434 tokens (6.1%)
5. `tools_web_analysis.py` - 1,465 tokens (3.7%)

**Total Statistics:**
- **Files Analyzed:** 26 files (35 excluded for security)
- **Total Tokens:** 39,975 tokens
- **Total Characters:** 189,387 chars
- **Average File Size:** 7.3 KB

### Code Organization
- **Modular Design:** 9 tool categories in separate files
- **Single Responsibility:** Each module handles one domain
- **Type Safety:** Pydantic models + MyPy type hints
- **Error Handling:** Comprehensive exception hierarchy
- **Logging:** Structured logging throughout
- **Testing:** pytest with async support

### Development Tools
```bash
# Linting
ruff check .                    # Fast Python linter
black --check .                 # Code formatting

# Type Checking
mypy jaegis_raverse_mcp_server/ # Static type analysis

# Testing
pytest tests/ -v                # Run tests
pytest --cov --cov-report=html  # Coverage report

# Formatting
black .                         # Auto-format code
ruff check --fix .              # Auto-fix linting issues
```

---

## Deployment Patterns

### 1. **Local Development**
```bash
npx raverse-mcp-server --dev
```
- Debug logging enabled
- Hot reload (manual restart)
- Local database/Redis

### 2. **Docker Container**
Pre-built wheels in `dist/` directory enable containerization:
```dockerfile
FROM python:3.13-slim
COPY dist/jaegis_raverse_mcp_server-1.0.14-py3-none-any.whl .
RUN pip install jaegis_raverse_mcp_server-1.0.14-py3-none-any.whl
CMD ["python", "-m", "jaegis_raverse_mcp_server.server"]
```

### 3. **MCP Client Integration**
Used as a long-running MCP server by AI clients:
- stdio transport (default)
- SSE transport (HTTP streaming)
- WebSocket transport (future)

### 4. **Production Considerations**
- PostgreSQL 17 with pgvector extension required
- Redis 8.2 for caching
- OpenRouter API key for LLM features
- Prometheus metrics endpoint (port 8000)
- Health check endpoint
- Graceful shutdown handling

---

## Version History & Updates

### Current Version: 1.0.14
- **Published:** October 26, 1985 (timestamp artifact)
- **Contains:** Two Python wheel versions (1.0.13 and 1.0.14)
- **Self-dependency:** Depends on `raverse-mcp-server@^1.0.13`

### Update Mechanism
The NPM package automatically updates the Python package:
```javascript
// From bin/raverse-mcp-server.js
function ensurePythonPackageVersion() {
    execSync(`${python} -m pip install --upgrade jaegis-raverse-mcp-server==${VERSION}`);
}
```

This ensures version consistency across NPM and PyPI distributions.

---

## Unique Characteristics

### 1. **Cross-Platform Hybrid**
- NPM for distribution and CLI
- Python for core functionality
- Automatic version synchronization
- Works on Windows, macOS, Linux

### 2. **Zero-Config Philosophy**
```bash
npx -y raverse-mcp-server@latest  # Just works!
```
- Auto-installs Python dependencies
- Detects Python executable
- Falls back to sensible defaults
- Interactive wizard for first-time setup

### 3. **MCP Protocol First**
Built specifically for Model Context Protocol:
- Native MCP SDK integration
- Full protocol compliance
- Tool discovery via MCP
- Streaming support (SSE)

### 4. **Production-Ready**
- Comprehensive error handling
- Structured logging
- Prometheus metrics
- Health checks
- Graceful shutdown
- Database connection pooling
- Redis pipelining

### 5. **Developer-Friendly**
- 95+ KB of documentation
- 20+ client configurations
- Example `.env` file
- Setup wizard
- Type hints throughout
- Pytest test suite
- Linting and formatting tools

---

## Comparison: NPM vs PyPI Packages

### NPM Package (`raverse-mcp-server`)
- **Purpose:** CLI wrapper and distribution
- **Entry Point:** `bin/raverse-mcp-server.js`
- **Size:** 316.7 KB
- **Installation:** `npm install -g raverse-mcp-server`
- **Usage:** `raverse-mcp-server`
- **Advantages:**
  - Easy `npx` usage without installation
  - Cross-platform CLI
  - Automatic Python package management
  - Fits MCP client ecosystem (mostly Node.js)

### PyPI Package (`jaegis-raverse-mcp-server`)
- **Purpose:** Core MCP server implementation
- **Entry Point:** `jaegis_raverse_mcp_server.server:main`
- **Size:** ~48 KB (wheel file)
- **Installation:** `pip install jaegis-raverse-mcp-server`
- **Usage:** `python -m jaegis_raverse_mcp_server.server`
- **Advantages:**
  - Direct Python integration
  - Lighter weight
  - Standard Python package
  - Better for Python-centric workflows

---

## Conclusion

### Strengths
✅ **Innovative Hybrid Architecture** - NPM + Python synergy  
✅ **35 Comprehensive Tools** - Covers binary analysis, RAG, web analysis, infrastructure  
✅ **MCP Protocol Native** - First-class MCP SDK integration  
✅ **Zero-Config Philosophy** - Works with `npx` out of the box  
✅ **Extensive Documentation** - 95+ KB across 7 detailed guides  
✅ **20+ Client Integrations** - Works with all major AI coding assistants  
✅ **Production-Ready** - Monitoring, logging, error handling  
✅ **Active Development** - Regular updates, dual NPM/PyPI publishing  

### Potential Improvements
⚠️ **Heavy Dependencies** - Requires PostgreSQL + Redis + Python  
⚠️ **Complexity** - Hybrid package may confuse users  
⚠️ **Large Surface Area** - 35 tools to maintain and document  
⚠️ **API Key Required** - OpenRouter API key needed for LLM features  

### Use Cases
1. **AI Coding Assistants** - Claude, Cursor, VSCode integration
2. **Binary Reverse Engineering** - Automated patching and analysis
3. **Security Research** - Web analysis and vulnerability detection
4. **Knowledge Management** - RAG-powered code search and retrieval
5. **API Reverse Engineering** - Traffic analysis and OpenAPI generation

### Target Audience
- 🔐 Security researchers and reverse engineers
- 🤖 AI agent developers and LLM integrators
- 🏗️ DevOps engineers needing multi-agent orchestration
- 📚 Knowledge base maintainers for code analysis
- 🔧 Tool builders in the MCP ecosystem

---

## Repomix Analysis Summary

**Command:** `repomix --output /tmp/repomix_output.txt`

**Results:**
- ✅ Successfully packed 26 files
- 🔒 10 files excluded for security (contains example credentials)
- 📊 39,975 tokens total (suitable for LLM context)
- 📄 189,387 characters analyzed
- 🎯 Largest file: `server.py` at 45.7 KB (19.3% of codebase)

**Security Note:** Repomix detected potential secrets in documentation files. These are example credentials only. Real secrets should never be committed.

---

## Metadata

**Analysis Date:** 2025-12-27  
**Analyzer:** Codegen AI  
**Package Version Analyzed:** 1.0.14  
**Analysis Method:** NPM pack + manual inspection + Repomix  
**Source:** https://registry.npmjs.org/raverse-mcp-server/-/raverse-mcp-server-1.0.14.tgz

---

## Additional Resources

- **NPM Package:** https://www.npmjs.com/package/raverse-mcp-server
- **PyPI Package:** https://pypi.org/project/jaegis-raverse-mcp-server/
- **GitHub Repository:** https://github.com/usemanusai/jaegis-RAVERSE
- **Documentation:** Included in package under `/docs/` directory
- **Issues:** https://github.com/usemanusai/jaegis-RAVERSE/issues

---

*This analysis provides a comprehensive overview of the raverse-mcp-server NPM package structure, dependencies, architecture, and deployment patterns. For implementation details, refer to the source code and official documentation.*

