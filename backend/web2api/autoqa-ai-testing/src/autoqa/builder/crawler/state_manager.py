"""
Application state tracking for intelligent test generation.

Provides:
- Cookie, localStorage, sessionStorage tracking
- State-changing action detection
- State transition graph building
- Prerequisite state identification
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from owl_browser import BrowserContext

logger = structlog.get_logger(__name__)


@dataclass
class StateConfig:
    """Configuration for state manager."""

    track_cookies: bool = True
    """Whether to track cookie changes."""

    track_local_storage: bool = True
    """Whether to track localStorage changes."""

    track_session_storage: bool = True
    """Whether to track sessionStorage changes."""

    track_dom_changes: bool = True
    """Whether to track DOM state changes."""

    max_states: int = 100
    """Maximum number of states to track."""

    state_timeout: int = 30000
    """Timeout for state capture in ms."""

    detect_auth_state: bool = True
    """Whether to detect authentication state changes."""


class StateChangeType(StrEnum):
    """Types of state changes."""

    NAVIGATION = auto()
    FORM_SUBMIT = auto()
    AUTHENTICATION = auto()
    DATA_MODIFICATION = auto()
    MODAL_OPEN = auto()
    MODAL_CLOSE = auto()
    TAB_SWITCH = auto()
    STORAGE_UPDATE = auto()
    COOKIE_UPDATE = auto()
    UNKNOWN = auto()


@dataclass
class StorageState:
    """Storage state snapshot."""

    local_storage: dict[str, str]
    session_storage: dict[str, str]
    cookies: list[dict[str, Any]]

    def get_hash(self) -> str:
        """Get hash of storage state."""
        content = json.dumps({
            "local": sorted(self.local_storage.items()),
            "session": sorted(self.session_storage.items()),
            "cookies": sorted([c.get("name", "") for c in self.cookies]),
        }, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class DOMState:
    """DOM state snapshot."""

    url: str
    title: str
    visible_text_hash: str
    element_count: int
    form_count: int
    modal_visible: bool
    active_element_selector: str | None

    def get_hash(self) -> str:
        """Get hash of DOM state."""
        content = f"{self.url}|{self.visible_text_hash}|{self.element_count}|{self.modal_visible}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class ApplicationState:
    """Complete application state snapshot."""

    state_id: str
    url: str
    storage_state: StorageState
    dom_state: DOMState
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_hash(self) -> str:
        """Get combined state hash."""
        return f"{self.storage_state.get_hash()}_{self.dom_state.get_hash()}"

    @property
    def is_authenticated(self) -> bool:
        """Check if state appears authenticated."""
        # Check for common auth indicators
        for cookie in self.storage_state.cookies:
            name = cookie.get("name", "").lower()
            if any(auth in name for auth in ["session", "token", "auth", "jwt"]):
                return True

        # Check localStorage for tokens
        for key in self.storage_state.local_storage:
            if any(auth in key.lower() for auth in ["token", "auth", "session"]):
                return True

        return False


@dataclass
class StateTransition:
    """Transition between application states."""

    from_state_id: str
    to_state_id: str
    trigger_action: str
    trigger_selector: str | None
    change_type: StateChangeType
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StateGraph:
    """Graph of application states and transitions."""

    states: dict[str, ApplicationState]
    transitions: list[StateTransition]
    initial_state_id: str | None = None
    authenticated_states: list[str] = field(default_factory=list)

    def add_state(self, state: ApplicationState) -> bool:
        """Add state to graph. Returns True if new state."""
        if state.state_id not in self.states:
            self.states[state.state_id] = state
            if state.is_authenticated:
                self.authenticated_states.append(state.state_id)
            return True
        return False

    def add_transition(self, transition: StateTransition) -> None:
        """Add transition to graph."""
        self.transitions.append(transition)

    def get_path_to_state(self, target_state_id: str) -> list[StateTransition]:
        """Get transitions needed to reach a target state from initial state."""
        if not self.initial_state_id or target_state_id == self.initial_state_id:
            return []

        # BFS to find shortest path
        from collections import deque

        visited: set[str] = set()
        queue: deque[tuple[str, list[StateTransition]]] = deque()
        queue.append((self.initial_state_id, []))

        while queue:
            current_state, path = queue.popleft()

            if current_state in visited:
                continue
            visited.add(current_state)

            if current_state == target_state_id:
                return path

            # Find transitions from current state
            for transition in self.transitions:
                if transition.from_state_id == current_state:
                    queue.append((transition.to_state_id, path + [transition]))

        return []

    def get_prerequisites(self, state_id: str) -> list[str]:
        """Get prerequisite states for a given state."""
        path = self.get_path_to_state(state_id)
        return [t.from_state_id for t in path]

    def get_authenticated_entry_points(self) -> list[StateTransition]:
        """Get transitions that lead to authenticated states."""
        entry_points: list[StateTransition] = []

        for transition in self.transitions:
            if transition.to_state_id in self.authenticated_states:
                if transition.from_state_id not in self.authenticated_states:
                    entry_points.append(transition)

        return entry_points

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary for serialization."""
        return {
            "states": {
                sid: {
                    "url": s.url,
                    "hash": s.get_hash(),
                    "is_authenticated": s.is_authenticated,
                    "timestamp": s.timestamp.isoformat(),
                }
                for sid, s in self.states.items()
            },
            "transitions": [
                {
                    "from": t.from_state_id,
                    "to": t.to_state_id,
                    "action": t.trigger_action,
                    "selector": t.trigger_selector,
                    "type": t.change_type.value,
                }
                for t in self.transitions
            ],
            "initial_state": self.initial_state_id,
            "authenticated_states": self.authenticated_states,
        }


class StateManager:
    """
    Manages application state tracking across page interactions.

    Features:
    - Captures complete application state (storage, DOM)
    - Tracks state transitions
    - Builds state graph for test prerequisites
    - Identifies authentication boundaries
    """

    def __init__(self, config: StateConfig | None = None) -> None:
        self.config = config or StateConfig()
        self._log = logger.bind(component="state_manager")
        self._graph = StateGraph(states={}, transitions=[])
        self._current_state: ApplicationState | None = None
        self._state_counter = 0

    @property
    def state_graph(self) -> StateGraph:
        """Get the current state graph."""
        return self._graph

    @property
    def current_state(self) -> ApplicationState | None:
        """Get the current application state."""
        return self._current_state

    async def capture_state(self, page: BrowserContext) -> ApplicationState:
        """
        Capture the current application state.

        Args:
            page: Browser context to capture state from

        Returns:
            ApplicationState snapshot
        """
        self._log.debug("Capturing application state")

        # Capture storage state
        storage_state = await self._capture_storage_state(page)

        # Capture DOM state
        dom_state = await self._capture_dom_state(page)

        # Generate state ID
        self._state_counter += 1
        state_id = f"state_{self._state_counter}_{storage_state.get_hash()}_{dom_state.get_hash()}"

        state = ApplicationState(
            state_id=state_id,
            url=page.get_current_url(),
            storage_state=storage_state,
            dom_state=dom_state,
            timestamp=datetime.now(UTC),
        )

        # Check if this is a new state
        is_new = self._graph.add_state(state)

        # Set as initial state if first
        if self._graph.initial_state_id is None:
            self._graph.initial_state_id = state_id

        # Update current state
        self._current_state = state

        self._log.debug(
            "State captured",
            state_id=state_id,
            is_new=is_new,
            is_authenticated=state.is_authenticated,
        )

        return state

    async def _capture_storage_state(self, page: BrowserContext) -> StorageState:
        """Capture browser storage state."""
        script = """
        (() => {
            const result = {
                localStorage: {},
                sessionStorage: {}
            };

            // Capture localStorage
            try {
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key) {
                        result.localStorage[key] = localStorage.getItem(key) || '';
                    }
                }
            } catch (e) {
                // localStorage may be blocked
            }

            // Capture sessionStorage
            try {
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    if (key) {
                        result.sessionStorage[key] = sessionStorage.getItem(key) || '';
                    }
                }
            } catch (e) {
                // sessionStorage may be blocked
            }

            return result;
        })()
        """

        storage = page.expression(script)

        # Get cookies via JavaScript (limited to accessible cookies)
        cookies_script = """
        (() => {
            const cookies = document.cookie.split(';').map(c => {
                const [name, ...rest] = c.trim().split('=');
                return {
                    name: name,
                    value: rest.join('=')
                };
            }).filter(c => c.name);
            return cookies;
        })()
        """

        cookies = page.expression(cookies_script)

        return StorageState(
            local_storage=storage.get("localStorage", {}),
            session_storage=storage.get("sessionStorage", {}),
            cookies=cookies,
        )

    async def _capture_dom_state(self, page: BrowserContext) -> DOMState:
        """Capture DOM state snapshot."""
        script = """
        (() => {
            const result = {
                url: window.location.href,
                title: document.title,
                elementCount: document.querySelectorAll('*').length,
                formCount: document.querySelectorAll('form').length,
                modalVisible: false,
                activeElementSelector: null
            };

            // Get visible text hash
            const visibleText = document.body ? document.body.innerText.substring(0, 5000) : '';
            result.visibleTextHash = visibleText.length.toString();

            // Check for modal
            const modal = document.querySelector('[role="dialog"], .modal.show, [aria-modal="true"]');
            result.modalVisible = modal !== null && window.getComputedStyle(modal).display !== 'none';

            // Get active element
            if (document.activeElement && document.activeElement !== document.body) {
                const active = document.activeElement;
                if (active.id) {
                    result.activeElementSelector = '#' + active.id;
                } else if (active.name) {
                    result.activeElementSelector = `[name="${active.name}"]`;
                }
            }

            return result;
        })()
        """

        dom_data = page.expression(script)

        # Create proper hash for visible text
        visible_text_hash = hashlib.md5(
            dom_data.get("visibleTextHash", "").encode()
        ).hexdigest()[:8]

        return DOMState(
            url=dom_data["url"],
            title=dom_data["title"],
            visible_text_hash=visible_text_hash,
            element_count=dom_data["elementCount"],
            form_count=dom_data["formCount"],
            modal_visible=dom_data["modalVisible"],
            active_element_selector=dom_data.get("activeElementSelector"),
        )

    async def record_transition(
        self,
        page: BrowserContext,
        action: str,
        selector: str | None = None,
        change_type: StateChangeType = StateChangeType.UNKNOWN,
    ) -> StateTransition | None:
        """
        Record a state transition after an action.

        Args:
            page: Browser context after action
            action: Action that triggered the transition
            selector: Selector of element that was interacted with
            change_type: Type of state change

        Returns:
            StateTransition if state changed, None otherwise
        """
        if self._current_state is None:
            self._log.warning("No current state to transition from")
            return None

        from_state = self._current_state

        # Capture new state
        new_state = await self.capture_state(page)

        # Check if state actually changed
        if new_state.get_hash() == from_state.get_hash():
            return None

        # Determine change type if not specified
        if change_type == StateChangeType.UNKNOWN:
            change_type = self._detect_change_type(from_state, new_state, action)

        # Create transition
        transition = StateTransition(
            from_state_id=from_state.state_id,
            to_state_id=new_state.state_id,
            trigger_action=action,
            trigger_selector=selector,
            change_type=change_type,
            timestamp=datetime.now(UTC),
        )

        self._graph.add_transition(transition)

        self._log.debug(
            "State transition recorded",
            from_state=from_state.state_id,
            to_state=new_state.state_id,
            change_type=change_type.value,
        )

        return transition

    def _detect_change_type(
        self,
        from_state: ApplicationState,
        to_state: ApplicationState,
        action: str,
    ) -> StateChangeType:
        """Detect the type of state change."""
        # URL change indicates navigation
        if from_state.url != to_state.url:
            return StateChangeType.NAVIGATION

        # Authentication change
        if not from_state.is_authenticated and to_state.is_authenticated:
            return StateChangeType.AUTHENTICATION

        # Modal state change
        if from_state.dom_state.modal_visible != to_state.dom_state.modal_visible:
            if to_state.dom_state.modal_visible:
                return StateChangeType.MODAL_OPEN
            return StateChangeType.MODAL_CLOSE

        # Storage change
        if from_state.storage_state.get_hash() != to_state.storage_state.get_hash():
            return StateChangeType.STORAGE_UPDATE

        # Form submit action
        if "submit" in action.lower() or "click" in action.lower():
            return StateChangeType.FORM_SUBMIT

        return StateChangeType.UNKNOWN

    def get_state_prerequisites(self, state_id: str) -> list[tuple[str, str, str]]:
        """
        Get prerequisites (actions) needed to reach a state.

        Returns:
            List of (action, selector, description) tuples
        """
        transitions = self._graph.get_path_to_state(state_id)

        prerequisites: list[tuple[str, str, str]] = []
        for t in transitions:
            description = f"{t.trigger_action} on {t.trigger_selector or 'page'}"
            prerequisites.append((t.trigger_action, t.trigger_selector or "", description))

        return prerequisites

    def get_authentication_flow(self) -> list[StateTransition]:
        """Get the authentication flow transitions."""
        return self._graph.get_authenticated_entry_points()

    def get_state_by_url(self, url: str) -> ApplicationState | None:
        """Find state matching a URL."""
        for state in self._graph.states.values():
            if state.url == url:
                return state
        return None

    def reset(self) -> None:
        """Reset state manager to initial state."""
        self._graph = StateGraph(states={}, transitions=[])
        self._current_state = None
        self._state_counter = 0

    def export_graph(self) -> dict[str, Any]:
        """Export state graph for visualization or storage."""
        return self._graph.to_dict()

    def get_statistics(self) -> dict[str, Any]:
        """Get state tracking statistics."""
        return {
            "total_states": len(self._graph.states),
            "total_transitions": len(self._graph.transitions),
            "authenticated_states": len(self._graph.authenticated_states),
            "current_state": self._current_state.state_id if self._current_state else None,
            "current_authenticated": self._current_state.is_authenticated if self._current_state else False,
        }
