"""
Chaos testing agents with distinct personas.

Provides generative testing through simulated user behaviors.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from owl_browser import Browser, BrowserContext

logger = structlog.get_logger(__name__)


class ChaosPersona(StrEnum):
    """Predefined chaos testing personas."""

    ANGRY_USER = "angry_user"
    IMPATIENT_USER = "impatient_user"
    CONFUSED_USER = "confused_user"
    MALICIOUS_USER = "malicious_user"
    ACCESSIBILITY_USER = "accessibility_user"
    SLOW_NETWORK_USER = "slow_network_user"
    MOBILE_USER = "mobile_user"
    POWER_USER = "power_user"
    RANDOM_MONKEY = "random_monkey"


class ChaosActionType(StrEnum):
    """Types of chaos actions."""

    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    NAVIGATE = "navigate"
    REFRESH = "refresh"
    BACK = "back"
    FORWARD = "forward"
    RESIZE = "resize"
    RAPID_CLICK = "rapid_click"
    FORM_SPAM = "form_spam"
    INJECTION = "injection"
    KEYBOARD_SHORTCUT = "keyboard_shortcut"
    TAB_SWITCH = "tab_switch"


@dataclass
class ChaosAction:
    """A single chaos action performed."""

    action_type: ChaosActionType
    target: str | None = None
    value: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    success: bool = True
    error: str | None = None
    duration_ms: int = 0


@dataclass
class ChaosSession:
    """Results of a chaos testing session."""

    persona: ChaosPersona
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int = 0
    actions: list[ChaosAction] = field(default_factory=list)
    errors_found: list[str] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    network_errors: list[str] = field(default_factory=list)
    crashed: bool = False
    screenshots: list[str] = field(default_factory=list)


class ChaosAgent:
    """Base chaos testing agent."""

    def __init__(
        self,
        page: BrowserContext,
        persona: ChaosPersona,
        max_actions: int = 100,
        action_delay_ms: int = 500,
    ) -> None:
        self._page = page
        self._persona = persona
        self._max_actions = max_actions
        self._action_delay = action_delay_ms / 1000
        self._log = logger.bind(component="chaos_agent", persona=persona)
        self._session: ChaosSession | None = None

    def run(self, duration_seconds: int = 60) -> ChaosSession:
        """
        Run chaos testing session.

        Args:
            duration_seconds: Maximum duration of chaos session

        Returns:
            ChaosSession with results
        """
        self._session = ChaosSession(
            persona=self._persona,
            started_at=datetime.now(UTC),
        )

        end_time = time.monotonic() + duration_seconds
        action_count = 0

        self._log.info(
            "Starting chaos session",
            max_actions=self._max_actions,
            duration_seconds=duration_seconds,
        )

        try:
            while time.monotonic() < end_time and action_count < self._max_actions:
                action = self._generate_action()
                result = self._execute_action(action)
                self._session.actions.append(result)

                if not result.success:
                    self._session.errors_found.append(
                        f"{result.action_type}: {result.error}"
                    )

                self._check_for_errors()

                action_count += 1
                time.sleep(self._action_delay)

        except Exception as e:
            self._session.crashed = True
            self._session.errors_found.append(f"Session crashed: {e}")
            self._log.error("Chaos session crashed", error=str(e))

        self._session.finished_at = datetime.now(UTC)
        self._session.duration_ms = int(
            (self._session.finished_at - self._session.started_at).total_seconds() * 1000
        )

        self._log.info(
            "Chaos session completed",
            actions=len(self._session.actions),
            errors=len(self._session.errors_found),
            crashed=self._session.crashed,
        )

        return self._session

    def _generate_action(self) -> ChaosAction:
        """Generate next chaos action based on persona."""
        raise NotImplementedError

    def _execute_action(self, action: ChaosAction) -> ChaosAction:
        """Execute a chaos action."""
        start_time = time.monotonic()

        try:
            match action.action_type:
                case ChaosActionType.CLICK:
                    if action.target:
                        self._page.click(action.target)

                case ChaosActionType.TYPE:
                    if action.target and action.value:
                        self._page.type(action.target, action.value)

                case ChaosActionType.SCROLL:
                    scroll_amount = random.randint(-500, 500)
                    self._page.scroll_by(0, scroll_amount)

                case ChaosActionType.NAVIGATE:
                    if action.value:
                        self._page.goto(action.value)

                case ChaosActionType.REFRESH:
                    self._page.reload()

                case ChaosActionType.BACK:
                    if self._page.can_go_back():
                        self._page.go_back()

                case ChaosActionType.FORWARD:
                    if self._page.can_go_forward():
                        self._page.go_forward()

                case ChaosActionType.RESIZE:
                    width = random.randint(320, 1920)
                    height = random.randint(480, 1080)
                    self._page.set_viewport(width=width, height=height)

                case ChaosActionType.RAPID_CLICK:
                    if action.target:
                        for _ in range(random.randint(3, 10)):
                            try:
                                self._page.click(action.target)
                            except Exception:
                                break
                            time.sleep(0.05)

                case ChaosActionType.FORM_SPAM:
                    self._spam_forms()

                case ChaosActionType.INJECTION:
                    if action.target and action.value:
                        self._page.type(action.target, action.value)

                case ChaosActionType.KEYBOARD_SHORTCUT:
                    if action.value:
                        self._page.press_key(action.value)

            action.success = True

        except Exception as e:
            action.success = False
            action.error = str(e)

        action.duration_ms = int((time.monotonic() - start_time) * 1000)
        return action

    def _spam_forms(self) -> None:
        """Spam all visible form inputs with random data."""
        inputs = [
            "input[type='text']",
            "input[type='email']",
            "input[type='password']",
            "input[type='number']",
            "textarea",
        ]

        for selector in inputs:
            try:
                if self._page.is_visible(selector):
                    spam_value = self._generate_spam_value()
                    self._page.type(selector, spam_value)
            except Exception:
                pass

    def _generate_spam_value(self) -> str:
        """Generate random spam value."""
        options = [
            "a" * 1000,
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "\x00\x00\x00",
            "https://evil.com/" + "a" * 100,
            "-1",
            "0",
            "999999999999",
            "null",
            "undefined",
            "NaN",
            "../../../etc/passwd",
            "${7*7}",
            "{{7*7}}",
        ]
        return random.choice(options)

    def _check_for_errors(self) -> None:
        """Check page for JavaScript and network errors."""
        if self._session is None:
            return

        try:
            console_logs = self._page.get_console_log()
            for log in console_logs:
                if log.get("level") == "error":
                    error_msg = log.get("message", "Unknown error")
                    if error_msg not in self._session.console_errors:
                        self._session.console_errors.append(error_msg)

            network_log = self._page.get_network_log()
            for entry in network_log:
                status = entry.get("status", 0)
                if status >= 400:
                    error_msg = f"{status}: {entry.get('url', 'Unknown URL')}"
                    if error_msg not in self._session.network_errors:
                        self._session.network_errors.append(error_msg)

        except Exception as e:
            self._log.debug("Error checking page errors", error=str(e))

    def _find_clickable_elements(self) -> list[str]:
        """Find clickable elements on page."""
        selectors = [
            "a",
            "button",
            "[role='button']",
            "input[type='submit']",
            "input[type='button']",
            "[onclick]",
            ".btn",
            ".button",
        ]
        return selectors

    def _find_input_elements(self) -> list[str]:
        """Find input elements on page."""
        selectors = [
            "input[type='text']",
            "input[type='email']",
            "input[type='password']",
            "input[type='search']",
            "input[type='number']",
            "textarea",
            "[contenteditable='true']",
        ]
        return selectors


class AngryUserAgent(ChaosAgent):
    """Simulates an angry, aggressive user."""

    def _generate_action(self) -> ChaosAction:
        weights = {
            ChaosActionType.RAPID_CLICK: 0.3,
            ChaosActionType.REFRESH: 0.2,
            ChaosActionType.BACK: 0.15,
            ChaosActionType.FORM_SPAM: 0.15,
            ChaosActionType.SCROLL: 0.1,
            ChaosActionType.KEYBOARD_SHORTCUT: 0.1,
        }

        action_type = random.choices(
            list(weights.keys()),
            weights=list(weights.values()),
        )[0]

        target = None
        value = None

        if action_type in (ChaosActionType.CLICK, ChaosActionType.RAPID_CLICK):
            target = random.choice(self._find_clickable_elements())
        elif action_type == ChaosActionType.KEYBOARD_SHORTCUT:
            value = random.choice(["Escape", "Enter", "F5"])

        return ChaosAction(action_type=action_type, target=target, value=value)


class ImpatientUserAgent(ChaosAgent):
    """Simulates an impatient user who doesn't wait."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._action_delay = 0.1

    def _generate_action(self) -> ChaosAction:
        weights = {
            ChaosActionType.CLICK: 0.35,
            ChaosActionType.REFRESH: 0.25,
            ChaosActionType.BACK: 0.2,
            ChaosActionType.FORWARD: 0.1,
            ChaosActionType.SCROLL: 0.1,
        }

        action_type = random.choices(
            list(weights.keys()),
            weights=list(weights.values()),
        )[0]

        target = None
        if action_type == ChaosActionType.CLICK:
            target = random.choice(self._find_clickable_elements())

        return ChaosAction(action_type=action_type, target=target)


class ConfusedUserAgent(ChaosAgent):
    """Simulates a confused user making random mistakes."""

    def _generate_action(self) -> ChaosAction:
        weights = {
            ChaosActionType.CLICK: 0.25,
            ChaosActionType.TYPE: 0.25,
            ChaosActionType.SCROLL: 0.15,
            ChaosActionType.BACK: 0.15,
            ChaosActionType.NAVIGATE: 0.1,
            ChaosActionType.RESIZE: 0.1,
        }

        action_type = random.choices(
            list(weights.keys()),
            weights=list(weights.values()),
        )[0]

        target = None
        value = None

        if action_type == ChaosActionType.CLICK:
            target = random.choice(self._find_clickable_elements())
        elif action_type == ChaosActionType.TYPE:
            target = random.choice(self._find_input_elements())
            value = random.choice([
                "help",
                "???",
                "how do i",
                "click here",
                "wrong field",
                " ",
            ])

        return ChaosAction(action_type=action_type, target=target, value=value)


class MaliciousUserAgent(ChaosAgent):
    """Simulates a malicious user attempting attacks."""

    def _generate_action(self) -> ChaosAction:
        weights = {
            ChaosActionType.INJECTION: 0.4,
            ChaosActionType.FORM_SPAM: 0.3,
            ChaosActionType.NAVIGATE: 0.15,
            ChaosActionType.TYPE: 0.15,
        }

        action_type = random.choices(
            list(weights.keys()),
            weights=list(weights.values()),
        )[0]

        target = None
        value = None

        if action_type in (ChaosActionType.INJECTION, ChaosActionType.TYPE):
            target = random.choice(self._find_input_elements())
            value = random.choice([
                "<script>alert(document.domain)</script>",
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "{{constructor.constructor('return this')()}}",
                "${7*7}",
                "../../../etc/passwd",
                "file:///etc/passwd",
                "javascript:alert(1)",
                "<img src=x onerror=alert(1)>",
                "{{7*7}}",
            ])
        elif action_type == ChaosActionType.NAVIGATE:
            value = random.choice([
                "javascript:alert(1)",
                "data:text/html,<script>alert(1)</script>",
            ])

        return ChaosAction(action_type=action_type, target=target, value=value)


class RandomMonkeyAgent(ChaosAgent):
    """Pure random chaos monkey."""

    def _generate_action(self) -> ChaosAction:
        action_types = list(ChaosActionType)
        action_type = random.choice(action_types)

        target = None
        value = None

        if action_type in (ChaosActionType.CLICK, ChaosActionType.RAPID_CLICK):
            target = random.choice(self._find_clickable_elements())
        elif action_type == ChaosActionType.TYPE:
            target = random.choice(self._find_input_elements())
            value = "".join(
                random.choices(
                    "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()",
                    k=random.randint(1, 50),
                )
            )
        elif action_type == ChaosActionType.KEYBOARD_SHORTCUT:
            value = random.choice([
                "Enter",
                "Escape",
                "Tab",
                "ArrowUp",
                "ArrowDown",
                "Delete",
                "Backspace",
            ])

        return ChaosAction(action_type=action_type, target=target, value=value)


class PowerUserAgent(ChaosAgent):
    """Simulates a power user using keyboard shortcuts and advanced features."""

    def _generate_action(self) -> ChaosAction:
        weights = {
            ChaosActionType.KEYBOARD_SHORTCUT: 0.4,
            ChaosActionType.TAB_SWITCH: 0.2,
            ChaosActionType.TYPE: 0.2,
            ChaosActionType.CLICK: 0.2,
        }

        action_type = random.choices(
            list(weights.keys()),
            weights=list(weights.values()),
        )[0]

        target = None
        value = None

        if action_type == ChaosActionType.KEYBOARD_SHORTCUT:
            value = random.choice([
                "Tab",
                "Enter",
                "Escape",
                "ArrowUp",
                "ArrowDown",
                "Home",
                "End",
                "PageUp",
                "PageDown",
            ])
        elif action_type == ChaosActionType.TYPE:
            target = random.choice(self._find_input_elements())
            value = "power user input"
        elif action_type == ChaosActionType.CLICK:
            target = random.choice(self._find_clickable_elements())

        return ChaosAction(action_type=action_type, target=target, value=value)


class ChaosAgentFactory:
    """Factory for creating chaos agents."""

    AGENT_CLASSES: dict[ChaosPersona, type[ChaosAgent]] = {
        ChaosPersona.ANGRY_USER: AngryUserAgent,
        ChaosPersona.IMPATIENT_USER: ImpatientUserAgent,
        ChaosPersona.CONFUSED_USER: ConfusedUserAgent,
        ChaosPersona.MALICIOUS_USER: MaliciousUserAgent,
        ChaosPersona.RANDOM_MONKEY: RandomMonkeyAgent,
        ChaosPersona.POWER_USER: PowerUserAgent,
    }

    @classmethod
    def create(
        cls,
        page: BrowserContext,
        persona: ChaosPersona,
        max_actions: int = 100,
        action_delay_ms: int = 500,
    ) -> ChaosAgent:
        """
        Create a chaos agent with specified persona.

        Args:
            page: Browser page to operate on
            persona: Type of chaos persona
            max_actions: Maximum number of actions
            action_delay_ms: Delay between actions

        Returns:
            Configured ChaosAgent instance
        """
        agent_class = cls.AGENT_CLASSES.get(persona)
        if agent_class is None:
            return ChaosAgent(
                page=page,
                persona=persona,
                max_actions=max_actions,
                action_delay_ms=action_delay_ms,
            )

        return agent_class(
            page=page,
            persona=persona,
            max_actions=max_actions,
            action_delay_ms=action_delay_ms,
        )

    @classmethod
    def run_all_personas(
        cls,
        browser: Browser,
        url: str,
        duration_per_persona: int = 30,
        max_actions: int = 50,
    ) -> list[ChaosSession]:
        """
        Run chaos testing with all personas.

        Args:
            browser: Browser instance
            url: URL to test
            duration_per_persona: Duration for each persona
            max_actions: Max actions per persona

        Returns:
            List of ChaosSession results
        """
        results: list[ChaosSession] = []

        for persona in ChaosPersona:
            if persona in cls.AGENT_CLASSES:
                page = browser.new_page()
                try:
                    page.goto(url)
                    agent = cls.create(page, persona, max_actions=max_actions)
                    session = agent.run(duration_seconds=duration_per_persona)
                    results.append(session)
                finally:
                    page.close()

        return results
