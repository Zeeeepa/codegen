"""Tests for DSL parser and models."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from autoqa.dsl.models import (
    TestSpec,
    TestSuite,
    TestStep,
    StepAction,
    AssertionConfig,
    AssertionOperator,
    VisualAssertionConfig,
    VisualComparisonMode,
)
from autoqa.dsl.parser import DSLParser, DSLParseError
from autoqa.dsl.validator import DSLValidator
from autoqa.dsl.transformer import StepTransformer


class TestDSLModels:
    """Tests for DSL Pydantic models."""

    def test_test_step_navigate(self) -> None:
        """Test navigate step validation."""
        step = TestStep(
            action=StepAction.NAVIGATE,
            url="https://example.com",
            wait_until="networkidle",
        )
        assert step.action == StepAction.NAVIGATE
        assert step.url == "https://example.com"

    def test_test_step_click_requires_selector(self) -> None:
        """Test that click action requires selector."""
        with pytest.raises(ValueError, match="requires parameter 'selector'"):
            TestStep(action=StepAction.CLICK)

    def test_test_step_type_requires_text(self) -> None:
        """Test that type action requires text."""
        with pytest.raises(ValueError, match="requires parameter 'text'"):
            TestStep(action=StepAction.TYPE, selector="#input")

    def test_assertion_config_validation(self) -> None:
        """Test assertion config validation."""
        config = AssertionConfig(
            selector=".element",
            operator=AssertionOperator.IS_VISIBLE,
        )
        assert config.selector == ".element"
        assert config.operator == AssertionOperator.IS_VISIBLE

    def test_assertion_requires_selector_for_visibility(self) -> None:
        """Test that visibility operators require selector."""
        with pytest.raises(ValueError, match="requires a selector"):
            AssertionConfig(operator=AssertionOperator.IS_VISIBLE)

    def test_visual_assertion_config(self) -> None:
        """Test visual assertion configuration."""
        config = VisualAssertionConfig(
            baseline_name="homepage",
            mode=VisualComparisonMode.SEMANTIC,
            threshold=0.05,
        )
        assert config.baseline_name == "homepage"
        assert config.threshold == 0.05

    def test_test_spec_validation(self) -> None:
        """Test test spec validation."""
        spec = TestSpec(
            name="Login Test",
            steps=[
                TestStep(action=StepAction.NAVIGATE, url="https://example.com"),
            ],
        )
        assert spec.name == "Login Test"
        assert len(spec.steps) == 1

    def test_test_spec_requires_steps(self) -> None:
        """Test that test spec requires at least one step."""
        with pytest.raises(ValueError):
            TestSpec(name="Empty Test", steps=[])


class TestDSLParser:
    """Tests for DSL parser."""

    def test_parse_simple_spec(self, sample_test_spec: str) -> None:
        """Test parsing a simple test specification."""
        os.environ["TEST_PASSWORD"] = "secret123"
        parser = DSLParser()
        spec = parser.parse_string(sample_test_spec)

        assert isinstance(spec, TestSpec)
        assert spec.name == "Sample Login Test"
        assert len(spec.steps) == 5

    def test_parse_test_suite(self, sample_test_suite: str) -> None:
        """Test parsing a test suite."""
        parser = DSLParser()
        suite = parser.parse_string(sample_test_suite)

        assert isinstance(suite, TestSuite)
        assert suite.name == "E2E Test Suite"
        assert len(suite.tests) == 2
        assert suite.parallel_execution is True

    def test_parse_invalid_yaml(self) -> None:
        """Test parsing invalid YAML."""
        parser = DSLParser()
        with pytest.raises(DSLParseError, match="Invalid YAML"):
            parser.parse_string("name: test\n  invalid: [")

    def test_parse_missing_required_field(self) -> None:
        """Test parsing with missing required field."""
        parser = DSLParser()
        with pytest.raises(DSLParseError, match="Validation failed"):
            parser.parse_string("name: Test\nsteps: []")

    def test_variable_interpolation(self) -> None:
        """Test variable interpolation in spec."""
        yaml_content = '''
name: Variable Test
variables:
  url: https://example.com
steps:
  - action: navigate
    url: ${url}/login
'''
        parser = DSLParser()
        spec = parser.parse_string(yaml_content)

        assert spec.steps[0].url == "https://example.com/login"

    def test_parse_file(self, temp_dir: Path, sample_test_spec: str) -> None:
        """Test parsing from file."""
        os.environ["TEST_PASSWORD"] = "secret123"
        file_path = temp_dir / "test.yaml"
        file_path.write_text(sample_test_spec)

        parser = DSLParser()
        spec = parser.parse_file(file_path)

        assert spec.name == "Sample Login Test"


class TestDSLValidator:
    """Tests for DSL validator."""

    def test_validate_duplicate_test_names(self) -> None:
        """Test validation of duplicate test names in suite."""
        suite = TestSuite(
            name="Duplicate Suite",
            tests=[
                TestSpec(
                    name="Same Name",
                    steps=[TestStep(action=StepAction.NAVIGATE, url="https://a.com")],
                ),
                TestSpec(
                    name="Same Name",
                    steps=[TestStep(action=StepAction.NAVIGATE, url="https://b.com")],
                ),
            ],
        )

        validator = DSLValidator()
        errors = validator.validate(suite)

        assert any("Duplicate test name" in e for e in errors)

    def test_validate_url_format(self) -> None:
        """Test URL format validation."""
        spec = TestSpec(
            name="URL Test",
            steps=[
                TestStep(action=StepAction.NAVIGATE, url="invalid-url"),
            ],
        )

        validator = DSLValidator()
        errors = validator.validate(spec)

        assert any("Invalid URL format" in e for e in errors)


class TestStepTransformer:
    """Tests for step transformer."""

    def test_transform_navigate(self) -> None:
        """Test transforming navigate step."""
        step = TestStep(
            action=StepAction.NAVIGATE,
            url="https://example.com",
            wait_until="networkidle",
        )

        transformer = StepTransformer()
        method, args = transformer.transform(step)

        assert method == "goto"
        assert args["url"] == "https://example.com"
        assert args["wait_until"] == "networkidle"

    def test_transform_click(self) -> None:
        """Test transforming click step."""
        step = TestStep(
            action=StepAction.CLICK,
            selector="#button",
        )

        transformer = StepTransformer()
        method, args = transformer.transform(step)

        assert method == "click"
        assert args["selector"] == "#button"

    def test_transform_type(self) -> None:
        """Test transforming type step."""
        step = TestStep(
            action=StepAction.TYPE,
            selector="#input",
            text="Hello World",
        )

        transformer = StepTransformer()
        method, args = transformer.transform(step)

        assert method == "type"
        assert args["selector"] == "#input"
        assert args["text"] == "Hello World"

    def test_transform_assertion(self) -> None:
        """Test transforming assertion step."""
        step = TestStep(
            action=StepAction.ASSERT,
            assertion=AssertionConfig(
                selector=".element",
                operator=AssertionOperator.IS_VISIBLE,
            ),
        )

        transformer = StepTransformer()
        method, args = transformer.transform(step)

        assert method == "_assert_element"
        assert "config" in args
