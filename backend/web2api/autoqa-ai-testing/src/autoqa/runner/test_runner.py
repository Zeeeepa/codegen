"""
Test runner for executing DSL test specifications.

Executes tests using owl-browser SDK v2 with:
- Self-healing selector recovery (no AI dependency)
- Automatic retries with exponential backoff
- Smart waits (network idle, selectors)
- Screenshot capture on failure
- Network log capture for debugging
- Async-first design with context management
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import re
import time
import traceback
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import structlog

from autoqa.dsl.models import (
    StepAction,
    TestSpec,
    TestStep,
    TestSuite,
)
from autoqa.dsl.transformer import StepTransformer
from autoqa.runner.self_healing import HealingResult, SelfHealingEngine
from autoqa.versioning.history_tracker import TestRunHistory
from autoqa.versioning.models import VersioningConfig

if TYPE_CHECKING:
    from owl_browser import OwlBrowser

logger = structlog.get_logger(__name__)


# Exception types for retry logic
class ElementNotFoundError(Exception):
    """Raised when an element cannot be found."""

    pass


class ElementNotInteractableError(Exception):
    """Raised when an element is found but not interactable."""

    pass


class NetworkTimeoutError(Exception):
    """Raised when network operations timeout."""

    pass


class StepStatus(StrEnum):
    """Status of a test step execution."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    HEALED = "healed"


@dataclass
class StepResult:
    """Result of a single step execution."""

    step_index: int
    step_name: str | None
    action: str
    status: StepStatus
    duration_ms: int = 0
    result: Any = None
    error: str | None = None
    error_traceback: str | None = None
    screenshot_path: str | None = None
    healing_result: HealingResult | None = None
    retries: int = 0
    network_log: list[dict[str, Any]] | None = None


@dataclass
class TestRunResult:
    """Result of a complete test run."""

    test_name: str
    status: StepStatus
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int = 0
    total_steps: int = 0
    passed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    healed_steps: int = 0
    step_results: list[StepResult] = field(default_factory=list)
    video_path: str | None = None
    artifacts: dict[str, str] = field(default_factory=dict)
    error: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    network_log: list[dict[str, Any]] = field(default_factory=list)


class PageRecoveryError(Exception):
    """Raised when page recovery (navigation to expected URL) fails."""

    pass


class TestRunner:
    """
    Executes test specifications using owl-browser SDK v2.

    Features:
    - Self-healing selector recovery (deterministic, no AI)
    - URL-aware recovery: navigates to expected page if on wrong page
    - Automatic retries with exponential backoff (tenacity)
    - Smart waits: wait_for_network_idle after navigation
    - wait_for_selector before interactions
    - is_visible/is_enabled checks before clicks
    - Video recording
    - Screenshot capture on failure
    - Network log capture for debugging
    - Variable capture and interpolation
    - Async-first design with context management

    SDK v2 Notes:
    - Uses OwlBrowser instead of Browser
    - All browser operations are async and require context_id
    - Context is created per test and closed after completion
    - Methods use await browser.method(context_id=..., ...)
    """

    # Actions that require element visibility/enabled checks
    INTERACTION_ACTIONS: frozenset[StepAction] = frozenset({
        StepAction.CLICK,
        StepAction.DOUBLE_CLICK,
        StepAction.RIGHT_CLICK,
        StepAction.TYPE,
        StepAction.PICK,
        StepAction.HOVER,
        StepAction.UPLOAD,
        StepAction.SUBMIT,
    })

    # Actions that should wait for network idle after execution
    NAVIGATION_ACTIONS: frozenset[StepAction] = frozenset({
        StepAction.NAVIGATE,
        StepAction.CLICK,
        StepAction.SUBMIT,
    })

    def __init__(
        self,
        browser: OwlBrowser,
        healing_engine: SelfHealingEngine | None = None,
        artifact_dir: str | Path | None = None,
        record_video: bool = False,
        screenshot_on_failure: bool = True,
        capture_network_on_failure: bool = True,
        default_timeout_ms: int = 30000,
        wait_for_network_idle: bool = True,
        network_idle_timeout_ms: int = 5000,
        pre_action_visibility_check: bool = True,
        enable_versioning: bool = False,
        versioning_storage_path: str = ".autoqa/history",
        enable_url_recovery: bool = True,
    ) -> None:
        self._browser = browser
        self._healing_engine = healing_engine or SelfHealingEngine()
        self._artifact_dir = Path(artifact_dir) if artifact_dir else Path("./artifacts")
        self._record_video = record_video
        self._screenshot_on_failure = screenshot_on_failure
        self._capture_network_on_failure = capture_network_on_failure
        self._default_timeout = default_timeout_ms
        self._wait_for_network_idle = wait_for_network_idle
        self._network_idle_timeout = network_idle_timeout_ms
        self._pre_action_visibility_check = pre_action_visibility_check
        self._enable_url_recovery = enable_url_recovery
        self._transformer = StepTransformer()
        self._log = logger.bind(component="test_runner")

        # URL recovery tracking - stores the expected URL from navigate actions
        # and step-level _expected_url metadata
        self._current_expected_url: str | None = None

        # Versioning support
        self._enable_versioning = enable_versioning
        self._versioning_storage_path = versioning_storage_path
        self._history_tracker: TestRunHistory | None = None

        if self._enable_versioning:
            self._history_tracker = TestRunHistory(storage_path=versioning_storage_path)

        self._artifact_dir.mkdir(parents=True, exist_ok=True)

    async def run_spec(
        self,
        spec: TestSpec,
        context_id: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> TestRunResult:
        """
        Run a single test specification.

        Args:
            spec: Test specification to run
            context_id: Browser context ID to use (creates new if not provided)
            variables: Additional variables for interpolation

        Returns:
            TestRunResult with execution details

        SDK v2 Notes:
            - Creates a new context via browser.create_context() if not provided
            - All operations use context_id parameter
            - Context is closed after completion if created here
        """
        result = TestRunResult(
            test_name=spec.name,
            status=StepStatus.RUNNING,
            started_at=datetime.now(UTC),
            total_steps=len(spec.steps),
            variables={**(variables or {}), **spec.variables},
        )

        own_context = context_id is None
        if own_context:
            ctx = await self._browser.create_context()
            context_id = ctx["context_id"]

        self._log.info("Starting test run", test=spec.name, steps=len(spec.steps), context_id=context_id)

        try:
            if self._record_video:
                await self._browser.start_video_recording(context_id=context_id, fps=30)

            if spec.before_all:
                await self._run_hook(context_id, spec.before_all.steps, "before_all", result)

            for i, step in enumerate(spec.steps):
                if spec.before_each:
                    await self._run_hook(context_id, spec.before_each.steps, "before_each", result)

                step_result = await self._execute_step(context_id, step, i, result)
                result.step_results.append(step_result)

                match step_result.status:
                    case StepStatus.PASSED:
                        result.passed_steps += 1
                    case StepStatus.FAILED:
                        result.failed_steps += 1
                        if not step.continue_on_failure:
                            break
                    case StepStatus.SKIPPED:
                        result.skipped_steps += 1
                    case StepStatus.HEALED:
                        result.healed_steps += 1
                        result.passed_steps += 1

                if spec.after_each:
                    await self._run_hook(context_id, spec.after_each.steps, "after_each", result)

            if spec.after_all:
                await self._run_hook(context_id, spec.after_all.steps, "after_all", result)

            if self._record_video:
                try:
                    video_result = await self._browser.stop_video_recording(context_id=context_id)
                    result.video_path = video_result.get("path") if isinstance(video_result, dict) else None
                except Exception as e:
                    self._log.warning("Failed to stop video recording", error=str(e))

        except Exception as e:
            result.error = str(e)
            self._log.error("Test run failed with exception", error=str(e))

        finally:
            if own_context:
                with contextlib.suppress(Exception):
                    await self._browser.close_context(context_id=context_id)

        result.finished_at = datetime.now(UTC)
        result.duration_ms = int(
            (result.finished_at - result.started_at).total_seconds() * 1000
        )
        result.status = (
            StepStatus.PASSED if result.failed_steps == 0 else StepStatus.FAILED
        )

        self._log.info(
            "Test run completed",
            test=spec.name,
            status=result.status,
            passed=result.passed_steps,
            failed=result.failed_steps,
            healed=result.healed_steps,
            duration_ms=result.duration_ms,
        )

        # Save snapshot if versioning is enabled (either globally or per-spec)
        versioning_enabled = self._enable_versioning or (
            spec.versioning and spec.versioning.enabled
        )
        if versioning_enabled:
            await self._save_test_snapshot(spec, result, context_id if not own_context else None)

        return result

    async def _save_test_snapshot(
        self,
        spec: TestSpec,
        result: TestRunResult,
        context_id: str | None,
    ) -> None:
        """Save a snapshot for versioned test tracking."""
        try:
            # Get versioning config from spec or use defaults
            versioning_config = VersioningConfig(
                enabled=True,
                storage_path=spec.versioning.storage_path if spec.versioning else self._versioning_storage_path,
                capture_screenshots=spec.versioning.capture_screenshots if spec.versioning else True,
                capture_network=spec.versioning.capture_network if spec.versioning else True,
                capture_elements=spec.versioning.capture_elements if spec.versioning else True,
                element_selectors=list(spec.versioning.element_selectors) if spec.versioning else [],
            )

            # Get or create history tracker
            tracker = self._history_tracker
            if tracker is None or (spec.versioning and spec.versioning.storage_path != self._versioning_storage_path):
                tracker = TestRunHistory(
                    storage_path=versioning_config.storage_path,
                    config=versioning_config,
                )

            # Save the snapshot (pass browser and context_id for SDK v2)
            snapshot = tracker.save_snapshot(
                test_name=spec.name,
                run_data=result,
                browser=self._browser if context_id else None,
                context_id=context_id,
            )

            self._log.info(
                "Snapshot saved",
                test=spec.name,
                version_id=snapshot.version_id,
            )

        except Exception as e:
            self._log.warning(
                "Failed to save test snapshot",
                test=spec.name,
                error=str(e),
            )

    async def run_suite(
        self,
        suite: TestSuite,
        variables: dict[str, Any] | None = None,
    ) -> list[TestRunResult]:
        """
        Run a test suite.

        Args:
            suite: Test suite to run
            variables: Additional variables for interpolation

        Returns:
            List of TestRunResult for each test

        SDK v2 Notes:
            - Creates separate context for each test
            - Hooks run in dedicated contexts
        """
        results: list[TestRunResult] = []
        combined_vars = {**(variables or {}), **suite.variables}

        self._log.info(
            "Starting test suite",
            suite=suite.name,
            tests=len(suite.tests),
            parallel=suite.parallel_execution,
        )

        if suite.before_suite:
            ctx = await self._browser.create_context()
            context_id = ctx["context_id"]
            try:
                dummy_result = TestRunResult(
                    test_name="_suite_setup",
                    status=StepStatus.RUNNING,
                    started_at=datetime.now(UTC),
                )
                await self._run_hook(context_id, suite.before_suite.steps, "before_suite", dummy_result)
            finally:
                await self._browser.close_context(context_id=context_id)

        if suite.parallel_execution:
            results = await self._run_parallel(suite, combined_vars)
        else:
            for test in suite.tests:
                test_vars = {**combined_vars, **test.variables}
                result = await self.run_spec(test, variables=test_vars)
                results.append(result)

                if suite.fail_fast and result.status == StepStatus.FAILED:
                    self._log.info("Fail-fast triggered, stopping suite execution")
                    break

        if suite.after_suite:
            ctx = await self._browser.create_context()
            context_id = ctx["context_id"]
            try:
                dummy_result = TestRunResult(
                    test_name="_suite_teardown",
                    status=StepStatus.RUNNING,
                    started_at=datetime.now(UTC),
                )
                await self._run_hook(context_id, suite.after_suite.steps, "after_suite", dummy_result)
            finally:
                await self._browser.close_context(context_id=context_id)

        passed = sum(1 for r in results if r.status == StepStatus.PASSED)
        failed = sum(1 for r in results if r.status == StepStatus.FAILED)

        self._log.info(
            "Test suite completed",
            suite=suite.name,
            total=len(results),
            passed=passed,
            failed=failed,
        )

        return results

    async def _run_parallel(
        self,
        suite: TestSuite,
        variables: dict[str, Any],
    ) -> list[TestRunResult]:
        """
        Run tests in parallel using asyncio.

        SDK v2 Notes:
            - Each test runs in its own context
            - asyncio.gather provides parallel execution
            - Semaphore limits concurrent tests
        """
        max_concurrent = min(suite.max_parallel, len(suite.tests))
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_single_test(test: TestSpec) -> TestRunResult:
            async with semaphore:
                test_vars = {**variables, **test.variables}
                try:
                    return await self.run_spec(test, variables=test_vars)
                except Exception as e:
                    self._log.error(
                        "Parallel test execution failed",
                        test=test.name,
                        error=str(e),
                    )
                    return TestRunResult(
                        test_name=test.name,
                        status=StepStatus.FAILED,
                        started_at=datetime.now(UTC),
                        finished_at=datetime.now(UTC),
                        error=str(e),
                    )

        tasks = [run_single_test(test) for test in suite.tests]
        return list(await asyncio.gather(*tasks))

    async def _execute_step(
        self,
        context_id: str,
        step: TestStep,
        index: int,
        test_result: TestRunResult,
    ) -> StepResult:
        """
        Execute a single test step with smart waits, URL recovery, and robustness.

        URL-aware recovery flow:
        1. Track expected URL from navigate actions and step metadata
        2. Before element actions, verify we're on the expected page
        3. If element not found, try URL recovery before selector healing
        4. Log all recovery attempts for debugging

        SDK v2 Notes:
            - All browser operations are async
            - Uses context_id instead of page object
            - Browser methods: navigate, click, type_, etc.
        """
        step_name = step.name or f"Step {index + 1}"
        start_time = time.monotonic()

        self._log.debug("Executing step", step=step_name, action=step.action, context_id=context_id)

        # Check skip condition
        if step.skip_if and self._evaluate_condition(step.skip_if, test_result.variables):
            return StepResult(
                step_index=index,
                step_name=step.name,
                action=step.action,
                status=StepStatus.SKIPPED,
            )

        # Track expected URL from navigate actions
        if step.action == StepAction.NAVIGATE and step.url:
            self._current_expected_url = step.url
            self._log.debug("Updated expected URL", url=step.url)

        # Update expected URL from step metadata if provided
        step_expected_url = step.expected_url
        if step_expected_url:
            self._current_expected_url = step_expected_url

        method_name, args = self._transformer.transform(step)
        args = self._interpolate_args(args, test_result.variables)

        last_error: Exception | None = None
        retries = 0
        network_log: list[dict[str, Any]] | None = None
        url_recovery_attempted = False

        for attempt in range(step.retry_count + 1):
            try:
                # URL-aware pre-check: verify we're on the expected page
                # before attempting element interactions
                if (
                    self._enable_url_recovery
                    and step.action in self.INTERACTION_ACTIONS
                    and step.selector
                    and self._current_expected_url
                ):
                    await self._verify_or_recover_url(context_id, self._current_expected_url)

                # Smart pre-action waits for interaction actions
                if step.action in self.INTERACTION_ACTIONS and step.selector:
                    await self._ensure_element_ready(context_id, step.selector, step.timeout)

                # Execute the browser command
                result = await self._execute_browser_command(
                    context_id, method_name, args, step
                )

                # Smart post-action waits for navigation actions
                if self._wait_for_network_idle and step.action in self.NAVIGATION_ACTIONS:
                    await self._wait_for_stable_state(context_id)

                if step.capture_as:
                    test_result.variables[step.capture_as] = result

                duration = int((time.monotonic() - start_time) * 1000)

                return StepResult(
                    step_index=index,
                    step_name=step.name,
                    action=step.action,
                    status=StepStatus.PASSED,
                    duration_ms=duration,
                    result=result if self._transformer.should_capture_result(step) else None,
                    retries=retries,
                )

            except Exception as e:
                last_error = e
                retries = attempt

                # RECOVERY STRATEGY 1: URL-aware recovery
                # If element not found and we have an expected URL, try navigating there first
                if (
                    self._enable_url_recovery
                    and not url_recovery_attempted
                    and step.selector
                    and self._is_element_not_found_error(e)
                    and self._current_expected_url
                ):
                    url_recovery_attempted = True
                    recovery_success = await self._attempt_url_recovery(
                        context_id,
                        self._current_expected_url,
                        step_name,
                    )

                    if recovery_success:
                        # After URL recovery, retry the step immediately
                        self._log.info(
                            "URL recovery successful, retrying step",
                            step=step_name,
                            url=self._current_expected_url,
                        )
                        try:
                            if step.action in self.INTERACTION_ACTIONS:
                                await self._ensure_element_ready(context_id, step.selector, step.timeout)

                            result = await self._execute_browser_command(
                                context_id, method_name, args, step
                            )

                            if self._wait_for_network_idle and step.action in self.NAVIGATION_ACTIONS:
                                await self._wait_for_stable_state(context_id)

                            if step.capture_as:
                                test_result.variables[step.capture_as] = result

                            duration = int((time.monotonic() - start_time) * 1000)

                            return StepResult(
                                step_index=index,
                                step_name=step.name,
                                action=step.action,
                                status=StepStatus.HEALED,
                                duration_ms=duration,
                                result=result if self._transformer.should_capture_result(step) else None,
                                retries=retries,
                            )
                        except Exception as recovery_error:
                            last_error = recovery_error
                            self._log.warning(
                                "Step still failed after URL recovery",
                                step=step_name,
                                error=str(recovery_error),
                            )

                # RECOVERY STRATEGY 2: Selector self-healing
                # Attempt self-healing for element not found errors
                if step.selector and self._is_element_not_found_error(e):
                    healing_result = await self._healing_engine.heal_selector_async(
                        self._browser,
                        context_id,
                        step.selector,
                        action_context=step.action,
                        element_description=step.description,
                    )

                    if healing_result.success and healing_result.healed_selector:
                        args["selector"] = healing_result.healed_selector
                        try:
                            # Re-check element readiness with healed selector
                            if step.action in self.INTERACTION_ACTIONS:
                                await self._ensure_element_ready(
                                    context_id, healing_result.healed_selector, step.timeout
                                )

                            result = await self._execute_browser_command(
                                context_id, method_name, args, step
                            )

                            if self._wait_for_network_idle and step.action in self.NAVIGATION_ACTIONS:
                                await self._wait_for_stable_state(context_id)

                            if step.capture_as:
                                test_result.variables[step.capture_as] = result

                            duration = int((time.monotonic() - start_time) * 1000)

                            return StepResult(
                                step_index=index,
                                step_name=step.name,
                                action=step.action,
                                status=StepStatus.HEALED,
                                duration_ms=duration,
                                result=result if self._transformer.should_capture_result(step) else None,
                                healing_result=healing_result,
                                retries=retries,
                            )
                        except Exception as heal_error:
                            last_error = heal_error

                # Exponential backoff before retry
                if attempt < step.retry_count:
                    delay = self._calculate_backoff_delay(attempt, step.retry_delay_ms)
                    self._log.debug(
                        "Step failed, retrying with backoff",
                        step=step_name,
                        attempt=attempt + 1,
                        max_retries=step.retry_count,
                        delay_ms=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay / 1000)

        duration = int((time.monotonic() - start_time) * 1000)

        # Capture failure artifacts
        screenshot_path: str | None = None
        if self._screenshot_on_failure:
            screenshot_path = await self._capture_failure_screenshot(
                context_id, test_result.test_name, index, test_result.artifacts
            )

        if self._capture_network_on_failure:
            network_log = await self._capture_network_log(context_id, test_result)

        return StepResult(
            step_index=index,
            step_name=step.name,
            action=step.action,
            status=StepStatus.FAILED,
            duration_ms=duration,
            error=str(last_error) if last_error else "Unknown error",
            error_traceback=traceback.format_exc() if last_error else None,
            screenshot_path=screenshot_path,
            retries=retries,
            network_log=network_log,
        )

    async def _ensure_element_ready(
        self,
        context_id: str,
        selector: str,
        timeout: int | None = None,
    ) -> None:
        """
        Ensure element is visible and enabled before interaction.

        SDK v2 Notes:
            - Uses wait_for_selector, is_visible, is_enabled async methods
            - All methods require context_id parameter
        """
        effective_timeout = timeout or self._default_timeout

        # Wait for selector to exist
        try:
            await self._browser.wait_for_selector(
                context_id=context_id,
                selector=selector,
                timeout=effective_timeout,
            )
        except Exception as e:
            raise ElementNotFoundError(f"Element not found: {selector}") from e

        # Check visibility if pre-action check is enabled
        if self._pre_action_visibility_check:
            try:
                visibility_result = await self._browser.is_visible(
                    context_id=context_id,
                    selector=selector,
                )
                # SDK v2 returns {'success': True, ...} when visible
                if isinstance(visibility_result, dict):
                    is_visible = visibility_result.get("success", visibility_result.get("visible", False))
                else:
                    is_visible = bool(visibility_result)

                if not is_visible:
                    # Element exists but not visible - scroll to it
                    try:
                        await self._browser.scroll_to_element(
                            context_id=context_id,
                            selector=selector,
                        )
                        await asyncio.sleep(0.2)  # Brief wait for scroll
                    except Exception:
                        pass

                    # Re-check visibility
                    visibility_result = await self._browser.is_visible(
                        context_id=context_id,
                        selector=selector,
                    )
                    if isinstance(visibility_result, dict):
                        is_visible = visibility_result.get("success", visibility_result.get("visible", False))
                    else:
                        is_visible = bool(visibility_result)
                    if not is_visible:
                        raise ElementNotInteractableError(
                            f"Element not visible: {selector}"
                        )

                # Check if element is enabled (for interactive elements)
                try:
                    enabled_result = await self._browser.is_enabled(
                        context_id=context_id,
                        selector=selector,
                    )
                    # SDK v2 returns {'success': True, ...} when enabled
                    if isinstance(enabled_result, dict):
                        is_enabled = enabled_result.get("success", enabled_result.get("enabled", True))
                    else:
                        is_enabled = bool(enabled_result)
                    if not is_enabled:
                        raise ElementNotInteractableError(
                            f"Element not enabled: {selector}"
                        )
                except Exception:
                    # is_enabled may not be applicable for all elements
                    pass

            except ElementNotInteractableError:
                raise
            except Exception:
                # Visibility check failed but element exists, proceed anyway
                pass

    async def _wait_for_stable_state(self, context_id: str) -> None:
        """Wait for network idle and stable DOM state."""
        try:
            await self._browser.wait_for_network_idle(
                context_id=context_id,
                idle_time=500,
                timeout=self._network_idle_timeout,
            )
        except Exception as e:
            self._log.debug("Network idle wait timed out", error=str(e))

    async def _verify_or_recover_url(
        self,
        context_id: str,
        expected_url: str,
    ) -> None:
        """
        Verify browser is on expected URL, navigate if not.

        This is a proactive check before element interactions to ensure
        we're on the correct page. Does NOT raise on recovery failure -
        that will be caught when the element interaction fails.

        SDK v2 Notes:
            - Uses get_page_info to get current URL
            - Uses navigate method instead of goto
        """
        try:
            page_info = await self._browser.get_page_info(context_id=context_id)
            current_url = page_info.get("url") if isinstance(page_info, dict) else None
            if not current_url:
                return

            # Check if current URL matches expected (either full URL or path)
            expected_parsed = urlparse(expected_url)
            current_parsed = urlparse(current_url)

            # Compare paths (more flexible than full URL match)
            expected_path = expected_parsed.path.rstrip("/") or "/"
            current_path = current_parsed.path.rstrip("/") or "/"

            if current_path != expected_path:
                self._log.info(
                    "URL mismatch detected, navigating to expected page",
                    current=current_url,
                    expected=expected_url,
                    current_path=current_path,
                    expected_path=expected_path,
                )
                # Navigate to expected URL
                await self._browser.navigate(
                    context_id=context_id,
                    url=expected_url,
                    wait_until="domcontentloaded",
                    timeout=10000,
                )
                await self._wait_for_stable_state(context_id)

        except Exception as e:
            self._log.warning(
                "URL verification/recovery failed",
                expected_url=expected_url,
                error=str(e),
            )

    async def _attempt_url_recovery(
        self,
        context_id: str,
        expected_url: str,
        step_name: str,
    ) -> bool:
        """
        Attempt to recover by navigating to the expected URL.

        Called when an element is not found and we have an expected URL.
        This handles the case where the browser ended up on a different page
        (e.g., due to a redirect, timeout, or prior navigation failure).

        SDK v2 Notes:
            - Uses navigate method instead of goto
            - Uses get_page_info to verify URL

        Args:
            context_id: Browser context ID
            expected_url: URL where the element should exist
            step_name: Name of the step (for logging)

        Returns:
            True if recovery navigation succeeded, False otherwise
        """
        try:
            page_info = await self._browser.get_page_info(context_id=context_id)
            current_url = page_info.get("url", "unknown") if isinstance(page_info, dict) else "unknown"
            self._log.info(
                "Attempting URL recovery",
                step=step_name,
                current_url=current_url,
                target_url=expected_url,
            )

            # Navigate to expected URL
            await self._browser.navigate(
                context_id=context_id,
                url=expected_url,
                wait_until="domcontentloaded",
                timeout=10000,
            )

            # Wait for page to stabilize
            await self._wait_for_stable_state(context_id)

            # Verify navigation succeeded
            page_info = await self._browser.get_page_info(context_id=context_id)
            new_url = page_info.get("url", "") if isinstance(page_info, dict) else ""
            expected_path = urlparse(expected_url).path.rstrip("/") or "/"
            new_path = urlparse(new_url).path.rstrip("/") or "/"

            if new_path == expected_path:
                self._log.info(
                    "URL recovery succeeded",
                    step=step_name,
                    url=new_url,
                )
                return True
            else:
                self._log.warning(
                    "URL recovery navigated to unexpected page",
                    step=step_name,
                    expected_path=expected_path,
                    actual_path=new_path,
                )
                return False

        except Exception as e:
            self._log.error(
                "URL recovery failed",
                step=step_name,
                expected_url=expected_url,
                error=str(e),
            )
            return False

    def _calculate_backoff_delay(self, attempt: int, base_delay_ms: int) -> int:
        """Calculate exponential backoff delay with jitter."""
        import random
        # Exponential backoff: base * 2^attempt with max cap
        delay = min(base_delay_ms * (2 ** attempt), 30000)
        # Add 10% jitter
        jitter = random.randint(0, int(delay * 0.1))
        return delay + jitter

    async def _capture_failure_screenshot(
        self,
        context_id: str,
        test_name: str,
        step_index: int,
        artifacts: dict[str, str],
    ) -> str | None:
        """
        Capture screenshot on failure.

        SDK v2 Notes:
            - Uses screenshot method with context_id
            - SDK returns base64-encoded image data
            - We decode and save to the specified path
        """
        try:
            # Sanitize test name for filename
            safe_name = re.sub(r"[^\w\-_]", "_", test_name)
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            screenshot_path = Path(
                self._artifact_dir / f"failure_{safe_name}_{step_index}_{timestamp}.png"
            )

            # SDK returns base64-encoded image data (no path parameter)
            result = await self._browser.screenshot(context_id=context_id)

            # Extract base64 data from result
            if isinstance(result, dict):
                image_data = result.get("data") or result.get("image") or result.get("screenshot")
            else:
                image_data = result

            if image_data:
                # Decode base64 and save to file
                image_bytes = base64.b64decode(image_data)
                screenshot_path.write_bytes(image_bytes)
                screenshot_path_str = str(screenshot_path)
                artifacts[f"failure_screenshot_{step_index}"] = screenshot_path_str
                self._log.info("Captured failure screenshot", path=screenshot_path_str)
                return screenshot_path_str
            else:
                self._log.warning("Screenshot result contained no image data", result=result)
                return None
        except Exception as ss_error:
            self._log.warning("Failed to capture failure screenshot", error=str(ss_error))
            return None

    async def _capture_network_log(
        self,
        context_id: str,
        test_result: TestRunResult,
    ) -> list[dict[str, Any]] | None:
        """
        Capture network log for debugging.

        SDK v2 Notes:
            - Uses get_network_log with context_id
        """
        try:
            network_log_result = await self._browser.get_network_log(context_id=context_id)
            network_log = network_log_result.get("entries", []) if isinstance(network_log_result, dict) else []
            test_result.network_log = network_log
            self._log.debug("Captured network log", entries=len(network_log))
            return network_log
        except Exception as e:
            self._log.debug("Failed to capture network log", error=str(e))
            return None

    async def _execute_browser_command(
        self,
        context_id: str,
        method_name: str,
        args: dict[str, Any],
        step: TestStep,
    ) -> Any:
        """
        Execute a browser command.

        SDK v2 Notes:
            - All browser methods are async
            - Method names map to OwlBrowser methods
            - context_id is always passed
            - Method names: goto -> navigate, type -> type_
            - screenshot: SDK returns base64, we handle path/filename saving
        """
        if method_name.startswith("_assert"):
            return await self._execute_assertion(context_id, method_name, args, step)

        # Map old method names to SDK v2 method names
        method_map = {
            "goto": "navigate",
            "get_current_url": "get_page_info",  # Extract url from result
        }
        actual_method_name = method_map.get(method_name, method_name)

        method = getattr(self._browser, actual_method_name, None)
        if method is None:
            raise ValueError(f"Unknown browser method: {method_name} (mapped to: {actual_method_name})")

        # Special handling for screenshot: SDK doesn't support path parameter
        # It returns base64-encoded image data, we save it ourselves
        if actual_method_name == "screenshot":
            screenshot_path = args.pop("path", None)
            args_with_context = {"context_id": context_id, **args}
            result = await method(**args_with_context)

            # SDK returns base64-encoded image string
            if screenshot_path and result:
                await self._save_screenshot(result, screenshot_path)

            return result

        # Add context_id to args
        args_with_context = {"context_id": context_id, **args}
        result = await method(**args_with_context)

        # Special handling for get_page_info when called as get_current_url
        if method_name == "get_current_url" and isinstance(result, dict):
            return result.get("url")

        return result

    async def _save_screenshot(self, base64_data: str, filename: str) -> None:
        """
        Save a base64-encoded screenshot to a file.

        Args:
            base64_data: Base64-encoded image data from SDK
            filename: Filename (will be placed in artifacts directory)
        """
        try:
            # Ensure artifacts directory exists
            self._artifact_dir.mkdir(parents=True, exist_ok=True)

            # Construct full path
            screenshot_path = self._artifact_dir / filename

            # Decode and save
            image_bytes = base64.b64decode(base64_data)
            screenshot_path.write_bytes(image_bytes)

            self._log.info("Screenshot saved", path=str(screenshot_path))
        except Exception as e:
            self._log.warning("Failed to save screenshot", filename=filename, error=str(e))

    async def _execute_assertion(
        self,
        context_id: str,
        method_name: str,
        args: dict[str, Any],
        step: TestStep,
    ) -> bool:
        """
        Execute an assertion step.

        SDK v2 Notes:
            - AssertionEngine takes browser and context_id
            - All assertions are async
        """
        from autoqa.assertions.engine import AssertionEngine

        engine = AssertionEngine(self._browser, context_id)

        match method_name:
            case "_assert_element":
                return await engine.assert_element(args["config"])
            case "_assert_visual":
                return await engine.assert_visual(args["config"], self._artifact_dir)
            case "_assert_network":
                return await engine.assert_network(args["config"])
            case "_assert_url":
                return await engine.assert_url(
                    args["url_pattern"],
                    is_regex=args.get("is_regex", False),
                )
            case "_assert_custom":
                return await engine.assert_custom(args["config"])
            # ML-based assertions
            case "_assert_ml":
                return await engine.assert_ml(args["config"])
            case "_assert_ocr":
                return await engine.assert_ocr(args["config"])
            case "_assert_ui_state":
                return await engine.assert_ui_state(args["config"])
            case "_assert_color":
                return await engine.assert_color(args["config"])
            case "_assert_layout":
                return await engine.assert_layout(args["config"])
            case "_assert_icon":
                return await engine.assert_icon(args["config"])
            case "_assert_accessibility":
                return await engine.assert_accessibility(args["config"])
            # LLM-based assertions
            case "_assert_llm" | "_assert_semantic" | "_assert_content":
                return await self._execute_llm_assertion(context_id, method_name, args)
            case _:
                raise ValueError(f"Unknown assertion type: {method_name}")

    async def _run_hook(
        self,
        context_id: str,
        steps: list[TestStep],
        hook_name: str,
        result: TestRunResult,
    ) -> None:
        """Run a lifecycle hook."""
        for i, step in enumerate(steps):
            step_result = await self._execute_step(context_id, step, i, result)
            if step_result.status == StepStatus.FAILED:
                self._log.warning(
                    "Hook step failed",
                    hook=hook_name,
                    step=step.name or i,
                    error=step_result.error,
                )

    def _interpolate_args(
        self, args: dict[str, Any], variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Interpolate variables in arguments."""
        import re

        pattern = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

        def replace(value: Any) -> Any:
            if isinstance(value, str):
                def replacer(match: re.Match[str]) -> str:
                    var_name = match.group(1)
                    if var_name in variables:
                        return str(variables[var_name])
                    return match.group(0)

                return pattern.sub(replacer, value)
            elif isinstance(value, dict):
                return {k: replace(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace(v) for v in value]
            return value

        return {k: replace(v) for k, v in args.items()}

    def _evaluate_condition(self, condition: str, variables: dict[str, Any]) -> bool:
        """Evaluate a skip condition."""
        import re

        interpolated = condition
        pattern = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

        for match in pattern.finditer(condition):
            var_name = match.group(1)
            if var_name in variables:
                value = variables[var_name]
                if isinstance(value, str):
                    interpolated = interpolated.replace(match.group(0), f'"{value}"')
                else:
                    interpolated = interpolated.replace(match.group(0), str(value))

        try:
            return bool(eval(interpolated, {"__builtins__": {}}, {}))
        except Exception:
            return False

    def _is_element_not_found_error(self, error: Exception) -> bool:
        """Check if error is an element not found error."""
        error_str = str(error).lower()
        indicators = [
            "element not found",
            "no such element",
            "unable to locate",
            "could not find",
            "selector did not match",
        ]
        return any(indicator in error_str for indicator in indicators)

    async def _execute_llm_assertion(
        self,
        context_id: str,
        method_name: str,
        args: dict[str, Any],
    ) -> bool:
        """
        Execute an LLM-based assertion.

        SDK v2 Notes:
            - Already in async context, no need for asyncio.run
            - LLMAssertionEngine takes browser and context_id
        """
        from autoqa.llm.assertions import LLMAssertionEngine, LLMAssertionError

        try:
            engine = LLMAssertionEngine(self._browser, context_id)

            match method_name:
                case "_assert_llm":
                    config = args["config"]
                    result = await engine.assert_semantic(
                        assertion=config.assertion,
                        context=config.context,
                        min_confidence=config.min_confidence,
                        message=config.message,
                    )
                    return result.passed

                case "_assert_semantic":
                    config = args["config"]
                    result = await engine.assert_state(
                        expected_state=config.expected_state,
                        indicators=config.indicators,
                        min_confidence=config.min_confidence,
                        message=config.message,
                    )
                    return result.passed

                case "_assert_content":
                    config = args["config"]
                    result = await engine.assert_content_valid(
                        content_type=config.content_type,
                        expected_patterns=config.expected_patterns,
                        selector=config.selector,
                        min_confidence=config.min_confidence,
                        message=config.message,
                    )
                    return result.passed

                case _:
                    raise ValueError(f"Unknown LLM assertion type: {method_name}")

        except LLMAssertionError:
            raise
        except Exception as e:
            self._log.warning(
                "LLM assertion execution failed, using fallback",
                error=str(e),
            )
            # Return True to allow fallback behavior (assertion passes with warning)
            return True
