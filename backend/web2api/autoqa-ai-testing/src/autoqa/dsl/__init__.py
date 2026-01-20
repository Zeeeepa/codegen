"""
DSL module for YAML test definitions.

Provides parsing, validation, and transformation of test specs.
No AI/LLM dependency - uses deterministic strategies.
"""

from autoqa.dsl.models import (
    AssertionConfig,
    AssertionOperator,
    CustomAssertionConfig,
    ElementAssertionConfig,
    EnvironmentConfig,
    NetworkAssertionConfig,
    SecretReference,
    StepAction,
    TestMetadata,
    TestSpec,
    TestStep,
    TestSuite,
    VisualAssertionConfig,
    VisualComparisonMode,
)
from autoqa.dsl.parser import DSLParser
from autoqa.dsl.transformer import StepTransformer
from autoqa.dsl.validator import DSLValidator

__all__ = [
    # Models
    "AssertionConfig",
    "AssertionOperator",
    "CustomAssertionConfig",
    "ElementAssertionConfig",
    "EnvironmentConfig",
    "NetworkAssertionConfig",
    "SecretReference",
    "StepAction",
    "TestMetadata",
    "TestSpec",
    "TestStep",
    "TestSuite",
    "VisualAssertionConfig",
    "VisualComparisonMode",
    # Parser & Transformer
    "DSLParser",
    "DSLValidator",
    "StepTransformer",
]
