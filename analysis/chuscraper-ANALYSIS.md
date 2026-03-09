# CODEBASE ANALYSIS: Chuscraper
Generated: 2026-03-09
Analyst: Claude (parallel 9-agent exploration)

---

## 1. Repository Topology

### Directory Tree (2–3 levels, annotated)

```
chuscraper/                         # Root repository
├── chuscraper/                     # Core Python package (v0.19.7)
│   ├── __init__.py                 # Public API exports: start(), Config, Browser, Tab, Element
│   ├── _version.py                 # Single source of truth: __version__ = "0.19.7"
│   ├── ai/                         # AI extraction layer
│   │   ├── base.py                 # BaseExtractor ABC
│   │   ├── openai_extractor.py     # OpenAI GPT-4o integration
│   │   └── ollama_extractor.py     # Local Ollama LLM integration
│   ├── cdp/                        # Chrome DevTools Protocol bindings (17 domain modules)
│   │   ├── browser.py, dom.py, emulation.py, fetch.py, network.py
│   │   ├── page.py, runtime.py, storage.py, target.py, ...
│   │   └── util.py                 # Event parser registry
│   ├── core/                       # Central browser/tab/connection control
│   │   ├── browser.py              # Browser class (424 lines) — process spawning, tab mgmt
│   │   ├── tab.py                  # Tab class (940 lines) — aggregates 8 mixins
│   │   ├── connection.py           # CDP WebSocket transport (322 lines)
│   │   ├── config.py               # Config class (279 lines) — CLI arg generation
│   │   ├── stealth.py              # SystemProfile — anti-detection (230 lines)
│   │   ├── element.py              # Element class (126 lines) — DOM wrapper
│   │   ├── intercept.py            # Request/response interception (223 lines)
│   │   ├── behavior.py             # HumanBehavior — natural browsing simulation (187 lines)
│   │   ├── local_proxy.py          # Auth proxy tunnel (Patchright architecture)
│   │   ├── limiter.py              # Rate/concurrency/session limiters
│   │   ├── observability.py        # FailureDumper, Logger, structured context
│   │   ├── process.py              # Cross-platform process spawning (Win/POSIX)
│   │   ├── expect.py               # Request/response/download expectations
│   │   ├── banner.py               # ASCII startup banner
│   │   ├── keys.py                 # Keyboard key event definitions
│   │   ├── _contradict.py          # Case-insensitive dict for attributes
│   │   ├── util.py                 # start() entrypoint, helpers
│   │   ├── browsers/               # Browser initialization, target management
│   │   ├── elements/               # Element mixins (base, interaction, content, query)
│   │   └── tabs/                   # Tab functionality split into 8 mixins
│   │       ├── navigation.py       # get(), goto(), back(), forward(), reload()
│   │       ├── dom.py              # select(), find(), query_selector_all()
│   │       ├── actions.py          # click(), type(), drag(), scroll()
│   │       ├── network.py          # intercept_fetch(), network monitoring
│   │       ├── wait.py             # wait_for(), wait_for_selector()
│   │       ├── storage.py          # cookies, localStorage
│   │       ├── screenshot.py       # screenshot_b64(), save_screenshot()
│   │       └── evaluation.py       # evaluate() JavaScript execution
│   ├── engine/                     # Advanced parsing and extraction engine
│   │   ├── parser.py               # Selector/Selectors (lxml-based, CSS→XPath)
│   │   ├── core/                   # Extraction utilities, storage, fingerprinting
│   │   │   ├── extract.py          # Convertor: HTML→Markdown/Text
│   │   │   ├── storage.py          # SQLite adaptive selector storage
│   │   │   ├── translator.py       # CSS-to-XPath compiler
│   │   │   └── mixins.py           # SelectorsGeneration (XPath/CSS auto-gen)
│   │   ├── engines/                # Toolbelt subpackage
│   │   │   └── toolbelt/
│   │   │       ├── fingerprints.py # browserforge header generation
│   │   │       └── navigation.py   # Playwright route handlers, bypass paths
│   │   └── bypasses/               # 6 JavaScript stealth scripts
│   │       ├── webdriver_fully.js
│   │       ├── window_chrome.js
│   │       ├── navigator_plugins.js
│   │       ├── notification_permission.js
│   │       ├── screen_props.js
│   │       └── playwright_fingerprint.js
│   ├── extractors/                 # Output format converters
│   │   └── markdown.py             # MarkdownConverter (html2text-based, noise removal)
│   ├── mobile/                     # Android device automation via ADB
│   │   ├── core.py                 # run_adb(), get_connected_devices()
│   │   ├── device.py               # MobileDevice class
│   │   └── element.py              # MobileElement class
│   └── spider/                     # Universal crawler
│       └── core.py                 # Crawler class (BFS, sitemap, AI extraction)
├── examples/                       # 11 reference scripts
│   ├── amazon_search_product.py
│   ├── flipkart_scraper.py
│   ├── walmart_search.py
│   ├── stealth_verify.py
│   └── ... (7 more)
├── tests/                          # 11 test files
│   ├── test_crawler_*.py           # Crawler tests (basic, comprehensive, formats, streaming, sitemap)
│   ├── test_interactions*.py       # Browser interaction tests
│   ├── test_ai_extraction.py       # AI extractor tests
│   └── Dockerfile                  # Docker test environment
├── website/                        # Docusaurus documentation site
│   └── docs/                       # 17 markdown guides
├── pyproject.toml                  # Package config (Python 3.10-3.13)
├── .github/workflows/publish.yml   # PyPI publish pipeline
├── README.md                       # Comprehensive project overview
└── LICENSE                         # AGPL-3.0
```

### Architectural Layers

| Layer | Purpose | Key Files |
|-------|---------|-----------|
| **API Surface** | Public SDK interface | `__init__.py`, `core/util.py` (start()) |
| **Browser Control** | Process mgmt, tabs, navigation | `core/browser.py`, `core/tab.py`, `core/tabs/*.py` |
| **CDP Transport** | WebSocket protocol bindings | `core/connection.py`, `cdp/*.py` |
| **DOM & Elements** | Element query, interaction | `core/element.py`, `core/elements/*.py`, `engine/parser.py` |
| **Stealth & Anti-Detection** | Fingerprinting, JS bypasses | `core/stealth.py`, `engine/bypasses/*.js`, `engine/engines/toolbelt/` |
| **Network** | Interception, proxy auth | `core/intercept.py`, `core/local_proxy.py` |
| **Extraction** | HTML→Markdown/Text | `extractors/markdown.py`, `engine/core/extract.py` |
| **AI** | LLM-based structured extraction | `ai/base.py`, `ai/openai_extractor.py`, `ai/ollama_extractor.py` |
| **Crawler** | Multi-page BFS/sitemap crawling | `spider/core.py` |
| **Mobile** | Android ADB automation | `mobile/device.py`, `mobile/element.py`, `mobile/core.py` |
| **Infrastructure** | Observability, rate limiting | `core/observability.py`, `core/limiter.py`, `core/behavior.py` |

### Ambiguous/Redundant Directories
- `engine/engines/` nests a `toolbelt/` that duplicates some concerns already in `core/stealth.py` (fingerprinting); the boundary between "engine" and "core" is not clearly documented.
- `core/browsers/` vs `core/browser.py` — both exist; `browsers/` contains initialization mixins while `browser.py` is the main class.


---

## 2. Entrypoints & Execution Flows

### Primary Entrypoint: `chuscraper.start()` — `core/util.py:start()`

```
External trigger: User calls `await chuscraper.start(config)`
  → Config.__call__() generates Chrome CLI args (~20 flags)
  → process.start_process(exe, args) spawns Chrome subprocess
  → read_process_stderr() extracts DevTools debugger URL
  → Connection.connect() opens WebSocket to ws://127.0.0.1:PORT/devtools/...
  → If stealth=True:
      → SystemProfile.from_system() generates browserforge fingerprint
      → profile.apply(tab) injects dual-layer UA + 6 JS bypass scripts
  → If proxy has auth:
      → LocalAuthProxy.start() spawns localhost TCP proxy
      → Browser connects through local proxy → upstream
  → If timezone set:
      → cdp.emulation.set_timezone_override()
  → register_browser_cleanup() registers atexit handler
  → Returns Browser instance (async context manager)
```

**Startup/Teardown Sequence:**
- **Init:** Port discovery → WebSocket → CDP domains enabled → Stealth → Cookies loaded
- **Teardown:** `Browser.stop()` → Close all tabs → Kill subprocess → atexit sends SIGKILL (POSIX) or taskkill (Win)

### Secondary Entrypoint: `Crawler.run()` — `spider/core.py:run()`

```
External trigger: User creates Crawler(start_urls/sitemap_url) then calls await crawler.run()
  → Browser.create(**browser_config)
  → If sitemap_url: _fetch_sitemap() parses XML (recursive for nested sitemaps)
  → Else: Seed queue with start_urls at depth 0
  → Spawn N concurrent asyncio workers
  → Each worker: pull URL from queue → navigate → extract → queue new links → callback
  → When queue empty or max_pages reached: cancel workers, stop browser
  → If output_file: _save_to_file() writes JSON/JSONL/CSV/Markdown
```

### Tertiary Entrypoint: `MobileDevice.connect()` — `mobile/device.py`

```
External trigger: User calls `await MobileDevice(serial).connect()`
  → run_adb(["devices"]) lists connected Android devices
  → Selects first device or specified serial
  → Returns connected MobileDevice instance
```

### Middleware/Hook Chains

- **CDP Event Handlers:** `Connection.add_handler(event_type, callback)` — registered per-domain (e.g., `cdp.fetch.RequestPaused`)
- **Stealth Script Injection:** `cdp.page.add_script_to_evaluate_on_new_document()` — runs before every page load
- **Request Interception:** `BaseFetchInterception` with `continue_request/fail_request/fulfill_request`
- **Download Expectations:** `BaseRequestExpectation` context manager waits for matching network events

### Dead/Unreachable Entrypoints

- `Tab.crawl()` at `core/tab.py` — marked with `# TODO: Implement full recursive crawler`. Returns only a URL list, does not actually navigate. The real crawler is in `spider/core.py`.
- `core/util.py:loop()` — deprecated helper, warns on use.


---

## 3. Data Flows & Architecture Diagrams

### 3a. Component Diagram (text)

```
┌─────────────────────────────────────────────────────────┐
│                      User Application                    │
│   (Python script calling chuscraper.start())             │
└───────────────┬─────────────────────────────────────────┘
                │ async start()
                ▼
┌──────────────────────────┐    ┌─────────────────────────┐
│     Browser (core/)      │───►│   Chrome Process        │
│ • Config → CLI args      │◄───│   (subprocess)          │
│ • Tab management         │ WS │   DevTools Protocol     │
│ • Process lifecycle      │    └─────────────────────────┘
└──────────┬───────────────┘
           │ delegates to
           ▼
┌──────────────────────────┐    ┌─────────────────────────┐
│     Tab (core/tabs/)     │───►│  Connection (core/)     │
│ • Navigation mixin       │    │  • WebSocket transport  │
│ • DOM query mixin        │    │  • Transaction mgmt     │
│ • Actions mixin          │◄───│  • Event dispatch       │
│ • Network mixin          │    └────────────┬────────────┘
│ • Wait mixin             │                 │ cdp commands
│ • Screenshot mixin       │                 ▼
│ • Storage mixin          │    ┌─────────────────────────┐
│ • Evaluation mixin       │    │     CDP Domains (cdp/)  │
└──────────┬───────────────┘    │ • 17 modules (dom,      │
           │ wraps               │   page, network, etc.)  │
           ▼                    └─────────────────────────┘
┌──────────────────────────┐
│   Element (core/)        │    ┌─────────────────────────┐
│ • DOM node wrapper       │───►│  Stealth (core/stealth) │
│ • Click, type, etc       │    │  • SystemProfile        │
│ • Text, HTML, markdown   │    │  • browserforge headers │
└──────────────────────────┘    │  • 6 JS bypass scripts  │
                                └─────────────────────────┘
┌──────────────────────────┐
│   Crawler (spider/)      │    ┌─────────────────────────┐
│ • BFS queue              │───►│  AI Extractors (ai/)    │
│ • Sitemap parser         │    │  • OpenAI GPT-4o        │
│ • Concurrent workers     │    │  • Ollama (local)       │
│ • Multi-format output    │    └─────────────────────────┘
└──────────────────────────┘
                                ┌─────────────────────────┐
┌──────────────────────────┐    │  Infrastructure         │
│   Mobile (mobile/)       │    │  • RateLimiter          │
│ • ADB device control     │    │  • ConcurrencyLimiter   │
│ • UI hierarchy parsing   │    │  • SessionManager       │
│ • Element interaction    │    │  • FailureDumper        │
└──────────────────────────┘    │  • HumanBehavior        │
                                └─────────────────────────┘
```

### 3b. Sequence Diagram — Primary: Single Page Scrape with AI Extraction

```
User            Browser         Tab          Connection      Chrome        AI Extractor
 │                │               │               │             │               │
 │─start(config)─►│               │               │             │               │
 │                │──spawn proc──►│               │─────────────►│ (subprocess)  │
 │                │               │               │◄─ws://port───│               │
 │                │               │──connect()───►│─────────────►│               │
 │                │               │◄──session id──│◄─────────────│               │
 │                │               │               │              │               │
 │◄──browser obj──│               │               │              │               │
 │                │               │               │              │               │
 │──get(url)─────►│──navigate()──►│──cdp.page.──►│──────────────►│               │
 │                │               │  navigate()   │◄─loadEvent───│               │
 │                │               │◄──page ready──│              │               │
 │◄──tab obj──────│               │               │              │               │
 │                │               │               │              │               │
 │──tab.markdown()───────────────►│──get_content()─►│            │               │
 │                │               │◄──raw HTML────│◄─────────────│               │
 │                │               │──html2text────│              │               │
 │◄──markdown─────│               │               │              │               │
 │                │               │               │              │               │
 │──extractor.extract(md,prompt)──│───────────────│──────────────│──GPT-4o API──►│
 │                │               │               │              │◄─JSON result──│
 │◄──structured JSON──────────────│               │              │               │
 │                │               │               │              │               │
 │──browser.stop()►│──close tabs──►│──disconnect()─►│─────────────►│ (kill)       │
 │◄──done─────────│               │               │              │               │
```

### 3c. Sequence Diagram — Secondary: Crawler with Streaming Callback

```
User           Crawler         Browser        Tab (worker)    Queue          AI Extractor
 │               │               │               │              │               │
 │──run(urls)───►│──create()────►│               │              │               │
 │               │               │◄──browser─────│              │               │
 │               │──seed queue──►│───────────────│──────────────►│(depth=0)     │
 │               │──spawn N workers─────────────►│              │               │
 │               │               │               │◄─dequeue url─│               │
 │               │               │               │──navigate()──│──────────────►│
 │               │               │               │◄─page ready──│               │
 │               │               │               │──markdown()──│               │
 │               │               │               │──extract()───│───────────────►│
 │               │               │               │◄─result──────│◄──────────────│
 │◄──callback(result)────────────│               │              │               │
 │               │               │               │──get_urls()──│               │
 │               │               │               │──enqueue children────────────►│(depth+1)
 │               │               │               │              │               │
 │               │               │  ... repeat until queue empty or max_pages ...│
 │               │               │               │              │               │
 │               │──save_to_file()               │              │               │
 │◄──results─────│──browser.stop()               │              │               │
```

### Data Validation Gaps

- **HTTP input to DOM queries:** CSS selectors are not sanitized (user input passed to `querySelector`) — `core/tabs/dom.py`
- **Proxy URL parsing:** No validation on proxy format (`Config._parse_proxy()`) — `core/config.py`
- **Sitemap XML parsing:** No DTD validation or XXE mitigation — `spider/core.py:_fetch_sitemap()`
- **AI extractor output:** No schema enforcement on LLM JSON responses beyond basic `json.loads()` — `ai/openai_extractor.py`


---

## 4. APIs, Interfaces & Public Contracts

### Core Public Interface: `chuscraper.start()`

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `config` | `Config \| dict \| None` | None | Full configuration object |
| `headless` | `bool` | None | Run without GUI |
| `stealth` | `bool` | None | Enable anti-detection |
| `stealth_domain` | `str` | None | Domain for cookie persistence |
| `user_data_dir` | `str` | None | Browser profile path |
| `proxy` | `str` | None | Proxy URL |
| `lang` | `str` | None | Browser locale |
| `timezone` | `str` | None | IANA timezone |
| `retry_enabled` | `bool` | None | Auto-retry failures |
| `disable_webrtc` | `bool` | None | Prevent WebRTC IP leaks |
| `stealth_options` | `dict` | None | Fine-grained stealth control |

**Returns:** `Browser` (async context manager)
**Side effects:** Spawns Chrome subprocess, opens WebSocket, injects stealth scripts

### Browser Class API

| Method | Parameters | Return | Side Effects |
|--------|-----------|--------|-------------|
| `get(url, new_tab, new_window)` | `str, bool, bool` | `Tab` | CDP navigation |
| `stop()` | — | — | Kills subprocess |
| `close()` | — | — | Graceful close |
| `wait(seconds)` | `float` | `Browser` | Chainable sleep |

**Properties:** `main_tab: Tab`, `tabs: List[Tab]`

### Tab Class API (aggregated from 8 mixins)

**Navigation** (`tabs/navigation.py`):
- `get(url, timeout=10)` → self
- `back()`, `forward()`, `reload(ignore_cache=True)` → self
- `title()` → str

**DOM** (`tabs/dom.py`):
- `select(selector, timeout=None)` → Element
- `select_all(selector, adaptive=False)` → List[Element]
- `find(text, best_match=True)` → Element
- `query_selector(selector)` → Element
- `query_selector_all(selector)` → List[Element]

**Actions** (`tabs/actions.py`):
- `click(selector)`, `type(selector, text)`, `hover(selector)` → None
- `drag(from_sel, to_sel)`, `scroll(direction, amount)` → None
- `submit(selector)` → None

**Content**:
- `get_content()` → str (raw HTML)
- `markdown()` → str (clean markdown)
- `to_text()` → str (plain text)
- `get_all_urls(absolute=True)` → List[str]

**Network** (`tabs/network.py`):
- `intercept_fetch()` → None (enables CDP.fetch)
- `get_cookies()` → List[dict]
- `set_cookie(name, value, **opts)` → None

**Wait** (`tabs/wait.py`):
- `wait_for(text=None, selector=None, timeout=10)` → self
- `wait_for_selector(selector, timeout=10)` → Element
- `wait_for_navigation(timeout=10)` → self
- `wait_for_function(js, timeout=10)` → Any

**Screenshot** (`tabs/screenshot.py`):
- `screenshot_b64(format, full_page)` → str
- `save_screenshot(filename)` → str (path)
- `print_to_pdf(filename)` → str (path)

**Evaluation** (`tabs/evaluation.py`):
- `evaluate(javascript)` → Any
- `send(cdp_command)` → Any (raw CDP)

### Element Class API (`core/element.py`)

| Method | Return | Notes |
|--------|--------|-------|
| `get_text()` | str | Async text retrieval |
| `get_html()` | str | Inner HTML |
| `to_markdown()` | str | Element → Markdown |
| `click()` / `human_click()` | None | Natural delay variant |
| `type(text)` / `human_type(text, wpm)` | None | WPM-controlled typing |
| `select(sel)` / `select_all(sel)` | Element / List | Child elements |
| `bounds` | dict | Position/size |
| `is_visible()` / `is_enabled()` | bool | State queries |
| `screenshot()` | bytes | Element screenshot |

**Properties:** `text: str`, `attrs: ContraDict`, `tag: str`

### Crawler Interface (`spider/core.py`)

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `start_urls` | `List[str]` | [] | Seed URLs |
| `sitemap_url` | `str` | None | Sitemap XML URL |
| `max_pages` | `int` | 100 | Page limit |
| `max_depth` | `int` | 2 | BFS depth |
| `concurrency` | `int` | 2 | Parallel tabs |
| `formats` | `List[str]` | ["markdown"] | Output types |
| `on_page_crawled` | `Callable` | None | Streaming callback |
| `extractor` | `BaseExtractor` | None | AI extraction hook |

**Method:** `run(output_file, prompt, schema)` → `List[dict]`
**Output formats:** JSON, JSONL, CSV, Markdown

### AI Extractors (`ai/`)

**BaseExtractor ABC:**
```python
async def extract(content: str, prompt: str, schema: dict = None) -> dict
```

**OpenAIExtractor:** `model="gpt-4o"`, `api_key` required
**OllamaExtractor:** `model="llama3"`, `host="http://localhost:11434"`

### Interfaces Lacking Documentation

- `stealth_options` dict keys (e.g., `patch_webdriver`, `patch_canvas`) — undocumented, requires reading `core/stealth.py`
- `Config.add_argument(arg)` — accepts raw Chrome flags without validation
- `Tab.send(cdp_command)` — requires knowledge of CDP spec

### Deprecated/Unstable Interfaces

- `core/util.py:loop()` — deprecated, warns on use
- `Tab.crawl()` — stub, not functional (TODO in source)


---

## 5. Core Files, Functions & Data Structures

### 15 Most Central Files (by dependency + critical logic)

| # | File | LOC | Role | Dependents |
|---|------|-----|------|-----------|
| 1 | `core/tab.py` | 940 | Tab class, aggregates all browsing | Everything user-facing |
| 2 | `core/connection.py` | 322 | WebSocket CDP transport | Browser, Tab, all CDP ops |
| 3 | `core/browser.py` | 424 | Browser lifecycle + process mgmt | start(), Crawler |
| 4 | `core/config.py` | 279 | CLI arg generation | Browser, start() |
| 5 | `core/stealth.py` | 230 | Anti-detection fingerprinting | Browser startup |
| 6 | `core/element.py` | 126 | DOM element wrapper | Tab (query results) |
| 7 | `core/intercept.py` | 223 | Network interception | Tab.network mixin |
| 8 | `spider/core.py` | ~350 | Crawler BFS/sitemap | User scripts |
| 9 | `engine/parser.py` | ~400 | Selector engine (CSS→XPath) | Tab.dom, Element |
| 10 | `extractors/markdown.py` | 82 | HTML→Markdown converter | Tab.markdown(), Crawler |
| 11 | `ai/openai_extractor.py` | ~80 | OpenAI GPT extraction | Crawler |
| 12 | `core/local_proxy.py` | ~150 | Auth proxy tunnel | Browser (proxy auth) |
| 13 | `core/behavior.py` | 187 | Human-like browsing | Element.human_click/type |
| 14 | `core/limiter.py` | 184 | Rate/concurrency limiting | Infrastructure |
| 15 | `core/observability.py` | ~100 | FailureDumper, logging | Error recovery |

### Critical Functions

**`Browser.create(config)` — `core/browser.py`:**
- **Inputs:** Config object
- **Algorithm:** Build CLI args → spawn subprocess → read stderr for debugger URL → regex extract WS endpoint → open WebSocket → enable CDP domains → apply stealth
- **Side effects:** Creates OS process, opens network connection, writes cookies to disk

**`Connection._recv_loop()` — `core/connection.py`:**
- **Inputs:** None (reads from WebSocket)
- **Algorithm:** Infinite async loop → receive JSON → parse method/id → match to pending Futures or dispatch to event handlers
- **Side effects:** Resolves pending CDP commands, fires event callbacks

**`SystemProfile.apply(tab)` — `core/stealth.py`:**
- **Inputs:** Tab instance
- **Algorithm:** Fetch real browser version → sync fingerprint → inject 6 JS scripts → override UA at Network + Emulation layers → set Client Hints → load cookies
- **Side effects:** Modifies browser fingerprint, reads/writes cookie files

**`Crawler._worker()` — `spider/core.py`:**
- **Inputs:** Shared asyncio Queue
- **Algorithm:** Loop: dequeue → check visited → navigate → wait 4s → extract content → discover links → filter by domain → enqueue children → invoke callback
- **Side effects:** Navigates browser tabs, modifies shared state (visited set, results list)

### Core Domain Models

**Config** (`core/config.py`): Browser configuration → Chrome CLI args
**SystemProfile** (`core/stealth.py`): Browser fingerprint container (UA, screen, CPU, memory, version)
**Element** (`core/element.py`): DOM node wrapper (nodeId, backendNodeId, tab reference)
**Selector/Selectors** (`engine/parser.py`): lxml-based parsed HTML with CSS/XPath querying
**ContraDict** (`core/_contradict.py`): Case-insensitive dict for HTML attributes
**ProxyDict** (`engine/engines/toolbelt/navigation.py`): Structured proxy config (server, username, password)

### Configuration Loading

- **Browser path:** Auto-detected from `core/config.py:_default_browser_path()` (scans known paths per OS)
- **User data dir:** `Config.user_data_dir` or `tempfile.mkdtemp()` in `/tmp/`
- **Cookies:** `~/.chuscraper/cookies/{domain}.json` — read on stealth apply, written on profile save
- **Env vars:** No env vars read directly; proxy auth embedded in URL string
- **Feature flags:** `Config.stealth`, `Config.disable_webrtc`, `Config.disable_webgl` etc.

### God Files / Complexity Flags

- **`core/tab.py` (940 lines):** Aggregates 8 mixins into one class. While mixins help, the Tab class has ~60+ methods. This is the single most complex file.
- **`engine/parser.py` (~400 lines):** The Selector class has extensive XPath compilation and DOM traversal — high cyclomatic complexity.


---

## 6. Frameworks, Libraries & Tech Stack

### Languages & Runtimes

| Language | Version | Source |
|----------|---------|--------|
| Python | 3.10 – 3.13 | `pyproject.toml: requires-python = ">=3.10"` |
| JavaScript | ES6+ | `engine/bypasses/*.js` (6 stealth scripts) |

### Major Dependencies (from `pyproject.toml`)

| Library | Version | Purpose |
|---------|---------|---------|
| websockets | ≥14.0 | CDP WebSocket transport |
| pydantic | ≥2.0.0 | Data validation |
| browserforge | ≥1.1.0 | Realistic fingerprint generation |
| curl_cffi | ≥0.7.0 | HTTP client (CFFI SSL) |
| playwright | ≥1.49.0 | Browser dependency (not used for automation) |
| beautifulsoup4 | ≥4.12.0 | HTML parsing |
| lxml | ≥5.0.0 | Fast XPath/XML parsing |
| html2text | ≥2024.2.26 | HTML→text conversion |
| markdownify | ≥0.13 | HTML→Markdown |
| orjson | ≥3.10.0 | Fast JSON serialization |
| cssselect | ≥1.2.0 | CSS selector parsing |
| msgspec | ≥0.18 | High-performance serialization |
| psutil | ≥7.1.0 | Process monitoring |
| mss | ≥9.0.2 | Screenshot capture |
| grapheme | ≥0.6.0 | Unicode grapheme support |
| tld | ≥0.13 | TLD extraction |
| w3lib | ≥2.1.2 | URL normalization |

### Optional Dependencies

| Library | Purpose |
|---------|---------|
| openai | GPT-4o extraction (`ai/openai_extractor.py`) |
| ollama | Local LLM extraction (`ai/ollama_extractor.py`) |

### Build Pipeline

```bash
# Package manager
pip install -e ".[dev]"     # Editable install with dev deps

# Build
python -m build             # Standard PEP 517 build (pyproject.toml)

# Lint/Type Check
ruff check .                # Fast Python linter
mypy --strict .             # Static type checking

# Tests
pytest tests/ -v --asyncio-mode=auto    # Async test suite
pytest --cov=chuscraper                 # Coverage
pytest -n auto                          # Parallel test execution (xdist)
```

### Local Development: Zero to Running

```bash
# 1. Clone
git clone https://github.com/ToufiqQureshi/chuscraper.git
cd chuscraper

# 2. Install
pip install -e ".[dev]"

# 3. Ensure Chrome/Brave is installed (auto-detected)

# 4. Run example
python examples/stealth_verify.py

# 5. Run tests (requires Docker for some tests)
pytest tests/ -v
```

### Containerization & CI/CD

- **Dockerfile:** `tests/Dockerfile` — Docker test environment
- **CI/CD:** `.github/workflows/publish.yml` — PyPI publish on release/tag
  - Runs on `ubuntu-latest`
  - Build with `python -m build`
  - Publish via `twine upload` with `PYPI_API_TOKEN` secret

### Dependency Concerns

- **playwright ≥1.49.0** is listed as a dependency but the project primarily uses CDP directly. It's pulled in for `route` handlers in `engine/engines/toolbelt/navigation.py` and some utility types. This adds ~150MB of browser binaries that may not be needed.
- **curl_cffi ≥0.7.0** has native C dependencies that can be problematic on some platforms.
- No `requirements.txt` or `pip-tools` lockfile; only `pyproject.toml` with minimum versions (no upper bounds).


---

## 7. Capabilities, Features & Use-Cases

### Core Value Proposition

Chuscraper is a **stealth-first, async Python browser automation and web scraping framework** that provides:
- Direct Chrome DevTools Protocol control (no Selenium/Playwright abstraction overhead)
- Industry-leading anti-bot evasion (verified against Cloudflare, DataDome, Akamai, BrowserScan)
- AI-powered data extraction via OpenAI/Ollama
- Universal multi-page crawling with configurable depth and concurrency
- Android mobile app automation via ADB

### Feature List

1. **Stealth Browser Automation** — Launch Chrome/Brave with realistic fingerprints
2. **Anti-Bot Evasion** — 6 JS bypass scripts, dual-layer UA override, Client Hints sync
3. **Cookie Persistence** — Domain-specific cookie storage in `~/.chuscraper/cookies/`
4. **CSS/XPath DOM Queries** — Full selector engine with lxml backend
5. **Human-Like Interaction** — Natural typing (WPM control), human click delays, scroll patterns
6. **Network Interception** — Request/response modification, mock responses, header injection
7. **Proxy Support** — Authenticated proxy via transparent local tunnel
8. **HTML→Markdown** — LLM-ready content extraction with noise removal
9. **Universal Crawler** — BFS traversal, sitemap parsing, domain-restricted, concurrent
10. **AI Data Extraction** — OpenAI GPT-4o and Ollama integration with schema support
11. **Multi-Format Output** — JSON, JSONL, CSV, Markdown
12. **Streaming Callbacks** — Memory-efficient page-by-page processing
13. **Screenshot/PDF** — Full page and element-level capture
14. **Android Mobile Automation** — ADB-based UI interaction, element finding, screenshots
15. **Rate Limiting** — Token bucket + adaptive + concurrency limiters
16. **Session Management** — Duration tracking with auto-warning
17. **Failure Observability** — Auto-dumps page state, screenshot, metadata on errors
18. **WebRTC/WebGL Protection** — Prevent IP and GPU fingerprint leaks
19. **Timezone/Locale Spoofing** — Override browser timezone and language
20. **Request Expectations** — Context manager to wait for specific network events

### 5 Concrete Use-Cases

```
Use-case 1: E-Commerce Price Monitoring
Trigger: User runs script with product URL
Flow: start() → Browser.get(product_page) → Tab.select(".price") → Element.get_text() → store to CSV
Output: Real-time price data bypassing Cloudflare protection

Use-case 2: AI-Powered Content Extraction
Trigger: User provides URL + natural language prompt
Flow: start() → Browser.get(url) → Tab.markdown() → OpenAIExtractor.extract(md, prompt, schema)
Output: Structured JSON matching user-defined schema (e.g., product names, specs)

Use-case 3: Full-Site Crawling with Sitemap
Trigger: User provides sitemap.xml URL + output format
Flow: Crawler._fetch_sitemap() → parse URLs → BFS workers → concurrent extraction → save_to_file()
Output: Complete site content in JSON/Markdown, respecting depth/page limits

Use-case 4: Mobile App Data Collection
Trigger: User connects Android device, runs script
Flow: MobileDevice.connect() → find_element(resource_id) → tap/type → screenshot
Output: Screenshots and UI data from native Android apps

Use-case 5: Anti-Bot Evasion Testing
Trigger: User runs stealth_verify.py against detection sites
Flow: start(stealth=True) → navigate to SannySoft/BrowserScan → screenshot proof
Output: Visual verification of 100% trust score on anti-bot detection platforms
```

### Partially Implemented / TODO Features

- `Tab.crawl()` in `core/tab.py` — marked TODO, returns URL list only (real crawler is `spider/core.py`)
- `core/util.py:loop()` — deprecated, warns on use
- Adaptive selector persistence (`engine/core/storage.py`) — SQLite storage exists but integration with Tab selectors is incomplete
- `Crawler` does not support JavaScript-heavy SPAs that require interaction before content loads

### README vs Reality Gaps

- README and docs describe the framework as supporting "complex multi-step workflows" — while possible, there's no built-in workflow engine or step orchestration
- Mobile automation is documented but the `mobile/` module has no tests and limited error handling
- The crawler's "AI extraction" feature depends on external LLM APIs; no fallback for offline use beyond Ollama


---

## 8. Code Quality & Onboarding Assessment

### Naming Consistency

| Convention | Standard | Followed? |
|-----------|----------|-----------|
| Files | snake_case | ✅ Uniform (core/browser.py, engine/parser.py) |
| Functions | snake_case async | ✅ Uniform (get_text(), select_all()) |
| Classes | PascalCase | ✅ Uniform (Browser, Tab, Element, Config) |
| Constants | UPPER_SNAKE_CASE | ✅ Uniform (BYPASS_FILES, COOKIE_DIR) |
| Private | Leading underscore | ✅ Uniform (_process_pid, _recv_loop()) |
| Modules | snake_case | ✅ Uniform |

### Modularity Assessment

**Single-Responsibility:** Generally good. Tab's 8 mixins each handle one domain. Browser manages lifecycle. Config handles args. Stealth is isolated.

**Coupling:**
- Tab ↔ Connection: Tight (Tab inherits Connection). Necessary but limits independent testing.
- Element ↔ Tab: Tight (Element holds Tab reference for CDP calls). Unavoidable.
- Crawler ↔ Browser: Tight (directly instantiates Browser). Could benefit from dependency injection.
- Stealth ↔ Config: Loose (through apply() method). Well-designed.

**Circular Dependencies:** None detected. All imports flow unidirectionally: Browser → Tab → Connection → CDP.

### Test Coverage

**11 test files, ~2,700 LOC of tests**

| Area | Tested | Coverage |
|------|--------|----------|
| Crawler basic flow | ✅ | Good |
| Crawler depth/domain filtering | ✅ | Comprehensive |
| Crawler output formats | ✅ | JSON, JSONL, CSV, MD |
| Crawler streaming callbacks | ✅ | Callback invocation verified |
| Sitemap XML parsing | ✅ | Nested sitemaps included |
| AI extraction (OpenAI/Ollama) | ✅ | Mock-based |
| Browser interactions | ✅ | Click, type, navigate |
| Production patterns | ✅ | 3,302 lines of production scenarios |

**Critical Untested Areas:**
1. ❌ Network interception (`core/intercept.py`) — no tests
2. ❌ Stealth evasion effectiveness — no automated anti-bot tests
3. ❌ Mobile automation (`mobile/`) — no tests at all
4. ❌ LocalAuthProxy (`core/local_proxy.py`) — complex async TCP forwarding untested
5. ❌ Error recovery paths — connection failures, timeout handling sparse
6. ❌ Rate limiter / SessionManager — no tests despite being production-critical
7. ❌ Cross-platform process management — Windows job objects untested

### Documentation Level

| Artifact | Quality |
|----------|---------|
| README.md | ✅ Comprehensive (badges, install, quickstart, examples) |
| Website docs | ✅ 17 guides covering all major features |
| Inline comments | ⚠️ Moderate — good in critical paths, sparse in utilities |
| Docstrings | ⚠️ Selective — public API documented, internal helpers sparse |
| Type hints | ✅ Excellent (Optional, Union, Literal, TYPE_CHECKING used) |
| Architecture docs | ❌ Missing — no formal architecture guide |
| API reference | ❌ No auto-generated API docs (mkdocstrings configured but not deployed) |

### Error Handling Consistency

- **Connection errors:** ✅ Caught and retried in `Connection.connect()`
- **CDP protocol errors:** ✅ Wrapped in `ProtocolException` with code + message
- **Timeouts:** ✅ `asyncio.TimeoutError` handled in wait methods
- **Process cleanup:** ✅ atexit handlers for POSIX/Windows
- **Logging levels:** ⚠️ Inconsistent (mix of logger.error, logger.debug, logger.warning)
- **Silent failures:** ⚠️ Some paths ignore exceptions (mobile bounds parsing, cookie loading)
- **Custom exceptions:** ❌ Limited hierarchy — mostly generic exceptions

### Onboarding Difficulty: **Medium-Hard**

**Justification:**
- ✅ Clean, intuitive entry point: `await chuscraper.start()` → Browser
- ✅ Good example scripts (11 examples) covering common patterns
- ✅ Type hints throughout help IDE navigation
- ✅ Docusaurus website with step-by-step guides
- ❌ CDP complexity hidden but surfaces on errors (user gets `ProtocolException` without context)
- ❌ stealth_options dict keys undocumented (must read source)
- ❌ Tab has 60+ methods across 8 mixins — overwhelming to discover
- ❌ Proxy auth architecture non-obvious (hidden LocalAuthProxy server)
- ❌ No architecture overview document

### Top 5 Most Confusing Parts for New Developers

1. **LocalAuthProxy** (`core/local_proxy.py`) — Hidden TCP server that transparently injects proxy auth headers. User must understand why Chrome connects to localhost.
2. **Stealth Options** (`core/stealth.py`) — `stealth_options` dict accepts keys like `patch_webdriver`, `patch_canvas` but these are undocumented and only discoverable by reading source.
3. **Engine vs Core** — `engine/parser.py` provides a Selector class, but `core/element.py` wraps CDP DOM nodes. The relationship between parsed HTML (engine) and live DOM (core) is unclear.
4. **Tab Mixin Discovery** — With 60+ methods split across 8 mixin files, finding the right method requires checking navigation.py, dom.py, actions.py, network.py, wait.py, storage.py, screenshot.py, or evaluation.py.
5. **CDP Domain Exposure** — `Tab.send(cdp_command)` accepts raw CDP commands. Users can accidentally break state by sending protocol-level commands without understanding the state machine.


---

## 9. Strengths, Risks & Strategic Assessment

### Top 5 Architectural Strengths

1. **Dual-Layer Stealth Implementation** — `core/stealth.py` + `engine/bypasses/*.js`
   - Network-level UA override (CDP `network.setUserAgentOverride`)
   - Emulation-level navigator spoofing (CDP `emulation.setUserAgentOverride`)
   - 6 independent JS bypass scripts injected before page load
   - Client Hints synchronized to prevent UA/kernel mismatch
   - Verified against Cloudflare Turnstile, DataDome, Akamai, SannySoft, BrowserScan, PixelScan

2. **Mixin-Based Tab Decomposition** — `core/tabs/*.py`
   - 8 focused mixins prevent a single 2000+ line god class
   - Each mixin is independently readable and maintainable
   - New capabilities can be added as additional mixins without touching existing code

3. **Universal Crawler with AI Hooks** — `spider/core.py`
   - Supports both BFS and sitemap-based discovery
   - Concurrent workers (configurable, default 2)
   - Streaming callbacks for memory efficiency
   - Pluggable AI extractors (OpenAI, Ollama, or custom via BaseExtractor ABC)
   - Multi-format output (JSON, JSONL, CSV, Markdown)

4. **Production-Grade Observability** — `core/observability.py`, `core/limiter.py`
   - FailureDumper captures page content + screenshot + metadata on errors
   - Adaptive rate limiter auto-adjusts based on error rates
   - Session duration management prevents long-running detection
   - Structured logging context for observability pipelines

5. **Cross-Platform Process Management** — `core/process.py`, `core/config.py`
   - Auto-detects Chrome/Brave binary on Windows, macOS, Linux
   - Windows job objects ensure child process cleanup on parent crash
   - Root user detection auto-disables sandbox flag
   - atexit handlers prevent zombie processes on all platforms

### Top 5 Technical Risks

1. **Stealth Evasion Brittleness** — Anti-bot vendors continuously update detection. The 6 JS bypass scripts are static and will become obsolete without regular updates. There is no automated test to verify evasion continues working, creating silent regression risk.

2. **Single Chrome Dependency** — The entire framework assumes Chrome/Brave as the browser backend. There is no abstraction layer to support Firefox, WebKit, or other CDP-compatible browsers. A Chrome breaking change in CDP protocol could break the entire framework.

3. **No Backpressure in Crawler** — `spider/core.py` uses `asyncio.Queue` without backpressure. If workers produce URLs faster than they consume, memory grows unbounded. The only protection is `max_pages`, which limits total pages but not queue depth.

4. **Proxy Auth Tunnel Security** — `core/local_proxy.py` opens a TCP server on localhost without authentication. Any local process can connect through the proxy tunnel and use the configured proxy credentials. This is a credential leak risk on multi-tenant systems.

5. **No Retry/Circuit Breaker for External APIs** — AI extractors (`ai/openai_extractor.py`, `ai/ollama_extractor.py`) make direct HTTP calls to external LLMs without retry logic, timeout configuration, or circuit breakers. A slow LLM response blocks the entire crawler worker.

### Anti-Patterns Present

- **Leaky Abstraction:** `Tab.send(cdp_command)` exposes raw CDP protocol, bypassing all safety checks
- **Incomplete Abstraction:** `engine/` provides a Selector class for parsed HTML, but `core/element.py` wraps live DOM — two incompatible query interfaces for similar concepts
- **Hidden Side Effects:** `SystemProfile.apply()` writes cookie files to disk, modifies browser fingerprint — not obvious from method signature
- **Tight Coupling to OS:** Process spawning, path detection, and cleanup are deeply OS-specific with `if platform.system()` branches scattered across multiple files

### Implementation Comprehensiveness Rating: **3 — MVP**

**Justification:**
- Primary use-cases (stealth scraping, AI extraction, crawling) work end-to-end ✅
- Anti-bot evasion verified against real-world vendors ✅
- 11 example scripts demonstrate working functionality ✅
- Published to PyPI with CI/CD pipeline ✅
- **However:**
  - Test coverage gaps in critical areas (interception, mobile, proxy, rate limiting)
  - No automated anti-bot regression tests
  - Mobile module has no tests and limited error handling
  - No retry/circuit breaker patterns for external dependencies
  - Limited custom exception hierarchy
  - No formal architecture documentation
  - Some TODO stubs remain (Tab.crawl())

### Suitability Assessment

**Best suited for:**
- ✅ Ad-hoc web scraping scripts that need to bypass anti-bot protections
- ✅ AI-powered data extraction pipelines (natural language → structured data)
- ✅ Small-to-medium crawling jobs (100s–1000s of pages)
- ✅ Stealth automation tasks (account creation, form filling behind WAF)
- ✅ Developer tooling for browser testing/debugging

**Ill-suited for:**
- ❌ Enterprise-scale production crawling (10M+ pages) — no distributed architecture, no backpressure
- ❌ Mission-critical data pipelines — insufficient error handling, no retry patterns
- ❌ Multi-browser testing — locked to Chrome/Brave CDP
- ❌ Real-time streaming data ingestion — no WebSocket/SSE subscription, no persistent connection pools
- ❌ High-frequency data collection (sub-second intervals) — rate limiters exist but are not battle-tested

---

## Live Web Data Ingestion Engine Rating

### Effectiveness for Live Web Data Ingestion: 3.5 / 5

**What works well for data ingestion:**
- ✅ Stealth bypass enables access to sites that block traditional scrapers
- ✅ AI extraction (OpenAI/Ollama) automates unstructured → structured data transformation
- ✅ Crawler with BFS + sitemap covers both discovery and targeted extraction
- ✅ Streaming callbacks (`on_page_crawled`) enable memory-efficient processing
- ✅ Multi-format output (JSON, JSONL) suits downstream ETL pipelines
- ✅ Rate limiting + session management prevent detection-based bans

**What limits it for serious data ingestion:**
- ❌ **No persistent connection management** — each crawl creates/destroys a browser process. For continuous ingestion, this overhead is significant.
- ❌ **No incremental/delta crawling** — no mechanism to track what has changed since the last run. Every crawl is a full re-scan.
- ❌ **No distributed architecture** — single-machine, single-browser. Cannot scale horizontally for high-volume ingestion.
- ❌ **No queue integration** — no native support for RabbitMQ, Kafka, Redis Streams, or SQS for job distribution and result delivery.
- ❌ **No schema evolution** — AI extraction returns freeform JSON. No version tracking, no schema migration, no data quality checks.
- ❌ **4-second hardcoded wait** in Crawler worker — `spider/core.py` has a `await asyncio.sleep(4)` after each page load. This limits throughput to ~15 pages/minute per worker.
- ❌ **No webhook/event output** — results are file-based or in-memory. No push to HTTP endpoints, databases, or message queues built-in.
- ❌ **No monitoring/alerting** — FailureDumper captures state but doesn't alert. No metrics export (Prometheus, StatsD, etc.).

**Verdict:** Chuscraper is a strong foundation for **ad-hoc and scheduled batch scraping** with excellent anti-bot evasion. It is **not yet** a live data ingestion engine. To serve that role, it would need: persistent browser pools, incremental change detection, distributed queue integration, schema validation, and push-based output delivery.

---

*Analysis produced by parallel codebase exploration. All findings reference actual source files across 124 Python files and 10 JavaScript files totaling 35,067 lines of code.*