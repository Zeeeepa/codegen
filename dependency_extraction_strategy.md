# Dependency Extraction Strategy

## 1. Complete Dependency Analysis

### SolidLSP Dependencies on Serena

#### Direct Imports
```python
# From serena/src/solidlsp/ls.py
from serena.text_utils import MatchedConsecutiveLines
from serena.util.file_system import match_path
```

#### External Dependencies
```python
# From serena/src/solidlsp/ls_handler.py
from sensai.util.string import ToStringMixin

# From serena/src/solidlsp/language_servers/typescript_language_server.py
from sensai.util.logging import LogTime
```

### Required Classes and Functions

#### From serena.text_utils
1. **MatchedConsecutiveLines** (dataclass)
   - Dependencies: TextLine, LineType
   - Used for: Text search results with context
   - Size: ~100 lines of code

2. **TextLine** (dataclass)
   - Dependencies: LineType enum
   - Used for: Individual line representation
   - Size: ~20 lines of code

3. **LineType** (StrEnum)
   - Dependencies: None (standard library)
   - Used for: Line type classification
   - Size: ~10 lines of code

#### From serena.util.file_system
1. **match_path** (function)
   - Dependencies: PathSpec (from pathspec package)
   - Used for: Path pattern matching
   - Size: ~25 lines of code

#### External Dependencies
1. **pathspec** package - Required for match_path function
2. **sensai** package - Used for ToStringMixin and LogTime

## 2. Extraction Strategy

### Phase 1: Create Utility Modules

#### solidlsp/utils/text_utils.py
```python
# Extract these classes/enums:
- LineType (StrEnum)
- TextLine (dataclass)  
- MatchedConsecutiveLines (dataclass)

# Dependencies to include:
- Standard library: re, logging, dataclasses, enum, typing
- No external dependencies needed
```

#### solidlsp/utils/file_system.py
```python
# Extract this function:
- match_path(relative_path, path_spec, root_path)

# Dependencies to include:
- pathspec package (add to requirements)
- Standard library: os
```

#### solidlsp/utils/sensai_compat.py
```python
# Create minimal replacements:
- ToStringMixin class
- LogTime context manager

# Dependencies:
- Standard library: logging, time, contextlib
```

### Phase 2: Update SolidLSP Imports

#### Before (in serena/src/solidlsp/ls.py)
```python
from serena.text_utils import MatchedConsecutiveLines
from serena.util.file_system import match_path
```

#### After (in src/codegen/sdk/extensions/solidlsp/ls.py)
```python
from codegen.sdk.extensions.solidlsp.utils.text_utils import MatchedConsecutiveLines
from codegen.sdk.extensions.solidlsp.utils.file_system import match_path
```

#### Before (in serena/src/solidlsp/ls_handler.py)
```python
from sensai.util.string import ToStringMixin
```

#### After (in src/codegen/sdk/extensions/solidlsp/ls_handler.py)
```python
from codegen.sdk.extensions.solidlsp.utils.sensai_compat import ToStringMixin
```

## 3. Detailed Extraction Plan

### Step 1: Extract text_utils Components
```python
# File: src/codegen/sdk/extensions/solidlsp/utils/text_utils.py
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

class LineType(StrEnum):
    """Enum for different types of lines in search results."""
    MATCH = "match"
    BEFORE_MATCH = "prefix" 
    AFTER_MATCH = "postfix"

@dataclass(kw_only=True)
class TextLine:
    """Represents a line of text with information on how it relates to the match."""
    line_number: int
    line_content: str
    match_type: LineType
    
    def get_display_prefix(self) -> str:
        """Get the display prefix for this line based on the match type."""
        if self.match_type == LineType.MATCH:
            return "  >"
        return "..."
    
    def format_line(self, include_line_numbers: bool = True) -> str:
        """Format the line for display."""
        prefix = self.get_display_prefix()
        if include_line_numbers:
            line_num = str(self.line_number).rjust(4)
            prefix = f"{prefix}{line_num}"
        return f"{prefix}:{self.line_content}"

@dataclass(kw_only=True)
class MatchedConsecutiveLines:
    """Represents a collection of consecutive lines found through some criterion."""
    lines: list[TextLine]
    source_file_path: str | None = None
    
    # set in post-init
    lines_before_matched: list[TextLine] = field(default_factory=list)
    matched_lines: list[TextLine] = field(default_factory=list)
    lines_after_matched: list[TextLine] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        for line in self.lines:
            if line.match_type == LineType.BEFORE_MATCH:
                self.lines_before_matched.append(line)
            elif line.match_type == LineType.MATCH:
                self.matched_lines.append(line)
            elif line.match_type == LineType.AFTER_MATCH:
                self.lines_after_matched.append(line)
        
        assert len(self.matched_lines) > 0, "At least one matched line is required"
    
    @property
    def start_line(self) -> int:
        return self.lines[0].line_number
    
    @property
    def end_line(self) -> int:
        return self.lines[-1].line_number
    
    @property
    def num_matched_lines(self) -> int:
        return len(self.matched_lines)
    
    def to_display_string(self, include_line_numbers: bool = True) -> str:
        return "\n".join([line.format_line(include_line_numbers) for line in self.lines])
    
    @classmethod
    def from_file_contents(
        cls, file_contents: str, line: int, context_lines_before: int = 0, 
        context_lines_after: int = 0, source_file_path: str | None = None
    ) -> Self:
        line_contents = file_contents.split("\n")
        start_lineno = max(0, line - context_lines_before)
        end_lineno = min(len(line_contents), line + context_lines_after + 1)
        
        lines = []
        for i in range(start_lineno, end_lineno):
            line_num = i + 1
            if line_num < line:
                match_type = LineType.BEFORE_MATCH
            elif line_num > line:
                match_type = LineType.AFTER_MATCH
            else:
                match_type = LineType.MATCH
            
            lines.append(TextLine(
                line_number=line_num,
                line_content=line_contents[i],
                match_type=match_type
            ))
        
        return cls(lines=lines, source_file_path=source_file_path)
```

### Step 2: Extract file_system Components
```python
# File: src/codegen/sdk/extensions/solidlsp/utils/file_system.py
import os
from pathspec import PathSpec

def match_path(relative_path: str, path_spec: PathSpec, root_path: str = "") -> bool:
    """
    Match a relative path against a given pathspec.
    
    :param relative_path: relative path to match against the pathspec
    :param path_spec: the pathspec to match against  
    :param root_path: the root path from which the relative path is derived
    :return: True if path matches the pathspec
    """
    normalized_path = str(relative_path).replace(os.path.sep, "/")
    
    # Always assume input path is relative to repo root and prefix with /
    if not normalized_path.startswith("/"):
        normalized_path = "/" + normalized_path
    
    # Handle directory matching - pathspec needs trailing slash for directories
    abs_path = os.path.abspath(os.path.join(root_path, relative_path))
    if os.path.isdir(abs_path) and not normalized_path.endswith("/"):
        normalized_path = normalized_path + "/"
        
    return path_spec.match_file(normalized_path)
```

### Step 3: Create SensAI Compatibility Layer
```python
# File: src/codegen/sdk/extensions/solidlsp/utils/sensai_compat.py
import logging
import time
from contextlib import contextmanager
from typing import Any

class ToStringMixin:
    """Minimal replacement for sensai.util.string.ToStringMixin"""
    
    def __str__(self) -> str:
        """Default string representation using class name and key attributes."""
        class_name = self.__class__.__name__
        attrs = []
        
        # Get key attributes (non-private, non-callable)
        for key, value in self.__dict__.items():
            if not key.startswith('_') and not callable(value):
                attrs.append(f"{key}={repr(value)}")
        
        if attrs:
            return f"{class_name}({', '.join(attrs)})"
        else:
            return f"{class_name}()"

@contextmanager
def LogTime(message: str, logger: logging.Logger = None):
    """Minimal replacement for sensai.util.logging.LogTime"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    start_time = time.time()
    logger.debug(f"Starting: {message}")
    
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        logger.debug(f"Completed: {message} (took {elapsed:.3f}s)")
```

## 4. Import Update Mapping

### Files to Update
1. `serena/src/solidlsp/ls.py` → `src/codegen/sdk/extensions/solidlsp/ls.py`
2. `serena/src/solidlsp/ls_handler.py` → `src/codegen/sdk/extensions/solidlsp/ls_handler.py`
3. `serena/src/solidlsp/language_servers/typescript_language_server.py` → `src/codegen/sdk/extensions/solidlsp/language_servers/typescript_language_server.py`

### Import Updates Required
```python
# Update 1: ls.py
OLD: from serena.text_utils import MatchedConsecutiveLines
NEW: from codegen.sdk.extensions.solidlsp.utils.text_utils import MatchedConsecutiveLines

OLD: from serena.util.file_system import match_path  
NEW: from codegen.sdk.extensions.solidlsp.utils.file_system import match_path

# Update 2: ls_handler.py
OLD: from sensai.util.string import ToStringMixin
NEW: from codegen.sdk.extensions.solidlsp.utils.sensai_compat import ToStringMixin

# Update 3: typescript_language_server.py
OLD: from sensai.util.logging import LogTime
NEW: from codegen.sdk.extensions.solidlsp.utils.sensai_compat import LogTime
```

## 5. Dependencies to Add

### pyproject.toml Updates
```toml
dependencies = [
    # Existing dependencies...
    
    # For SolidLSP integration
    "pathspec>=0.11.0",  # For file path matching
    "psutil>=5.9.0",     # Already used by SolidLSP
]
```

## 6. Validation Strategy

### Unit Tests for Extracted Utilities
```python
# Test MatchedConsecutiveLines functionality
def test_matched_consecutive_lines():
    lines = [
        TextLine(line_number=1, line_content="before", match_type=LineType.BEFORE_MATCH),
        TextLine(line_number=2, line_content="match", match_type=LineType.MATCH),
        TextLine(line_number=3, line_content="after", match_type=LineType.AFTER_MATCH),
    ]
    matched = MatchedConsecutiveLines(lines=lines)
    assert matched.num_matched_lines == 1
    assert matched.start_line == 1
    assert matched.end_line == 3

# Test match_path functionality  
def test_match_path():
    from pathspec import PathSpec
    spec = PathSpec.from_lines('gitwildmatch', ['*.py'])
    assert match_path('test.py', spec) == True
    assert match_path('test.txt', spec) == False

# Test sensai compatibility
def test_sensai_compat():
    class TestClass(ToStringMixin):
        def __init__(self):
            self.value = 42
    
    obj = TestClass()
    assert 'TestClass' in str(obj)
    assert 'value=42' in str(obj)
```

### Integration Tests
```python
# Test SolidLSP with extracted utilities
def test_solidlsp_with_extracted_utils():
    # Import should work without errors
    from codegen.sdk.extensions.solidlsp.ls import SolidLanguageServer
    
    # Basic functionality should work
    # (specific tests depend on SolidLSP implementation)
```

## 7. Risk Mitigation

### Potential Issues
1. **Missing transitive dependencies** - Some utilities might have hidden dependencies
2. **Version compatibility** - pathspec version compatibility with existing code
3. **Behavioral differences** - Minimal sensai replacements might not match exact behavior

### Mitigation Strategies
1. **Comprehensive testing** - Test all extracted utilities thoroughly
2. **Gradual migration** - Test each component individually before full integration
3. **Fallback options** - Keep original sensai dependency as optional fallback
4. **Documentation** - Document any behavioral differences in compatibility layer

## 8. Success Criteria

### Extraction Success Indicators
- [ ] All SolidLSP files import successfully with new paths
- [ ] MatchedConsecutiveLines functionality works identically
- [ ] match_path function produces same results
- [ ] SensAI compatibility layer provides required functionality
- [ ] No runtime errors in SolidLSP language servers
- [ ] All existing SolidLSP tests pass (if any)

### Performance Validation
- [ ] No significant performance degradation
- [ ] Memory usage remains similar
- [ ] Import times are acceptable

This extraction strategy provides a clear, systematic approach to removing SolidLSP's dependencies on Serena modules while maintaining full functionality.
