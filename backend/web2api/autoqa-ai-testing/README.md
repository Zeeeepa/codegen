# AutoQA AI Testing System

Production-ready test automation with natural language YAML definitions, self-healing selectors, and visual regression.

**No LLM/AI dependency required** - All core features use deterministic algorithms.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Where to Start?

The fastest way to get started is to **automatically generate tests** for any website:

```bash
# Install
pip install autoqa-ai-testing

# Build tests automatically for any website
autoqa build https://your-website.com --output my_tests.yaml

# Run the generated tests
autoqa run my_tests.yaml
```

That's it! AutoQA will:
1. Crawl your website and discover all interactive elements
2. Detect login forms, navigation flows, and key user journeys
3. Generate a complete YAML test specification
4. Execute the tests with self-healing selector recovery

---

## Quick Start

### 1. Generate Tests Automatically

```bash
# Simple page
autoqa build https://example.com -o tests/example.yaml

# With authentication (auto-detects login forms)
autoqa build https://myapp.com/login -u testuser -p secret123 -o tests/login.yaml

# Deep crawl (multiple pages)
autoqa build https://myapp.com --depth 2 --max-pages 20 -o tests/full.yaml
```

### 2. Run Tests

```bash
# Run single test
autoqa run tests/example.yaml

# Run all tests with verbose output
autoqa run tests/ -v

# Parallel execution with JUnit report
autoqa run tests/ --parallel --output-format junit --output-file results.xml
```

### 3. Write Custom Tests (YAML)

```yaml
name: Login Flow Test
description: Verify user can log in successfully

variables:
  base_url: https://example.com

steps:
  - name: Navigate to login
    action: navigate
    url: ${base_url}/login

  - name: Enter credentials
    action: type
    selector: "#username"
    text: testuser

  - name: Enter password
    action: type
    selector: "#password"
    text: secret123

  - name: Click login
    action: click
    selector: "button[type='submit']"

  - name: Verify dashboard
    action: assert
    assertion:
      selector: ".dashboard"
      operator: is_visible
      message: "Dashboard should be visible after login"
```

---

## Key Features

- **Auto Test Generation** - Build tests automatically from any URL
- **Natural Language YAML** - Human-readable test definitions
- **Self-Healing Selectors** - Automatic recovery from broken selectors (no AI required)
- **Visual Regression** - Screenshot comparison with anti-aliasing tolerance
- **ML Assertions** - OCR, color analysis, layout validation, accessibility checks
- **Version Tracking** - Compare test runs over time with visual diffs
- **Parallel Execution** - Run tests concurrently with resource-aware scaling
- **CI/CD Ready** - GitHub Actions, GitLab CI, Jenkins, Azure, CircleCI templates

---

## Installation

```bash
# From source
git clone https://github.com/Olib-AI/owl-projects.git
cd owl-projects/autoqa-ai-testing
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

### Environment Setup

Create a `.env` file:

```bash
# Required: Remote browser connection
OWL_BROWSER_URL=https://your-browser-server.example.com
OWL_BROWSER_TOKEN=your-auth-token

# Optional: Storage
ARTIFACT_PATH=./artifacts
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `autoqa build <url>` | Auto-generate tests from a webpage |
| `autoqa run <paths>` | Execute test specifications |
| `autoqa validate <paths>` | Validate YAML syntax |
| `autoqa history <test>` | View test version history |
| `autoqa diff <test>` | Compare test versions |
| `autoqa ci <provider>` | Generate CI/CD config |
| `autoqa server` | Start API server |

See [CLI Reference](docs/TECHNICAL.md#cli-reference) for full options.

---

## Example: Visual Regression

```yaml
steps:
  - action: navigate
    url: https://example.com

  - action: visual_assert
    visual_assertion:
      baseline_name: homepage
      threshold_mode: normal  # strict, normal, loose
      auto_mask_dynamic: true  # Mask ads, timestamps
      anti_aliasing_tolerance: 0.5
```

---

## Example: Self-Healing

Tests automatically recover from broken selectors:

```bash
autoqa run tests/ --healing-history ./healing.json
```

Self-healing uses deterministic strategies:
- Text content matching
- ID/name/aria-label fallbacks
- Attribute fuzzy matching
- XPath alternatives

---

## Configuration

### Variables

```yaml
variables:
  base_url: https://example.com
  api_key: ${env:API_KEY}           # Environment variable
  password: ${vault:secrets/pass}    # HashiCorp Vault
```

### Version Tracking

```yaml
versioning:
  enabled: true
  storage_path: .autoqa/history
  capture_screenshots: true
```

```bash
# View history
autoqa history "My Test" --limit 10

# Compare runs
autoqa diff "My Test" --latest 2 --output html
```

---

## CI/CD Integration

Generate ready-to-use CI configurations:

```bash
# GitHub Actions
autoqa ci github -o .github/workflows/autoqa.yml

# GitLab CI (parallel)
autoqa ci gitlab --parallel --nodes 3 -o .gitlab-ci.yml

# Jenkins
autoqa ci jenkins -o Jenkinsfile
```

---

## API Server

Start the REST API:

```bash
autoqa server --port 8080
```

Key endpoints:
- `POST /api/v1/jobs` - Submit test job
- `GET /api/v1/jobs/{id}` - Get job status
- `POST /api/v1/build` - Auto-generate tests
- `GET /api/v1/runs` - List test runs

See [API Reference](docs/TECHNICAL.md#api-reference) for full documentation.

---

## Documentation

- **[Technical Documentation](docs/TECHNICAL.md)** - Complete architecture, module reference, DSL schema
- **[Examples](examples/)** - Sample test specifications

---

## Project Structure

```
autoqa-ai-testing/
├── src/autoqa/
│   ├── builder/       # Auto Test Builder (test generation)
│   ├── runner/        # Test execution engine
│   ├── dsl/           # YAML parser and models
│   ├── llm/           # Optional LLM integration
│   ├── concurrency/   # Parallel execution
│   ├── visual/        # Visual regression
│   ├── versioning/    # Version tracking
│   └── api/           # REST API
├── tests/             # Test specifications
├── examples/          # Example tests
└── docs/              # Documentation
```

---

## License

MIT License - see LICENSE file for details.

---

## Links

- **Repository**: [https://github.com/Olib-AI/owl-projects](https://github.com/Olib-AI/owl-projects)
- **Homepage**: [https://owlbrowser.net](https://owlbrowser.net)
