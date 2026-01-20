"""
Assertion engine module for test validations.

Provides comprehensive assertions:
- Element state (visibility, enabled, checked, text, attributes)
- Visual regression
- Network requests (status codes, response times)
- URL validation
- Custom JavaScript assertions
- ML-based UI assertions (OCR, color, layout, icons, accessibility)
"""

from autoqa.assertions.engine import (
    AssertionEngine,
    AssertionError,
    AssertionResult,
)
from autoqa.assertions.ml_engine import (
    AccessibilityChecker,
    AlignmentType,
    ColorAnalyzer,
    ColorInfo,
    ContrastResult,
    DetectedElement,
    FormFieldDetector,
    IconMatcher,
    IconMatchResult,
    ImageClassifier,
    ImageLoader,
    LayoutAnalyzer,
    LayoutInfo,
    MLAssertionEngine,
    MLAssertionResult,
    OCRAssertion,
    OCRResult,
    RegionDiffAnalyzer,
    UIState,
)

__all__ = [
    # Core assertion engine
    "AssertionEngine",
    "AssertionError",
    "AssertionResult",
    # ML assertion engine
    "MLAssertionEngine",
    "MLAssertionResult",
    # ML assertion types
    "OCRAssertion",
    "OCRResult",
    "ImageClassifier",
    "UIState",
    "ColorAnalyzer",
    "ColorInfo",
    "LayoutAnalyzer",
    "LayoutInfo",
    "DetectedElement",
    "AlignmentType",
    "IconMatcher",
    "IconMatchResult",
    "AccessibilityChecker",
    "ContrastResult",
    "FormFieldDetector",
    "RegionDiffAnalyzer",
    # Utilities
    "ImageLoader",
]
