"""
Deep form analysis for intelligent test generation.

Provides:
- Field type detection (email, phone, date, etc.)
- Validation rule inference
- Required field detection
- Boundary test case generation
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from autoqa.builder.analyzer.page_analyzer import InteractiveElement

logger = structlog.get_logger(__name__)


@dataclass
class FormConfig:
    """Configuration for form analyzer."""

    detect_validation_rules: bool = True
    """Whether to infer validation rules."""

    generate_test_cases: bool = True
    """Whether to generate test cases."""

    include_boundary_tests: bool = True
    """Whether to include boundary value tests."""

    include_negative_tests: bool = True
    """Whether to include negative test cases."""

    include_injection_tests: bool = True
    """Whether to include XSS/SQL injection tests."""

    max_test_cases_per_field: int = 10
    """Maximum test cases per field."""

    detect_field_relationships: bool = True
    """Whether to detect field relationships (confirm password, etc.)."""


class FieldType(StrEnum):
    """Detected field types."""

    TEXT = auto()
    EMAIL = auto()
    PASSWORD = auto()
    PHONE = auto()
    NUMBER = auto()
    INTEGER = auto()
    DECIMAL = auto()
    DATE = auto()
    TIME = auto()
    DATETIME = auto()
    URL = auto()
    CREDIT_CARD = auto()
    CVV = auto()
    ZIP_CODE = auto()
    SSN = auto()
    NAME = auto()
    FIRST_NAME = auto()
    LAST_NAME = auto()
    ADDRESS = auto()
    CITY = auto()
    STATE = auto()
    COUNTRY = auto()
    USERNAME = auto()
    FILE = auto()
    TEXTAREA = auto()
    SELECT = auto()
    CHECKBOX = auto()
    RADIO = auto()
    HIDDEN = auto()
    UNKNOWN = auto()


class ValidationType(StrEnum):
    """Types of validation rules."""

    REQUIRED = auto()
    MIN_LENGTH = auto()
    MAX_LENGTH = auto()
    MIN_VALUE = auto()
    MAX_VALUE = auto()
    PATTERN = auto()
    EMAIL_FORMAT = auto()
    URL_FORMAT = auto()
    PHONE_FORMAT = auto()
    DATE_FORMAT = auto()
    NUMERIC = auto()
    ALPHA = auto()
    ALPHANUMERIC = auto()
    CREDIT_CARD_FORMAT = auto()
    CUSTOM = auto()


class TestCaseType(StrEnum):
    """Types of test cases."""

    VALID = auto()
    INVALID = auto()
    BOUNDARY_MIN = auto()
    BOUNDARY_MAX = auto()
    BOUNDARY_BELOW_MIN = auto()
    BOUNDARY_ABOVE_MAX = auto()
    EMPTY = auto()
    NULL = auto()
    SPECIAL_CHARACTERS = auto()
    SQL_INJECTION = auto()
    XSS = auto()
    OVERFLOW = auto()


@dataclass
class ValidationRule:
    """A detected validation rule."""

    validation_type: ValidationType
    value: Any = None
    message: str = ""
    confidence: float = 1.0


@dataclass
class TestCase:
    """A generated test case for a field."""

    test_type: TestCaseType
    input_value: str
    expected_valid: bool
    description: str
    validation_rules_tested: list[ValidationType] = field(default_factory=list)


@dataclass
class FieldAnalysis:
    """Analysis of a single form field."""

    selector: str
    semantic_selector: str
    field_type: FieldType
    name: str | None
    label: str | None
    placeholder: str | None
    is_required: bool
    validation_rules: list[ValidationRule]
    test_cases: list[TestCase]
    sample_valid_value: str
    sample_invalid_value: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FormAnalysis:
    """Complete analysis of a form."""

    form_id: str
    form_selector: str
    action: str | None
    method: str
    fields: list[FieldAnalysis]
    submit_selector: str | None
    total_fields: int
    required_fields: int
    test_cases: list[dict[str, Any]]
    complexity_score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class FormAnalyzer:
    """
    Deep form analyzer for intelligent test generation.

    Features:
    - Field type detection from multiple signals
    - Validation rule inference
    - Test case generation (valid, invalid, boundary)
    - Form complexity scoring
    """

    # Field type patterns
    FIELD_TYPE_PATTERNS: dict[FieldType, dict[str, list[str]]] = {
        FieldType.EMAIL: {
            "type": ["email"],
            "name": ["email", "mail", "e-mail", "e_mail"],
            "placeholder": ["email", "e-mail", "your email"],
        },
        FieldType.PASSWORD: {
            "type": ["password"],
            "name": ["password", "passwd", "pwd", "pass"],
        },
        FieldType.PHONE: {
            "type": ["tel"],
            "name": ["phone", "tel", "mobile", "cell", "fax"],
            "placeholder": ["phone", "telephone", "mobile"],
        },
        FieldType.NUMBER: {
            "type": ["number"],
            "name": ["number", "num", "amount", "quantity", "qty"],
        },
        FieldType.DATE: {
            "type": ["date"],
            "name": ["date", "dob", "birthday", "birth_date"],
        },
        FieldType.TIME: {
            "type": ["time"],
            "name": ["time"],
        },
        FieldType.DATETIME: {
            "type": ["datetime", "datetime-local"],
            "name": ["datetime"],
        },
        FieldType.URL: {
            "type": ["url"],
            "name": ["url", "website", "link", "homepage"],
        },
        FieldType.CREDIT_CARD: {
            "name": ["card", "credit", "cc_number", "card_number", "cardnumber"],
            "placeholder": ["card number", "credit card"],
        },
        FieldType.CVV: {
            "name": ["cvv", "cvc", "security_code", "card_code"],
            "placeholder": ["cvv", "cvc", "security code"],
        },
        FieldType.ZIP_CODE: {
            "name": ["zip", "postal", "postcode", "zip_code"],
            "placeholder": ["zip", "postal code"],
        },
        FieldType.NAME: {
            "name": ["name", "fullname", "full_name"],
            "placeholder": ["your name", "full name"],
        },
        FieldType.FIRST_NAME: {
            "name": ["first", "firstname", "first_name", "fname", "given_name"],
            "placeholder": ["first name"],
        },
        FieldType.LAST_NAME: {
            "name": ["last", "lastname", "last_name", "lname", "surname", "family_name"],
            "placeholder": ["last name", "surname"],
        },
        FieldType.ADDRESS: {
            "name": ["address", "street", "addr", "address1", "address_line"],
            "placeholder": ["address", "street address"],
        },
        FieldType.CITY: {
            "name": ["city", "town"],
            "placeholder": ["city"],
        },
        FieldType.STATE: {
            "name": ["state", "province", "region"],
            "placeholder": ["state", "province"],
        },
        FieldType.COUNTRY: {
            "name": ["country", "nation"],
            "placeholder": ["country"],
        },
        FieldType.USERNAME: {
            "name": ["username", "user", "userid", "user_id", "login", "account"],
            "placeholder": ["username", "user name"],
        },
    }

    # Sample values for each field type
    SAMPLE_VALUES: dict[FieldType, tuple[str, str]] = {
        FieldType.TEXT: ("Test Text", ""),
        FieldType.EMAIL: ("test@example.com", "invalid-email"),
        FieldType.PASSWORD: ("SecureP@ss123!", "weak"),
        FieldType.PHONE: ("+1234567890", "not-a-phone"),
        FieldType.NUMBER: ("42", "not-a-number"),
        FieldType.INTEGER: ("100", "12.5"),
        FieldType.DECIMAL: ("99.99", "abc"),
        FieldType.DATE: ("2025-01-01", "invalid-date"),
        FieldType.TIME: ("14:30", "25:00"),
        FieldType.DATETIME: ("2025-01-01T14:30", "invalid"),
        FieldType.URL: ("https://example.com", "not-a-url"),
        FieldType.CREDIT_CARD: ("4111111111111111", "1234"),
        FieldType.CVV: ("123", "12"),
        FieldType.ZIP_CODE: ("12345", "ABCDE"),
        FieldType.SSN: ("123-45-6789", "invalid"),
        FieldType.NAME: ("John Doe", ""),
        FieldType.FIRST_NAME: ("John", ""),
        FieldType.LAST_NAME: ("Doe", ""),
        FieldType.ADDRESS: ("123 Main St", ""),
        FieldType.CITY: ("New York", ""),
        FieldType.STATE: ("NY", ""),
        FieldType.COUNTRY: ("United States", ""),
        FieldType.USERNAME: ("testuser123", ""),
        FieldType.FILE: ("test.pdf", ""),
        FieldType.TEXTAREA: ("This is a longer text input for testing purposes.", ""),
        FieldType.SELECT: ("option1", ""),
        FieldType.CHECKBOX: ("true", ""),
        FieldType.RADIO: ("option1", ""),
        FieldType.UNKNOWN: ("test value", ""),
    }

    def __init__(self, config: FormConfig | None = None) -> None:
        self.config = config or FormConfig()
        self._log = logger.bind(component="form_analyzer")

    def analyze_form(
        self,
        form_element: dict[str, Any],
        interactive_elements: list[InteractiveElement],
    ) -> FormAnalysis:
        """
        Analyze a form and its fields.

        Args:
            form_element: Form element information
            interactive_elements: Interactive elements within form

        Returns:
            Complete form analysis
        """
        form_id = form_element.get("id", "unknown_form")
        self._log.info("Analyzing form", form_id=form_id)

        # Filter elements belonging to this form
        form_fields = [
            el for el in interactive_elements
            if el.parent_component and form_id in el.parent_component
        ] or interactive_elements  # Fallback to all if no parent match

        # Analyze each field
        field_analyses: list[FieldAnalysis] = []
        for element in form_fields:
            if element.tag_name in ("input", "select", "textarea"):
                field_analysis = self.analyze_field(element)
                field_analyses.append(field_analysis)

        # Find submit button
        submit_selector = None
        for element in form_fields:
            if (element.tag_name == "button" or
                element.element_type in ("submit", "button")):
                submit_selector = element.semantic_selector or element.selector
                break

        # Calculate complexity score
        complexity = self._calculate_form_complexity(field_analyses)

        # Generate form-level test cases
        form_test_cases = self._generate_form_test_cases(field_analyses)

        return FormAnalysis(
            form_id=form_id,
            form_selector=f"#{form_id}" if form_id != "unknown_form" else "form",
            action=form_element.get("action"),
            method=form_element.get("method", "GET").upper(),
            fields=field_analyses,
            submit_selector=submit_selector,
            total_fields=len(field_analyses),
            required_fields=sum(1 for f in field_analyses if f.is_required),
            test_cases=form_test_cases,
            complexity_score=complexity,
        )

    def analyze_field(self, element: InteractiveElement) -> FieldAnalysis:
        """Analyze a single form field."""
        # Detect field type
        field_type = self._detect_field_type(element)

        # Detect validation rules
        validation_rules = self._detect_validation_rules(element, field_type)

        # Check if required
        is_required = (
            element.is_required or
            any(r.validation_type == ValidationType.REQUIRED for r in validation_rules)
        )
        if is_required and not any(r.validation_type == ValidationType.REQUIRED for r in validation_rules):
            validation_rules.insert(0, ValidationRule(
                validation_type=ValidationType.REQUIRED,
                confidence=1.0,
            ))

        # Generate test cases
        test_cases = self._generate_field_test_cases(field_type, validation_rules)

        # Get sample values
        valid_value, invalid_value = self.SAMPLE_VALUES.get(
            field_type, self.SAMPLE_VALUES[FieldType.TEXT]
        )

        # Determine label
        label = element.aria_label or element.placeholder or element.name

        return FieldAnalysis(
            selector=element.selector,
            semantic_selector=element.semantic_selector,
            field_type=field_type,
            name=element.name,
            label=label,
            placeholder=element.placeholder,
            is_required=is_required,
            validation_rules=validation_rules,
            test_cases=test_cases,
            sample_valid_value=valid_value,
            sample_invalid_value=invalid_value,
            confidence=0.8,
        )

    def _detect_field_type(self, element: InteractiveElement) -> FieldType:
        """Detect field type from element attributes."""
        # Direct type mapping
        type_map = {
            "password": FieldType.PASSWORD,
            "email": FieldType.EMAIL,
            "tel": FieldType.PHONE,
            "number": FieldType.NUMBER,
            "date": FieldType.DATE,
            "time": FieldType.TIME,
            "datetime-local": FieldType.DATETIME,
            "datetime": FieldType.DATETIME,
            "url": FieldType.URL,
            "file": FieldType.FILE,
            "checkbox": FieldType.CHECKBOX,
            "radio": FieldType.RADIO,
            "hidden": FieldType.HIDDEN,
        }

        el_type = element.element_type.lower()
        if el_type in type_map:
            return type_map[el_type]

        if element.tag_name == "textarea":
            return FieldType.TEXTAREA
        if element.tag_name == "select":
            return FieldType.SELECT

        # Pattern-based detection
        name = (element.name or "").lower()
        element_id = (element.element_id or "").lower()
        placeholder = (element.placeholder or "").lower()

        combined = f"{name} {element_id} {placeholder}"

        for field_type, patterns in self.FIELD_TYPE_PATTERNS.items():
            for category, keywords in patterns.items():
                for keyword in keywords:
                    if keyword in combined:
                        return field_type

        return FieldType.TEXT

    def _detect_validation_rules(
        self,
        element: InteractiveElement,
        field_type: FieldType,
    ) -> list[ValidationRule]:
        """Detect validation rules from element attributes."""
        rules: list[ValidationRule] = []
        validation_attrs = element.validation_attributes

        # Required
        if element.is_required or validation_attrs.get("required"):
            rules.append(ValidationRule(
                validation_type=ValidationType.REQUIRED,
                confidence=1.0,
            ))

        # Min/Max length
        if "minlength" in validation_attrs:
            rules.append(ValidationRule(
                validation_type=ValidationType.MIN_LENGTH,
                value=int(validation_attrs["minlength"]),
                confidence=1.0,
            ))
        if "maxlength" in validation_attrs:
            rules.append(ValidationRule(
                validation_type=ValidationType.MAX_LENGTH,
                value=int(validation_attrs["maxlength"]),
                confidence=1.0,
            ))

        # Min/Max value (for numbers)
        if "min" in validation_attrs:
            rules.append(ValidationRule(
                validation_type=ValidationType.MIN_VALUE,
                value=float(validation_attrs["min"]),
                confidence=1.0,
            ))
        if "max" in validation_attrs:
            rules.append(ValidationRule(
                validation_type=ValidationType.MAX_VALUE,
                value=float(validation_attrs["max"]),
                confidence=1.0,
            ))

        # Pattern
        if "pattern" in validation_attrs:
            rules.append(ValidationRule(
                validation_type=ValidationType.PATTERN,
                value=validation_attrs["pattern"],
                confidence=1.0,
            ))

        # Type-based implicit validations
        type_validations = {
            FieldType.EMAIL: ValidationType.EMAIL_FORMAT,
            FieldType.URL: ValidationType.URL_FORMAT,
            FieldType.PHONE: ValidationType.PHONE_FORMAT,
            FieldType.DATE: ValidationType.DATE_FORMAT,
            FieldType.NUMBER: ValidationType.NUMERIC,
            FieldType.INTEGER: ValidationType.NUMERIC,
            FieldType.DECIMAL: ValidationType.NUMERIC,
            FieldType.CREDIT_CARD: ValidationType.CREDIT_CARD_FORMAT,
        }

        if field_type in type_validations:
            rules.append(ValidationRule(
                validation_type=type_validations[field_type],
                confidence=0.9,
            ))

        return rules

    def _generate_field_test_cases(
        self,
        field_type: FieldType,
        validation_rules: list[ValidationRule],
    ) -> list[TestCase]:
        """Generate test cases for a field."""
        test_cases: list[TestCase] = []
        valid_value, invalid_value = self.SAMPLE_VALUES.get(
            field_type, self.SAMPLE_VALUES[FieldType.TEXT]
        )

        # Valid input test
        test_cases.append(TestCase(
            test_type=TestCaseType.VALID,
            input_value=valid_value,
            expected_valid=True,
            description="Valid input",
        ))

        # Empty input test
        is_required = any(r.validation_type == ValidationType.REQUIRED for r in validation_rules)
        test_cases.append(TestCase(
            test_type=TestCaseType.EMPTY,
            input_value="",
            expected_valid=not is_required,
            description="Empty input (should fail if required)",
            validation_rules_tested=[ValidationType.REQUIRED] if is_required else [],
        ))

        # Format violation test
        if invalid_value:
            test_cases.append(TestCase(
                test_type=TestCaseType.INVALID,
                input_value=invalid_value,
                expected_valid=False,
                description="Invalid format",
            ))

        # Boundary tests
        for rule in validation_rules:
            if rule.validation_type == ValidationType.MIN_LENGTH:
                min_len = rule.value
                test_cases.append(TestCase(
                    test_type=TestCaseType.BOUNDARY_MIN,
                    input_value="a" * min_len,
                    expected_valid=True,
                    description=f"Minimum length ({min_len})",
                    validation_rules_tested=[ValidationType.MIN_LENGTH],
                ))
                test_cases.append(TestCase(
                    test_type=TestCaseType.BOUNDARY_BELOW_MIN,
                    input_value="a" * (min_len - 1) if min_len > 1 else "",
                    expected_valid=False,
                    description=f"Below minimum length ({min_len - 1})",
                    validation_rules_tested=[ValidationType.MIN_LENGTH],
                ))

            if rule.validation_type == ValidationType.MAX_LENGTH:
                max_len = rule.value
                test_cases.append(TestCase(
                    test_type=TestCaseType.BOUNDARY_MAX,
                    input_value="a" * max_len,
                    expected_valid=True,
                    description=f"Maximum length ({max_len})",
                    validation_rules_tested=[ValidationType.MAX_LENGTH],
                ))
                test_cases.append(TestCase(
                    test_type=TestCaseType.BOUNDARY_ABOVE_MAX,
                    input_value="a" * (max_len + 1),
                    expected_valid=False,
                    description=f"Above maximum length ({max_len + 1})",
                    validation_rules_tested=[ValidationType.MAX_LENGTH],
                ))

            if rule.validation_type == ValidationType.MIN_VALUE:
                min_val = rule.value
                test_cases.append(TestCase(
                    test_type=TestCaseType.BOUNDARY_MIN,
                    input_value=str(min_val),
                    expected_valid=True,
                    description=f"Minimum value ({min_val})",
                    validation_rules_tested=[ValidationType.MIN_VALUE],
                ))
                test_cases.append(TestCase(
                    test_type=TestCaseType.BOUNDARY_BELOW_MIN,
                    input_value=str(min_val - 1),
                    expected_valid=False,
                    description=f"Below minimum value ({min_val - 1})",
                    validation_rules_tested=[ValidationType.MIN_VALUE],
                ))

            if rule.validation_type == ValidationType.MAX_VALUE:
                max_val = rule.value
                test_cases.append(TestCase(
                    test_type=TestCaseType.BOUNDARY_MAX,
                    input_value=str(max_val),
                    expected_valid=True,
                    description=f"Maximum value ({max_val})",
                    validation_rules_tested=[ValidationType.MAX_VALUE],
                ))
                test_cases.append(TestCase(
                    test_type=TestCaseType.BOUNDARY_ABOVE_MAX,
                    input_value=str(max_val + 1),
                    expected_valid=False,
                    description=f"Above maximum value ({max_val + 1})",
                    validation_rules_tested=[ValidationType.MAX_VALUE],
                ))

        # Security tests
        if field_type in (FieldType.TEXT, FieldType.TEXTAREA, FieldType.NAME):
            test_cases.append(TestCase(
                test_type=TestCaseType.SPECIAL_CHARACTERS,
                input_value="<script>alert('test')</script>",
                expected_valid=False,
                description="XSS attempt",
                validation_rules_tested=[],
            ))
            test_cases.append(TestCase(
                test_type=TestCaseType.SQL_INJECTION,
                input_value="'; DROP TABLE users; --",
                expected_valid=False,
                description="SQL injection attempt",
                validation_rules_tested=[],
            ))

        return test_cases

    def _calculate_form_complexity(self, fields: list[FieldAnalysis]) -> float:
        """Calculate form complexity score (0-1)."""
        if not fields:
            return 0.0

        # Factors
        field_count_score = min(len(fields) / 20, 1.0)
        required_ratio = sum(1 for f in fields if f.is_required) / len(fields)
        validation_count = sum(len(f.validation_rules) for f in fields)
        validation_score = min(validation_count / (len(fields) * 3), 1.0)

        # Unique field types
        unique_types = len(set(f.field_type for f in fields))
        type_diversity = min(unique_types / 10, 1.0)

        complexity = (
            0.3 * field_count_score +
            0.2 * required_ratio +
            0.3 * validation_score +
            0.2 * type_diversity
        )

        return round(complexity, 3)

    def _generate_form_test_cases(
        self,
        fields: list[FieldAnalysis],
    ) -> list[dict[str, Any]]:
        """Generate form-level test cases."""
        test_cases: list[dict[str, Any]] = []

        # All valid inputs
        valid_inputs = {f.name or f.selector: f.sample_valid_value for f in fields}
        test_cases.append({
            "name": "All valid inputs",
            "type": "positive",
            "inputs": valid_inputs,
            "expected_result": "success",
        })

        # All empty inputs
        empty_inputs = {f.name or f.selector: "" for f in fields}
        required_fields = [f for f in fields if f.is_required]
        test_cases.append({
            "name": "All empty inputs",
            "type": "negative",
            "inputs": empty_inputs,
            "expected_result": "failure" if required_fields else "success",
            "expected_errors": [f.name or f.label for f in required_fields],
        })

        # Each required field empty (one at a time)
        for req_field in required_fields:
            inputs = valid_inputs.copy()
            inputs[req_field.name or req_field.selector] = ""
            test_cases.append({
                "name": f"Missing required: {req_field.label or req_field.name}",
                "type": "negative",
                "inputs": inputs,
                "expected_result": "failure",
                "expected_errors": [req_field.name or req_field.label],
            })

        # Each field with invalid format
        for field_analysis in fields:
            if field_analysis.sample_invalid_value:
                inputs = valid_inputs.copy()
                inputs[field_analysis.name or field_analysis.selector] = field_analysis.sample_invalid_value
                test_cases.append({
                    "name": f"Invalid format: {field_analysis.label or field_analysis.name}",
                    "type": "negative",
                    "inputs": inputs,
                    "expected_result": "failure",
                    "expected_errors": [field_analysis.name or field_analysis.label],
                })

        return test_cases
