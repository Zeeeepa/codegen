# Target SDK Extensions Structure Design

## 1. Final Target Structure

### Complete SDK Extensions Directory
```
src/codegen/sdk/extensions/
├── __init__.py                     # Main extensions package
├── autogenlib/                     # ✅ ALREADY EXISTS - Enhanced context
│   ├── __init__.py
│   ├── _cache.py
│   ├── _caller.py
│   ├── _context.py
│   ├── _exception_handler.py
│   ├── _finder.py
│   ├── _generator.py
│   └── _state.py
├── solidlsp/                       # 🆕 MIGRATE FROM serena/src/solidlsp/
│   ├── __init__.py
│   ├── ls.py                       # Main language server
│   ├── ls_handler.py               # LSP message handling
│   ├── ls_config.py                # Configuration
│   ├── ls_exceptions.py            # Exception handling
│   ├── ls_logger.py                # Logging
│   ├── ls_request.py               # Request handling
│   ├── ls_types.py                 # Type definitions
│   ├── ls_utils.py                 # Utilities
│   ├── settings.py                 # Settings
│   ├── language_servers/           # Language-specific servers
│   │   ├── __init__.py
│   │   ├── bash_language_server.py
│   │   ├── clangd_language_server.py
│   │   ├── clojure_language_server.py
│   │   ├── csharp_language_server.py
│   │   ├── dart_language_server.py
│   │   ├── elixir_language_server.py
│   │   ├── erlang_language_server.py
│   │   ├── go_language_server.py
│   │   ├── java_language_server.py
│   │   ├── php_language_server.py
│   │   ├── python_language_server.py
│   │   ├── rust_language_server.py
│   │   ├── swift_language_server.py
│   │   ├── typescript_language_server.py
│   │   └── [other language servers]
│   ├── lsp_protocol_handler/       # LSP protocol implementation
│   │   ├── __init__.py
│   │   └── [protocol files]
│   ├── util/                       # SolidLSP utilities
│   │   ├── __init__.py
│   │   └── [utility files]
│   └── utils/                      # 🆕 EXTRACTED DEPENDENCIES
│       ├── __init__.py
│       ├── text_utils.py           # From serena.text_utils
│       ├── file_system.py          # From serena.util.file_system
│       └── sensai_compat.py        # SensAI compatibility layer
├── serena/                         # 🆕 MIGRATE FROM serena/src/serena/tools/ (FILTERED)
│   ├── __init__.py
│   ├── base/                       # Base classes and infrastructure
│   │   ├── __init__.py
│   │   └── tools_base.py           # Filtered tool base classes
│   ├── utils/                      # Extracted utilities and adapters
│   │   ├── __init__.py
│   │   ├── text_utils.py           # Text processing utilities
│   │   ├── file_system.py          # File system utilities
│   │   ├── symbol_adapter.py       # Symbol functionality adapter
│   │   └── project_adapter.py      # Project functionality adapter
│   ├── file_tools.py               # Non-agentic file tools
│   ├── symbol_tools.py             # Non-agentic symbol tools
│   └── config_tools.py             # Non-agentic config tools
├── [existing extensions...]        # Other existing extensions
│   ├── attribution/
│   ├── clients/
│   ├── github/
│   ├── graph/
│   ├── index/
│   ├── linear/
│   ├── lsp/                        # ⚠️ EXISTING LSP - may need integration
│   ├── mcp/
│   ├── slack/
│   ├── swebench/
│   └── tools/
```

## 2. Package Initialization Strategy

### Main Extensions __init__.py
```python
# src/codegen/sdk/extensions/__init__.py
"""
Codegen SDK Extensions Package

This package contains all extensions for the Codegen SDK including:
- SolidLSP: Language Server Protocol integration
- Serena: Non-agentic codebase tools
- AutogenLib: Enhanced context generation
"""

from . import autogenlib
from . import solidlsp
from . import serena

__all__ = ['autogenlib', 'solidlsp', 'serena']
```

### SolidLSP Package __init__.py
```python
# src/codegen/sdk/extensions/solidlsp/__init__.py
"""
SolidLSP - Language Server Protocol Integration

Provides comprehensive LSP support for 15+ programming languages
with diagnostic collection, symbol analysis, and code actions.
"""

from .ls import SolidLanguageServer
from .ls_handler import SolidLanguageServerHandler
from .ls_config import LanguageServerConfig
from .ls_types import LSPTypes

__all__ = [
    'SolidLanguageServer',
    'SolidLanguageServerHandler', 
    'LanguageServerConfig',
    'LSPTypes'
]
```

### Serena Package __init__.py
```python
# src/codegen/sdk/extensions/serena/__init__.py
"""
Serena - Non-Agentic Codebase Tools

Provides file operations, symbol manipulation, and project management
tools for codebase analysis and modification.
"""

from .file_tools import (
    ReadFileTool,
    CreateTextFileTool,
    ListDirTool,
    FindFileTool,
    ReplaceRegexTool,
    SearchForPatternTool
)

from .symbol_tools import (
    GetSymbolsOverviewTool,
    FindSymbolTool,
    FindReferencingSymbolsTool,
    ReplaceSymbolBodyTool,
    InsertAfterSymbolTool,
    InsertBeforeSymbolTool
)

from .config_tools import (
    ActivateProjectTool
)

__all__ = [
    # File Tools
    'ReadFileTool',
    'CreateTextFileTool', 
    'ListDirTool',
    'FindFileTool',
    'ReplaceRegexTool',
    'SearchForPatternTool',
    # Symbol Tools
    'GetSymbolsOverviewTool',
    'FindSymbolTool',
    'FindReferencingSymbolsTool',
    'ReplaceSymbolBodyTool',
    'InsertAfterSymbolTool',
    'InsertBeforeSymbolTool',
    # Config Tools
    'ActivateProjectTool'
]
```

## 3. Configuration Integration Design

### Graph-Sitter Configuration Support
```python
# src/codegen/sdk/core/graph_sitter_config.py
"""
Graph-Sitter Configuration Management

Supports configuration parameters:
- lspserver: Enable SolidLSP integration
- diagnostics: Enable diagnostic collection  
- errorautoresolve: Enable automatic error resolution
- enhancedcontext: Enable AutogenLib enhanced context
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import json
import os

@dataclass
class GraphSitterConfig:
    """Graph-sitter configuration with extension parameters"""
    lspserver: bool = True
    diagnostics: bool = True
    errorautoresolve: bool = True
    enhancedcontext: bool = True
    
    # Additional configuration
    language_servers: Optional[Dict[str, Any]] = None
    project_root: Optional[str] = None
    
    @classmethod
    def from_file(cls, config_path: str) -> 'GraphSitterConfig':
        """Load configuration from file"""
        if not os.path.exists(config_path):
            return cls()  # Return defaults
            
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            
        return cls(**config_data)
    
    @classmethod
    def from_project(cls, project_path: str) -> 'GraphSitterConfig':
        """Load configuration from project directory"""
        config_files = [
            os.path.join(project_path, '.graph-sitter.json'),
            os.path.join(project_path, 'graph-sitter.json'),
            os.path.join(project_path, '.codegen', 'config.json')
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                return cls.from_file(config_file)
                
        return cls()  # Return defaults
```

### Unified Configuration System
```python
# src/codegen/sdk/core/unified_config.py (ENHANCED)
"""
Enhanced Unified Configuration System

Integrates graph-sitter configuration with SDK core configuration.
"""

from .graph_sitter_config import GraphSitterConfig
from typing import Optional

class UnifiedConfiguration:
    """Unified configuration for SDK and extensions"""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path
        self.graph_sitter_config = GraphSitterConfig.from_project(project_path) if project_path else GraphSitterConfig()
        
    @property
    def lsp_enabled(self) -> bool:
        """Check if LSP server integration is enabled"""
        return self.graph_sitter_config.lspserver
        
    @property
    def diagnostics_enabled(self) -> bool:
        """Check if diagnostic collection is enabled"""
        return self.graph_sitter_config.diagnostics
        
    @property
    def error_resolution_enabled(self) -> bool:
        """Check if automatic error resolution is enabled"""
        return self.graph_sitter_config.errorautoresolve
        
    @property
    def enhanced_context_enabled(self) -> bool:
        """Check if enhanced context is enabled"""
        return self.graph_sitter_config.enhancedcontext
```

## 4. Top-Level API Design

### Enhanced Unified API
```python
# src/codegen/sdk/core/unified_api.py (ENHANCED)
"""
Enhanced Unified API for SDK Extensions Integration

Provides the main codebase.from_repo() function and related functionality.
"""

from typing import Optional, Dict, Any
from .unified_config import UnifiedConfiguration
from .project_context import ProjectContext

class CodebaseAPI:
    """Main API for codebase operations"""
    
    @staticmethod
    def from_repo(repo_name: str, config: Optional[Dict[str, Any]] = None) -> 'ProjectContext':
        """
        Initialize a complete project context with all configured features.
        
        Args:
            repo_name: Name or path of the repository
            config: Optional configuration overrides
            
        Returns:
            ProjectContext: Unified project context with all enabled features
        """
        # Load configuration
        unified_config = UnifiedConfiguration(repo_name)
        
        # Apply config overrides
        if config:
            for key, value in config.items():
                if hasattr(unified_config.graph_sitter_config, key):
                    setattr(unified_config.graph_sitter_config, key, value)
        
        # Initialize project context
        project_context = ProjectContext(repo_name, unified_config)
        
        # Initialize components based on configuration
        if unified_config.lsp_enabled:
            project_context.initialize_lsp()
            
        if unified_config.diagnostics_enabled:
            project_context.initialize_diagnostics()
            
        if unified_config.error_resolution_enabled:
            project_context.initialize_error_resolution()
            
        if unified_config.enhanced_context_enabled:
            project_context.initialize_enhanced_context()
            
        return project_context

# Global API instance
codebase = CodebaseAPI()
```

### Project Context Design
```python
# src/codegen/sdk/core/project_context.py
"""
Project Context - Central coordinator for all systems
"""

from typing import Optional, List, Dict, Any
from .unified_config import UnifiedConfiguration

class ProjectContext:
    """Central project context managing all integrated systems"""
    
    def __init__(self, repo_path: str, config: UnifiedConfiguration):
        self.repo_path = repo_path
        self.config = config
        
        # Component instances
        self._lsp_manager = None
        self._diagnostic_collector = None
        self._error_resolver = None
        self._enhanced_context = None
        self._serena_tools = None
        
    def initialize_lsp(self):
        """Initialize SolidLSP integration"""
        if self.config.lsp_enabled:
            from ..extensions.solidlsp import SolidLanguageServer
            self._lsp_manager = LanguageServerManager(self.repo_path)
            
    def initialize_diagnostics(self):
        """Initialize diagnostic collection"""
        if self.config.diagnostics_enabled and self._lsp_manager:
            self._diagnostic_collector = DiagnosticCollector(self._lsp_manager)
            
    def initialize_error_resolution(self):
        """Initialize automatic error resolution"""
        if self.config.error_resolution_enabled and self._diagnostic_collector:
            self._error_resolver = ErrorResolver(self._diagnostic_collector)
            
    def initialize_enhanced_context(self):
        """Initialize enhanced context with AutogenLib"""
        if self.config.enhanced_context_enabled:
            from ..extensions.autogenlib import AutogenLib
            self._enhanced_context = AutogenLib()
            
    def initialize_serena_tools(self):
        """Initialize Serena tools"""
        from ..extensions.serena import SerenaToolRegistry
        self._serena_tools = SerenaToolRegistry()
        
    # Public API methods
    @property
    def lsp(self):
        """Access to LSP functionality"""
        return self._lsp_manager
        
    @property
    def diagnostics(self):
        """Access to diagnostic functionality"""
        return self._diagnostic_collector
        
    @property
    def resolver(self):
        """Access to error resolution functionality"""
        return self._error_resolver
        
    @property
    def context(self):
        """Access to enhanced context functionality"""
        return self._enhanced_context
        
    @property
    def tools(self):
        """Access to Serena tools"""
        return self._serena_tools
```

## 5. Import Path Strategy

### Consistent Import Patterns
```python
# Top-level API access
from codegen.sdk import codebase

# Direct extension access
from codegen.sdk.extensions.solidlsp import SolidLanguageServer
from codegen.sdk.extensions.serena import ReadFileTool
from codegen.sdk.extensions.autogenlib import AutogenLib

# Configuration access
from codegen.sdk.core.unified_config import UnifiedConfiguration
from codegen.sdk.core.graph_sitter_config import GraphSitterConfig
```

### Internal Extension Imports
```python
# Within SolidLSP
from codegen.sdk.extensions.solidlsp.utils.text_utils import MatchedConsecutiveLines
from codegen.sdk.extensions.solidlsp.utils.file_system import match_path

# Within Serena
from codegen.sdk.extensions.serena.base.tools_base import Tool
from codegen.sdk.extensions.serena.utils.symbol_adapter import SymbolAdapter
```

## 6. Build System Integration

### Package Discovery Configuration
```python
# pyproject.toml updates
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "codegen-sdk"
dynamic = ["version"]
dependencies = [
    # Core dependencies
    "tree-sitter>=0.20.0",
    "tree-sitter-python>=0.20.0",
    "tree-sitter-javascript>=0.20.0",
    "tree-sitter-typescript>=0.20.0",
    # Add other tree-sitter language parsers
    
    # LSP dependencies (for SolidLSP)
    "psutil>=5.9.0",
    
    # Optional: SensAI compatibility (or create minimal replacements)
    # "sensai>=1.0.0",  # Only if we decide to keep full dependency
]

[tool.setuptools.packages.find]
where = ["src"]
include = ["codegen*"]

[tool.setuptools.package-data]
"codegen.sdk.extensions.solidlsp" = ["**/*.json", "**/*.yaml"]
"codegen.sdk.extensions.serena" = ["**/*.json", "**/*.yaml"]
```

## 7. Migration Mapping Summary

### File Migration Map
```
# SolidLSP Migration
serena/src/solidlsp/                    → src/codegen/sdk/extensions/solidlsp/
serena/src/serena/text_utils.py         → src/codegen/sdk/extensions/solidlsp/utils/text_utils.py
serena/src/serena/util/file_system.py   → src/codegen/sdk/extensions/solidlsp/utils/file_system.py

# Serena Tools Migration (Filtered)
serena/src/serena/tools/tools_base.py   → src/codegen/sdk/extensions/serena/base/tools_base.py
serena/src/serena/tools/file_tools.py   → src/codegen/sdk/extensions/serena/file_tools.py
serena/src/serena/tools/symbol_tools.py → src/codegen/sdk/extensions/serena/symbol_tools.py
serena/src/serena/tools/config_tools.py → src/codegen/sdk/extensions/serena/config_tools.py

# Dependencies and Adapters
serena/src/serena/symbol.py             → src/codegen/sdk/extensions/serena/utils/symbol_adapter.py
serena/src/serena/project.py            → src/codegen/sdk/extensions/serena/utils/project_adapter.py
```

## 8. Testing Integration Points

### Test Structure
```
tests/
├── unit/
│   ├── extensions/
│   │   ├── test_solidlsp/
│   │   ├── test_serena/
│   │   └── test_autogenlib/
│   └── core/
│       ├── test_unified_config.py
│       └── test_project_context.py
├── integration/
│   ├── test_lsp_integration.py
│   ├── test_serena_integration.py
│   └── test_unified_system.py
└── end_to_end/
    └── test_codebase_from_repo.py
```

## 9. Configuration File Examples

### Example .graph-sitter.json
```json
{
  "lspserver": true,
  "diagnostics": true,
  "errorautoresolve": true,
  "enhancedcontext": true,
  "language_servers": {
    "python": {
      "enabled": true,
      "server": "pylsp"
    },
    "typescript": {
      "enabled": true,
      "server": "typescript-language-server"
    }
  }
}
```

## Next Steps
1. Implement migration scripts based on this design
2. Create the directory structure and package files
3. Execute the migration with proper import updates
4. Test the integrated system
5. Validate configuration parameter functionality
