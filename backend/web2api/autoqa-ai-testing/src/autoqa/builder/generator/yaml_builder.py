"""
YAML Builder for intelligent test construction.

Transforms analysis results into valid YAML test specifications
with comprehensive assertions, metadata, and documentation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

import structlog
import yaml

from autoqa.builder.generator.assertion_generator import Assertion, AssertionType


logger = structlog.get_logger(__name__)


class StepType(str, Enum):
    """Types of test steps."""
    
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    HOVER = "hover"
    SCROLL = "scroll"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    ASSERT = "assert"
    EXECUTE_JS = "execute_js"
    UPLOAD = "upload"
    DRAG_DROP = "drag_drop"
    KEYBOARD = "keyboard"
    FOCUS = "focus"
    BLUR = "blur"
    CLEAR = "clear"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    PRESS_KEY = "press_key"
    SET_COOKIE = "set_cookie"
    DELETE_COOKIE = "delete_cookie"
    SET_LOCAL_STORAGE = "set_local_storage"
    SET_SESSION_STORAGE = "set_session_storage"
    IFRAME_SWITCH = "iframe_switch"
    FRAME_EXIT = "frame_exit"
    DIALOG_ACCEPT = "dialog_accept"
    DIALOG_DISMISS = "dialog_dismiss"
    DIALOG_INPUT = "dialog_input"
    WAIT_FOR_NAVIGATION = "wait_for_navigation"
    WAIT_FOR_ELEMENT = "wait_for_element"
    WAIT_FOR_NETWORK_IDLE = "wait_for_network_idle"


@dataclass
class YAMLStep:
    """Represents a single test step."""
    
    step_type: StepType
    description: str
    selector: str | None = None
    value: str | None = None
    timeout: int | None = None
    options: dict[str, Any] = field(default_factory=dict)
    assertions: list[Assertion] = field(default_factory=list)
    screenshot: bool = False
    continue_on_failure: bool = False
    retry_count: int = 0
    delay_before: int | None = None
    delay_after: int | None = None
    condition: str | None = None  # JavaScript condition for conditional execution
    variables: dict[str, str] = field(default_factory=dict)  # Variable extraction
    
    def to_dict(self) -> dict[str, Any]:
        """Convert step to dictionary for YAML serialization."""
        result: dict[str, Any] = {
            "action": self.step_type.value,
            "description": self.description,
        }
        
        if self.selector:
            result["selector"] = self.selector
        
        if self.value is not None:
            result["value"] = self.value
        
        if self.timeout:
            result["timeout"] = self.timeout
        
        if self.options:
            result["options"] = self.options
        
        if self.assertions:
            result["assertions"] = [
                self._assertion_to_dict(a) for a in self.assertions
            ]
        
        if self.screenshot:
            result["screenshot"] = True
        
        if self.continue_on_failure:
            result["continue_on_failure"] = True
        
        if self.retry_count > 0:
            result["retry"] = self.retry_count
        
        if self.delay_before:
            result["delay_before"] = self.delay_before
        
        if self.delay_after:
            result["delay_after"] = self.delay_after
        
        if self.condition:
            result["condition"] = self.condition
        
        if self.variables:
            result["extract_variables"] = self.variables
        
        return result
    
    def _assertion_to_dict(self, assertion: Assertion) -> dict[str, Any]:
        """Convert assertion to dictionary."""
        result: dict[str, Any] = {
            "type": assertion.assertion_type.value,
        }
        
        if assertion.selector:
            result["selector"] = assertion.selector
        
        if assertion.expected_value is not None:
            result["expected"] = assertion.expected_value
        
        if assertion.comparison:
            result["comparison"] = assertion.comparison
        
        if assertion.options:
            result["options"] = assertion.options
        
        if assertion.message:
            result["message"] = assertion.message
        
        return result


@dataclass
class YAMLTestSpec:
    """Complete test specification."""
    
    name: str
    description: str
    steps: list[YAMLStep] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    priority: str = "medium"
    timeout: int = 30000
    retries: int = 0
    setup_steps: list[YAMLStep] = field(default_factory=list)
    teardown_steps: list[YAMLStep] = field(default_factory=list)
    data_driven: dict[str, list[Any]] | None = None
    preconditions: list[str] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)
    browser_options: dict[str, Any] = field(default_factory=dict)
    viewport: dict[str, int] | None = None
    skip_condition: str | None = None
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert test spec to dictionary for YAML serialization."""
        result: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "timeout": self.timeout,
        }
        
        if self.tags:
            result["tags"] = self.tags
        
        if self.retries > 0:
            result["retries"] = self.retries
        
        if self.variables:
            result["variables"] = self.variables
        
        if self.preconditions:
            result["preconditions"] = self.preconditions
        
        if self.browser_options:
            result["browser_options"] = self.browser_options
        
        if self.viewport:
            result["viewport"] = self.viewport
        
        if self.skip_condition:
            result["skip_if"] = self.skip_condition
        
        if self.dependencies:
            result["depends_on"] = self.dependencies
        
        if self.data_driven:
            result["data"] = self.data_driven
        
        if self.setup_steps:
            result["setup"] = [s.to_dict() for s in self.setup_steps]
        
        result["steps"] = [s.to_dict() for s in self.steps]
        
        if self.teardown_steps:
            result["teardown"] = [s.to_dict() for s in self.teardown_steps]
        
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result


@dataclass
class BuilderConfig:
    """Configuration for YAML builder."""
    
    include_screenshots: bool = True
    include_timing: bool = True
    include_accessibility: bool = True
    include_visual_assertions: bool = True
    include_api_assertions: bool = True
    include_state_assertions: bool = True
    default_timeout: int = 30000
    default_retry: int = 1
    selector_strategy: str = "auto"  # auto, data-testid, css, xpath
    generate_variations: bool = True
    max_variations: int = 5
    include_negative_tests: bool = True
    include_boundary_tests: bool = True
    include_comments: bool = True
    yaml_style: str = "block"  # block, flow


class FlowAnalysisProtocol(Protocol):
    """Protocol for flow analysis results."""
    
    @property
    def flow_type(self) -> str: ...
    
    @property
    def steps(self) -> list[dict[str, Any]]: ...
    
    @property
    def entry_point(self) -> str: ...


class FormAnalysisProtocol(Protocol):
    """Protocol for form analysis results."""
    
    @property
    def fields(self) -> list[dict[str, Any]]: ...
    
    @property
    def submit_button(self) -> dict[str, Any] | None: ...
    
    @property
    def validation_rules(self) -> list[dict[str, Any]]: ...


class YAMLBuilder:
    """
    Intelligent YAML test builder.
    
    Constructs valid YAML test specifications from analysis results
    with comprehensive assertions and documentation.
    """
    
    def __init__(self, config: BuilderConfig | None = None) -> None:
        """Initialize builder with configuration."""
        self.config = config or BuilderConfig()
        self._test_counter = 0
        self._variable_counter = 0
    
    async def build_from_flow(
        self,
        flow: FlowAnalysisProtocol,
        assertions: list[Assertion] | None = None,
    ) -> YAMLTestSpec:
        """
        Build test spec from detected user flow.
        
        Args:
            flow: Detected user flow with steps
            assertions: Optional pre-generated assertions
            
        Returns:
            Complete YAML test specification
        """
        logger.info("building_test_from_flow", flow_type=flow.flow_type)
        
        self._test_counter += 1
        
        steps: list[YAMLStep] = []
        
        # Add navigation step if entry point exists
        if flow.entry_point:
            steps.append(YAMLStep(
                step_type=StepType.NAVIGATE,
                description=f"Navigate to {flow.flow_type} page",
                value=flow.entry_point,
                timeout=self.config.default_timeout,
            ))
        
        # Convert flow steps to YAML steps
        for flow_step in flow.steps:
            yaml_step = self._convert_flow_step(flow_step)
            if yaml_step:
                steps.append(yaml_step)
        
        # Add assertions to relevant steps
        if assertions:
            self._distribute_assertions(steps, assertions)
        
        # Generate test name
        test_name = self._generate_test_name(flow.flow_type)
        
        return YAMLTestSpec(
            name=test_name,
            description=f"Test {flow.flow_type} user flow",
            steps=steps,
            tags=[flow.flow_type, "automated", "flow-test"],
            priority=self._determine_priority(flow.flow_type),
            timeout=self.config.default_timeout * len(steps),
            retries=self.config.default_retry,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "generator": "autoqa-yaml-builder",
                "flow_type": flow.flow_type,
            },
        )
    
    async def build_from_form(
        self,
        form: FormAnalysisProtocol,
        assertions: list[Assertion] | None = None,
    ) -> list[YAMLTestSpec]:
        """
        Build test specs from form analysis.
        
        Generates multiple test cases including:
        - Happy path (valid data)
        - Validation tests (invalid data)
        - Boundary tests
        - Required field tests
        
        Args:
            form: Form analysis result
            assertions: Optional pre-generated assertions
            
        Returns:
            List of test specifications
        """
        logger.info("building_tests_from_form", field_count=len(form.fields))
        
        tests: list[YAMLTestSpec] = []
        
        # Happy path test
        happy_path = await self._build_happy_path_test(form, assertions)
        tests.append(happy_path)
        
        # Validation tests
        if self.config.include_negative_tests:
            validation_tests = await self._build_validation_tests(form)
            tests.extend(validation_tests)
        
        # Boundary tests
        if self.config.include_boundary_tests:
            boundary_tests = await self._build_boundary_tests(form)
            tests.extend(boundary_tests)
        
        return tests
    
    async def build_from_page(
        self,
        url: str,
        elements: list[dict[str, Any]],
        assertions: list[Assertion],
    ) -> YAMLTestSpec:
        """
        Build test spec from page analysis.
        
        Args:
            url: Page URL
            elements: Analyzed interactive elements
            assertions: Generated assertions
            
        Returns:
            Page test specification
        """
        logger.info("building_test_from_page", url=url)
        
        self._test_counter += 1
        
        steps: list[YAMLStep] = []
        
        # Navigation step
        steps.append(YAMLStep(
            step_type=StepType.NAVIGATE,
            description=f"Navigate to page",
            value=url,
            timeout=self.config.default_timeout,
            assertions=self._filter_assertions(
                assertions, 
                [AssertionType.URL_CONTAINS, AssertionType.PAGE_TITLE],
            ),
        ))
        
        # Wait for page load
        steps.append(YAMLStep(
            step_type=StepType.WAIT_FOR_NETWORK_IDLE,
            description="Wait for page to fully load",
            timeout=self.config.default_timeout,
        ))
        
        # Add visibility assertions step
        visibility_assertions = self._filter_assertions(
            assertions,
            [AssertionType.VISIBLE, AssertionType.EXISTS],
        )
        if visibility_assertions:
            steps.append(YAMLStep(
                step_type=StepType.ASSERT,
                description="Verify critical elements are visible",
                assertions=visibility_assertions[:10],  # Limit to avoid bloat
            ))
        
        # Add accessibility assertions if enabled
        if self.config.include_accessibility:
            a11y_assertions = self._filter_assertions(
                assertions,
                [
                    AssertionType.ACCESSIBLE_NAME,
                    AssertionType.ARIA_ROLE,
                    AssertionType.COLOR_CONTRAST,
                    AssertionType.KEYBOARD_FOCUSABLE,
                ],
            )
            if a11y_assertions:
                steps.append(YAMLStep(
                    step_type=StepType.ASSERT,
                    description="Verify accessibility requirements",
                    assertions=a11y_assertions[:10],
                ))
        
        # Take screenshot if enabled
        if self.config.include_screenshots:
            steps.append(YAMLStep(
                step_type=StepType.SCREENSHOT,
                description="Capture page state",
                value="page_loaded.png",
            ))
        
        # Test interactive elements
        interactive_steps = self._create_interactive_tests(elements)
        steps.extend(interactive_steps)
        
        # Extract page identifier from URL
        page_id = self._extract_page_identifier(url)
        
        return YAMLTestSpec(
            name=f"test_{page_id}_page_verification",
            description=f"Comprehensive page verification for {url}",
            steps=steps,
            tags=["page-test", "automated", page_id],
            priority="high",
            timeout=self.config.default_timeout * len(steps),
            retries=self.config.default_retry,
            viewport={"width": 1920, "height": 1080},
            metadata={
                "generated_at": datetime.now().isoformat(),
                "generator": "autoqa-yaml-builder",
                "url": url,
                "element_count": len(elements),
            },
        )
    
    async def build_api_test(
        self,
        endpoint: dict[str, Any],
        assertions: list[Assertion] | None = None,
    ) -> YAMLTestSpec:
        """
        Build test spec for API endpoint verification.
        
        Args:
            endpoint: API endpoint details
            assertions: Optional assertions
            
        Returns:
            API test specification
        """
        logger.info("building_api_test", endpoint=endpoint.get("url", "unknown"))
        
        self._test_counter += 1
        
        steps: list[YAMLStep] = []
        
        # Navigate to page that triggers API
        if endpoint.get("trigger_url"):
            steps.append(YAMLStep(
                step_type=StepType.NAVIGATE,
                description="Navigate to page triggering API",
                value=endpoint["trigger_url"],
                timeout=self.config.default_timeout,
            ))
        
        # Execute action that triggers API if available
        if endpoint.get("trigger_action"):
            action = endpoint["trigger_action"]
            steps.append(YAMLStep(
                step_type=StepType(action.get("type", "click")),
                description=f"Trigger API call via {action.get('type', 'click')}",
                selector=action.get("selector"),
                value=action.get("value"),
            ))
        
        # Wait for network response
        steps.append(YAMLStep(
            step_type=StepType.WAIT_FOR_NETWORK_IDLE,
            description="Wait for API response",
            timeout=self.config.default_timeout,
        ))
        
        # Add API-specific assertions
        api_assertions = assertions or []
        response_assertions = self._filter_assertions(
            api_assertions,
            [
                AssertionType.RESPONSE_STATUS,
                AssertionType.RESPONSE_BODY_CONTAINS,
                AssertionType.RESPONSE_HEADER,
                AssertionType.RESPONSE_TIME,
            ],
        )
        
        if response_assertions:
            steps.append(YAMLStep(
                step_type=StepType.ASSERT,
                description="Verify API response",
                assertions=response_assertions,
            ))
        
        endpoint_id = self._sanitize_name(
            endpoint.get("url", f"api_{self._test_counter}")
        )
        
        return YAMLTestSpec(
            name=f"test_api_{endpoint_id}",
            description=f"API verification for {endpoint.get('url', 'endpoint')}",
            steps=steps,
            tags=["api-test", "automated", endpoint.get("method", "GET")],
            priority="high",
            timeout=self.config.default_timeout * 3,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "generator": "autoqa-yaml-builder",
                "endpoint": endpoint.get("url"),
                "method": endpoint.get("method"),
            },
        )
    
    def generate_yaml(
        self,
        specs: list[YAMLTestSpec],
        include_header: bool = True,
    ) -> str:
        """
        Generate YAML string from test specifications.
        
        Args:
            specs: List of test specifications
            include_header: Whether to include header comment
            
        Returns:
            YAML string
        """
        logger.info("generating_yaml", test_count=len(specs))
        
        output_parts: list[str] = []
        
        if include_header:
            header = self._generate_header(len(specs))
            output_parts.append(header)
        
        test_dicts = [spec.to_dict() for spec in specs]
        
        yaml_content = yaml.dump(
            {"tests": test_dicts},
            default_flow_style=self.config.yaml_style == "flow",
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )
        
        output_parts.append(yaml_content)
        
        return "\n".join(output_parts)
    
    def write_yaml(
        self,
        specs: list[YAMLTestSpec],
        output_path: Path,
        include_header: bool = True,
    ) -> Path:
        """
        Write YAML test specifications to file.
        
        Args:
            specs: List of test specifications
            output_path: Output file path
            include_header: Whether to include header comment
            
        Returns:
            Path to written file
        """
        yaml_content = self.generate_yaml(specs, include_header)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(yaml_content, encoding="utf-8")
        
        logger.info("yaml_written", path=str(output_path), size=len(yaml_content))
        
        return output_path
    
    def _convert_flow_step(
        self,
        flow_step: dict[str, Any],
    ) -> YAMLStep | None:
        """Convert flow step to YAML step."""
        action = flow_step.get("action", "").lower()
        
        step_type_map: dict[str, StepType] = {
            "click": StepType.CLICK,
            "type": StepType.TYPE,
            "input": StepType.TYPE,
            "fill": StepType.TYPE,
            "select": StepType.SELECT,
            "hover": StepType.HOVER,
            "scroll": StepType.SCROLL,
            "wait": StepType.WAIT,
            "navigate": StepType.NAVIGATE,
            "submit": StepType.CLICK,
            "upload": StepType.UPLOAD,
            "press": StepType.PRESS_KEY,
            "focus": StepType.FOCUS,
        }
        
        step_type = step_type_map.get(action)
        if not step_type:
            logger.warning("unknown_flow_action", action=action)
            return None
        
        return YAMLStep(
            step_type=step_type,
            description=flow_step.get("description", f"Perform {action}"),
            selector=flow_step.get("selector"),
            value=flow_step.get("value"),
            timeout=flow_step.get("timeout", self.config.default_timeout),
            screenshot=self.config.include_screenshots,
        )
    
    def _distribute_assertions(
        self,
        steps: list[YAMLStep],
        assertions: list[Assertion],
    ) -> None:
        """Distribute assertions to relevant steps."""
        # Group assertions by selector
        selector_assertions: dict[str, list[Assertion]] = {}
        general_assertions: list[Assertion] = []
        
        for assertion in assertions:
            if assertion.selector:
                selector_assertions.setdefault(assertion.selector, []).append(assertion)
            else:
                general_assertions.append(assertion)
        
        # Assign assertions to steps with matching selectors
        for step in steps:
            if step.selector and step.selector in selector_assertions:
                step.assertions.extend(selector_assertions[step.selector])
        
        # Add general assertions to first navigation step
        for step in steps:
            if step.step_type == StepType.NAVIGATE:
                step.assertions.extend(general_assertions[:5])
                break
    
    def _filter_assertions(
        self,
        assertions: list[Assertion],
        types: list[AssertionType],
    ) -> list[Assertion]:
        """Filter assertions by type."""
        return [a for a in assertions if a.assertion_type in types]
    
    def _generate_test_name(self, flow_type: str) -> str:
        """Generate unique test name."""
        sanitized = self._sanitize_name(flow_type)
        return f"test_{sanitized}_flow_{self._test_counter}"
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize string for use in test name."""
        # Remove protocol and special characters
        sanitized = re.sub(r"https?://", "", name)
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", sanitized)
        sanitized = re.sub(r"_+", "_", sanitized)
        return sanitized.strip("_").lower()[:50]
    
    def _determine_priority(self, flow_type: str) -> str:
        """Determine test priority based on flow type."""
        high_priority = {"login", "checkout", "payment", "registration", "authentication"}
        medium_priority = {"search", "profile", "settings", "navigation"}
        
        flow_lower = flow_type.lower()
        
        if any(hp in flow_lower for hp in high_priority):
            return "critical"
        elif any(mp in flow_lower for mp in medium_priority):
            return "high"
        return "medium"
    
    def _extract_page_identifier(self, url: str) -> str:
        """Extract identifier from URL for naming."""
        # Remove protocol
        clean = re.sub(r"https?://", "", url)
        # Remove query string
        clean = clean.split("?")[0]
        # Get path
        parts = clean.split("/")
        
        if len(parts) > 1 and parts[-1]:
            return self._sanitize_name(parts[-1])
        elif len(parts) > 1 and parts[-2]:
            return self._sanitize_name(parts[-2])
        else:
            return self._sanitize_name(parts[0])
    
    def _create_interactive_tests(
        self,
        elements: list[dict[str, Any]],
    ) -> list[YAMLStep]:
        """Create test steps for interactive elements."""
        steps: list[YAMLStep] = []
        
        for elem in elements[:10]:  # Limit to avoid excessive tests
            elem_type = elem.get("type", "").lower()
            selector = elem.get("selector")
            
            if not selector:
                continue
            
            if elem_type in ("button", "link", "a"):
                steps.append(YAMLStep(
                    step_type=StepType.HOVER,
                    description=f"Hover over {elem.get('text', 'element')[:30]}",
                    selector=selector,
                    assertions=[
                        Assertion(
                            assertion_type=AssertionType.VISIBLE,
                            selector=selector,
                            message=f"Element should be visible: {selector}",
                        ),
                    ],
                ))
            elif elem_type in ("input", "textarea"):
                steps.append(YAMLStep(
                    step_type=StepType.FOCUS,
                    description=f"Focus on input {elem.get('name', 'field')[:30]}",
                    selector=selector,
                    assertions=[
                        Assertion(
                            assertion_type=AssertionType.FOCUSED,
                            selector=selector,
                            message=f"Input should be focusable: {selector}",
                        ),
                    ],
                ))
        
        return steps
    
    async def _build_happy_path_test(
        self,
        form: FormAnalysisProtocol,
        assertions: list[Assertion] | None = None,
    ) -> YAMLTestSpec:
        """Build happy path test for form."""
        self._test_counter += 1
        
        steps: list[YAMLStep] = []
        
        # Fill each field with valid data
        for field_info in form.fields:
            selector = field_info.get("selector")
            if not selector:
                continue
            
            field_type = field_info.get("type", "text")
            test_value = self._generate_valid_value(field_info)
            
            step = YAMLStep(
                step_type=StepType.TYPE if field_type != "select" else StepType.SELECT,
                description=f"Fill {field_info.get('name', 'field')} with valid data",
                selector=selector,
                value=test_value,
                assertions=[
                    Assertion(
                        assertion_type=AssertionType.VALUE,
                        selector=selector,
                        expected_value=test_value,
                    ),
                ],
            )
            steps.append(step)
        
        # Submit form
        if form.submit_button:
            steps.append(YAMLStep(
                step_type=StepType.CLICK,
                description="Submit form",
                selector=form.submit_button.get("selector"),
                screenshot=True,
            ))
        
        # Add success assertions
        steps.append(YAMLStep(
            step_type=StepType.WAIT_FOR_NAVIGATION,
            description="Wait for form submission",
            timeout=self.config.default_timeout,
        ))
        
        return YAMLTestSpec(
            name=f"test_form_happy_path_{self._test_counter}",
            description="Form submission with valid data",
            steps=steps,
            tags=["form-test", "happy-path", "automated"],
            priority="high",
            timeout=self.config.default_timeout * len(steps),
            retries=self.config.default_retry,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "generator": "autoqa-yaml-builder",
                "test_type": "happy_path",
            },
        )
    
    async def _build_validation_tests(
        self,
        form: FormAnalysisProtocol,
    ) -> list[YAMLTestSpec]:
        """Build validation tests for form fields."""
        tests: list[YAMLTestSpec] = []
        
        for rule in form.validation_rules:
            self._test_counter += 1
            
            field_selector = rule.get("field_selector")
            rule_type = rule.get("rule_type", "required")
            
            steps: list[YAMLStep] = []
            
            # Fill field with invalid data based on rule
            invalid_value = self._generate_invalid_value(rule)
            
            steps.append(YAMLStep(
                step_type=StepType.TYPE,
                description=f"Enter invalid data for {rule_type} validation",
                selector=field_selector,
                value=invalid_value,
            ))
            
            # Try to submit
            if form.submit_button:
                steps.append(YAMLStep(
                    step_type=StepType.CLICK,
                    description="Attempt form submission",
                    selector=form.submit_button.get("selector"),
                ))
            
            # Assert validation error appears
            steps.append(YAMLStep(
                step_type=StepType.ASSERT,
                description="Verify validation error",
                assertions=[
                    Assertion(
                        assertion_type=AssertionType.HAS_CLASS,
                        selector=field_selector,
                        expected_value="error|invalid|is-invalid",
                        comparison="regex",
                        message=f"Field should show validation error for {rule_type}",
                    ),
                ],
            ))
            
            tests.append(YAMLTestSpec(
                name=f"test_form_validation_{rule_type}_{self._test_counter}",
                description=f"Test {rule_type} validation",
                steps=steps,
                tags=["form-test", "validation", "negative-test"],
                priority="medium",
                timeout=self.config.default_timeout * len(steps),
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "generator": "autoqa-yaml-builder",
                    "test_type": "validation",
                    "rule_type": rule_type,
                },
            ))
        
        return tests[:self.config.max_variations]  # Limit count
    
    async def _build_boundary_tests(
        self,
        form: FormAnalysisProtocol,
    ) -> list[YAMLTestSpec]:
        """Build boundary tests for form fields."""
        tests: list[YAMLTestSpec] = []
        
        for field_info in form.fields:
            max_length = field_info.get("max_length")
            min_length = field_info.get("min_length")
            
            if max_length or min_length:
                self._test_counter += 1
                
                steps: list[YAMLStep] = []
                
                # Test max boundary
                if max_length:
                    boundary_value = "x" * (max_length + 1)
                    steps.append(YAMLStep(
                        step_type=StepType.TYPE,
                        description=f"Enter value exceeding max length ({max_length})",
                        selector=field_info.get("selector"),
                        value=boundary_value,
                    ))
                    
                    steps.append(YAMLStep(
                        step_type=StepType.ASSERT,
                        description="Verify max length enforcement",
                        assertions=[
                            Assertion(
                                assertion_type=AssertionType.VALUE,
                                selector=field_info.get("selector"),
                                comparison="length_lte",
                                expected_value=str(max_length),
                            ),
                        ],
                    ))
                
                # Test min boundary
                if min_length and min_length > 1:
                    steps.append(YAMLStep(
                        step_type=StepType.CLEAR,
                        description="Clear field",
                        selector=field_info.get("selector"),
                    ))
                    
                    steps.append(YAMLStep(
                        step_type=StepType.TYPE,
                        description=f"Enter value below min length ({min_length})",
                        selector=field_info.get("selector"),
                        value="x" * (min_length - 1),
                    ))
                
                tests.append(YAMLTestSpec(
                    name=f"test_form_boundary_{self._test_counter}",
                    description=f"Boundary test for {field_info.get('name', 'field')}",
                    steps=steps,
                    tags=["form-test", "boundary-test", "automated"],
                    priority="low",
                    timeout=self.config.default_timeout * len(steps),
                    metadata={
                        "generated_at": datetime.now().isoformat(),
                        "generator": "autoqa-yaml-builder",
                        "test_type": "boundary",
                        "field": field_info.get("name"),
                    },
                ))
        
        return tests[:self.config.max_variations]
    
    def _generate_valid_value(self, field_info: dict[str, Any]) -> str:
        """Generate valid test value for field."""
        field_type = field_info.get("type", "text").lower()
        field_name = field_info.get("name", "").lower()
        
        # Email field
        if field_type == "email" or "email" in field_name:
            return "test@example.com"
        
        # Password field
        if field_type == "password" or "password" in field_name:
            return "TestPassword123!"
        
        # Phone field
        if field_type == "tel" or "phone" in field_name:
            return "+1234567890"
        
        # URL field
        if field_type == "url" or "url" in field_name:
            return "https://example.com"
        
        # Number field
        if field_type == "number":
            min_val = field_info.get("min", 0)
            max_val = field_info.get("max", 100)
            return str((min_val + max_val) // 2)
        
        # Date field
        if field_type == "date":
            return "2024-01-15"
        
        # Default text
        max_len = field_info.get("max_length", 50)
        return f"Test Value"[:max_len]
    
    def _generate_invalid_value(self, rule: dict[str, Any]) -> str:
        """Generate invalid value based on validation rule."""
        rule_type = rule.get("rule_type", "")
        
        if rule_type == "required":
            return ""
        elif rule_type == "email":
            return "invalid-email"
        elif rule_type == "min_length":
            min_len = rule.get("min_length", 5)
            return "x" * max(0, min_len - 1)
        elif rule_type == "max_length":
            max_len = rule.get("max_length", 10)
            return "x" * (max_len + 10)
        elif rule_type == "pattern":
            return "!!!invalid!!!"
        elif rule_type == "number":
            return "not-a-number"
        elif rule_type == "url":
            return "not-a-url"
        
        return "invalid_value"
    
    def _generate_header(self, test_count: int) -> str:
        """Generate YAML file header comment."""
        return f"""# =============================================================================
# AutoQA Generated Test Suite
# =============================================================================
# Generated: {datetime.now().isoformat()}
# Total Tests: {test_count}
# Generator: autoqa-yaml-builder v1.0.0
#
# IMPORTANT: These tests were automatically generated. Review before execution.
# =============================================================================

"""
