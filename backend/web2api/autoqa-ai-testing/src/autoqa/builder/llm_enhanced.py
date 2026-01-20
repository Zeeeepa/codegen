"""
LLM-enhanced test builder for generating intelligent test specifications.

Extends AutoTestBuilder with LLM capabilities for:
- Generating meaningful test names and descriptions
- Creating semantic step descriptions
- Suggesting intelligent assertions
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import structlog

from autoqa.builder.test_builder import (
    AutoTestBuilder,
    BuilderConfig,
    ElementInfo,
    PageAnalysis,
)
from autoqa.llm.config import LLMConfig, ToolName, load_llm_config
from autoqa.llm.service import LLMService, get_llm_service

if TYPE_CHECKING:
    from owl_browser import Browser

logger = structlog.get_logger(__name__)


class LLMEnhancedTestBuilder(AutoTestBuilder):
    """
    Test builder with LLM enhancements for intelligent test generation.

    When LLM is enabled, provides:
    - Meaningful test names based on page content
    - Descriptive step names and descriptions
    - Intelligent assertion suggestions

    Falls back to base behavior when LLM is disabled.
    """

    def __init__(
        self,
        browser: Browser,
        config: BuilderConfig,
        llm_config: LLMConfig | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        super().__init__(browser, config)
        self._llm_config = llm_config or load_llm_config()
        self._llm_service = llm_service or get_llm_service(self._llm_config)
        self._log = logger.bind(
            component="llm_enhanced_test_builder",
            llm_enabled=self._llm_service.is_enabled(ToolName.TEST_BUILDER),
        )

    @property
    def llm_enabled(self) -> bool:
        """Check if LLM is enabled for test builder."""
        return self._llm_service.is_enabled(ToolName.TEST_BUILDER)

    def _run_async(self, coro: Any) -> Any:
        """Run an async coroutine in sync context."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, need to run in executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result(timeout=30)
            else:
                return asyncio.run(coro)
        except Exception as e:
            self._log.debug("Async execution failed", error=str(e))
            return None

    def _generate_yaml_spec(self) -> str:
        """Generate complete YAML test specification with LLM enhancements."""
        if not self._page_analyses:
            return self._generate_empty_spec()

        first_analysis = self._page_analyses[0]

        # Generate test name with LLM
        test_name = self._generate_test_name_llm(first_analysis)

        # Generate description with LLM
        description = self._generate_description_llm()

        import yaml
        from datetime import UTC, datetime

        spec: dict[str, Any] = {
            "name": test_name,
            "description": description,
            "metadata": {
                "tags": ["auto-generated", "builder", "llm-enhanced"] if self.llm_enabled else ["auto-generated", "builder"],
                "priority": "medium",
                "timeout_ms": 60000,
            },
            "variables": {
                "base_url": self._extract_base_url(self._config.url),
            },
            "steps": [],
        }

        # Add initial navigation step with LLM-enhanced name
        nav_step_name = self._generate_step_name_llm(
            action="navigate",
            selector=None,
            text=None,
            context=f"Navigating to {self._config.url}",
            fallback="Navigate to starting page",
        )
        spec["steps"].append({
            "name": nav_step_name,
            "action": "navigate",
            "url": self._config.url,
            "wait_until": "domcontentloaded",
            "timeout": 10000,
        })

        # Add wait for page load
        spec["steps"].append({
            "name": "Wait for page to load",
            "action": "wait_for_network_idle",
            "timeout": 5000,
        })

        # Add login steps if credentials were provided
        if self._config.username and self._config.password:
            login_steps = self._generate_login_steps_llm()
            spec["steps"].extend(login_steps)

        # Generate test steps for each analyzed page
        for analysis in self._page_analyses:
            page_steps = self._generate_page_steps_llm(analysis)
            spec["steps"].extend(page_steps)

        # Add LLM-suggested assertions if enabled
        if self.llm_enabled:
            suggested_assertions = self._get_llm_assertion_suggestions(first_analysis)
            spec["steps"].extend(suggested_assertions)

        # Add final assertions
        final_assertions = self._generate_final_assertions()
        spec["steps"].extend(final_assertions)

        # Convert to YAML
        yaml_content = yaml.dump(
            spec,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=100,
        )

        # Add header comment
        llm_note = " (LLM-enhanced)" if self.llm_enabled else ""
        header = f"""# Auto-generated test specification{llm_note}
# Generated: {datetime.now(UTC).isoformat()}
# URL: {self._config.url}
# Pages analyzed: {len(self._page_analyses)}
# Total elements discovered: {sum(len(p.elements) for p in self._page_analyses)}
#
# Review and customize before running in production.
# Semantic selectors are used for owl-browser compatibility.

"""
        return header + yaml_content

    def _generate_test_name_llm(self, analysis: PageAnalysis) -> str:
        """Generate test name using LLM or fallback."""
        fallback = f"Auto-generated test for {analysis.title}"

        if not self.llm_enabled:
            return fallback

        # Prepare elements summary
        element_types = {}
        for el in analysis.elements[:30]:
            elem_type = el.element_type.value
            element_types[elem_type] = element_types.get(elem_type, 0) + 1

        elements_summary = ", ".join(f"{count} {t}(s)" for t, count in element_types.items())

        result = self._run_async(
            self._llm_service.generate_test_name(
                url=analysis.url,
                page_title=analysis.title,
                elements_summary=elements_summary,
                has_login=analysis.has_login_form,
                form_count=len(analysis.forms),
                fallback=fallback,
            )
        )

        return result or fallback

    def _generate_description_llm(self) -> str:
        """Generate test description using LLM or fallback."""
        fallback = super()._generate_description()

        if not self.llm_enabled or not self._page_analyses:
            return fallback

        first_analysis = self._page_analyses[0]

        # Prepare summaries
        element_types = {}
        for analysis in self._page_analyses:
            for el in analysis.elements:
                elem_type = el.element_type.value
                element_types[elem_type] = element_types.get(elem_type, 0) + 1

        elements_summary = ", ".join(f"{count} {t}(s)" for t, count in element_types.items())

        forms_summary = f"{sum(len(a.forms) for a in self._page_analyses)} form(s)"
        total_steps = len(self._page_analyses) * 5  # Rough estimate

        result = self._run_async(
            self._llm_service.generate_test_description(
                test_name=f"Test for {first_analysis.title}",
                url=first_analysis.url,
                page_title=first_analysis.title,
                elements_summary=elements_summary,
                forms_summary=forms_summary,
                steps_count=total_steps,
                fallback=fallback,
            )
        )

        return result or fallback

    def _generate_step_name_llm(
        self,
        action: str,
        selector: str | None = None,
        text: str | None = None,
        element_description: str | None = None,
        context: str | None = None,
        fallback: str | None = None,
    ) -> str:
        """Generate step name using LLM or fallback."""
        default_fallback = fallback or f"{action.title()}: {selector or text or 'action'}"

        if not self.llm_enabled:
            return default_fallback

        result = self._run_async(
            self._llm_service.generate_step_name(
                action=action,
                selector=selector,
                text=text,
                element_description=element_description,
                context=context,
                fallback=default_fallback,
            )
        )

        return result or default_fallback

    def _generate_login_steps_llm(self) -> list[dict[str, Any]]:
        """Generate login steps with LLM-enhanced names."""
        # Get base login steps
        base_steps = super()._generate_login_steps()

        if not self.llm_enabled or not base_steps:
            return base_steps

        # Enhance step names
        enhanced_steps = []
        for step in base_steps:
            new_name = self._generate_step_name_llm(
                action=step.get("action", ""),
                selector=step.get("selector"),
                text=step.get("text"),
                context="Login flow step",
                fallback=step.get("name"),
            )
            enhanced_step = {**step, "name": new_name}
            enhanced_steps.append(enhanced_step)

        return enhanced_steps

    def _generate_page_steps_llm(self, analysis: PageAnalysis) -> list[dict[str, Any]]:
        """Generate page steps with LLM-enhanced names."""
        # Get base page steps
        base_steps = super()._generate_page_steps(analysis)

        if not self.llm_enabled:
            return base_steps

        # Enhance step names
        enhanced_steps = []
        for step in base_steps:
            action = step.get("action", "")
            selector = step.get("selector")
            text = step.get("text")

            # Get element description from analysis if available
            element_desc = None
            if selector:
                for el in analysis.elements:
                    if el.selector == selector:
                        element_desc = el.semantic_description
                        break

            new_name = self._generate_step_name_llm(
                action=action,
                selector=selector,
                text=text,
                element_description=element_desc,
                context=f"Testing page: {analysis.title}",
                fallback=step.get("name"),
            )
            enhanced_step = {**step, "name": new_name}
            enhanced_steps.append(enhanced_step)

        return enhanced_steps

    def _get_llm_assertion_suggestions(
        self,
        analysis: PageAnalysis,
    ) -> list[dict[str, Any]]:
        """Get LLM-suggested assertions for the page."""
        if not self.llm_enabled:
            return []

        # Prepare element data for LLM
        elements_data = [
            {
                "type": el.element_type.value,
                "selector": el.selector,
                "description": el.semantic_description,
                "text": el.text_content,
            }
            for el in analysis.elements[:20]
        ]

        forms_data = [
            {
                "id": f.get("id"),
                "name": f.get("name"),
                "input_count": f.get("input_count"),
            }
            for f in analysis.forms
        ]

        suggestions = self._run_async(
            self._llm_service.suggest_assertions(
                url=analysis.url,
                page_title=analysis.title,
                elements=elements_data,
                forms=forms_data,
                test_purpose="Verify page functionality and content",
            )
        )

        if not suggestions:
            return []

        # Convert LLM suggestions to test steps
        steps: list[dict[str, Any]] = []
        for suggestion in suggestions[:5]:  # Limit to 5 suggestions
            assertion_type = suggestion.get("type", "visibility")
            selector = suggestion.get("selector", "body")
            operator = suggestion.get("operator", "is_visible")
            expected = suggestion.get("expected")
            message = suggestion.get("message", "LLM-suggested assertion")

            step: dict[str, Any] = {
                "name": f"LLM Suggestion: {message[:50]}",
                "action": "assert",
                "assertion": {
                    "selector": selector,
                    "operator": operator,
                    "message": message,
                },
                "continue_on_failure": True,
            }

            if expected is not None:
                step["assertion"]["expected"] = expected

            steps.append(step)

        return steps


def create_enhanced_builder(
    browser: Browser,
    config: BuilderConfig,
    llm_config: LLMConfig | None = None,
) -> AutoTestBuilder:
    """
    Create a test builder, automatically using LLM enhancement if available.

    Args:
        browser: Browser instance
        config: Builder configuration
        llm_config: Optional LLM configuration

    Returns:
        LLMEnhancedTestBuilder if LLM is enabled, else AutoTestBuilder
    """
    effective_config = llm_config or load_llm_config()

    if effective_config.is_tool_enabled(ToolName.TEST_BUILDER):
        return LLMEnhancedTestBuilder(browser, config, effective_config)

    return AutoTestBuilder(browser, config)
