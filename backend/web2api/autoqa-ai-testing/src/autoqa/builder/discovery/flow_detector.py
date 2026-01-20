"""
User flow detection for intelligent test generation.

Detects common user flows:
- Login and authentication flows
- Registration flows
- Checkout and payment flows
- Search flows
- Multi-step wizard flows
- CRUD operations
- Navigation patterns
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from autoqa.builder.analyzer.page_analyzer import (
        PageAnalysisResult,
        InteractiveElement,
        ComponentInfo,
    )
    from autoqa.builder.analyzer.element_classifier import (
        ClassificationResult,
        ElementPurpose,
    )
    from autoqa.builder.crawler.state_manager import StateGraph, StateTransition

logger = structlog.get_logger(__name__)


@dataclass
class FlowConfig:
    """Configuration for flow detector."""

    detect_login: bool = True
    """Whether to detect login flows."""

    detect_registration: bool = True
    """Whether to detect registration flows."""

    detect_checkout: bool = True
    """Whether to detect checkout flows."""

    detect_search: bool = True
    """Whether to detect search flows."""

    detect_crud: bool = True
    """Whether to detect CRUD flows."""

    detect_wizard: bool = True
    """Whether to detect multi-step wizard flows."""

    min_confidence: float = 0.6
    """Minimum confidence threshold for flow detection."""

    max_steps: int = 20
    """Maximum number of steps in a detected flow."""


class FlowType(StrEnum):
    """Types of user flows."""

    LOGIN = auto()
    REGISTRATION = auto()
    CHECKOUT = auto()
    SEARCH = auto()
    WIZARD = auto()
    CRUD_CREATE = auto()
    CRUD_READ = auto()
    CRUD_UPDATE = auto()
    CRUD_DELETE = auto()
    NAVIGATION = auto()
    FILTER = auto()
    SORT = auto()
    PAGINATION = auto()
    FILE_UPLOAD = auto()
    FORM_SUBMISSION = auto()
    MODAL_INTERACTION = auto()
    TAB_NAVIGATION = auto()
    ACCORDION = auto()
    CUSTOM = auto()


class StepType(StrEnum):
    """Types of flow steps."""

    NAVIGATE = auto()
    CLICK = auto()
    INPUT = auto()
    SELECT = auto()
    UPLOAD = auto()
    WAIT = auto()
    ASSERT = auto()
    SCREENSHOT = auto()


@dataclass
class FlowStep:
    """A single step in a user flow."""

    step_type: StepType
    selector: str
    action_value: str | None = None
    description: str = ""
    is_required: bool = True
    timeout_ms: int = 5000
    wait_after_ms: int = 0
    assertion: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserFlow:
    """A detected user flow."""

    flow_id: str
    flow_type: FlowType
    name: str
    description: str
    steps: list[FlowStep]
    entry_url: str | None = None
    exit_url: str | None = None
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    confidence: float = 1.0
    priority: int = 1
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class FlowDetector:
    """
    Detects user flows from page analysis and state transitions.

    Uses pattern matching and heuristics to identify:
    - Authentication flows (login, register, logout)
    - E-commerce flows (search, cart, checkout)
    - CRUD operations
    - Multi-step wizards
    - Navigation patterns
    """

    # Flow detection patterns
    LOGIN_INDICATORS = frozenset({
        "login", "signin", "sign-in", "sign_in", "log-in", "log_in",
        "authenticate", "auth", "sso",
    })

    REGISTRATION_INDICATORS = frozenset({
        "register", "signup", "sign-up", "sign_up", "create-account",
        "create_account", "join", "enroll",
    })

    CHECKOUT_INDICATORS = frozenset({
        "checkout", "check-out", "payment", "purchase", "order",
        "cart", "basket", "buy",
    })

    SEARCH_INDICATORS = frozenset({
        "search", "find", "query", "lookup", "browse",
    })

    WIZARD_INDICATORS = frozenset({
        "step", "wizard", "progress", "stage", "phase",
        "next", "previous", "continue", "back",
    })

    def __init__(self, config: FlowConfig | None = None) -> None:
        self.config = config or FlowConfig()
        self._log = logger.bind(component="flow_detector")
        self._flow_counter = 0

    def detect_flows(
        self,
        page_analyses: list[PageAnalysisResult],
        classifications: list[ClassificationResult] | None = None,
        state_graph: StateGraph | None = None,
    ) -> list[UserFlow]:
        """
        Detect user flows from page analyses.

        Args:
            page_analyses: List of page analysis results
            classifications: Optional element classifications
            state_graph: Optional state transition graph

        Returns:
            List of detected user flows
        """
        self._log.info(
            "Detecting user flows",
            pages=len(page_analyses),
            has_classifications=classifications is not None,
            has_state_graph=state_graph is not None,
        )

        flows: list[UserFlow] = []

        # Detect flows from each page
        for analysis in page_analyses:
            page_flows = self._detect_page_flows(analysis, classifications)
            flows.extend(page_flows)

        # Detect cross-page flows from state graph
        if state_graph:
            transition_flows = self._detect_transition_flows(state_graph)
            flows.extend(transition_flows)

        # Detect multi-step wizards
        wizard_flows = self._detect_wizard_flows(page_analyses)
        flows.extend(wizard_flows)

        # Deduplicate and merge similar flows
        flows = self._merge_similar_flows(flows)

        # Sort by priority and confidence
        flows.sort(key=lambda f: (f.priority, -f.confidence))

        self._log.info("Flow detection complete", flows_found=len(flows))

        return flows

    def _detect_page_flows(
        self,
        analysis: PageAnalysisResult,
        classifications: list[ClassificationResult] | None = None,
    ) -> list[UserFlow]:
        """Detect flows from a single page analysis."""
        flows: list[UserFlow] = []

        url = analysis.url.lower()
        title = analysis.title.lower()

        # Check for login flow
        login_flow = self._detect_login_flow(analysis, url, title)
        if login_flow:
            flows.append(login_flow)

        # Check for registration flow
        registration_flow = self._detect_registration_flow(analysis, url, title)
        if registration_flow:
            flows.append(registration_flow)

        # Check for search flow
        search_flow = self._detect_search_flow(analysis)
        if search_flow:
            flows.append(search_flow)

        # Check for checkout flow
        checkout_flow = self._detect_checkout_flow(analysis, url, title)
        if checkout_flow:
            flows.append(checkout_flow)

        # Detect form submission flows
        form_flows = self._detect_form_flows(analysis)
        flows.extend(form_flows)

        # Detect navigation flows
        nav_flows = self._detect_navigation_flows(analysis)
        flows.extend(nav_flows)

        # Detect CRUD flows
        crud_flows = self._detect_crud_flows(analysis)
        flows.extend(crud_flows)

        return flows

    def _detect_login_flow(
        self,
        analysis: PageAnalysisResult,
        url: str,
        title: str,
    ) -> UserFlow | None:
        """Detect login flow on page."""
        # Check URL/title indicators
        has_url_indicator = any(ind in url for ind in self.LOGIN_INDICATORS)
        has_title_indicator = any(ind in title for ind in self.LOGIN_INDICATORS)

        # Find login form components
        password_field = None
        username_field = None
        submit_button = None

        for element in analysis.interactive_elements:
            el_type = element.element_type.lower()
            el_name = (element.name or "").lower()
            el_id = (element.element_id or "").lower()
            el_placeholder = (element.placeholder or "").lower()
            el_text = (element.text_content or "").lower()

            # Find password field
            if el_type == "password":
                password_field = element

            # Find username/email field
            elif el_type in ("text", "email"):
                if any(ind in f"{el_name} {el_id} {el_placeholder}" for ind in
                       ["user", "email", "login", "account"]):
                    username_field = element

            # Find submit button
            elif element.tag_name == "button" or el_type == "submit":
                if any(ind in el_text for ind in self.LOGIN_INDICATORS):
                    submit_button = element

        # Require at least password field
        if not password_field:
            return None

        # Build flow steps
        steps: list[FlowStep] = []

        if username_field:
            steps.append(FlowStep(
                step_type=StepType.INPUT,
                selector=username_field.semantic_selector or username_field.selector,
                action_value="${username}",
                description="Enter username or email",
            ))

        steps.append(FlowStep(
            step_type=StepType.INPUT,
            selector=password_field.semantic_selector or password_field.selector,
            action_value="${password}",
            description="Enter password",
        ))

        if submit_button:
            steps.append(FlowStep(
                step_type=StepType.CLICK,
                selector=submit_button.semantic_selector or submit_button.selector,
                description="Click login button",
                wait_after_ms=2000,
            ))
        else:
            steps.append(FlowStep(
                step_type=StepType.INPUT,
                selector=password_field.selector,
                action_value="Enter",
                description="Submit login form",
                wait_after_ms=2000,
            ))

        # Add assertion for successful login
        steps.append(FlowStep(
            step_type=StepType.ASSERT,
            selector="body",
            description="Verify login succeeded",
            assertion={
                "type": "url_changed",
                "message": "Should redirect after login",
            },
        ))

        confidence = 0.9 if (has_url_indicator or has_title_indicator) else 0.7

        return UserFlow(
            flow_id=self._generate_flow_id("login"),
            flow_type=FlowType.LOGIN,
            name="Login Flow",
            description="Authenticate user with username/email and password",
            steps=steps,
            entry_url=analysis.url,
            confidence=confidence,
            priority=1,
            tags=["authentication", "login"],
            preconditions=["User is not authenticated"],
            postconditions=["User is authenticated"],
        )

    def _detect_registration_flow(
        self,
        analysis: PageAnalysisResult,
        url: str,
        title: str,
    ) -> UserFlow | None:
        """Detect registration flow on page."""
        has_indicator = (
            any(ind in url for ind in self.REGISTRATION_INDICATORS) or
            any(ind in title for ind in self.REGISTRATION_INDICATORS)
        )

        # Find registration form elements
        email_field = None
        password_field = None
        confirm_password_field = None
        name_fields: list[InteractiveElement] = []
        submit_button = None

        for element in analysis.interactive_elements:
            el_type = element.element_type.lower()
            el_name = (element.name or "").lower()
            el_id = (element.element_id or "").lower()
            el_text = (element.text_content or "").lower()

            if el_type == "email":
                email_field = element
            elif el_type == "password":
                if "confirm" in el_name or "confirm" in el_id:
                    confirm_password_field = element
                elif not password_field:
                    password_field = element
            elif el_type == "text":
                if any(n in el_name for n in ["name", "first", "last"]):
                    name_fields.append(element)
            elif element.tag_name == "button" or el_type == "submit":
                if any(ind in el_text for ind in self.REGISTRATION_INDICATORS):
                    submit_button = element

        # Require email and password
        if not (email_field and password_field):
            return None

        # Build steps
        steps: list[FlowStep] = []

        for name_field in name_fields:
            steps.append(FlowStep(
                step_type=StepType.INPUT,
                selector=name_field.semantic_selector or name_field.selector,
                action_value="${name}",
                description=f"Enter name in {name_field.name or 'name field'}",
            ))

        steps.append(FlowStep(
            step_type=StepType.INPUT,
            selector=email_field.semantic_selector or email_field.selector,
            action_value="${email}",
            description="Enter email address",
        ))

        steps.append(FlowStep(
            step_type=StepType.INPUT,
            selector=password_field.semantic_selector or password_field.selector,
            action_value="${password}",
            description="Enter password",
        ))

        if confirm_password_field:
            steps.append(FlowStep(
                step_type=StepType.INPUT,
                selector=confirm_password_field.semantic_selector or confirm_password_field.selector,
                action_value="${password}",
                description="Confirm password",
            ))

        if submit_button:
            steps.append(FlowStep(
                step_type=StepType.CLICK,
                selector=submit_button.semantic_selector or submit_button.selector,
                description="Submit registration",
                wait_after_ms=2000,
            ))

        confidence = 0.85 if has_indicator else 0.65

        return UserFlow(
            flow_id=self._generate_flow_id("registration"),
            flow_type=FlowType.REGISTRATION,
            name="Registration Flow",
            description="Create new user account",
            steps=steps,
            entry_url=analysis.url,
            confidence=confidence,
            priority=2,
            tags=["authentication", "registration", "signup"],
        )

    def _detect_search_flow(self, analysis: PageAnalysisResult) -> UserFlow | None:
        """Detect search flow on page."""
        search_input = None
        search_button = None

        for element in analysis.interactive_elements:
            el_type = element.element_type.lower()
            el_name = (element.name or "").lower()
            el_id = (element.element_id or "").lower()
            el_text = (element.text_content or "").lower()
            el_aria = (element.aria_label or "").lower()

            if el_type == "search" or any(s in f"{el_name} {el_id} {el_aria}" for s in self.SEARCH_INDICATORS):
                search_input = element
            elif (element.tag_name == "button" or el_type == "submit") and "search" in el_text:
                search_button = element

        if not search_input:
            return None

        steps: list[FlowStep] = [
            FlowStep(
                step_type=StepType.INPUT,
                selector=search_input.semantic_selector or search_input.selector,
                action_value="${search_query}",
                description="Enter search query",
            ),
        ]

        if search_button:
            steps.append(FlowStep(
                step_type=StepType.CLICK,
                selector=search_button.semantic_selector or search_button.selector,
                description="Submit search",
                wait_after_ms=1000,
            ))
        else:
            steps.append(FlowStep(
                step_type=StepType.INPUT,
                selector=search_input.selector,
                action_value="Enter",
                description="Submit search",
                wait_after_ms=1000,
            ))

        steps.append(FlowStep(
            step_type=StepType.ASSERT,
            selector="body",
            description="Verify search results",
            assertion={
                "type": "contains_text",
                "value": "${search_query}",
            },
        ))

        return UserFlow(
            flow_id=self._generate_flow_id("search"),
            flow_type=FlowType.SEARCH,
            name="Search Flow",
            description="Search for content on the page",
            steps=steps,
            entry_url=analysis.url,
            confidence=0.8,
            priority=3,
            tags=["search", "navigation"],
        )

    def _detect_checkout_flow(
        self,
        analysis: PageAnalysisResult,
        url: str,
        title: str,
    ) -> UserFlow | None:
        """Detect checkout/e-commerce flow."""
        has_indicator = (
            any(ind in url for ind in self.CHECKOUT_INDICATORS) or
            any(ind in title for ind in self.CHECKOUT_INDICATORS)
        )

        if not has_indicator:
            return None

        # Find checkout-related elements
        checkout_button = None
        add_to_cart_button = None

        for element in analysis.interactive_elements:
            el_text = (element.text_content or "").lower()
            el_aria = (element.aria_label or "").lower()

            if "checkout" in el_text or "checkout" in el_aria:
                checkout_button = element
            elif any(c in el_text for c in ["add to cart", "add to bag", "buy"]):
                add_to_cart_button = element

        if not (checkout_button or add_to_cart_button):
            return None

        steps: list[FlowStep] = []

        if add_to_cart_button:
            steps.append(FlowStep(
                step_type=StepType.CLICK,
                selector=add_to_cart_button.semantic_selector or add_to_cart_button.selector,
                description="Add item to cart",
                wait_after_ms=1000,
            ))

        if checkout_button:
            steps.append(FlowStep(
                step_type=StepType.CLICK,
                selector=checkout_button.semantic_selector or checkout_button.selector,
                description="Proceed to checkout",
                wait_after_ms=2000,
            ))

        return UserFlow(
            flow_id=self._generate_flow_id("checkout"),
            flow_type=FlowType.CHECKOUT,
            name="Checkout Flow",
            description="Complete purchase flow",
            steps=steps,
            entry_url=analysis.url,
            confidence=0.75,
            priority=1,
            tags=["ecommerce", "checkout", "purchase"],
        )

    def _detect_form_flows(self, analysis: PageAnalysisResult) -> list[UserFlow]:
        """Detect general form submission flows."""
        flows: list[UserFlow] = []

        for component in analysis.components:
            if component.component_type.value != "form":
                continue

            # Get form elements
            form_elements = [
                el for el in analysis.interactive_elements
                if el.parent_component and component.selector in el.parent_component
            ]

            if not form_elements:
                continue

            steps: list[FlowStep] = []

            for element in form_elements:
                if element.tag_name in ("input", "textarea", "select"):
                    step_type = StepType.SELECT if element.tag_name == "select" else StepType.INPUT
                    steps.append(FlowStep(
                        step_type=step_type,
                        selector=element.semantic_selector or element.selector,
                        action_value="${" + (element.name or "field") + "}",
                        description=f"Fill {element.semantic_selector or element.name or 'field'}",
                        is_required=element.is_required,
                    ))
                elif element.tag_name == "button" or element.element_type == "submit":
                    steps.append(FlowStep(
                        step_type=StepType.CLICK,
                        selector=element.semantic_selector or element.selector,
                        description="Submit form",
                        wait_after_ms=1000,
                    ))

            if steps:
                flows.append(UserFlow(
                    flow_id=self._generate_flow_id("form"),
                    flow_type=FlowType.FORM_SUBMISSION,
                    name=f"Form: {component.attributes.get('name', 'Unknown')}",
                    description="Submit form data",
                    steps=steps,
                    entry_url=analysis.url,
                    confidence=0.7,
                    priority=4,
                    tags=["form"],
                ))

        return flows

    def _detect_navigation_flows(self, analysis: PageAnalysisResult) -> list[UserFlow]:
        """Detect navigation patterns."""
        flows: list[UserFlow] = []

        # Find navigation components
        nav_components = [
            c for c in analysis.components
            if c.component_type.value in ("navigation", "tabs", "breadcrumb", "pagination")
        ]

        for nav in nav_components:
            nav_elements = [
                el for el in analysis.interactive_elements
                if el.href or el.aria_role == "tab"
            ][:5]  # Limit to first 5

            if not nav_elements:
                continue

            steps = [
                FlowStep(
                    step_type=StepType.CLICK,
                    selector=el.semantic_selector or el.selector,
                    description=f"Navigate to {el.text_content or el.href or 'page'}",
                    wait_after_ms=1000,
                )
                for el in nav_elements
            ]

            flows.append(UserFlow(
                flow_id=self._generate_flow_id("nav"),
                flow_type=FlowType.NAVIGATION,
                name=f"Navigation: {nav.component_type.value}",
                description="Navigation through site sections",
                steps=steps,
                entry_url=analysis.url,
                confidence=0.6,
                priority=5,
                tags=["navigation"],
            ))

        return flows

    def _detect_crud_flows(self, analysis: PageAnalysisResult) -> list[UserFlow]:
        """Detect CRUD operation flows."""
        flows: list[UserFlow] = []

        crud_patterns = {
            FlowType.CRUD_CREATE: ["create", "add", "new", "+"],
            FlowType.CRUD_UPDATE: ["edit", "update", "modify", "save"],
            FlowType.CRUD_DELETE: ["delete", "remove", "trash", "x"],
        }

        for flow_type, patterns in crud_patterns.items():
            for element in analysis.interactive_elements:
                el_text = (element.text_content or "").lower()
                el_aria = (element.aria_label or "").lower()

                if any(p in el_text or p in el_aria for p in patterns):
                    steps = [
                        FlowStep(
                            step_type=StepType.CLICK,
                            selector=element.semantic_selector or element.selector,
                            description=f"{flow_type.value.split('_')[1].title()} action",
                            wait_after_ms=1000,
                        ),
                    ]

                    flows.append(UserFlow(
                        flow_id=self._generate_flow_id(flow_type.value),
                        flow_type=flow_type,
                        name=f"CRUD: {flow_type.value.split('_')[1].title()}",
                        description=f"Perform {flow_type.value} operation",
                        steps=steps,
                        entry_url=analysis.url,
                        confidence=0.6,
                        priority=3,
                        tags=["crud", flow_type.value.split("_")[1]],
                    ))
                    break  # Only one per type per page

        return flows

    def _detect_wizard_flows(
        self, page_analyses: list[PageAnalysisResult]
    ) -> list[UserFlow]:
        """Detect multi-step wizard flows across pages."""
        flows: list[UserFlow] = []

        # Look for step indicators across pages
        wizard_pages: list[tuple[PageAnalysisResult, int]] = []

        for analysis in page_analyses:
            url = analysis.url.lower()
            title = analysis.title.lower()

            # Check for step indicators
            step_match = re.search(r"step[_\-\s]*(\d+)", f"{url} {title}")
            if step_match:
                step_num = int(step_match.group(1))
                wizard_pages.append((analysis, step_num))

        if len(wizard_pages) >= 2:
            # Sort by step number
            wizard_pages.sort(key=lambda x: x[1])

            steps: list[FlowStep] = []
            for analysis, step_num in wizard_pages:
                steps.append(FlowStep(
                    step_type=StepType.NAVIGATE,
                    selector=analysis.url,
                    description=f"Wizard step {step_num}",
                ))

                # Add form interactions from each step
                for element in analysis.interactive_elements[:3]:
                    if element.tag_name in ("input", "select"):
                        steps.append(FlowStep(
                            step_type=StepType.INPUT,
                            selector=element.selector,
                            action_value="${step_" + str(step_num) + "_value}",
                            description=f"Fill step {step_num} field",
                        ))

            flows.append(UserFlow(
                flow_id=self._generate_flow_id("wizard"),
                flow_type=FlowType.WIZARD,
                name="Multi-step Wizard",
                description=f"Complete {len(wizard_pages)}-step wizard flow",
                steps=steps,
                entry_url=wizard_pages[0][0].url,
                exit_url=wizard_pages[-1][0].url,
                confidence=0.8,
                priority=2,
                tags=["wizard", "multi-step"],
            ))

        return flows

    def _detect_transition_flows(self, state_graph: StateGraph) -> list[UserFlow]:
        """Detect flows from state transitions."""
        flows: list[UserFlow] = []

        # Get authentication flow
        auth_transitions = state_graph.get_authenticated_entry_points()
        if auth_transitions:
            steps = [
                FlowStep(
                    step_type=StepType.CLICK,
                    selector=t.trigger_selector or "",
                    description=f"Action: {t.trigger_action}",
                )
                for t in auth_transitions
            ]

            flows.append(UserFlow(
                flow_id=self._generate_flow_id("auth_transition"),
                flow_type=FlowType.LOGIN,
                name="Authentication Transition",
                description="Authentication flow from state graph",
                steps=steps,
                confidence=0.9,
                priority=1,
                tags=["authentication", "state-based"],
            ))

        return flows

    def _merge_similar_flows(self, flows: list[UserFlow]) -> list[UserFlow]:
        """Merge similar flows to avoid duplication."""
        if len(flows) <= 1:
            return flows

        merged: list[UserFlow] = []
        seen_signatures: set[str] = set()

        for flow in flows:
            # Create signature from flow type and step selectors
            step_selectors = "|".join(s.selector for s in flow.steps[:3])
            signature = f"{flow.flow_type}:{step_selectors}"

            if signature not in seen_signatures:
                seen_signatures.add(signature)
                merged.append(flow)

        return merged

    def _generate_flow_id(self, prefix: str) -> str:
        """Generate unique flow ID."""
        self._flow_counter += 1
        return f"{prefix}_{self._flow_counter}"
