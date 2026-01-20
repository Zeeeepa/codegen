"""
Analyzer module for intelligent page and element analysis.

Provides deep inspection capabilities:
- Page structure and DOM analysis
- ML-based element classification
- Visual/UI analysis for accessibility and layout
"""

from autoqa.builder.analyzer.element_classifier import (
    ElementClassifier,
    ClassifierConfig,
    ElementPurpose,
    ElementRelationship,
    ClassificationResult,
)
from autoqa.builder.analyzer.page_analyzer import (
    PageAnalyzer,
    AnalyzerConfig,
    DOMAnalysis,
    ComponentInfo,
    InteractiveElement,
    PageComplexity,
)
from autoqa.builder.analyzer.visual_analyzer import (
    VisualAnalyzer,
    VisualConfig,
    LayoutInfo,
    AccessibilityCheck,
    ResponsiveBreakpoint,
    VisualHierarchy,
)

__all__ = [
    # Element Classifier
    "ElementClassifier",
    "ClassifierConfig",
    "ElementPurpose",
    "ElementRelationship",
    "ClassificationResult",
    # Page Analyzer
    "PageAnalyzer",
    "AnalyzerConfig",
    "DOMAnalysis",
    "ComponentInfo",
    "InteractiveElement",
    "PageComplexity",
    # Visual Analyzer
    "VisualAnalyzer",
    "VisualConfig",
    "LayoutInfo",
    "AccessibilityCheck",
    "ResponsiveBreakpoint",
    "VisualHierarchy",
]
