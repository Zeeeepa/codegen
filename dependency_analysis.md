# Dependency Mapping and Import Analysis

## 1. SolidLSP Dependencies on Serena Modules

### Direct Serena Imports in SolidLSP
```python
# From serena/src/solidlsp/ls.py
from serena.text_utils import MatchedConsecutiveLines
from serena.util.file_system import match_path
```

### External Dependencies in SolidLSP
```python
# From serena/src/solidlsp/ls_handler.py
from sensai.util.string import ToStringMixin

# From serena/src/solidlsp/language_servers/typescript_language_server.py
from sensai.util.logging import LogTime
```

## 2. Required Serena Modules for SolidLSP

### serena.text_utils
**Location**: `serena/src/serena/text_utils.py`
**Used by**: `solidlsp/ls.py`
**Required class**: `MatchedConsecutiveLines`

**Analysis of text_utils.py**:
```python
# Key exports needed by SolidLSP
class MatchedConsecutiveLines:
    # Text processing functionality
    pass

# Other utilities in text_utils
- search_files()
- search_text()
- glob_match()
- glob_to_regex()
```

### serena.util.file_system
**Location**: `serena/src/serena/util/file_system.py`
**Used by**: `solidlsp/ls.py`
**Required function**: `match_path`

**Analysis of file_system.py**:
```python
# Key function needed by SolidLSP
def match_path(path, patterns):
    # Path matching functionality
    pass

# Other utilities in file_system
- File operations
- Path utilities
- Directory traversal
```

## 3. External Package Dependencies

### SensAI Dependencies
**Package**: `sensai`
**Used by**: 
- `solidlsp/ls_handler.py` - `ToStringMixin`
- `solidlsp/language_servers/typescript_language_server.py` - `LogTime`

**Resolution Strategy**: 
- Option 1: Add sensai as dependency
- Option 2: Create minimal replacements for ToStringMixin and LogTime
- Option 3: Remove/replace usage

## 4. Internal SolidLSP Dependencies

### Internal Imports (No Issues)
```python
# These work fine within SolidLSP
from solidlsp.ls_exceptions import SolidLSPException
from solidlsp.ls_request import LanguageServerRequest
from solidlsp.lsp_protocol_handler.lsp_requests import LspNotification
from solidlsp.lsp_protocol_handler.lsp_types import ErrorCodes
from solidlsp.util.subprocess_util import subprocess_kwargs
```

## 5. Serena Tools Dependencies

### Non-Agentic Tools Import Analysis

#### file_tools.py Dependencies
```python
# Standard library imports (no issues)
import os
import pathlib
import re
from typing import List, Optional

# Internal serena imports (need resolution)
from serena.tools.tools_base import Tool, ToolMarkerCanEdit
```

#### symbol_tools.py Dependencies
```python
# Standard library imports (no issues)
import logging
from typing import List, Optional, Dict

# Internal serena imports (need resolution)
from serena.tools.tools_base import Tool, ToolMarkerSymbolicRead, ToolMarkerSymbolicEdit
from serena.symbol import SymbolManager  # ⚠️ Major dependency
```

#### config_tools.py Dependencies
```python
# Standard library imports (no issues)
import logging
from typing import Optional

# Internal serena imports (need resolution)
from serena.tools.tools_base import Tool, ToolMarkerDoesNotRequireActiveProject
from serena.project import ProjectManager  # ⚠️ Major dependency
```

## 6. Dependency Resolution Strategy

### Phase 1: Extract Required Utilities
1. **Extract serena.text_utils.MatchedConsecutiveLines**
   - Copy to `src/codegen/sdk/extensions/solidlsp/utils/text_utils.py`
   - Update import in `ls.py`

2. **Extract serena.util.file_system.match_path**
   - Copy to `src/codegen/sdk/extensions/solidlsp/utils/file_system.py`
   - Update import in `ls.py`

### Phase 2: Handle External Dependencies
1. **SensAI Dependencies**
   - Create minimal replacements in `src/codegen/sdk/extensions/solidlsp/utils/`
   - `ToStringMixin` - Simple string representation mixin
   - `LogTime` - Basic timing utility

### Phase 3: Serena Tools Base Classes
1. **Extract tools_base.py (Filtered)**
   - Copy base Tool class and markers
   - Remove agentic functionality
   - Place in `src/codegen/sdk/extensions/serena/base/`

2. **Handle Major Dependencies**
   - `SymbolManager` - Extract or create adapter
   - `ProjectManager` - Extract or create adapter

## 7. Migration Mapping

### SolidLSP Migration
```
Source: serena/src/solidlsp/
Target: src/codegen/sdk/extensions/solidlsp/

Files to migrate:
├── ls.py                   → solidlsp/ls.py (update imports)
├── ls_handler.py           → solidlsp/ls_handler.py (update imports)
├── ls_config.py            → solidlsp/ls_config.py
├── ls_exceptions.py        → solidlsp/ls_exceptions.py
├── ls_logger.py            → solidlsp/ls_logger.py
├── ls_request.py           → solidlsp/ls_request.py
├── ls_types.py             → solidlsp/ls_types.py
├── ls_utils.py             → solidlsp/ls_utils.py
├── settings.py             → solidlsp/settings.py
├── language_servers/       → solidlsp/language_servers/
├── lsp_protocol_handler/   → solidlsp/lsp_protocol_handler/
└── util/                   → solidlsp/util/

Dependencies to extract:
├── serena.text_utils       → solidlsp/utils/text_utils.py
├── serena.util.file_system → solidlsp/utils/file_system.py
└── sensai utilities        → solidlsp/utils/sensai_compat.py
```

### Serena Tools Migration
```
Source: serena/src/serena/tools/
Target: src/codegen/sdk/extensions/serena/

Files to migrate (filtered):
├── tools_base.py (filtered) → serena/base/tools_base.py
├── file_tools.py (filtered) → serena/file_tools.py
├── symbol_tools.py (filtered) → serena/symbol_tools.py
└── config_tools.py (filtered) → serena/config_tools.py

Dependencies to extract:
├── serena.symbol           → serena/utils/symbol.py (or adapter)
└── serena.project          → serena/utils/project.py (or adapter)
```

## 8. Import Update Plan

### SolidLSP Import Updates
```python
# Before (in serena/src/solidlsp/ls.py)
from serena.text_utils import MatchedConsecutiveLines
from serena.util.file_system import match_path

# After (in src/codegen/sdk/extensions/solidlsp/ls.py)
from codegen.sdk.extensions.solidlsp.utils.text_utils import MatchedConsecutiveLines
from codegen.sdk.extensions.solidlsp.utils.file_system import match_path
```

### Serena Tools Import Updates
```python
# Before (in serena/src/serena/tools/file_tools.py)
from serena.tools.tools_base import Tool, ToolMarkerCanEdit

# After (in src/codegen/sdk/extensions/serena/file_tools.py)
from codegen.sdk.extensions.serena.base.tools_base import Tool, ToolMarkerCanEdit
```

## 9. Validation Strategy

### Dependency Validation Steps
1. **Extract and test each utility function independently**
2. **Verify SolidLSP functionality with new imports**
3. **Test Serena tools with filtered base classes**
4. **Integration testing with SDK extensions**

### Testing Requirements
- Unit tests for extracted utilities
- Integration tests for SolidLSP language servers
- Functional tests for Serena tools
- End-to-end tests for unified system

## Next Steps
1. Extract required utilities from serena modules
2. Create compatibility layer for external dependencies
3. Implement migration scripts
4. Execute migration with import updates
