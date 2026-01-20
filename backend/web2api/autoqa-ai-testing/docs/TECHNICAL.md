# AutoQA Technical Documentation

Comprehensive technical reference for the AutoQA AI Testing System.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Structure](#module-structure)
3. [Builder Module](#builder-module)
4. [Runner Module](#runner-module)
5. [LLM Module](#llm-module)
6. [Concurrency Module](#concurrency-module)
7. [DSL/YAML Format Reference](#dslyaml-format-reference)
8. [API Reference](#api-reference)
9. [CLI Reference](#cli-reference)

---

## Architecture Overview

### High-Level Architecture

```
                                    +------------------+
                                    |     CLI/API      |
                                    +--------+---------+
                                             |
              +------------------------------+------------------------------+
              |                              |                              |
     +--------v--------+          +----------v----------+         +---------v---------+
     |   Test Builder  |          |     Test Runner     |         |    LLM Service    |
     |  (Auto-generate)|          |     (Execute)       |         |    (Optional)     |
     +--------+--------+          +----------+----------+         +---------+---------+
              |                              |                              |
   +----------+----------+        +----------+----------+                   |
   |                     |        |                     |                   |
+--v---+  +------+  +----v--+  +--v---+  +-------+  +---v----+              |
|Crawl |  |Analyze|  |Generate| |Execute|  |Heal  |  |Assert  |<-------------+
+------+  +------+  +-------+  +------+  +-------+  +--------+
                                    |
                            +-------v-------+
                            |  owl-browser  |
                            +---------------+
```

### Data Flow

1. **Test Generation Flow:**
   ```
   URL -> Crawler -> Page Analyzer -> Element Classifier -> Flow Detector
       -> Form Analyzer -> API Detector -> Test Strategy -> YAML Builder -> Output
   ```

2. **Test Execution Flow:**
   ```
   YAML Spec -> Parser -> TestRunner -> Step Execution -> Assertions
            -> Self-Healing (if needed) -> Results -> Artifacts
   ```

### Component Relationships

| Component | Depends On | Used By |
|-----------|------------|---------|
| DSL Parser | Pydantic | Runner, CLI |
| Test Runner | owl-browser, DSL, Self-Healing | CLI, API, AsyncRunner |
| Builder | owl-browser, LLM (optional) | CLI, API |
| Concurrency | Browser Pool, Resource Monitor | Parallel execution |
| LLM Service | HTTP clients | Builder, Assertions |

---

## Module Structure

```
src/autoqa/
├── __init__.py              # Package exports
├── cli.py                   # CLI entry point (Click-based)
│
├── builder/                 # Auto Test Builder
│   ├── __init__.py         # Public API exports
│   ├── test_builder.py     # Legacy AutoTestBuilder class
│   ├── orchestrator.py     # TestBuilderOrchestrator (main entry)
│   ├── llm_enhanced.py     # LLM-enhanced test generation
│   ├── analyzer/           # Page analysis submodule
│   │   ├── page_analyzer.py
│   │   ├── element_classifier.py
│   │   └── visual_analyzer.py
│   ├── crawler/            # Intelligent crawling
│   │   ├── intelligent_crawler.py
│   │   └── state_manager.py
│   ├── discovery/          # Flow/API/Form detection
│   │   ├── flow_detector.py
│   │   ├── api_detector.py
│   │   └── form_analyzer.py
│   └── generator/          # Test generation
│       ├── test_strategy.py
│       ├── assertion_generator.py
│       └── yaml_builder.py
│
├── runner/                  # Test execution
│   ├── __init__.py
│   ├── test_runner.py      # Main TestRunner class
│   └── self_healing.py     # SelfHealingEngine
│
├── dsl/                     # YAML DSL
│   ├── __init__.py
│   ├── models.py           # Pydantic models
│   ├── parser.py           # YAML parsing
│   ├── transformer.py      # Step transformation
│   └── validator.py        # Schema validation
│
├── llm/                     # LLM integration
│   ├── __init__.py
│   ├── config.py           # LLM configuration
│   ├── client.py           # HTTP client wrappers
│   ├── prompts.py          # Prompt templates
│   ├── service.py          # LLMService singleton
│   └── assertions.py       # LLM-based assertions
│
├── concurrency/             # Parallel execution
│   ├── __init__.py
│   ├── config.py           # ConcurrencyConfig
│   ├── browser_pool.py     # BrowserPool
│   ├── runner.py           # AsyncTestRunner
│   └── resource_monitor.py # ResourceMonitor
│
├── api/                     # REST API
│   ├── __init__.py
│   └── main.py             # FastAPI application
│
├── assertions/              # Assertion engine
├── visual/                  # Visual regression
├── versioning/              # Version tracking
├── storage/                 # Persistence (S3, PostgreSQL)
├── orchestrator/            # Distributed scheduling
├── generative/              # Generative test features
└── ci/                      # CI/CD template generation
```

---

## Builder Module

The Builder module automatically generates YAML test specifications from web pages.

### Core Classes

#### TestBuilderOrchestrator

Main orchestration layer coordinating all analysis and generation components.

```python
from autoqa.builder import TestBuilderOrchestrator, OrchestratorConfig

config = OrchestratorConfig(
    mode=BuildMode.STANDARD,      # quick, standard, deep, targeted
    scope=TestScope.FULL,         # full, functional, visual, accessibility, api
    max_pages=50,
    max_depth=3,
    enable_visual_analysis=True,
    enable_accessibility_checks=True,
    enable_api_detection=True,
    parallel_analysis=True,
)

orchestrator = TestBuilderOrchestrator(browser, config)
result = await orchestrator.build("https://example.com")
```

**Build Phases:**
1. **Crawl Phase** - Discover pages via IntelligentCrawler
2. **Analysis Phase** - PageAnalyzer, ElementClassifier, VisualAnalyzer
3. **Discovery Phase** - FlowDetector, APIDetector, FormAnalyzer
4. **Strategy Phase** - TestStrategy generates test plan
5. **Assertion Phase** - AssertionGenerator creates assertions
6. **Generation Phase** - YAMLBuilder produces output
7. **Output Phase** - Write YAML files and reports

#### AutoTestBuilder (Legacy)

Simpler, synchronous builder for basic use cases.

```python
from autoqa.builder import AutoTestBuilder, BuilderConfig

config = BuilderConfig(
    url="https://example.com",
    username="testuser",
    password="secret",
    depth=2,
    max_pages=20,
)

builder = AutoTestBuilder(browser, config)
yaml_content = builder.build()
```

### Analyzer Submodule

#### PageAnalyzer

Deep DOM analysis with component detection.

```python
from autoqa.builder.analyzer import PageAnalyzer, AnalyzerConfig

analyzer = PageAnalyzer(config=AnalyzerConfig(
    include_hidden=False,
    max_elements=500,
    detect_shadow_dom=True,
    detect_iframes=True,
))

analysis = await analyzer.analyze(html, url)
# Returns: DOMAnalysis with components, elements, complexity metrics
```

**Output: DOMAnalysis**
- `components: list[ComponentInfo]` - Detected UI components
- `interactive_elements: list[InteractiveElement]` - Buttons, inputs, links
- `complexity: PageComplexity` - Low/Medium/High/Critical
- `accessibility_issues: list[str]`

#### ElementClassifier

ML-based element classification.

```python
from autoqa.builder.analyzer import ElementClassifier, ClassifierConfig

classifier = ElementClassifier(config=ClassifierConfig(
    use_ml_classification=True,
    confidence_threshold=0.7,
))

result = await classifier.classify({
    "tag": "button",
    "attributes": {"class": "submit-btn"},
    "text": "Submit Order",
    "selector": "button.submit-btn",
})
# Returns: ClassificationResult with purpose, relationships, confidence
```

**ElementPurpose Values:**
- `NAVIGATION`, `ACTION`, `INPUT`, `DISPLAY`, `CONTAINER`
- `FORM_SUBMIT`, `FORM_FIELD`, `MENU`, `MODAL`, `ALERT`

#### VisualAnalyzer

Visual/UI analysis for layout, accessibility, responsiveness.

```python
from autoqa.builder.analyzer import VisualAnalyzer, VisualConfig

analyzer = VisualAnalyzer(config=VisualConfig(
    detect_layout=True,
    check_accessibility=True,
    analyze_colors=True,
))

result = await analyzer.analyze(screenshot_bytes, html)
# Returns: layout info, accessibility checks, visual hierarchy
```

### Crawler Submodule

#### IntelligentCrawler

Smart same-domain crawling with priority queue.

```python
from autoqa.builder.crawler import IntelligentCrawler, CrawlConfig

crawler = IntelligentCrawler(
    browser=browser,
    config=CrawlConfig(
        max_pages=50,
        max_depth=3,
        same_domain_only=True,
        exclude_patterns=[r"/admin/", r"/api/"],
        include_patterns=[r"/products/"],
        respect_robots_txt=True,
    ),
)

result = await crawler.crawl("https://example.com")
# Returns: CrawlResult with pages_crawled, urls_discovered, errors
```

#### StateManager

Application state tracking for flow detection.

```python
from autoqa.builder.crawler import StateManager, StateConfig

manager = StateManager(config=StateConfig(
    track_url_state=True,
    track_dom_state=True,
    detect_modals=True,
))

await manager.capture_state(page, url, html)
transitions = manager.get_state_transitions()
```

### Discovery Submodule

#### FlowDetector

Detect user flows (login, registration, checkout, search, CRUD).

```python
from autoqa.builder.discovery import FlowDetector, FlowConfig, FlowType

detector = FlowDetector(config=FlowConfig(
    detect_login=True,
    detect_registration=True,
    detect_checkout=True,
    detect_search=True,
    detect_crud=True,
    min_confidence=0.7,
))

flows = await detector.detect_from_page(html, url, elements)
# Returns: list[UserFlow] with type, steps, confidence
```

**FlowType Values:**
- `LOGIN`, `REGISTRATION`, `CHECKOUT`, `SEARCH`, `CRUD`
- `NAVIGATION`, `FORM_SUBMISSION`, `FILE_UPLOAD`

#### APIDetector

Detect API calls (REST, GraphQL).

```python
from autoqa.builder.discovery import APIDetector, APIConfig

detector = APIDetector(config=APIConfig(
    detect_rest=True,
    detect_graphql=True,
    capture_headers=True,
))

await detector.start_monitoring()
# ... page interactions ...
endpoints = await detector.stop_monitoring()
# Returns: list[APIEndpoint] with url, method, type, request/response
```

#### FormAnalyzer

Deep form analysis with validation rule inference.

```python
from autoqa.builder.discovery import FormAnalyzer, FormConfig

analyzer = FormAnalyzer(config=FormConfig(
    infer_validation_rules=True,
    generate_test_data=True,
    detect_field_relationships=True,
))

forms = await analyzer.analyze(html)
# Returns: list[FormAnalysis] with fields, validation, test cases
```

**Output: FormAnalysis**
- `fields: list[FieldAnalysis]` - Field info with type, validation
- `validation_rules: list[ValidationRule]` - Inferred rules
- `test_cases: list[TestCase]` - Generated test data

### Generator Submodule

#### TestStrategy

Risk-based test prioritization and planning.

```python
from autoqa.builder.generator import TestStrategy, StrategyConfig

strategy = TestStrategy(config=StrategyConfig(
    prioritize_critical_flows=True,
    include_negative_tests=True,
    include_boundary_tests=True,
    test_coverage_target=0.8,
))

plan = await strategy.generate_plan(analysis_data, scope="full")
# Returns: TestPlan with test_cases, priorities, coverage
```

#### AssertionGenerator

Generate appropriate assertions.

```python
from autoqa.builder.generator import AssertionGenerator, AssertionConfig

generator = AssertionGenerator(config=AssertionConfig(
    include_visibility=True,
    include_accessibility=True,
    include_visual=True,
    include_network=True,
))

assertions = await generator.generate_for_page(url, elements, visual_data)
# Returns: list[Assertion] with type, selector, expected, confidence
```

#### YAMLBuilder

Construct YAML test specifications.

```python
from autoqa.builder.generator import YAMLBuilder, BuilderConfig

builder = YAMLBuilder(config=BuilderConfig(
    include_comments=True,
    include_metadata=True,
    semantic_selectors=True,
))

spec = await builder.build_from_page(url, elements, assertions)
yaml_content = builder.generate_yaml([spec])
```

---

## Runner Module

The Runner module executes YAML test specifications.

### TestRunner

Main test execution engine.

```python
from autoqa.runner import TestRunner

runner = TestRunner(
    browser=browser,
    healing_engine=healing_engine,
    artifact_dir="./artifacts",
    record_video=True,
    screenshot_on_failure=True,
    default_timeout_ms=30000,
    wait_for_network_idle=True,
    enable_versioning=True,
    enable_url_recovery=True,
)

result = runner.run_spec(spec, variables={"base_url": "https://example.com"})
```

**Features:**
- Self-healing selector recovery
- URL-aware page recovery
- Automatic retries with exponential backoff
- Smart waits (network idle, selector visibility)
- Video recording and screenshot capture
- Network log capture for debugging
- Variable interpolation
- Version tracking integration

**Step Execution Flow:**

```
1. Check skip condition
2. Track expected URL from navigate actions
3. Transform step to browser command
4. URL-aware pre-check (verify correct page)
5. Ensure element ready (visibility/enabled)
6. Execute browser command
7. Post-action wait (network idle)
8. Capture result or handle failure
9. Recovery strategies if failed:
   a. URL recovery (navigate to expected page)
   b. Selector self-healing
   c. Exponential backoff retry
```

### SelfHealingEngine

Deterministic selector recovery (no AI/LLM required).

```python
from autoqa.runner import SelfHealingEngine

engine = SelfHealingEngine(
    history_path="./healing_history.json",
    min_confidence=0.6,
    enable_learning=True,
)

result = engine.heal_selector(
    page,
    original_selector="#old-button",
    action_context="click",
    element_description="Submit button",
)

if result.success:
    print(f"Healed: {result.healed_selector}")
    print(f"Strategy: {result.strategy_used}")
    print(f"Confidence: {result.confidence}")
```

**Healing Strategies (in order of confidence):**

| Strategy | Confidence | Description |
|----------|------------|-------------|
| `CACHED_HISTORY` | 98% | Previously successful selector |
| `ID_FALLBACK` | 95% | Element ID variations |
| `DATA_TESTID` | 92% | `data-testid` attribute |
| `TEXT_MATCH` | 82-90% | Visible text content matching |
| `NAME_FALLBACK` | 90% | Form element `name` attribute |
| `ARIA_LABEL` | 88% | Accessibility labels |
| `PLACEHOLDER_FALLBACK` | 85% | Input placeholders |
| `XPATH_FALLBACK` | 70-90% | XPath alternatives |
| `ATTRIBUTE_FUZZY` | 65-85% | Partial attribute matching |
| `DOM_STRUCTURE` | 70% | DOM tree analysis |

### Result Types

#### TestRunResult

```python
@dataclass
class TestRunResult:
    test_name: str
    status: StepStatus  # PASSED, FAILED, SKIPPED
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int
    total_steps: int
    passed_steps: int
    failed_steps: int
    healed_steps: int
    step_results: list[StepResult]
    video_path: str | None
    artifacts: dict[str, str]
    error: str | None
    network_log: list[dict]
```

#### StepResult

```python
@dataclass
class StepResult:
    step_index: int
    step_name: str | None
    action: str
    status: StepStatus
    duration_ms: int
    result: Any
    error: str | None
    screenshot_path: str | None
    healing_result: HealingResult | None
    retries: int
```

---

## LLM Module

Optional LLM integration for enhanced test generation and assertions.

### Configuration

```python
from autoqa.llm import LLMConfig, LLMProvider, load_llm_config

config = load_llm_config()  # Loads from environment/config file

# Or manual configuration:
config = LLMConfig(
    enabled=True,
    default_provider=LLMProvider.OPENAI,
    endpoints={
        LLMProvider.OPENAI: LLMEndpointConfig(
            api_key="${env:OPENAI_API_KEY}",
            model="gpt-4",
            max_tokens=4096,
        ),
        LLMProvider.ANTHROPIC: LLMEndpointConfig(
            api_key="${env:ANTHROPIC_API_KEY}",
            model="claude-3-sonnet-20240229",
        ),
    },
    retry_config=RetryConfig(max_retries=3, backoff_factor=2.0),
    rate_limit_config=RateLimitConfig(requests_per_minute=60),
)
```

### LLMService

Singleton service for LLM operations.

```python
from autoqa.llm import get_llm_service, LLMResult

service = get_llm_service()

result: LLMResult = await service.complete(
    prompt="Analyze this page and suggest test assertions",
    context={"html": page_html, "url": url},
    tool="test_builder",
)

if result.success:
    print(result.content)
```

### LLM Assertions

```python
from autoqa.llm import LLMAssertionEngine

engine = LLMAssertionEngine(page)

# Semantic assertion
result = await engine.assert_semantic(
    assertion="The page shows a successful order confirmation",
    context="After checkout completion",
    min_confidence=0.7,
)

# State assertion
result = await engine.assert_state(
    expected_state="logged_in",
    indicators=["welcome message", "user avatar", "logout button"],
)

# Content validation
result = await engine.assert_content_valid(
    content_type="product_page",
    expected_patterns=["price", "add to cart", "product image"],
)
```

### Prompt Templates

```python
from autoqa.llm import get_prompt, format_prompt, PromptType

# Get predefined prompt
prompt = get_prompt(PromptType.TEST_GENERATION)

# Format with variables
formatted = format_prompt(
    PromptType.ELEMENT_ANALYSIS,
    html=element_html,
    context="login form",
)
```

---

## Concurrency Module

Parallel test execution with resource management.

### BrowserPool

Efficient browser context pooling.

```python
from autoqa.concurrency import BrowserPool, ConcurrencyConfig

config = ConcurrencyConfig(
    max_parallel_tests=5,
    max_browser_contexts=10,
    min_browser_contexts=2,
    context_max_uses=50,
    context_max_age_seconds=3600,
    context_idle_timeout_seconds=300,
    acquire_timeout_seconds=30,
)

async with BrowserPool(browser, config) as pool:
    async with pool.acquire("my_test") as context:
        context.goto("https://example.com")
        # ... test actions ...
```

**Pool Features:**
- Lifecycle management (creation, recycling, cleanup)
- Usage tracking and limits
- Health checks and automatic recovery
- Async-first design with proper cleanup

### AsyncTestRunner

Parallel test execution with concurrency control.

```python
from autoqa.concurrency import AsyncTestRunner, ParallelExecutionResult

async with AsyncTestRunner(browser, config) as runner:
    result: ParallelExecutionResult = await runner.run_tests(
        specs=test_specs,
        variables={"base_url": "https://example.com"},
        fail_fast=False,
    )
    
    print(f"Passed: {result.passed_tests}/{result.total_tests}")
    print(f"Max parallelism: {result.max_parallelism_reached}")
```

**Sync Entry Point:**
```python
runner = AsyncTestRunner(browser, config)
result = runner.run_tests_sync(specs, variables)
```

### ResourceMonitor

Memory-aware scaling.

```python
from autoqa.concurrency import ResourceMonitor, MemoryPressure

monitor = ResourceMonitor(
    config,
    on_pressure_change=handle_pressure,
)

await monitor.start_monitoring()
snapshot = monitor.take_snapshot()

print(f"Memory: {snapshot.memory_percent}%")
print(f"Pressure: {snapshot.memory_pressure.name}")  # NONE, LOW, MEDIUM, HIGH, CRITICAL
print(f"Can scale up: {snapshot.can_scale_up}")
```

**MemoryPressure Thresholds:**
- `NONE`: < 50% memory
- `LOW`: 50-70% memory
- `MEDIUM`: 70-85% memory
- `HIGH`: 85-95% memory
- `CRITICAL`: > 95% memory

---

## DSL/YAML Format Reference

### Full Test Specification Schema

```yaml
# Test Specification
name: string (required, 1-256 chars)
description: string
metadata:
  tags: [string]
  priority: critical | high | medium | low
  owner: string
  timeout_ms: int (0-3600000)
  retry_count: int (0-10)
  parallel: bool
  browser_profiles: [string]

environment:
  base_url: string
  variables: {key: value | ${env:KEY} | ${vault:path}}
  timeouts: {name: ms}
  headers: {name: value}

variables: {key: value | ${source:key}}

versioning:
  enabled: bool
  storage_path: string
  retention_days: int (1-365)
  capture_screenshots: bool
  capture_network: bool
  capture_elements: bool
  element_selectors: [string]

before_all:
  steps: [TestStep]
before_each:
  steps: [TestStep]
steps: [TestStep] (required, min 1)
after_each:
  steps: [TestStep]
after_all:
  steps: [TestStep]
```

### Actions Reference

#### Navigation Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `navigate` | `url`, `wait_until`, `timeout` | Navigate to URL |
| `wait` | `timeout` | Wait for time (ms) |
| `wait_for_selector` | `selector`, `timeout` | Wait for element |
| `wait_for_network_idle` | `timeout` | Wait for network idle |
| `wait_for_url` | `url`, `timeout` | Wait for URL change |

```yaml
- action: navigate
  url: https://example.com
  wait_until: networkidle  # load, domcontentloaded, networkidle
  timeout: 10000
```

#### Interaction Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `click` | `selector`, `timeout` | Click element |
| `double_click` | `selector`, `timeout` | Double-click element |
| `right_click` | `selector`, `timeout` | Right-click element |
| `hover` | `selector`, `timeout` | Hover over element |
| `drag_drop` | `start_x`, `start_y`, `end_x`, `end_y` | Drag and drop |

```yaml
- action: click
  selector: "button.submit"
  timeout: 5000

- action: drag_drop
  start_x: 100
  start_y: 200
  end_x: 300
  end_y: 400
```

#### Form Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `type` | `selector`, `text` | Type text into element |
| `pick` | `selector`, `value` | Select dropdown option |
| `press_key` | `key`, `modifiers` | Press keyboard key |
| `submit` | `selector` | Submit form |
| `upload` | `selector`, `file_paths` | Upload files |

```yaml
- action: type
  selector: "#email"
  text: "user@example.com"

- action: pick
  selector: "#country"
  value: "US"

- action: press_key
  key: Enter
  modifiers: ["Control"]  # Shift, Control, Alt, Meta
```

#### Scroll Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `scroll` | `scroll_x`, `scroll_y` | Scroll by offset |
| `scroll_to` | `x`, `y` | Scroll to position |
| `scroll_to_element` | `selector` | Scroll element into view |

#### Extraction Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `screenshot` | `filename` | Take screenshot |
| `extract_text` | `selector`, `capture_as` | Extract element text |
| `extract_json` | `template`, `capture_as` | Extract JSON data |
| `get_html` | `selector`, `capture_as` | Get element HTML |
| `get_markdown` | `capture_as` | Get page as markdown |
| `get_attribute` | `selector`, `attribute_name`, `capture_as` | Get attribute |
| `get_network_log` | `capture_as` | Get network requests |

```yaml
- action: extract_text
  selector: ".price"
  capture_as: product_price

- action: get_attribute
  selector: "img.logo"
  attribute_name: "src"
  capture_as: logo_url
```

#### Cookie Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `set_cookie` | `cookie_name`, `cookie_value`, `cookie_*` | Set cookie |
| `delete_cookies` | - | Delete all cookies |

```yaml
- action: set_cookie
  cookie_name: session
  cookie_value: abc123
  cookie_domain: example.com
  cookie_path: /
  cookie_secure: true
  cookie_http_only: true
```

#### Viewport Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `set_viewport` | `width`, `height` | Set viewport size |
| `new_page` | - | Open new page |
| `close_page` | - | Close current page |

### Assertions Reference

#### Standard Assertions

```yaml
- action: assert
  assertion:
    selector: ".element"
    operator: <operator>
    expected: <value>
    attribute: <attr_name>  # Optional
    timeout: 5000
    message: "Custom error message"
```

**Operators:**

| Category | Operators |
|----------|-----------|
| Value | `equals`, `not_equals`, `contains`, `not_contains`, `matches`, `starts_with`, `ends_with` |
| Numeric | `greater_than`, `less_than`, `greater_or_equal`, `less_or_equal` |
| Element State | `is_visible`, `is_hidden`, `is_enabled`, `is_disabled`, `is_checked`, `is_unchecked`, `exists`, `not_exists` |
| Boolean | `is_truthy`, `is_falsy` |
| Attribute | `has_attribute`, `attribute_equals`, `attribute_contains` |
| URL | `url_equals`, `url_contains`, `url_matches` |

#### Visual Assertions

```yaml
- action: visual_assert
  visual_assertion:
    baseline_name: homepage
    selector: "body"  # Optional: element-specific
    mode: semantic    # pixel, perceptual, structural, semantic
    threshold: 0.05
    threshold_mode: normal  # strict, normal, loose, custom
    anti_aliasing_tolerance: 0.5
    anti_aliasing_sigma: 1.5
    auto_mask_dynamic: true
    normalize_scroll: true
    generate_html_report: true
    ignore_regions:
      - x: 0
        y: 0
        width: 100
        height: 50
    update_baseline: false
```

**Threshold Modes:**
| Mode | Similarity Required |
|------|---------------------|
| `strict` | 99% (1% tolerance) |
| `normal` | 95% (5% tolerance) |
| `loose` | 85% (15% tolerance) |
| `custom` | Use threshold value |

#### Network Assertions

```yaml
- action: network_assert
  network_assertion:
    url_pattern: "/api/users"
    is_regex: false
    method: GET
    status_code: 200
    status_range: [200, 299]
    response_contains: "success"
    headers_contain:
      Content-Type: "application/json"
    max_response_time_ms: 2000
    should_be_blocked: false
    timeout: 30000
```

#### URL Assertions

```yaml
- action: url_assert
  url_pattern: "/dashboard"
  is_regex: false
```

#### ML-Based Assertions (No LLM Required)

**OCR Assertion:**
```yaml
- action: ocr_assert
  ocr_assertion:
    backend: easyocr  # pytesseract, easyocr
    languages: ["en"]
    region: [100, 100, 400, 200]  # x, y, width, height
    expected_text: "Welcome"
    contains: "Hello"
    min_confidence: 0.5
```

**UI State Assertion:**
```yaml
- action: ui_state_assert
  ui_state_assertion:
    expected_state: normal  # loading, error, success, empty, normal
    min_confidence: 0.5
```

**Color Assertion:**
```yaml
- action: color_assert
  color_assertion:
    dominant_color: "#ffffff"  # or RGB: "(255, 255, 255)"
    has_color: "#007bff"
    tolerance: 30
    min_percentage: 0.01
```

**Layout Assertion:**
```yaml
- action: layout_assert
  layout_assertion:
    expected_count: 5
    min_count: 3
    max_count: 10
    alignment: center  # left, right, center, top, bottom, vertical_center
    alignment_tolerance: 10
    element_type: button
```

**Icon/Logo Assertion:**
```yaml
- action: icon_assert
  icon_assertion:
    template_path: ./templates/logo.png
    method: feature  # feature (ORB), correlation
    min_confidence: 0.5
```

**Accessibility Assertion:**
```yaml
- action: accessibility_assert
  accessibility_assertion:
    min_contrast_ratio: 4.5  # WCAG AA=4.5, AAA=7.0
    wcag_level: AA
    region: [0, 0, 1920, 1080]
```

#### LLM-Based Assertions (Optional)

**Semantic Assertion:**
```yaml
- action: llm_assert
  llm_assertion:
    assertion: "page shows successful order confirmation"
    context: "after checkout completion"
    min_confidence: 0.7
```

**State Assertion:**
```yaml
- action: semantic_assert
  semantic_assertion:
    expected_state: logged_in
    indicators:
      - welcome message
      - user avatar
      - logout button
    min_confidence: 0.7
```

**Content Assertion:**
```yaml
- action: content_assert
  content_assertion:
    content_type: product_page
    expected_patterns:
      - price
      - add to cart
      - product image
    selector: ".product-details"
    min_confidence: 0.7
```

### Variables and Interpolation

```yaml
variables:
  base_url: https://example.com
  username: testuser
  timeout: 5000
  # Environment variable
  api_key: ${env:API_KEY}
  # HashiCorp Vault
  password: ${vault:secrets/test-password}
  # AWS Secrets Manager
  token: ${aws_secrets:my-api-token}
  # Kubernetes Secret
  db_pass: ${k8s_secret:db-credentials/password}

steps:
  - action: navigate
    url: ${base_url}/login
  - action: type
    selector: "#username"
    text: ${username}
```

### Flow Control

```yaml
steps:
  - name: Conditional step
    action: click
    selector: "#button"
    skip_if: "${is_mobile} == True"
    continue_on_failure: true
    retry_count: 3
    retry_delay_ms: 2000
```

### Test Suite Schema

```yaml
name: "Full Regression Suite"
description: "Complete test suite"

parallel_execution: true
max_parallel: 5
fail_fast: false

variables:
  base_url: https://example.com

before_suite:
  steps:
    - action: navigate
      url: ${base_url}/setup

tests:
  - name: "Login Test"
    steps:
      - action: navigate
        url: ${base_url}/login
      # ... more steps

  - name: "Dashboard Test"
    steps:
      # ... steps

after_suite:
  steps:
    - action: navigate
      url: ${base_url}/cleanup
```

---

## API Reference

### Endpoints

#### Health Check

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-07T10:00:00Z",
  "version": "1.0.0"
}
```

#### Submit Job

```
POST /api/v1/jobs
```

Request:
```json
{
  "test_spec_path": "tests/login.yaml",
  "test_spec_content": null,
  "suite_name": "Login Suite",
  "priority": "normal",
  "timeout_seconds": 300,
  "variables": {"base_url": "https://example.com"},
  "tags": ["login", "smoke"],
  "ci_metadata": {"branch": "main", "commit": "abc123"}
}
```

Response:
```json
{
  "id": "job-123",
  "status": "pending",
  "suite_name": "Login Suite",
  "priority": "normal",
  "created_at": "2025-01-07T10:00:00Z"
}
```

#### Get Job

```
GET /api/v1/jobs/{job_id}
```

#### Cancel Job

```
DELETE /api/v1/jobs/{job_id}
```

#### Retry Job

```
POST /api/v1/jobs/{job_id}/retry
```

#### List Jobs

```
GET /api/v1/jobs?status=pending&limit=100
```

#### Get Statistics

```
GET /api/v1/stats
```

Response:
```json
{
  "queue_length": 5,
  "total_workers": 10,
  "active_workers": 3,
  "max_concurrent_jobs": 10
}
```

#### List Test Runs

```
GET /api/v1/runs?suite_name=Login&status=passed&limit=100&offset=0
```

#### Get Test Run Details

```
GET /api/v1/runs/{run_id}
```

#### Get Step Results

```
GET /api/v1/runs/{run_id}/steps
```

#### List Artifacts

```
GET /api/v1/runs/{run_id}/artifacts
```

#### Validate Test Spec

```
POST /api/v1/validate
Content-Type: multipart/form-data

file: test.yaml
```

Response:
```json
{
  "valid": true,
  "name": "Login Test",
  "steps": 10
}
```

#### Build Test Spec (Auto-generate)

```
POST /api/v1/build?url=https://example.com&depth=2&max_pages=20
```

Response:
```json
{
  "success": true,
  "yaml_content": "name: Auto-generated...",
  "summary": {
    "url": "https://example.com",
    "pages_analyzed": 5,
    "total_elements": 150,
    "has_login_form": true,
    "depth": 2
  }
}
```

#### Get Test Statistics

```
GET /api/v1/statistics?suite_name=Login&days=30
```

---

## CLI Reference

### `autoqa build`

Auto-generate YAML tests from a webpage.

```bash
autoqa build <url> [options]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-u, --username` | Username for authentication | - |
| `-p, --password` | Password for authentication | - |
| `-d, --depth` | Crawl depth | `1` |
| `--max-pages` | Maximum pages to analyze | `10` |
| `-o, --output` | Output file path | stdout |
| `--include-hidden` | Include hidden elements | `false` |
| `--timeout` | Timeout in ms | `30000` |
| `--exclude PATTERN` | Exclude URL regex (repeatable) | - |
| `--include PATTERN` | Include URL regex (repeatable) | - |

Examples:
```bash
# Basic usage
autoqa build https://example.com -o tests/example.yaml

# With authentication
autoqa build https://app.example.com/login -u admin -p secret -o tests/login.yaml

# Deep crawl
autoqa build https://example.com --depth 3 --max-pages 50 -o tests/full.yaml

# Filter URLs
autoqa build https://example.com --exclude "/admin/" --exclude "/api/"
```

### `autoqa run`

Execute test specifications.

```bash
autoqa run <paths> [options]
```

| Flag | Description | Default |
|------|-------------|---------|
| `-e, --environment` | Target environment | `default` |
| `--parallel` | Run in parallel | `false` |
| `--max-parallel` | Max parallel tests | `5` |
| `--record-video` | Record video | `false` |
| `--artifacts-dir` | Artifacts directory | `./artifacts` |
| `--output-format` | `json`, `junit`, `html` | `json` |
| `--output-file` | Results file | stdout |
| `--var KEY=VALUE` | Set variable (repeatable) | - |
| `--healing-history` | Healing history file | - |
| `--default-timeout` | Default timeout ms | `10000` |
| `--no-network-idle-wait` | Skip network idle | `false` |
| `--fast-mode` | Reduced timeouts | `false` |
| `--versioned` | Enable versioning | `false` |
| `--versioning-path` | Version storage path | `.autoqa/history` |
| `-v, --verbose` | Verbose output | `false` |

Examples:
```bash
# Run single test
autoqa run tests/login.yaml -v

# Run all tests with JUnit output
autoqa run tests/ --output-format junit --output-file results.xml

# Parallel execution
autoqa run tests/ --parallel --max-parallel 5

# With variables
autoqa run tests/ --var BASE_URL=https://staging.example.com

# With versioning
autoqa run tests/ --versioned --versioning-path .autoqa/history
```

### `autoqa validate`

Validate test specifications without running.

```bash
autoqa validate <paths>
```

Example:
```bash
autoqa validate tests/
# Output: Valid: tests/login_test.yaml (Login Flow Test, 5 steps)
```

### `autoqa history`

View test version history.

```bash
autoqa history <test_name> [options]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--storage-path` | Version history path | `.autoqa/history` |
| `--limit` | Max versions to show | `20` |
| `--format` | `table`, `json` | `table` |

### `autoqa diff`

Compare test versions.

```bash
autoqa diff <test_name> [options]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--from` | Start date/version | - |
| `--to` | End date/version | latest |
| `--latest N` | Compare last N runs | - |
| `--storage-path` | Version history path | `.autoqa/history` |
| `--output` | `terminal`, `html`, `json` | `terminal` |
| `--output-file` | Save report | - |

Examples:
```bash
# Compare last 2 runs
autoqa diff "Login Test" --latest 2

# Compare date range
autoqa diff "Login Test" --from 2025-01-01 --to 2025-01-07

# HTML report
autoqa diff "Login Test" --latest 2 --output html --output-file diff.html
```

### `autoqa ci`

Generate CI/CD configuration.

```bash
autoqa ci <provider> [options]
```

Providers: `github`, `gitlab`, `jenkins`, `azure`, `circleci`

| Flag | Description | Default |
|------|-------------|---------|
| `--test-paths` | Test spec paths | `tests/` |
| `-o, --output` | Output file | stdout |
| `--python-version` | Python version | `3.12` |
| `--parallel` | Enable parallel | `false` |
| `--nodes` | Parallel nodes | `1` |

Examples:
```bash
autoqa ci github -o .github/workflows/autoqa.yml
autoqa ci gitlab --parallel --nodes 3 -o .gitlab-ci.yml
```

### `autoqa server`

Start the API server.

```bash
autoqa server [options]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--host` | Server host | `0.0.0.0` |
| `--port` | Server port | `8080` |

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OWL_BROWSER_URL` | Remote browser server URL | Yes |
| `OWL_BROWSER_TOKEN` | Authentication token | No |
| `ARTIFACT_PATH` | Local artifact directory | No |
| `REDIS_URL` | Redis connection URL | No |
| `DATABASE_URL` | PostgreSQL connection URL | No |
| `S3_BUCKET` | S3 bucket for artifacts | No |
| `OPENAI_API_KEY` | OpenAI API key (for LLM) | No |
| `ANTHROPIC_API_KEY` | Anthropic API key (for LLM) | No |
| `MAX_CONCURRENT_JOBS` | Max parallel jobs | No |
| `CORS_ORIGINS` | CORS allowed origins | No |

---

## License

MIT License - see LICENSE file for details.
