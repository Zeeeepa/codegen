"""
Auto Test Builder module.

Provides intelligent, enterprise-grade automated test generation through
deep page analysis, ML-based element classification, and smart assertion creation.

Features:
- Deep page analysis with DOM structure, component detection, Shadow DOM/iframe handling
- ML-based element classification and visual grouping
- Visual/UI analysis for accessibility, layout, and visual regression
- Smart crawling with priority queues, state tracking, authentication handling
- User flow detection (login, registration, checkout, search, CRUD)
- API/XHR detection with GraphQL vs REST identification
- Deep form analysis with validation rule inference and test case generation
- Intelligent test strategy with risk-based prioritization
- Smart assertion generation including accessibility (WCAG)
- YAML test construction with comprehensive metadata

Submodules:
- analyzer: Page analysis, element classification, visual analysis
- crawler: Intelligent crawling, state management
- discovery: Flow detection, API detection, form analysis
- generator: Test strategy, assertion generation, YAML building
- orchestrator: Main coordination layer
"""

# Legacy exports (backward compatibility)
from autoqa.builder.test_builder import (
    AutoTestBuilder,
    BuilderConfig as LegacyBuilderConfig,
    ElementInfo,
    PageAnalysis,
)
from autoqa.builder.llm_enhanced import (
    LLMEnhancedTestBuilder,
    create_enhanced_builder,
)

# Analyzer module
from autoqa.builder.analyzer import (
    PageAnalyzer,
    AnalyzerConfig,
    DOMAnalysis,
    ComponentInfo,
    InteractiveElement,
    PageComplexity,
    ElementClassifier,
    ClassifierConfig,
    ElementPurpose,
    ElementRelationship,
    ClassificationResult,
    VisualAnalyzer,
    VisualConfig,
    LayoutInfo,
    AccessibilityCheck,
    VisualHierarchy,
    ResponsiveBreakpoint,
)

# Crawler module
from autoqa.builder.crawler import (
    IntelligentCrawler,
    CrawlConfig,
    CrawlResult,
    CrawledPage,
    URLPriority,
    CrawlState,
    StateManager,
    StateConfig,
    ApplicationState,
    StateTransition,
    StateGraph,
)

# Discovery module
from autoqa.builder.discovery import (
    FlowDetector,
    FlowConfig,
    FlowType,
    FlowStep,
    UserFlow,
    APIDetector,
    APIConfig,
    APIType,
    RequestMethod,
    APIEndpoint,
    FormAnalyzer,
    FormConfig,
    FormAnalysis,
    FieldAnalysis,
    FieldType,
    ValidationRule,
    TestCase as FormTestCase,
)

# Generator module
from autoqa.builder.generator import (
    TestStrategy,
    StrategyConfig,
    TestPlan,
    TestPriority,
    TestType,
    StrategyTestCase,
    TestSuite,
    AssertionGenerator,
    AssertionConfig,
    Assertion,
    AssertionType,
    AssertionGroup,
    YAMLBuilder,
    BuilderConfig,
    YAMLTestSpec,
    YAMLStep,
    StepType,
)

# Orchestrator
from autoqa.builder.orchestrator import (
    TestBuilderOrchestrator,
    OrchestratorConfig,
    BuildResult,
    BuildMode,
    TestScope,
    build_tests,
)

__all__ = [
    # Legacy (backward compatibility)
    "AutoTestBuilder",
    "LegacyBuilderConfig",
    "ElementInfo",
    "LLMEnhancedTestBuilder",
    "PageAnalysis",
    "create_enhanced_builder",
    # Analyzer
    "PageAnalyzer",
    "AnalyzerConfig",
    "DOMAnalysis",
    "ComponentInfo",
    "InteractiveElement",
    "PageComplexity",
    "ElementClassifier",
    "ClassifierConfig",
    "ElementPurpose",
    "ElementRelationship",
    "ClassificationResult",
    "VisualAnalyzer",
    "VisualConfig",
    "LayoutInfo",
    "AccessibilityCheck",
    "VisualHierarchy",
    "ResponsiveBreakpoint",
    # Crawler
    "IntelligentCrawler",
    "CrawlConfig",
    "CrawlResult",
    "CrawledPage",
    "URLPriority",
    "CrawlState",
    "StateManager",
    "StateConfig",
    "ApplicationState",
    "StateTransition",
    "StateGraph",
    # Discovery
    "FlowDetector",
    "FlowConfig",
    "FlowType",
    "FlowStep",
    "UserFlow",
    "APIDetector",
    "APIConfig",
    "APIType",
    "RequestMethod",
    "APIEndpoint",
    "FormAnalyzer",
    "FormConfig",
    "FormAnalysis",
    "FieldAnalysis",
    "FieldType",
    "ValidationRule",
    "FormTestCase",
    # Generator
    "TestStrategy",
    "StrategyConfig",
    "TestPlan",
    "TestPriority",
    "TestType",
    "StrategyTestCase",
    "TestSuite",
    "AssertionGenerator",
    "AssertionConfig",
    "Assertion",
    "AssertionType",
    "AssertionGroup",
    "YAMLBuilder",
    "BuilderConfig",
    "YAMLTestSpec",
    "YAMLStep",
    "StepType",
    # Orchestrator
    "TestBuilderOrchestrator",
    "OrchestratorConfig",
    "BuildResult",
    "BuildMode",
    "TestScope",
    "build_tests",
]
