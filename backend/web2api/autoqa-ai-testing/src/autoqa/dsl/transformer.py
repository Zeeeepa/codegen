"""
Step transformer for converting DSL steps to owl-browser commands.

Transforms test steps into executable browser commands without AI dependency.
"""

from __future__ import annotations

from typing import Any

import structlog

from autoqa.dsl.models import StepAction, TestStep

logger = structlog.get_logger(__name__)


class StepTransformer:
    """Transforms DSL test steps into owl-browser commands."""

    def __init__(self) -> None:
        self._log = logger.bind(component="step_transformer")
        self._action_handlers: dict[StepAction, str] = {
            # Navigation
            StepAction.NAVIGATE: "goto",
            StepAction.WAIT: "wait",
            StepAction.WAIT_FOR_SELECTOR: "wait_for_selector",
            StepAction.WAIT_FOR_NETWORK_IDLE: "wait_for_network_idle",
            StepAction.WAIT_FOR_URL: "wait_for_url",
            # Clicks & Interactions
            StepAction.CLICK: "click",
            StepAction.DOUBLE_CLICK: "double_click",
            StepAction.RIGHT_CLICK: "right_click",
            StepAction.HOVER: "hover",
            StepAction.DRAG_DROP: "drag_drop",
            # Forms
            StepAction.TYPE: "type",
            StepAction.PICK: "pick",
            StepAction.PRESS_KEY: "press_key",
            StepAction.SUBMIT: "submit_form",
            StepAction.UPLOAD: "upload_file",
            # Scroll
            StepAction.SCROLL: "scroll_by",
            StepAction.SCROLL_TO: "scroll_to",
            StepAction.SCROLL_TO_ELEMENT: "scroll_to_element",
            # Extraction
            StepAction.SCREENSHOT: "screenshot",
            StepAction.EXTRACT_TEXT: "extract_text",
            StepAction.EXTRACT_JSON: "extract_json",
            StepAction.GET_HTML: "get_html",
            StepAction.GET_MARKDOWN: "get_markdown",
            StepAction.GET_ATTRIBUTE: "get_attribute",
            StepAction.GET_NETWORK_LOG: "get_network_log",
            # Script execution
            StepAction.EVALUATE: "evaluate",
            StepAction.FIND_ELEMENT: "find_element",
            # State checks
            StepAction.CHECK_VISIBLE: "is_visible",
            StepAction.CHECK_ENABLED: "is_enabled",
            StepAction.CHECK_CHECKED: "is_checked",
            # Cookies
            StepAction.SET_COOKIE: "set_cookie",
            StepAction.DELETE_COOKIES: "delete_cookies",
            # Viewport & Pages
            StepAction.SET_VIEWPORT: "set_viewport",
            StepAction.NEW_PAGE: "new_page",
            StepAction.CLOSE_PAGE: "close",
            # Recording
            StepAction.START_VIDEO: "start_video_recording",
            StepAction.STOP_VIDEO: "stop_video_recording",
        }

    def transform(self, step: TestStep) -> tuple[str, dict[str, Any]]:
        """
        Transform a test step into a method name and arguments.

        Returns:
            Tuple of (method_name, arguments_dict)
        """
        if step.action in (
            StepAction.ASSERT,
            StepAction.VISUAL_ASSERT,
            StepAction.NETWORK_ASSERT,
            StepAction.URL_ASSERT,
            StepAction.CUSTOM,
            # ML-based assertions
            StepAction.ML_ASSERT,
            StepAction.OCR_ASSERT,
            StepAction.UI_STATE_ASSERT,
            StepAction.COLOR_ASSERT,
            StepAction.LAYOUT_ASSERT,
            StepAction.ICON_ASSERT,
            StepAction.ACCESSIBILITY_ASSERT,
            # LLM-based assertions
            StepAction.LLM_ASSERT,
            StepAction.SEMANTIC_ASSERT,
            StepAction.CONTENT_ASSERT,
        ):
            return self._transform_assertion(step)

        method = self._action_handlers.get(step.action)
        if not method:
            raise ValueError(f"Unknown action: {step.action}")

        args = self._build_arguments(step)
        return method, args

    def _build_arguments(self, step: TestStep) -> dict[str, Any]:
        """Build argument dictionary for the step."""
        args: dict[str, Any] = {}

        match step.action:
            # Navigation
            case StepAction.NAVIGATE:
                args["url"] = step.url
                if step.wait_until:
                    args["wait_until"] = step.wait_until
                if step.timeout:
                    args["timeout"] = step.timeout

            case StepAction.WAIT:
                args["timeout"] = step.timeout or 1000

            case StepAction.WAIT_FOR_SELECTOR:
                args["selector"] = step.selector
                if step.timeout:
                    args["timeout"] = step.timeout

            case StepAction.WAIT_FOR_NETWORK_IDLE:
                args["idle_time"] = getattr(step, "idle_time", None) or 500
                if step.timeout:
                    args["timeout"] = step.timeout

            case StepAction.WAIT_FOR_URL:
                args["url_pattern"] = step.url
                if step.timeout:
                    args["timeout"] = step.timeout

            # Clicks & Interactions
            case StepAction.CLICK:
                args["selector"] = step.selector

            case StepAction.DOUBLE_CLICK:
                args["selector"] = step.selector

            case StepAction.RIGHT_CLICK:
                args["selector"] = step.selector

            case StepAction.HOVER:
                args["selector"] = step.selector
                if step.timeout is not None:
                    args["duration"] = step.timeout

            case StepAction.DRAG_DROP:
                args["start_x"] = step.start_x
                args["start_y"] = step.start_y
                args["end_x"] = step.end_x
                args["end_y"] = step.end_y

            # Forms
            case StepAction.TYPE:
                args["selector"] = step.selector
                args["text"] = step.text

            case StepAction.PICK:
                args["selector"] = step.selector
                args["value"] = step.value

            case StepAction.PRESS_KEY:
                args["key"] = step.key
                if step.modifiers:
                    args["modifiers"] = step.modifiers

            case StepAction.SUBMIT:
                if step.selector:
                    args["selector"] = step.selector

            case StepAction.UPLOAD:
                args["selector"] = step.selector
                args["file_paths"] = step.file_paths

            # Scroll
            case StepAction.SCROLL:
                args["x"] = step.scroll_x or 0
                args["y"] = step.scroll_y or 0

            case StepAction.SCROLL_TO:
                args["x"] = step.x or 0
                args["y"] = step.y or 0

            case StepAction.SCROLL_TO_ELEMENT:
                args["selector"] = step.selector

            # Extraction
            case StepAction.SCREENSHOT:
                if step.filename:
                    args["path"] = step.filename

            case StepAction.EXTRACT_TEXT:
                if step.selector:
                    args["selector"] = step.selector

            case StepAction.EXTRACT_JSON:
                if step.template:
                    args["template"] = step.template

            case StepAction.GET_HTML:
                if step.clean_level:
                    args["clean_level"] = step.clean_level

            case StepAction.GET_MARKDOWN:
                pass

            case StepAction.GET_ATTRIBUTE:
                args["selector"] = step.selector
                args["attribute"] = step.attribute_name

            case StepAction.GET_NETWORK_LOG:
                pass

            # Script execution
            case StepAction.EVALUATE:
                args["script"] = step.script
                if step.args:
                    args["args"] = step.args
                args["return_value"] = True

            case StepAction.FIND_ELEMENT:
                args["selector"] = step.selector
                if step.text:
                    args["text"] = step.text

            # State checks
            case StepAction.CHECK_VISIBLE:
                args["selector"] = step.selector

            case StepAction.CHECK_ENABLED:
                args["selector"] = step.selector

            case StepAction.CHECK_CHECKED:
                args["selector"] = step.selector

            # Cookies
            case StepAction.SET_COOKIE:
                args["url"] = step.url or ""
                args["name"] = step.cookie_name
                args["value"] = step.cookie_value
                if step.cookie_domain:
                    args["domain"] = step.cookie_domain
                if step.cookie_path:
                    args["path"] = step.cookie_path
                if step.cookie_secure is not None:
                    args["secure"] = step.cookie_secure
                if step.cookie_http_only is not None:
                    args["http_only"] = step.cookie_http_only
                if step.cookie_expires is not None:
                    args["expires"] = step.cookie_expires

            case StepAction.DELETE_COOKIES:
                if step.url:
                    args["url"] = step.url
                if step.cookie_name:
                    args["name"] = step.cookie_name

            # Viewport & Pages
            case StepAction.SET_VIEWPORT:
                args["width"] = step.width
                args["height"] = step.height

            case StepAction.NEW_PAGE:
                pass

            case StepAction.CLOSE_PAGE:
                pass

            # Recording
            case StepAction.START_VIDEO:
                if step.fps:
                    args["fps"] = step.fps

            case StepAction.STOP_VIDEO:
                pass

        return args

    def _transform_assertion(self, step: TestStep) -> tuple[str, dict[str, Any]]:
        """Transform assertion steps into special assertion commands."""
        match step.action:
            case StepAction.ASSERT:
                return "_assert_element", {"config": step.assertion}
            case StepAction.VISUAL_ASSERT:
                return "_assert_visual", {"config": step.visual_assertion}
            case StepAction.NETWORK_ASSERT:
                return "_assert_network", {"config": step.network_assertion}
            case StepAction.URL_ASSERT:
                return "_assert_url", {
                    "url_pattern": step.url_pattern,
                    "is_regex": step.is_regex,
                }
            case StepAction.CUSTOM:
                return "_assert_custom", {"config": step.custom_assertion}
            # ML-based assertions
            case StepAction.ML_ASSERT:
                return "_assert_ml", {"config": step.ml_assertion}
            case StepAction.OCR_ASSERT:
                return "_assert_ocr", {"config": step.ocr_assertion}
            case StepAction.UI_STATE_ASSERT:
                return "_assert_ui_state", {"config": step.ui_state_assertion}
            case StepAction.COLOR_ASSERT:
                return "_assert_color", {"config": step.color_assertion}
            case StepAction.LAYOUT_ASSERT:
                return "_assert_layout", {"config": step.layout_assertion}
            case StepAction.ICON_ASSERT:
                return "_assert_icon", {"config": step.icon_assertion}
            case StepAction.ACCESSIBILITY_ASSERT:
                return "_assert_accessibility", {"config": step.accessibility_assertion}
            # LLM-based assertions
            case StepAction.LLM_ASSERT:
                return "_assert_llm", {"config": step.llm_assertion}
            case StepAction.SEMANTIC_ASSERT:
                return "_assert_semantic", {"config": step.semantic_assertion}
            case StepAction.CONTENT_ASSERT:
                return "_assert_content", {"config": step.content_assertion}
            case _:
                raise ValueError(f"Unknown assertion type: {step.action}")

    def get_return_type(self, action: StepAction) -> type | None:
        """Get the expected return type for an action."""
        return_types: dict[StepAction, type] = {
            StepAction.SCREENSHOT: bytes,
            StepAction.EXTRACT_TEXT: str,
            StepAction.EXTRACT_JSON: dict,
            StepAction.GET_HTML: str,
            StepAction.GET_MARKDOWN: str,
            StepAction.GET_ATTRIBUTE: str,
            StepAction.GET_NETWORK_LOG: list,
            StepAction.EVALUATE: object,
            StepAction.CHECK_VISIBLE: bool,
            StepAction.CHECK_ENABLED: bool,
            StepAction.CHECK_CHECKED: bool,
        }
        return return_types.get(action)

    def should_capture_result(self, step: TestStep) -> bool:
        """Check if step result should be captured."""
        if step.capture_as:
            return True
        capturable_actions = {
            StepAction.EXTRACT_TEXT,
            StepAction.EXTRACT_JSON,
            StepAction.GET_HTML,
            StepAction.GET_MARKDOWN,
            StepAction.GET_ATTRIBUTE,
            StepAction.GET_NETWORK_LOG,
            StepAction.EVALUATE,
            StepAction.SCREENSHOT,
            StepAction.CHECK_VISIBLE,
            StepAction.CHECK_ENABLED,
            StepAction.CHECK_CHECKED,
        }
        return step.action in capturable_actions
