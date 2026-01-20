"""
AutoQA AI Testing System.

Production-ready AI-powered testing framework with natural language YAML definitions,
self-healing tests, visual regression, and generative testing capabilities.
"""

__version__ = "1.0.0"
__author__ = "Olib AI"

from autoqa.assertions.engine import AssertionEngine
from autoqa.builder.test_builder import (
    AutoTestBuilder,
    BuilderConfig,
    ElementInfo,
    PageAnalysis,
)
from autoqa.concurrency import (
    AsyncTestRunner,
    BrowserPool,
    ConcurrencyConfig,
    MemoryPressure,
    ParallelExecutionResult,
    ResourceLimits,
    ResourceMonitor,
    load_concurrency_config,
)
from autoqa.dsl.models import (
    AssertionConfig,
    ContentAssertionConfig,
    LLMAssertionConfig,
    NetworkAssertionConfig,
    SemanticAssertionConfig,
    TestSpec,
    TestStep,
    TestSuite,
    VersioningConfigModel,
    VisualAssertionConfig,
)
from autoqa.dsl.parser import DSLParser
from autoqa.generative.chaos_agents import ChaosAgentFactory, ChaosPersona
from autoqa.orchestrator.scheduler import TestOrchestrator
from autoqa.runner.self_healing import SelfHealingEngine
from autoqa.runner.test_runner import TestRunner
from autoqa.storage.artifact_manager import ArtifactManager
from autoqa.versioning import (
    TestRunHistory,
    TestSnapshot,
    VersionDiff,
    VersionDiffAnalyzer,
    VersioningConfig,
)
from autoqa.visual.regression_engine import VisualRegressionEngine

# LLM integration (optional)
from autoqa.llm import (
    LLMAssertionEngine,
    LLMClient,
    LLMConfig,
    LLMService,
    ToolName as LLMToolName,
    get_llm_service,
    load_llm_config,
)

__all__ = [
    # Core
    "ArtifactManager",
    "AssertionConfig",
    "AssertionEngine",
    "AutoTestBuilder",
    "BuilderConfig",
    "ChaosAgentFactory",
    "ChaosPersona",
    "ContentAssertionConfig",
    "DSLParser",
    "ElementInfo",
    "LLMAssertionConfig",
    "NetworkAssertionConfig",
    "PageAnalysis",
    "SelfHealingEngine",
    "SemanticAssertionConfig",
    "TestOrchestrator",
    "TestRunHistory",
    "TestRunner",
    "TestSnapshot",
    "TestSpec",
    "TestStep",
    "TestSuite",
    "VersionDiff",
    "VersionDiffAnalyzer",
    "VersioningConfig",
    "VersioningConfigModel",
    "VisualAssertionConfig",
    "VisualRegressionEngine",
    "__version__",
    # Concurrency
    "AsyncTestRunner",
    "BrowserPool",
    "ConcurrencyConfig",
    "MemoryPressure",
    "ParallelExecutionResult",
    "ResourceLimits",
    "ResourceMonitor",
    "load_concurrency_config",
    # LLM integration
    "LLMAssertionEngine",
    "LLMClient",
    "LLMConfig",
    "LLMService",
    "LLMToolName",
    "get_llm_service",
    "load_llm_config",
]
