"""
Intelligent test strategy generation.

Provides:
- Test prioritization by risk/importance
- Test type classification (smoke, regression, edge case)
- Coverage optimization
- Test dependency ordering
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, StrEnum, auto
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from autoqa.builder.analyzer.page_analyzer import PageAnalysisResult
    from autoqa.builder.analyzer.element_classifier import ClassificationResult, UserJourney
    from autoqa.builder.discovery.flow_detector import UserFlow
    from autoqa.builder.discovery.form_analyzer import FormAnalysis
    from autoqa.builder.discovery.api_detector import APIDetectionResult

logger = structlog.get_logger(__name__)


class TestPriority(IntEnum):
    """Test priority levels."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    OPTIONAL = 5


class TestType(StrEnum):
    """Types of tests."""

    SMOKE = auto()
    REGRESSION = auto()
    SANITY = auto()
    FUNCTIONAL = auto()
    INTEGRATION = auto()
    E2E = auto()
    BOUNDARY = auto()
    NEGATIVE = auto()
    SECURITY = auto()
    PERFORMANCE = auto()
    ACCESSIBILITY = auto()
    VISUAL = auto()
    API = auto()


class RiskLevel(StrEnum):
    """Risk level assessment."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class StrategyConfig:
    """Configuration for test strategy generation."""

    include_smoke_tests: bool = True
    include_regression_tests: bool = True
    include_boundary_tests: bool = True
    include_negative_tests: bool = True
    include_security_tests: bool = True
    include_accessibility_tests: bool = True
    include_visual_tests: bool = True
    include_api_tests: bool = True
    max_tests_per_flow: int = 10
    max_total_tests: int = 100
    prioritize_critical_paths: bool = True
    generate_dependencies: bool = True


@dataclass
class TestCase:
    """A single test case."""

    test_id: str
    name: str
    description: str
    test_type: TestType
    priority: TestPriority
    risk_level: RiskLevel
    steps: list[dict[str, Any]]
    assertions: list[dict[str, Any]]
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    estimated_duration_ms: int = 5000
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuite:
    """A collection of related test cases."""

    suite_id: str
    name: str
    description: str
    test_cases: list[TestCase]
    setup_steps: list[dict[str, Any]] = field(default_factory=list)
    teardown_steps: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class TestPlan:
    """Complete test plan."""

    plan_id: str
    name: str
    description: str
    test_suites: list[TestSuite]
    execution_order: list[str]  # Test case IDs in execution order
    coverage_summary: dict[str, Any]
    risk_summary: dict[str, int]
    estimated_total_duration_ms: int
    metadata: dict[str, Any] = field(default_factory=dict)


class TestStrategy:
    """
    Generates intelligent test strategies from analysis results.

    Features:
    - Risk-based test prioritization
    - Test type classification
    - Coverage optimization
    - Dependency ordering
    """

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self._config = config or StrategyConfig()
        self._log = logger.bind(component="test_strategy")
        self._test_counter = 0

    def generate_test_plan(
        self,
        page_analyses: list[PageAnalysisResult],
        user_flows: list[UserFlow] | None = None,
        form_analyses: list[FormAnalysis] | None = None,
        api_detection: APIDetectionResult | None = None,
        classifications: list[ClassificationResult] | None = None,
    ) -> TestPlan:
        """
        Generate a comprehensive test plan.

        Args:
            page_analyses: Page analysis results
            user_flows: Detected user flows
            form_analyses: Form analysis results
            api_detection: API detection results
            classifications: Element classifications

        Returns:
            Complete test plan
        """
        self._log.info(
            "Generating test plan",
            pages=len(page_analyses),
            flows=len(user_flows) if user_flows else 0,
            forms=len(form_analyses) if form_analyses else 0,
        )

        test_suites: list[TestSuite] = []

        # Generate smoke tests
        if self._config.include_smoke_tests:
            smoke_suite = self._generate_smoke_tests(page_analyses)
            test_suites.append(smoke_suite)

        # Generate flow-based tests
        if user_flows:
            flow_suite = self._generate_flow_tests(user_flows)
            test_suites.append(flow_suite)

        # Generate form tests
        if form_analyses and self._config.include_regression_tests:
            form_suite = self._generate_form_tests(form_analyses)
            test_suites.append(form_suite)

        # Generate API tests
        if api_detection and self._config.include_api_tests:
            api_suite = self._generate_api_tests(api_detection)
            test_suites.append(api_suite)

        # Generate accessibility tests
        if self._config.include_accessibility_tests:
            a11y_suite = self._generate_accessibility_tests(page_analyses)
            test_suites.append(a11y_suite)

        # Generate visual regression tests
        if self._config.include_visual_tests:
            visual_suite = self._generate_visual_tests(page_analyses)
            test_suites.append(visual_suite)

        # Determine execution order
        all_tests = [tc for suite in test_suites for tc in suite.test_cases]
        execution_order = self._determine_execution_order(all_tests)

        # Calculate coverage
        coverage_summary = self._calculate_coverage(page_analyses, all_tests)

        # Calculate risk summary
        risk_summary = self._calculate_risk_summary(all_tests)

        # Calculate total duration
        total_duration = sum(tc.estimated_duration_ms for tc in all_tests)

        plan = TestPlan(
            plan_id=f"plan_{self._test_counter}",
            name="Auto-Generated Test Plan",
            description=f"Comprehensive test plan covering {len(page_analyses)} pages with {len(all_tests)} test cases",
            test_suites=test_suites,
            execution_order=execution_order,
            coverage_summary=coverage_summary,
            risk_summary=risk_summary,
            estimated_total_duration_ms=total_duration,
        )

        self._log.info(
            "Test plan generated",
            suites=len(test_suites),
            total_tests=len(all_tests),
            estimated_duration_ms=total_duration,
        )

        return plan

    def _generate_smoke_tests(
        self, page_analyses: list[PageAnalysisResult]
    ) -> TestSuite:
        """Generate smoke tests for quick validation."""
        test_cases: list[TestCase] = []

        for analysis in page_analyses:
            # Page load test
            test_cases.append(TestCase(
                test_id=self._next_test_id("smoke"),
                name=f"Smoke: Load {analysis.title}",
                description=f"Verify {analysis.title} page loads successfully",
                test_type=TestType.SMOKE,
                priority=TestPriority.CRITICAL,
                risk_level=RiskLevel.HIGH,
                steps=[
                    {"action": "navigate", "url": analysis.url},
                    {"action": "wait_for_network_idle"},
                ],
                assertions=[
                    {"type": "page_loaded", "timeout": 10000},
                    {"type": "title_contains", "value": analysis.title[:20] if analysis.title else ""},
                    {"type": "no_console_errors"},
                ],
                tags=["smoke", "critical"],
                estimated_duration_ms=3000,
            ))

            # Key elements visible test
            if analysis.interactive_elements:
                key_elements = analysis.interactive_elements[:5]
                test_cases.append(TestCase(
                    test_id=self._next_test_id("smoke"),
                    name=f"Smoke: Key Elements on {analysis.title}",
                    description="Verify key interactive elements are visible",
                    test_type=TestType.SMOKE,
                    priority=TestPriority.HIGH,
                    risk_level=RiskLevel.HIGH,
                    steps=[
                        {"action": "navigate", "url": analysis.url},
                    ],
                    assertions=[
                        {
                            "type": "element_visible",
                            "selector": el.semantic_selector or el.selector,
                        }
                        for el in key_elements
                    ],
                    tags=["smoke", "visibility"],
                    estimated_duration_ms=5000,
                ))

        return TestSuite(
            suite_id="smoke_suite",
            name="Smoke Tests",
            description="Quick validation tests to ensure basic functionality",
            test_cases=test_cases,
            tags=["smoke", "critical"],
        )

    def _generate_flow_tests(self, user_flows: list[UserFlow]) -> TestSuite:
        """Generate tests for user flows."""
        test_cases: list[TestCase] = []

        # Sort flows by priority
        sorted_flows = sorted(user_flows, key=lambda f: f.priority)

        for flow in sorted_flows[:self._config.max_tests_per_flow]:
            # Map flow type to test priority and risk
            priority = self._flow_to_priority(flow)
            risk = self._flow_to_risk(flow)

            # Convert flow steps to test steps
            steps = [
                {
                    "action": step.step_type.value,
                    "selector": step.selector,
                    "value": step.action_value,
                    "timeout": step.timeout_ms,
                }
                for step in flow.steps
            ]

            # Generate assertions based on flow type
            assertions = self._generate_flow_assertions(flow)

            test_cases.append(TestCase(
                test_id=self._next_test_id("flow"),
                name=f"Flow: {flow.name}",
                description=flow.description,
                test_type=TestType.E2E,
                priority=priority,
                risk_level=risk,
                steps=steps,
                assertions=assertions,
                preconditions=flow.preconditions,
                postconditions=flow.postconditions,
                tags=["flow", flow.flow_type.value] + flow.tags,
                estimated_duration_ms=len(flow.steps) * 2000,
            ))

            # Generate negative test for critical flows
            if priority <= TestPriority.HIGH and self._config.include_negative_tests:
                negative_test = self._generate_negative_flow_test(flow)
                if negative_test:
                    test_cases.append(negative_test)

        return TestSuite(
            suite_id="flow_suite",
            name="User Flow Tests",
            description="End-to-end tests for detected user flows",
            test_cases=test_cases,
            tags=["flow", "e2e"],
        )

    def _generate_form_tests(
        self, form_analyses: list[FormAnalysis]
    ) -> TestSuite:
        """Generate tests for form submissions."""
        test_cases: list[TestCase] = []

        for form in form_analyses:
            # Valid submission test
            valid_inputs = {
                f.name or f.selector: f.sample_valid_value
                for f in form.fields
            }
            test_cases.append(TestCase(
                test_id=self._next_test_id("form"),
                name=f"Form: Valid submission - {form.form_id}",
                description="Test form with all valid inputs",
                test_type=TestType.FUNCTIONAL,
                priority=TestPriority.HIGH,
                risk_level=RiskLevel.MEDIUM,
                steps=[
                    {"action": "type", "selector": f.selector, "value": f.sample_valid_value}
                    for f in form.fields if f.field_type.value not in ("checkbox", "radio", "select")
                ] + [
                    {"action": "click", "selector": form.submit_selector}
                ] if form.submit_selector else [],
                assertions=[
                    {"type": "form_submitted"},
                    {"type": "no_validation_errors"},
                ],
                tags=["form", "positive"],
                estimated_duration_ms=5000,
            ))

            # Add boundary tests for each field
            if self._config.include_boundary_tests:
                for field_analysis in form.fields:
                    for test_case in field_analysis.test_cases[:3]:  # Limit per field
                        if test_case.test_type.value.startswith("boundary"):
                            test_cases.append(TestCase(
                                test_id=self._next_test_id("boundary"),
                                name=f"Boundary: {field_analysis.label or field_analysis.name} - {test_case.description}",
                                description=test_case.description,
                                test_type=TestType.BOUNDARY,
                                priority=TestPriority.MEDIUM,
                                risk_level=RiskLevel.LOW,
                                steps=[
                                    {"action": "type", "selector": field_analysis.selector, "value": test_case.input_value},
                                ],
                                assertions=[
                                    {"type": "validation_state", "expected": "valid" if test_case.expected_valid else "invalid"},
                                ],
                                tags=["form", "boundary", field_analysis.field_type.value],
                                estimated_duration_ms=2000,
                            ))

        return TestSuite(
            suite_id="form_suite",
            name="Form Tests",
            description="Form validation and submission tests",
            test_cases=test_cases,
            tags=["form", "validation"],
        )

    def _generate_api_tests(
        self, api_detection: APIDetectionResult
    ) -> TestSuite:
        """Generate API validation tests."""
        test_cases: list[TestCase] = []

        for endpoint in api_detection.endpoints[:20]:  # Limit endpoints
            # Basic API smoke test
            test_cases.append(TestCase(
                test_id=self._next_test_id("api"),
                name=f"API: {endpoint.method} {endpoint.path}",
                description=f"Validate {endpoint.method} endpoint returns expected status",
                test_type=TestType.API,
                priority=TestPriority.HIGH if endpoint.is_authenticated else TestPriority.MEDIUM,
                risk_level=RiskLevel.HIGH if endpoint.is_authenticated else RiskLevel.MEDIUM,
                steps=[
                    {
                        "action": "api_request",
                        "method": endpoint.method.value,
                        "url": endpoint.url,
                        "headers": endpoint.headers,
                    },
                ],
                assertions=[
                    {"type": "status_code", "expected": endpoint.response_status},
                    {"type": "response_time", "max_ms": 5000},
                ],
                tags=["api"] + endpoint.tags,
                estimated_duration_ms=2000,
            ))

        # Add generated validation tests
        for validation_test in api_detection.validation_tests[:10]:
            test_cases.append(TestCase(
                test_id=self._next_test_id("api"),
                name=validation_test.name,
                description=f"API validation: {validation_test.test_type}",
                test_type=TestType.API,
                priority=TestPriority.MEDIUM,
                risk_level=RiskLevel.MEDIUM,
                steps=[
                    {
                        "action": "api_request",
                        "method": validation_test.endpoint.method.value,
                        "url": validation_test.endpoint.url,
                        "body": validation_test.request_data,
                    },
                ],
                assertions=validation_test.assertions,
                tags=["api", validation_test.test_type],
                estimated_duration_ms=2000,
            ))

        return TestSuite(
            suite_id="api_suite",
            name="API Tests",
            description="API endpoint validation tests",
            test_cases=test_cases,
            tags=["api"],
        )

    def _generate_accessibility_tests(
        self, page_analyses: list[PageAnalysisResult]
    ) -> TestSuite:
        """Generate accessibility tests."""
        test_cases: list[TestCase] = []

        for analysis in page_analyses:
            test_cases.append(TestCase(
                test_id=self._next_test_id("a11y"),
                name=f"Accessibility: {analysis.title}",
                description="Validate page meets accessibility standards",
                test_type=TestType.ACCESSIBILITY,
                priority=TestPriority.MEDIUM,
                risk_level=RiskLevel.MEDIUM,
                steps=[
                    {"action": "navigate", "url": analysis.url},
                ],
                assertions=[
                    {"type": "wcag_contrast", "level": "AA"},
                    {"type": "images_have_alt"},
                    {"type": "form_labels_present"},
                    {"type": "heading_structure"},
                    {"type": "focus_visible"},
                ],
                tags=["accessibility", "wcag"],
                estimated_duration_ms=5000,
            ))

        return TestSuite(
            suite_id="accessibility_suite",
            name="Accessibility Tests",
            description="WCAG compliance and accessibility validation",
            test_cases=test_cases,
            tags=["accessibility"],
        )

    def _generate_visual_tests(
        self, page_analyses: list[PageAnalysisResult]
    ) -> TestSuite:
        """Generate visual regression tests."""
        test_cases: list[TestCase] = []

        for analysis in page_analyses:
            test_cases.append(TestCase(
                test_id=self._next_test_id("visual"),
                name=f"Visual: {analysis.title}",
                description="Visual regression test for page appearance",
                test_type=TestType.VISUAL,
                priority=TestPriority.LOW,
                risk_level=RiskLevel.LOW,
                steps=[
                    {"action": "navigate", "url": analysis.url},
                    {"action": "wait_for_network_idle"},
                    {"action": "screenshot", "name": f"visual_{analysis.dom_analysis.dom_hash}"},
                ],
                assertions=[
                    {"type": "visual_diff", "threshold": 0.05, "baseline": f"baseline_{analysis.dom_analysis.dom_hash}"},
                ],
                tags=["visual", "regression"],
                estimated_duration_ms=3000,
            ))

        return TestSuite(
            suite_id="visual_suite",
            name="Visual Regression Tests",
            description="Visual comparison tests to detect UI changes",
            test_cases=test_cases,
            tags=["visual"],
        )

    def _flow_to_priority(self, flow: UserFlow) -> TestPriority:
        """Map flow to test priority."""
        priority_map = {
            "login": TestPriority.CRITICAL,
            "registration": TestPriority.CRITICAL,
            "checkout": TestPriority.CRITICAL,
            "crud_delete": TestPriority.HIGH,
            "search": TestPriority.HIGH,
            "crud_create": TestPriority.HIGH,
            "crud_update": TestPriority.MEDIUM,
            "navigation": TestPriority.LOW,
        }
        return priority_map.get(flow.flow_type.value, TestPriority.MEDIUM)

    def _flow_to_risk(self, flow: UserFlow) -> RiskLevel:
        """Map flow to risk level."""
        risk_map = {
            "login": RiskLevel.CRITICAL,
            "registration": RiskLevel.CRITICAL,
            "checkout": RiskLevel.CRITICAL,
            "crud_delete": RiskLevel.HIGH,
        }
        return risk_map.get(flow.flow_type.value, RiskLevel.MEDIUM)

    def _generate_flow_assertions(self, flow: UserFlow) -> list[dict[str, Any]]:
        """Generate assertions for a flow."""
        assertions: list[dict[str, Any]] = []

        # URL change assertion for flows with exit URL
        if flow.exit_url:
            assertions.append({
                "type": "url_contains",
                "value": flow.exit_url,
            })

        # Flow-specific assertions
        if flow.flow_type.value == "login":
            assertions.extend([
                {"type": "authenticated"},
                {"type": "no_error_message"},
            ])
        elif flow.flow_type.value == "registration":
            assertions.extend([
                {"type": "success_message"},
                {"type": "no_validation_errors"},
            ])
        elif flow.flow_type.value == "search":
            assertions.append({"type": "results_displayed"})
        elif flow.flow_type.value == "checkout":
            assertions.append({"type": "order_confirmation"})

        # Generic success assertion
        assertions.append({"type": "no_console_errors"})

        return assertions

    def _generate_negative_flow_test(self, flow: UserFlow) -> TestCase | None:
        """Generate negative test for a flow."""
        if flow.flow_type.value == "login":
            return TestCase(
                test_id=self._next_test_id("negative"),
                name=f"Negative: Invalid {flow.name}",
                description="Test flow with invalid credentials",
                test_type=TestType.NEGATIVE,
                priority=TestPriority.HIGH,
                risk_level=RiskLevel.HIGH,
                steps=[
                    {**step.__dict__, "value": "invalid_" + (step.action_value or "")}
                    if step.step_type.value == "input" else step.__dict__
                    for step in flow.steps
                ],
                assertions=[
                    {"type": "error_message_displayed"},
                    {"type": "not_authenticated"},
                ],
                tags=["negative", "security"],
                estimated_duration_ms=3000,
            )
        return None

    def _determine_execution_order(
        self, test_cases: list[TestCase]
    ) -> list[str]:
        """Determine optimal test execution order."""
        # Sort by priority, then by dependencies
        ordered: list[str] = []
        remaining = {tc.test_id: tc for tc in test_cases}
        completed: set[str] = set()

        while remaining:
            # Find tests with satisfied dependencies
            ready = [
                tc for tc in remaining.values()
                if all(dep in completed for dep in tc.dependencies)
            ]

            if not ready:
                # No tests ready, add remaining by priority
                ready = list(remaining.values())

            # Sort by priority
            ready.sort(key=lambda tc: tc.priority)

            # Add first ready test
            next_test = ready[0]
            ordered.append(next_test.test_id)
            completed.add(next_test.test_id)
            del remaining[next_test.test_id]

        return ordered

    def _calculate_coverage(
        self,
        page_analyses: list[PageAnalysisResult],
        test_cases: list[TestCase],
    ) -> dict[str, Any]:
        """Calculate test coverage metrics."""
        total_pages = len(page_analyses)
        total_elements = sum(len(p.interactive_elements) for p in page_analyses)
        total_components = sum(len(p.components) for p in page_analyses)

        # Count unique URLs in tests
        tested_urls: set[str] = set()
        for tc in test_cases:
            for step in tc.steps:
                if step.get("action") == "navigate":
                    tested_urls.add(step.get("url", ""))

        return {
            "pages_total": total_pages,
            "pages_covered": len(tested_urls),
            "page_coverage_percent": len(tested_urls) / total_pages * 100 if total_pages > 0 else 0,
            "elements_total": total_elements,
            "components_total": total_components,
            "test_types": dict(self._count_by_type(test_cases)),
            "tests_by_priority": dict(self._count_by_priority(test_cases)),
        }

    def _calculate_risk_summary(
        self, test_cases: list[TestCase]
    ) -> dict[str, int]:
        """Calculate risk coverage summary."""
        risk_counts: dict[str, int] = {r.value: 0 for r in RiskLevel}
        for tc in test_cases:
            risk_counts[tc.risk_level.value] += 1
        return risk_counts

    def _count_by_type(
        self, test_cases: list[TestCase]
    ) -> dict[str, int]:
        """Count tests by type."""
        counts: dict[str, int] = {}
        for tc in test_cases:
            counts[tc.test_type.value] = counts.get(tc.test_type.value, 0) + 1
        return counts

    def _count_by_priority(
        self, test_cases: list[TestCase]
    ) -> dict[int, int]:
        """Count tests by priority."""
        counts: dict[int, int] = {}
        for tc in test_cases:
            counts[tc.priority] = counts.get(tc.priority, 0) + 1
        return counts

    def _next_test_id(self, prefix: str) -> str:
        """Generate next test ID."""
        self._test_counter += 1
        return f"{prefix}_{self._test_counter}"
