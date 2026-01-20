"""
Test Builder Orchestrator.

Main orchestration layer that coordinates all analyzers, crawlers,
detectors, and generators to produce comprehensive test suites.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from autoqa.builder.analyzer import (
    PageAnalyzer,
    AnalyzerConfig,
    ElementClassifier,
    ClassifierConfig,
    VisualAnalyzer,
    VisualConfig,
)
from autoqa.builder.crawler import (
    IntelligentCrawler,
    CrawlConfig,
    StateManager,
    StateConfig,
)
from autoqa.builder.discovery import (
    FlowDetector,
    FlowConfig,
    APIDetector,
    APIConfig,
    FormAnalyzer,
    FormConfig,
)
from autoqa.builder.generator import (
    TestStrategy,
    StrategyConfig,
    AssertionGenerator,
    AssertionConfig,
    YAMLBuilder,
    BuilderConfig,
    YAMLTestSpec,
)


if TYPE_CHECKING:
    from owl_browser import Browser as BrowserController, BrowserContext


logger = structlog.get_logger(__name__)


class BuildMode(str, Enum):
    """Test building modes."""
    
    QUICK = "quick"  # Fast scan, basic tests
    STANDARD = "standard"  # Balanced scan, comprehensive tests
    DEEP = "deep"  # Full crawl, exhaustive tests
    TARGETED = "targeted"  # Focus on specific flows/pages


class TestScope(str, Enum):
    """Scope of test generation."""
    
    FULL = "full"  # All test types
    FUNCTIONAL = "functional"  # Functional tests only
    VISUAL = "visual"  # Visual/UI tests only
    ACCESSIBILITY = "accessibility"  # A11y tests only
    PERFORMANCE = "performance"  # Performance tests only
    API = "api"  # API tests only


@dataclass
class OrchestratorConfig:
    """Configuration for the test builder orchestrator."""
    
    # Build settings
    mode: BuildMode = BuildMode.STANDARD
    scope: TestScope = TestScope.FULL
    max_pages: int = 50
    max_depth: int = 3
    timeout_per_page: int = 30000
    
    # Feature toggles
    enable_visual_analysis: bool = True
    enable_accessibility_checks: bool = True
    enable_api_detection: bool = True
    enable_form_analysis: bool = True
    enable_flow_detection: bool = True
    enable_ml_classification: bool = True
    
    # Output settings
    output_dir: Path = field(default_factory=lambda: Path("./tests/generated"))
    yaml_file_name: str = "test_suite.yaml"
    generate_report: bool = True
    
    # Parallelization
    parallel_analysis: bool = True
    max_concurrent_pages: int = 5
    
    # Authentication
    auth_config: dict[str, Any] | None = None
    
    # Filtering
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    
    # Priority configuration
    critical_flows: list[str] = field(
        default_factory=lambda: ["login", "checkout", "registration", "payment"]
    )
    
    # Component configs (optional overrides)
    analyzer_config: AnalyzerConfig | None = None
    classifier_config: ClassifierConfig | None = None
    visual_config: VisualConfig | None = None
    crawl_config: CrawlConfig | None = None
    state_config: StateConfig | None = None
    flow_config: FlowConfig | None = None
    api_config: APIConfig | None = None
    form_config: FormConfig | None = None
    strategy_config: StrategyConfig | None = None
    assertion_config: AssertionConfig | None = None
    builder_config: BuilderConfig | None = None


@dataclass
class BuildResult:
    """Result of test building process."""
    
    success: bool
    tests: list[YAMLTestSpec]
    yaml_content: str
    output_path: Path | None
    
    # Statistics
    pages_analyzed: int = 0
    flows_detected: int = 0
    forms_analyzed: int = 0
    api_endpoints_found: int = 0
    assertions_generated: int = 0
    
    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    duration_seconds: float = 0.0
    
    # Errors
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    # Detailed results
    page_results: list[dict[str, Any]] = field(default_factory=list)
    flow_results: list[dict[str, Any]] = field(default_factory=list)
    api_results: list[dict[str, Any]] = field(default_factory=list)
    
    def to_report(self) -> dict[str, Any]:
        """Generate report dictionary."""
        return {
            "success": self.success,
            "summary": {
                "tests_generated": len(self.tests),
                "pages_analyzed": self.pages_analyzed,
                "flows_detected": self.flows_detected,
                "forms_analyzed": self.forms_analyzed,
                "api_endpoints_found": self.api_endpoints_found,
                "assertions_generated": self.assertions_generated,
            },
            "timing": {
                "started_at": self.started_at.isoformat(),
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "duration_seconds": self.duration_seconds,
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "output_path": str(self.output_path) if self.output_path else None,
        }


class TestBuilderOrchestrator:
    """
    Main orchestrator for intelligent test building.
    
    Coordinates all analysis, detection, and generation components
    to produce comprehensive, high-quality test suites.
    """
    
    def __init__(
        self,
        browser: "BrowserController",
        config: OrchestratorConfig | None = None,
        llm_service: Any | None = None,
    ) -> None:
        """
        Initialize orchestrator with browser and configuration.
        
        Args:
            browser: Browser controller for page interactions
            config: Orchestrator configuration
            llm_service: Optional LLM service for enhanced analysis
        """
        self.browser = browser
        self.config = config or OrchestratorConfig()
        self.llm_service = llm_service

        # Page context for browser interactions (created per build)
        self._page: "BrowserContext | None" = None

        # Initialize components
        self._init_components()

        # State tracking
        self._analyzed_urls: set[str] = set()
        self._detected_flows: list[Any] = []
        self._detected_apis: list[Any] = []
        self._analyzed_forms: list[Any] = []
        self._all_assertions: list[Any] = []
    
    def _init_components(self) -> None:
        """Initialize all analysis and generation components."""
        # Analyzers
        self.page_analyzer = PageAnalyzer(
            config=self.config.analyzer_config or AnalyzerConfig()
        )
        self.element_classifier = ElementClassifier(
            config=self.config.classifier_config or ClassifierConfig()
        )
        self.visual_analyzer = VisualAnalyzer(
            config=self.config.visual_config or VisualConfig()
        )
        
        # Crawlers
        self.crawler = IntelligentCrawler(
            browser=self.browser,
            config=self.config.crawl_config or CrawlConfig(
                max_pages=self.config.max_pages,
                max_depth=self.config.max_depth,
            ),
        )
        self.state_manager = StateManager(
            config=self.config.state_config or StateConfig()
        )
        
        # Discovery
        self.flow_detector = FlowDetector(
            config=self.config.flow_config or FlowConfig()
        )
        self.api_detector = APIDetector(
            config=self.config.api_config or APIConfig(),
        )
        self.form_analyzer = FormAnalyzer(
            config=self.config.form_config or FormConfig()
        )
        
        # Generators
        self.test_strategy = TestStrategy(
            config=self.config.strategy_config or StrategyConfig()
        )
        self.assertion_generator = AssertionGenerator(
            config=self.config.assertion_config or AssertionConfig()
        )
        self.yaml_builder = YAMLBuilder(
            config=self.config.builder_config or BuilderConfig()
        )
    
    async def build(
        self,
        start_url: str,
        target_flows: list[str] | None = None,
    ) -> BuildResult:
        """
        Execute full test building process.
        
        Args:
            start_url: Starting URL for analysis
            target_flows: Optional list of specific flows to target
            
        Returns:
            Complete build result with generated tests
        """
        logger.info(
            "starting_test_build",
            url=start_url,
            mode=self.config.mode.value,
            scope=self.config.scope.value,
        )

        result = BuildResult(success=False, tests=[], yaml_content="", output_path=None)

        # Create page context for browser interactions
        self._page = self.browser.new_page()

        try:
            # Phase 1: Crawl and discover pages
            pages = await self._crawl_phase(start_url, result)
            
            # Phase 2: Analyze pages
            await self._analysis_phase(pages, result)
            
            # Phase 3: Detect flows and APIs
            await self._discovery_phase(pages, target_flows, result)
            
            # Phase 4: Generate test strategy
            test_plan = await self._strategy_phase(result)
            
            # Phase 5: Generate assertions
            await self._assertion_phase(test_plan, result)
            
            # Phase 6: Build YAML tests
            await self._generation_phase(test_plan, result)
            
            # Phase 7: Output and finalize
            await self._output_phase(result)
            
            result.success = True
            
        except Exception as e:
            logger.exception("build_failed", error=str(e))
            result.errors.append(f"Build failed: {str(e)}")
        
        finally:
            # Clean up page context
            if self._page:
                try:
                    self._page.close()
                except Exception:
                    pass
                self._page = None

            result.completed_at = datetime.now()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()

        logger.info(
            "build_completed",
            success=result.success,
            tests_generated=len(result.tests),
            duration=result.duration_seconds,
        )
        
        return result
    
    async def build_from_page(
        self,
        url: str,
        html: str,
        screenshot: bytes | None = None,
    ) -> BuildResult:
        """
        Build tests from a single page without crawling.
        
        Args:
            url: Page URL
            html: Page HTML content
            screenshot: Optional page screenshot
            
        Returns:
            Build result with generated tests
        """
        logger.info("building_from_page", url=url)
        
        result = BuildResult(success=False, tests=[], yaml_content="", output_path=None)
        
        try:
            # Analyze page
            page_analysis = await self.page_analyzer.analyze(html, url)
            result.pages_analyzed = 1
            
            # Classify elements
            if self.config.enable_ml_classification:
                for element in page_analysis.interactive_elements:
                    element_dict = {
                        "tag": element.tag,
                        "attributes": element.attributes,
                        "text": element.text,
                        "selector": element.selector,
                    }
                    classification = await self.element_classifier.classify(element_dict)
                    element.metadata["classification"] = classification
            
            # Visual analysis
            if self.config.enable_visual_analysis and screenshot:
                visual_result = await self.visual_analyzer.analyze(screenshot, html)
                result.page_results.append({
                    "url": url,
                    "analysis": page_analysis,
                    "visual": visual_result,
                })
            else:
                result.page_results.append({
                    "url": url,
                    "analysis": page_analysis,
                })
            
            # Analyze forms
            if self.config.enable_form_analysis:
                forms = await self.form_analyzer.analyze(html)
                self._analyzed_forms.extend(forms)
                result.forms_analyzed = len(forms)
            
            # Detect flows on single page
            if self.config.enable_flow_detection:
                flows = await self.flow_detector.detect_from_page(
                    html,
                    url,
                    page_analysis.interactive_elements,
                )
                self._detected_flows.extend(flows)
                result.flows_detected = len(flows)
            
            # Generate assertions
            elements_data = [
                {
                    "selector": e.selector,
                    "tag": e.tag,
                    "type": e.element_type,
                    "text": e.text,
                    "attributes": e.attributes,
                }
                for e in page_analysis.interactive_elements
            ]
            
            assertions = await self.assertion_generator.generate_for_page(
                url=url,
                elements=elements_data,
                visual_data=result.page_results[0].get("visual") if result.page_results else None,
            )
            self._all_assertions.extend(assertions)
            result.assertions_generated = len(assertions)
            
            # Build YAML test
            page_test = await self.yaml_builder.build_from_page(
                url=url,
                elements=elements_data,
                assertions=assertions,
            )
            result.tests.append(page_test)
            
            # Build form tests
            for form in self._analyzed_forms:
                form_tests = await self.yaml_builder.build_from_form(
                    form=form,
                    assertions=assertions,
                )
                result.tests.extend(form_tests)
            
            # Build flow tests
            for flow_obj in self._detected_flows:
                flow_test = await self.yaml_builder.build_from_flow(
                    flow=flow_obj,
                    assertions=assertions,
                )
                result.tests.append(flow_test)
            
            # Generate YAML content
            result.yaml_content = self.yaml_builder.generate_yaml(result.tests)
            
            # Write output
            if self.config.output_dir:
                result.output_path = self.yaml_builder.write_yaml(
                    result.tests,
                    self.config.output_dir / self.config.yaml_file_name,
                )
            
            result.success = True
            
        except Exception as e:
            logger.exception("build_from_page_failed", error=str(e))
            result.errors.append(f"Build failed: {str(e)}")
        
        finally:
            result.completed_at = datetime.now()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()
        
        return result
    
    async def _crawl_phase(
        self,
        start_url: str,
        result: BuildResult,
    ) -> list[dict[str, Any]]:
        """Execute crawl phase to discover pages."""
        logger.info("crawl_phase_start", url=start_url)
        
        pages: list[dict[str, Any]] = []
        
        if self.config.mode == BuildMode.QUICK:
            # Quick mode: just analyze start URL
            pages.append({
                "url": start_url,
                "depth": 0,
                "html": None,  # Will be fetched during analysis
            })
            
        elif self.config.mode == BuildMode.TARGETED:
            # Targeted mode: start URL + specific pages
            pages.append({"url": start_url, "depth": 0, "html": None})
            # Additional targeted pages would be added by caller
            
        else:
            # Standard/Deep mode: full crawl
            try:
                # Navigate to start URL using page context
                self._page.goto(start_url)
                html = self._page.get_html()

                # Capture initial state
                await self.state_manager.capture_state(
                    self._page,
                    start_url,
                    html,
                )
                
                # Execute crawl
                crawl_result = await self.crawler.crawl(start_url)

                for page_info in crawl_result.pages_crawled:
                    pages.append({
                        "url": page_info.url,
                        "depth": page_info.depth,
                        "html": page_info.html_content,
                    })
                    self._analyzed_urls.add(page_info.url)
                
                result.page_results.extend([
                    {"url": p["url"], "depth": p["depth"]}
                    for p in pages
                ])
                
            except Exception as e:
                logger.warning("crawl_error", error=str(e))
                result.warnings.append(f"Crawl warning: {str(e)}")
                # Fall back to single page
                pages.append({"url": start_url, "depth": 0, "html": None})
        
        result.pages_analyzed = len(pages)
        logger.info("crawl_phase_complete", pages_discovered=len(pages))
        
        return pages
    
    async def _analysis_phase(
        self,
        pages: list[dict[str, Any]],
        result: BuildResult,
    ) -> None:
        """Execute analysis phase on discovered pages."""
        logger.info("analysis_phase_start", page_count=len(pages))
        
        async def analyze_page(page: dict[str, Any]) -> dict[str, Any]:
            """Analyze a single page."""
            url = page["url"]
            html = page.get("html")
            
            try:
                # Fetch HTML if not available
                if not html:
                    self._page.goto(url)
                    html = self._page.get_html()
                
                # Page analysis
                page_analysis = await self.page_analyzer.analyze(html, url)
                
                # Element classification
                if self.config.enable_ml_classification:
                    for element in page_analysis.interactive_elements[:50]:  # Limit
                        element_dict = {
                            "tag": element.tag,
                            "attributes": element.attributes,
                            "text": element.text,
                            "selector": element.selector,
                        }
                        classification = await self.element_classifier.classify(
                            element_dict
                        )
                        element.metadata["classification"] = classification
                
                # Visual analysis
                visual_result = None
                if self.config.enable_visual_analysis:
                    try:
                        screenshot = await self.browser.screenshot()
                        visual_result = await self.visual_analyzer.analyze(
                            screenshot, html
                        )
                    except Exception as ve:
                        logger.warning("visual_analysis_error", url=url, error=str(ve))
                
                return {
                    "url": url,
                    "analysis": page_analysis,
                    "visual": visual_result,
                    "success": True,
                }
                
            except Exception as e:
                logger.warning("page_analysis_error", url=url, error=str(e))
                return {"url": url, "success": False, "error": str(e)}
        
        # Execute analysis
        if self.config.parallel_analysis:
            semaphore = asyncio.Semaphore(self.config.max_concurrent_pages)
            
            async def bounded_analyze(page: dict[str, Any]) -> dict[str, Any]:
                async with semaphore:
                    return await analyze_page(page)
            
            analysis_results = await asyncio.gather(
                *[bounded_analyze(p) for p in pages],
                return_exceptions=True,
            )
        else:
            analysis_results = []
            for page in pages:
                page_result = await analyze_page(page)
                analysis_results.append(page_result)
        
        # Process results
        for page_result in analysis_results:
            if isinstance(page_result, Exception):
                result.warnings.append(f"Analysis error: {str(page_result)}")
                continue
            
            if page_result.get("success"):
                result.page_results.append(page_result)
            else:
                result.warnings.append(
                    f"Failed to analyze {page_result.get('url')}: {page_result.get('error')}"
                )
        
        logger.info(
            "analysis_phase_complete",
            successful=len([r for r in result.page_results if r.get("success", True)]),
        )
    
    async def _discovery_phase(
        self,
        pages: list[dict[str, Any]],
        target_flows: list[str] | None,
        result: BuildResult,
    ) -> None:
        """Execute discovery phase for flows, APIs, and forms."""
        logger.info("discovery_phase_start")
        
        # Flow detection
        if self.config.enable_flow_detection:
            try:
                for page_result in result.page_results:
                    if not page_result.get("analysis"):
                        continue
                    
                    analysis = page_result["analysis"]
                    url = page_result["url"]
                    
                    # Get HTML for flow detection
                    if hasattr(analysis, "raw_html"):
                        html = analysis.raw_html
                    else:
                        # Fetch if needed
                        self._page.goto(url)
                        html = self._page.get_html()
                    
                    flows = await self.flow_detector.detect_from_page(
                        html,
                        url,
                        analysis.interactive_elements if hasattr(analysis, "interactive_elements") else [],
                    )
                    
                    # Filter by target flows if specified
                    if target_flows:
                        flows = [
                            f for f in flows
                            if any(tf.lower() in f.flow_type.value.lower() for tf in target_flows)
                        ]
                    
                    self._detected_flows.extend(flows)
                    result.flow_results.extend([
                        {
                            "type": f.flow_type.value,
                            "url": url,
                            "steps": len(f.steps),
                            "confidence": f.confidence,
                        }
                        for f in flows
                    ])
                
                result.flows_detected = len(self._detected_flows)
                
            except Exception as e:
                logger.warning("flow_detection_error", error=str(e))
                result.warnings.append(f"Flow detection warning: {str(e)}")
        
        # API detection
        if self.config.enable_api_detection:
            try:
                # Start monitoring
                await self.api_detector.start_monitoring()
                
                # Re-navigate to pages to capture API calls
                for page_result in result.page_results[:10]:  # Limit
                    url = page_result["url"]
                    try:
                        self._page.goto(url)
                        await asyncio.sleep(1)  # Wait for API calls
                    except Exception:
                        continue
                
                # Stop and get results
                apis = await self.api_detector.stop_monitoring()
                self._detected_apis.extend(apis)
                
                result.api_results.extend([
                    {
                        "url": api.url,
                        "method": api.method.value if hasattr(api.method, "value") else api.method,
                        "type": api.api_type.value if hasattr(api.api_type, "value") else api.api_type,
                    }
                    for api in apis
                ])
                result.api_endpoints_found = len(apis)
                
            except Exception as e:
                logger.warning("api_detection_error", error=str(e))
                result.warnings.append(f"API detection warning: {str(e)}")
        
        # Form analysis
        if self.config.enable_form_analysis:
            try:
                for page_result in result.page_results:
                    analysis = page_result.get("analysis")
                    if not analysis:
                        continue
                    
                    # Get HTML
                    url = page_result["url"]
                    self._page.goto(url)
                    html = self._page.get_html()
                    
                    forms = await self.form_analyzer.analyze(html)
                    self._analyzed_forms.extend(forms)
                
                result.forms_analyzed = len(self._analyzed_forms)
                
            except Exception as e:
                logger.warning("form_analysis_error", error=str(e))
                result.warnings.append(f"Form analysis warning: {str(e)}")
        
        logger.info(
            "discovery_phase_complete",
            flows=result.flows_detected,
            apis=result.api_endpoints_found,
            forms=result.forms_analyzed,
        )
    
    async def _strategy_phase(self, result: BuildResult) -> Any:
        """Generate test strategy and plan."""
        logger.info("strategy_phase_start")
        
        # Collect all analysis data
        analysis_data = {
            "pages": result.page_results,
            "flows": self._detected_flows,
            "apis": self._detected_apis,
            "forms": self._analyzed_forms,
            "critical_flows": self.config.critical_flows,
        }
        
        # Generate test plan
        test_plan = await self.test_strategy.generate_plan(
            analysis_data,
            scope=self.config.scope.value,
        )
        
        logger.info(
            "strategy_phase_complete",
            test_cases=len(test_plan.test_cases) if hasattr(test_plan, "test_cases") else 0,
        )
        
        return test_plan
    
    async def _assertion_phase(self, test_plan: Any, result: BuildResult) -> None:
        """Generate assertions for test plan."""
        logger.info("assertion_phase_start")
        
        # Generate assertions for each page
        for page_result in result.page_results:
            analysis = page_result.get("analysis")
            visual = page_result.get("visual")
            url = page_result.get("url", "")
            
            if not analysis:
                continue
            
            # Convert elements to dict format
            elements: list[dict[str, Any]] = []
            if hasattr(analysis, "interactive_elements"):
                elements = [
                    {
                        "selector": e.selector,
                        "tag": e.tag,
                        "type": e.element_type,
                        "text": e.text,
                        "attributes": e.attributes,
                    }
                    for e in analysis.interactive_elements
                ]
            
            assertions = await self.assertion_generator.generate_for_page(
                url=url,
                elements=elements,
                visual_data=visual,
            )
            self._all_assertions.extend(assertions)
        
        # Generate assertions for flows
        for flow in self._detected_flows:
            flow_assertions = await self.assertion_generator.generate_for_flow(flow)
            self._all_assertions.extend(flow_assertions)
        
        # Generate assertions for forms
        for form in self._analyzed_forms:
            form_assertions = await self.assertion_generator.generate_for_form(form)
            self._all_assertions.extend(form_assertions)
        
        result.assertions_generated = len(self._all_assertions)
        
        logger.info(
            "assertion_phase_complete",
            assertions=result.assertions_generated,
        )
    
    async def _generation_phase(self, test_plan: Any, result: BuildResult) -> None:
        """Generate YAML test specifications."""
        logger.info("generation_phase_start")
        
        tests: list[YAMLTestSpec] = []
        
        # Generate page tests
        for page_result in result.page_results:
            url = page_result.get("url", "")
            analysis = page_result.get("analysis")
            
            if not analysis:
                continue
            
            # Get elements
            elements: list[dict[str, Any]] = []
            if hasattr(analysis, "interactive_elements"):
                elements = [
                    {
                        "selector": e.selector,
                        "tag": e.tag,
                        "type": e.element_type,
                        "text": e.text,
                        "attributes": e.attributes,
                    }
                    for e in analysis.interactive_elements
                ]
            
            # Filter assertions for this page
            page_assertions = [
                a for a in self._all_assertions
                if not a.selector or any(
                    e.get("selector") == a.selector for e in elements
                )
            ]
            
            page_test = await self.yaml_builder.build_from_page(
                url=url,
                elements=elements,
                assertions=page_assertions[:50],  # Limit
            )
            tests.append(page_test)
        
        # Generate flow tests
        for flow in self._detected_flows:
            flow_assertions = [
                a for a in self._all_assertions
                if hasattr(a, "flow_id") and a.flow_id == getattr(flow, "id", None)
            ]
            
            flow_test = await self.yaml_builder.build_from_flow(
                flow=flow,
                assertions=flow_assertions,
            )
            tests.append(flow_test)
        
        # Generate form tests
        for form in self._analyzed_forms:
            form_tests = await self.yaml_builder.build_from_form(
                form=form,
                assertions=None,  # Assertions generated within builder
            )
            tests.extend(form_tests)
        
        # Generate API tests
        for api in self._detected_apis:
            api_test = await self.yaml_builder.build_api_test(
                endpoint={
                    "url": api.url,
                    "method": api.method.value if hasattr(api.method, "value") else api.method,
                    "type": api.api_type.value if hasattr(api.api_type, "value") else api.api_type,
                },
            )
            tests.append(api_test)
        
        result.tests = tests
        
        logger.info("generation_phase_complete", tests_generated=len(tests))
    
    async def _output_phase(self, result: BuildResult) -> None:
        """Output generated tests to files."""
        logger.info("output_phase_start")
        
        if not result.tests:
            result.warnings.append("No tests generated")
            return
        
        # Generate YAML content
        result.yaml_content = self.yaml_builder.generate_yaml(result.tests)
        
        # Write to file
        if self.config.output_dir:
            self.config.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.config.output_dir / self.config.yaml_file_name
            
            result.output_path = self.yaml_builder.write_yaml(
                result.tests,
                output_path,
            )
            
            # Generate report if enabled
            if self.config.generate_report:
                report_path = self.config.output_dir / "build_report.json"
                import json
                report_path.write_text(
                    json.dumps(result.to_report(), indent=2),
                    encoding="utf-8",
                )
        
        logger.info(
            "output_phase_complete",
            output_path=str(result.output_path) if result.output_path else None,
        )
    
    def reset(self) -> None:
        """Reset orchestrator state for new build."""
        self._analyzed_urls.clear()
        self._detected_flows.clear()
        self._detected_apis.clear()
        self._analyzed_forms.clear()
        self._all_assertions.clear()


# Convenience function for CLI/API usage
async def build_tests(
    browser: "BrowserController",
    start_url: str,
    config: OrchestratorConfig | None = None,
    llm_service: Any | None = None,
) -> BuildResult:
    """
    Convenience function to build tests from URL.
    
    Args:
        browser: Browser controller
        start_url: Starting URL
        config: Optional configuration
        llm_service: Optional LLM service
        
    Returns:
        Build result with generated tests
    """
    orchestrator = TestBuilderOrchestrator(
        browser=browser,
        config=config,
        llm_service=llm_service,
    )
    
    return await orchestrator.build(start_url)
