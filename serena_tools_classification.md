# Serena Tools Classification and Filtering

## 1. Complete Tool Inventory

### file_tools.py - File System Operations
```python
class ReadFileTool(Tool):                           # ✅ NON-AGENTIC - File reading
class CreateTextFileTool(Tool, ToolMarkerCanEdit): # ✅ NON-AGENTIC - File creation
class ListDirTool(Tool):                           # ✅ NON-AGENTIC - Directory listing
class FindFileTool(Tool):                          # ✅ NON-AGENTIC - File finding
class ReplaceRegexTool(Tool, ToolMarkerCanEdit):   # ✅ NON-AGENTIC - Text replacement
class DeleteLinesTool(Tool, ToolMarkerCanEdit, ToolMarkerOptional):  # ⚠️ OPTIONAL - Line deletion
class ReplaceLinesTool(Tool, ToolMarkerCanEdit, ToolMarkerOptional): # ⚠️ OPTIONAL - Line replacement
class InsertAtLineTool(Tool, ToolMarkerCanEdit, ToolMarkerOptional):  # ⚠️ OPTIONAL - Line insertion
class SearchForPatternTool(Tool):                  # ✅ NON-AGENTIC - Pattern search
```

### symbol_tools.py - Symbol Operations
```python
class RestartLanguageServerTool(Tool, ToolMarkerOptional):           # ⚠️ OPTIONAL - LSP management
class GetSymbolsOverviewTool(Tool, ToolMarkerSymbolicRead):          # ✅ NON-AGENTIC - Symbol overview
class FindSymbolTool(Tool, ToolMarkerSymbolicRead):                  # ✅ NON-AGENTIC - Symbol finding
class FindReferencingSymbolsTool(Tool, ToolMarkerSymbolicRead):      # ✅ NON-AGENTIC - Reference finding
class ReplaceSymbolBodyTool(Tool, ToolMarkerSymbolicEdit):           # ✅ NON-AGENTIC - Symbol editing
class InsertAfterSymbolTool(Tool, ToolMarkerSymbolicEdit):           # ✅ NON-AGENTIC - Symbol insertion
class InsertBeforeSymbolTool(Tool, ToolMarkerSymbolicEdit):          # ✅ NON-AGENTIC - Symbol insertion
```

### config_tools.py - Configuration Management
```python
class ActivateProjectTool(Tool, ToolMarkerDoesNotRequireActiveProject): # ✅ NON-AGENTIC - Project activation
class RemoveProjectTool(Tool, ToolMarkerDoesNotRequireActiveProject, ToolMarkerOptional): # ⚠️ OPTIONAL - Project removal
class SwitchModesTool(Tool, ToolMarkerOptional):                     # ❌ AGENTIC - Mode switching
class GetCurrentConfigTool(Tool, ToolMarkerOptional):                # ⚠️ OPTIONAL - Config retrieval
```

### memory_tools.py - Memory Management (ALL AGENTIC)
```python
class WriteMemoryTool(Tool):        # ❌ AGENTIC - Memory writing
class ReadMemoryTool(Tool):         # ❌ AGENTIC - Memory reading
class ListMemoriesTool(Tool):       # ❌ AGENTIC - Memory listing
class DeleteMemoryTool(Tool):       # ❌ AGENTIC - Memory deletion
```

### cmd_tools.py - Command Execution (ALL AGENTIC)
```python
class ExecuteShellCommandTool(Tool, ToolMarkerCanEdit): # ❌ AGENTIC - Shell execution
```

### workflow_tools.py - Workflow Management (ALL AGENTIC)
```python
class CheckOnboardingPerformedTool(Tool):               # ❌ AGENTIC - Onboarding check
class OnboardingTool(Tool):                             # ❌ AGENTIC - Onboarding process
class ThinkAboutCollectedInformationTool(Tool):         # ❌ AGENTIC - Thinking process
class ThinkAboutTaskAdherenceTool(Tool):                # ❌ AGENTIC - Task adherence
class ThinkAboutWhetherYouAreDoneTool(Tool):            # ❌ AGENTIC - Completion check
class PrepareForNewConversationTool(Tool):              # ❌ AGENTIC - Conversation prep
```

## 2. Final Classification

### ✅ INCLUDE - Non-Agentic Tools (Core Requirements)
**File Tools:**
- `ReadFileTool` - Read file contents
- `CreateTextFileTool` - Create new text files
- `ListDirTool` - List directory contents
- `FindFileTool` - Find files by pattern
- `ReplaceRegexTool` - Replace text using regex
- `SearchForPatternTool` - Search for text patterns

**Symbol Tools:**
- `GetSymbolsOverviewTool` - Get symbol overview
- `FindSymbolTool` - Find specific symbols
- `FindReferencingSymbolsTool` - Find symbol references
- `ReplaceSymbolBodyTool` - Replace symbol body
- `InsertAfterSymbolTool` - Insert after symbol
- `InsertBeforeSymbolTool` - Insert before symbol

**Config Tools:**
- `ActivateProjectTool` - Activate project workspace

### ⚠️ OPTIONAL - Consider for Inclusion
**File Tools (Optional):**
- `DeleteLinesTool` - Delete specific lines
- `ReplaceLinesTool` - Replace specific lines
- `InsertAtLineTool` - Insert at specific line

**Symbol Tools (Optional):**
- `RestartLanguageServerTool` - Restart LSP server

**Config Tools (Optional):**
- `RemoveProjectTool` - Remove project
- `GetCurrentConfigTool` - Get current configuration

### ❌ EXCLUDE - Agentic Tools
**Memory Tools (All Excluded):**
- `WriteMemoryTool`, `ReadMemoryTool`, `ListMemoriesTool`, `DeleteMemoryTool`

**Command Tools (All Excluded):**
- `ExecuteShellCommandTool`

**Workflow Tools (All Excluded):**
- `CheckOnboardingPerformedTool`, `OnboardingTool`
- `ThinkAbout*Tool` classes
- `PrepareForNewConversationTool`

**Config Tools (Excluded):**
- `SwitchModesTool`

## 3. Dependency Analysis for Included Tools

### Base Dependencies (Required for All Tools)
```python
# From tools_base.py (REQUIRED)
class Tool(Component):                              # Base tool class
class ToolMarker:                                   # Base marker
class ToolMarkerCanEdit(ToolMarker):               # Edit capability marker
class ToolMarkerDoesNotRequireActiveProject(ToolMarker): # Project independence marker
class ToolMarkerOptional(ToolMarker):              # Optional tool marker
class ToolMarkerSymbolicRead(ToolMarker):          # Symbolic read marker
class ToolMarkerSymbolicEdit(ToolMarkerCanEdit):   # Symbolic edit marker
class ToolRegistry:                                 # Tool registration system
```

### External Dependencies for Included Tools
```python
# File Tools Dependencies
from serena.text_utils import search_files          # Text search functionality
from serena.util.file_system import scan_directory # Directory scanning

# Symbol Tools Dependencies
from serena.symbol import SymbolManager             # ⚠️ MAJOR DEPENDENCY
from serena.project import ProjectManager           # ⚠️ MAJOR DEPENDENCY

# Config Tools Dependencies
from serena.project import ProjectManager           # ⚠️ MAJOR DEPENDENCY
```

## 4. Migration Strategy

### Phase 1: Extract Base Classes
1. **Extract tools_base.py (Filtered)**
   - Copy base Tool class and required markers
   - Remove agentic-specific functionality
   - Place in `src/codegen/sdk/extensions/serena/base/tools_base.py`

### Phase 2: Extract Utilities
1. **Extract Required Utilities**
   - `serena.text_utils.search_files` → `serena/utils/text_utils.py`
   - `serena.util.file_system.scan_directory` → `serena/utils/file_system.py`

### Phase 3: Handle Major Dependencies
1. **SymbolManager Dependency**
   - Option 1: Extract minimal SymbolManager functionality
   - Option 2: Create adapter that bridges to SDK symbol functionality
   - Option 3: Reimplement using SDK's existing symbol system

2. **ProjectManager Dependency**
   - Option 1: Extract minimal ProjectManager functionality
   - Option 2: Create adapter that bridges to SDK project functionality
   - Option 3: Reimplement using SDK's existing project system

### Phase 4: Migrate Tools
1. **File Tools Migration**
   - Copy: `ReadFileTool`, `CreateTextFileTool`, `ListDirTool`, `FindFileTool`
   - Copy: `ReplaceRegexTool`, `SearchForPatternTool`
   - Update imports to use SDK extensions paths

2. **Symbol Tools Migration**
   - Copy: `GetSymbolsOverviewTool`, `FindSymbolTool`, `FindReferencingSymbolsTool`
   - Copy: `ReplaceSymbolBodyTool`, `InsertAfterSymbolTool`, `InsertBeforeSymbolTool`
   - Update imports and resolve SymbolManager dependency

3. **Config Tools Migration**
   - Copy: `ActivateProjectTool`
   - Update imports and resolve ProjectManager dependency

## 5. Target Structure

### Final Serena Extension Structure
```
src/codegen/sdk/extensions/serena/
├── __init__.py                     # Package initialization
├── base/
│   ├── __init__.py
│   └── tools_base.py               # Filtered base classes
├── utils/
│   ├── __init__.py
│   ├── text_utils.py               # Extracted text utilities
│   ├── file_system.py              # Extracted file system utilities
│   ├── symbol_adapter.py           # Symbol functionality adapter
│   └── project_adapter.py          # Project functionality adapter
├── file_tools.py                   # Non-agentic file tools
├── symbol_tools.py                 # Non-agentic symbol tools
└── config_tools.py                 # Non-agentic config tools
```

## 6. Import Mapping

### Before Migration
```python
# In serena/src/serena/tools/file_tools.py
from serena.tools.tools_base import Tool, ToolMarkerCanEdit
from serena.text_utils import search_files
from serena.util.file_system import scan_directory
```

### After Migration
```python
# In src/codegen/sdk/extensions/serena/file_tools.py
from codegen.sdk.extensions.serena.base.tools_base import Tool, ToolMarkerCanEdit
from codegen.sdk.extensions.serena.utils.text_utils import search_files
from codegen.sdk.extensions.serena.utils.file_system import scan_directory
```

## 7. Testing Strategy

### Unit Testing
- Test each migrated tool independently
- Verify tool functionality with new imports
- Test base class functionality

### Integration Testing
- Test tool registration and discovery
- Test tool interaction with SDK systems
- Verify configuration integration

### Validation Criteria
- All included tools function correctly
- No agentic functionality is accessible
- Tools integrate properly with SDK extensions system
- Configuration parameters control tool availability

## Next Steps
1. Extract and migrate base classes
2. Extract required utilities and create adapters
3. Migrate individual tool classes
4. Update imports and test functionality
5. Integrate with SDK configuration system
