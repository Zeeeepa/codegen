# Import Fixes for Agents Directory

This document outlines the import fixes needed across the agents directory and its dependencies to resolve circular imports and ensure proper module imports.

## Key Issues Fixed

1. Fixed the import of `PlanStepStatus` in `tools/planning/__init__.py` to import from the correct location (`agents/planning/planning.py`)
2. Updated `agents/pr_review/__init__.py` to import `PRReviewAgent` from `pr_review_agent.py` instead of `agent.py`
3. Fixed imports in `research_agent.py` to use the correct classes from `context_understanding.py`
4. Ensured all necessary imports are properly defined in the various `__init__.py` files

## Specific Changes

### 1. tools/planning/__init__.py

```python
"""
Planning tools for codegen.

This module provides tools for planning and executing tasks.
"""

from codegen.tools.planning.manager import PlanManager
# Import PlanStepStatus from the correct location
from codegen.agents.planning.planning import PlanStepStatus

__all__ = [
    "PlanManager",
    "PlanStepStatus",
]
```

### 2. tools/research/__init__.py

```python
"""
Research tools for codegen.

This module provides tools for researching code and providing analysis.
"""

from codegen.tools.research.researcher import Researcher, CodeInsight, ResearchResult
from codegen.tools.research.context_understanding import ContextItem, ContextCollection, ContextAnalyzer, ContextManager

__all__ = [
    "Researcher",
    "CodeInsight",
    "ResearchResult",
    "ContextItem",
    "ContextCollection", 
    "ContextAnalyzer",
    "ContextManager",
]
```

### 3. tools/__init__.py

```python
"""
Tools for codegen.

This module provides a collection of tools for various tasks.
"""

from codegen.tools import base
from codegen.tools.planning import manager
from codegen.tools.reflection import reflector
from codegen.tools.research import researcher

__all__ = [
    "base",
    "manager",
    "reflector",
    "researcher",
]
```

### 4. agents/research/research_agent.py

```python
from codegen.agents.base import BaseAgent
from codegen.tools.research.researcher import Researcher
from codegen.tools.research.context_understanding import ContextManager, ContextAnalyzer
```

### 5. agents/pr_review/__init__.py

```python
"""
PR Review Agent module.

This module provides a PR review agent for code review.
"""

from codegen.agents.pr_review.pr_review_agent import PRReviewAgent

__all__ = ["PRReviewAgent"]
```

### 6. agents/__init__.py

```python
from codegen.agents.base import BaseAgent
from codegen.agents.chat.chat_agent import ChatAgent
from codegen.agents.code.code_agent import CodeAgent
from codegen.agents.mcp.mcp_agent import MCPAgent
from codegen.agents.planning.planning_agent import PlanningAgent
from codegen.agents.pr_review.pr_review_agent import PRReviewAgent
from codegen.agents.reflection.reflection_agent import ReflectionAgent
from codegen.agents.research.research_agent import ResearchAgent
from codegen.agents.toolcall.toolcall_agent import Tool, ToolCallAgent
```

### 7. codegen/__init__.py

```python
from codegen.agents.code.code_agent import CodeAgent
import codegen.agents
from codegen.cli.sdk.decorator import function
from codegen.cli.sdk.functions import Function
from codegen.extensions.events.codegen_app import CodegenApp

# from codegen.extensions.index.file_index import FileIndex
# from codegen.extensions.langchain.agent import create_agent_with_tools, create_codebase_agent
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage

__all__ = ["CodeAgent", "Codebase", "CodegenApp", "Function", "ProgrammingLanguage", "function", "agents"]
```

## Testing

After applying these changes, the import errors in the agents directory should be resolved, and the tests should pass.
