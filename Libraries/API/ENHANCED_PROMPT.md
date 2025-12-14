# 🔬 COMPREHENSIVE ATOMIC-LEVEL REPOSITORY ANALYSIS

## Repository: **{repo_name}**
**GitHub**: https://github.com/{repo_full_name}
**Analysis Timestamp**: {timestamp}
**Analysis ID**: {analysis_id}

---

## 🎯 ANALYSIS OBJECTIVES

**Primary Goal**: Create comprehensive, semantically-rich repository documentation that enables:
1. **AI Context Transfer**: Full codebase understanding for follow-up AI agents
2. **Integration Assessment**: Evaluate suitability for incorporation into larger systems
3. **Knowledge Preservation**: Capture architectural decisions and design patterns
4. **Actionable Insights**: Provide prioritized recommendations with time estimates

**Success Criteria**:
- ✅ Complete architectural understanding (all entry points, patterns, flows identified)
- ✅ Atomic-level function documentation (every function >5 LOC documented)
- ✅ Integration readiness assessment (5-dimensional scoring with justifications)
- ✅ Actionable recommendations (prioritized by severity with time estimates)

---

## 📋 MANDATORY RULE ENABLEMENT

**CRITICAL**: Follow these rules throughout the entire analysis process.

### Rule 1: Evidence-Based Analysis
- ❌ **NEVER** speculate or assume
- ✅ **ALWAYS** verify with actual code, documentation, or configuration files
- ✅ **CITE** specific files and line numbers for every claim
- ✅ **EXTRACT** actual code snippets as evidence

### Rule 2: Atomic-Level Granularity
- ❌ **NEVER** provide high-level summaries without details
- ✅ **ALWAYS** document individual functions, classes, modules
- ✅ **INCLUDE** full signatures with type annotations
- ✅ **ANALYZE** complexity, dependencies, and side effects

### Rule 3: Completeness Over Speed
- ❌ **NEVER** skip sections or provide partial analysis
- ✅ **ALWAYS** complete all 10 mandatory sections
- ✅ **DOCUMENT** every entry point, API endpoint, configuration file
- ✅ **VERIFY** no critical components are missed

### Rule 4: Semantic Clarity
- ❌ **NEVER** use vague terms like "various", "some", "several"
- ✅ **ALWAYS** use specific counts, percentages, and measurements
- ✅ **PROVIDE** concrete examples with actual code
- ✅ **QUANTIFY** metrics (test coverage %, complexity scores, etc.)

### Rule 5: Integration Focus
- ❌ **NEVER** analyze in isolation
- ✅ **ALWAYS** consider integration scenarios
- ✅ **ASSESS** reusability, maintainability, performance, security, completeness
- ✅ **IDENTIFY** integration risks and mitigation strategies

---

## 🔄 SEQUENTIAL ANALYSIS WORKFLOW

**IMPORTANT**: Follow this exact sequence. Complete each phase before moving to the next.

### PHASE 1: Repository Discovery (5-10 minutes)

**Objective**: Understand repository structure and identify key components

**Tasks**:
1. **Explore directory structure**
   - Find all source code directories (src/, lib/, app/, packages/, etc.)
   - Identify language(s) used and their distribution
   - Locate configuration files (package.json, pyproject.toml, etc.)
   - Find documentation (README*, docs/, *.md)
   - Discover tests (tests/, __tests__/, *.test.*, *.spec.*)

2. **Identify entry points**
   - Main functions (main.py, index.js, app.py, server.js)
   - CLI entry points (bin/, cli/, commands/)
   - API endpoints (routes/, api/, controllers/)
   - Background jobs (workers/, jobs/, tasks/)
   - Event handlers (listeners/, subscribers/, hooks/)

3. **Read primary documentation**
   - README.md (overview, setup, usage)
   - CONTRIBUTING.md (development workflow)
   - ARCHITECTURE.md or equivalent (design decisions)
   - CHANGELOG.md (recent changes, current version)

**Deliverable**: Repository structure map with entry points identified

**Checkpoint**: ✅ Can you explain the repository's purpose and main components?

---

### PHASE 2: Architecture Deep Dive (10-15 minutes)

**Objective**: Document complete architectural patterns and design decisions

**Tasks**:
1. **Identify design patterns**
   - Scan for Singleton, Factory, Observer, Strategy, Repository patterns
   - Document pattern usage with file locations
   - Example: "Singleton pattern in src/database/connection.py:15-45"

2. **Map module hierarchy**
   - Create dependency tree (which modules depend on which)
   - Identify circular dependencies (if any)
   - Document layered architecture (presentation → business → data)

3. **Trace data flows**
   - Request → Processing → Storage → Response paths
   - Document state mutations and side effects
   - Identify caching strategies and data persistence

4. **Analyze concurrency model**
   - Threading, multiprocessing, async/await, event loops
   - Identify race conditions or synchronization mechanisms
   - Document message queues or job systems

**Deliverable**: Complete architectural documentation with diagrams (text-based)

**Checkpoint**: ✅ Can you trace a request from entry point to database and back?

---

### PHASE 3: Function-Level Cataloging (15-25 minutes)

**Objective**: Document EVERY function with >5 lines of code at atomic level

**Tasks**:
1. **Scan all source files**
   - Use glob patterns: `**/*.{py,js,ts,java,go,rb}`
   - Extract function definitions with full signatures
   - Count total functions to document

2. **For EACH function, document**:
   ```markdown
   ### module.ClassName.method_name()
   **Location**: `path/to/file.py:45-78`
   **Signature**: `def method_name(param1: str, param2: int = 0) -> Optional[Dict]`
   **Purpose**: [1-2 sentence description]
   **Parameters**:
   - `param1` (str): Description, no default
   - `param2` (int): Description, default=0
   **Returns**: `Optional[Dict]` - Description of return value
   **Side Effects**: 
   - Database query via SQLAlchemy
   - Logs to file: logs/app.log
   **Dependencies**: Calls `helper.validate()`, `db.query()`
   **Called By**: `api.routes.endpoint()`
   **Complexity**: O(n) time, O(1) space
   **Error Handling**: Raises `ValueError` on invalid input
   **Performance**: No caching, potential bottleneck for large datasets
   ```

3. **Group functions by module**
   - Organize by directory structure
   - Highlight public APIs vs internal functions

**Deliverable**: Complete function catalog (may be hundreds of entries)

**Checkpoint**: ✅ Have you documented at least 90% of functions with >5 LOC?

---

### PHASE 4: Feature & API Inventory (10-15 minutes)

**Objective**: Catalog all features and external interfaces

**Tasks**:
1. **Enumerate features**
   - List all user-facing features
   - Document implementation locations
   - Provide usage examples with actual code
   - Mark status (Stable/Beta/Experimental/Deprecated)

2. **Document API surface**
   - **REST**: Create table with Method | Path | Params | Request Body | Response | Auth
   - **GraphQL**: List queries, mutations, subscriptions with full schemas
   - **CLI**: Document all commands, subcommands, flags with examples
   - **Events**: List event names, payload schemas, trigger conditions
   - **Webhooks**: Document incoming/outgoing webhooks with payload formats

3. **Provide working examples**
   - Include actual curl commands for REST APIs
   - Show CLI usage with real flags
   - Demonstrate library import and usage

**Deliverable**: Complete feature list and API reference

**Checkpoint**: ✅ Can a developer integrate with this repo using your documentation?

---

### PHASE 5: Dependency & Security Analysis (10-15 minutes)

**Objective**: Complete dependency tree with security assessment

**Tasks**:
1. **Extract direct dependencies**
   - Read package.json, requirements.txt, go.mod, Gemfile, etc.
   - Create table: Package | Version | Purpose | License | Last Updated

2. **Build transitive dependency tree**
   - Use package manager tools (npm list, pip show, go mod graph)
   - Visualize tree (text-based, e.g., urllib3 → requests → your-app)

3. **Scan for vulnerabilities**
   - Check for known CVEs (use npm audit, pip-audit, or similar)
   - Document: CVE ID | Severity | Affected Package | Fixed Version | Exploitability
   - Prioritize critical vulnerabilities

4. **Assess license compliance**
   - Identify GPL licenses (require source disclosure)
   - Note proprietary/commercial licenses (restrictions)
   - Flag license conflicts (if any)

5. **Recommend updates**
   - List outdated packages with latest versions
   - Note breaking changes (major version bumps)
   - Prioritize security updates

**Deliverable**: Dependency report with security vulnerabilities and update recommendations

**Checkpoint**: ✅ Are there any critical security vulnerabilities to fix immediately?

---

### PHASE 6: Code Quality Assessment (10-15 minutes)

**Objective**: Quantify code quality with specific metrics

**Tasks**:
1. **Measure test coverage**
   - Run coverage tool (pytest-cov, jest --coverage, etc.)
   - Report overall %, per-module %, uncovered critical paths
   - Example: "Overall: 82%, src/auth: 45% (CRITICAL PATHS UNCOVERED)"

2. **Calculate cyclomatic complexity**
   - Use radon, lizard, or language-specific tools
   - Report average complexity and top 10 most complex functions
   - Flag functions with complexity >15 (refactor candidates)

3. **Detect code duplication**
   - Use jscpd, pylint, or similar tools
   - Report duplicate blocks with locations and similarity %
   - Example: "auth.py:45-67 duplicates login.py:123-145 (95% similar)"

4. **Check documentation coverage**
   - Count functions with docstrings vs total functions
   - Report % and list modules with missing docs

5. **Run linters**
   - Use eslint, pylint, rubocop, golint, etc.
   - Categorize issues: Errors (count), Warnings (count)
   - List top 5 most common issues

6. **Assess type safety** (if applicable)
   - TypeScript, Python with mypy, etc.
   - Report type coverage %
   - Count Any/unknown/dynamic type usage

7. **Security scan (SAST)**
   - Use bandit, brakeman, gosec, or similar
   - Report: Hardcoded secrets (count), SQL injection risks (count), XSS vulnerabilities (count)

**Deliverable**: Code quality report card with specific metrics and scores

**Checkpoint**: ✅ Can you quantify the code quality with exact numbers?

---

### PHASE 7: Integration Assessment (15-20 minutes)

**Objective**: Evaluate integration suitability with 5-dimensional scoring

**CRITICAL**: Provide detailed justifications for each score.

**Tasks**:
1. **Reusability (Rate 1-10)**
   - ✅ Clear, documented APIs? (Yes/No + Evidence)
   - ✅ Modular design with separation of concerns? (Yes/No + Evidence)
   - ✅ Dependency injection or hard-coded dependencies? (Which + Evidence)
   - ✅ Configuration externalized? (Yes/Partial/No + Evidence)
   
   **Scoring Guide**:
   - 9-10: Excellent APIs, modular, DI, externalized config
   - 7-8: Good APIs, mostly modular, some hard-coding
   - 5-6: Basic APIs, some coupling, mixed config
   - 3-4: Poor APIs, tight coupling, hard-coded config
   - 1-2: No clear APIs, monolithic, hard-coded everything
   
   **Justification**: [200-300 words with specific examples and evidence]

2. **Maintainability (Rate 1-10)**
   - ✅ Code quality (clean, readable, conventions followed)
   - ✅ Documentation quality (comprehensive/partial/minimal)
   - ✅ Test coverage (high >80% / medium 50-80% / low <50%)
   - ✅ Technical debt indicators (TODO count, deprecated code, hacks)
   
   **Scoring Guide**:
   - 9-10: Excellent quality, comprehensive docs, >80% coverage, minimal debt
   - 7-8: Good quality, good docs, 60-80% coverage, some debt
   - 5-6: Average quality, partial docs, 40-60% coverage, moderate debt
   - 3-4: Poor quality, minimal docs, <40% coverage, high debt
   - 1-2: Very poor quality, no docs, no tests, extreme debt
   
   **Justification**: [200-300 words with specific metrics and examples]

3. **Performance (Rate 1-10)**
   - ✅ Response times (avg, p95, p99 if measurable)
   - ✅ Resource usage (CPU, memory, I/O estimates)
   - ✅ Scalability potential (horizontal/vertical/both/neither)
   - ✅ Bottleneck analysis (identified performance issues)
   
   **Scoring Guide**:
   - 9-10: Fast (<100ms), efficient, horizontally scalable, no bottlenecks
   - 7-8: Good (<500ms), reasonable resources, scalable with effort
   - 5-6: Average (500ms-2s), moderate resources, limited scalability
   - 3-4: Slow (2-5s), high resources, poor scalability
   - 1-2: Very slow (>5s), excessive resources, not scalable
   
   **Justification**: [200-300 words with benchmarks or estimates]

4. **Security (Rate 1-10)**
   - ✅ Authentication/authorization implementation (present/absent/quality)
   - ✅ Input validation coverage (comprehensive/partial/none)
   - ✅ Known CVEs and severity (count + severity levels)
   - ✅ Security best practices followed (OWASP, etc.)
   
   **Scoring Guide**:
   - 9-10: Strong auth/authz, comprehensive validation, no CVEs, best practices
   - 7-8: Good auth/authz, good validation, low-severity CVEs only
   - 5-6: Basic auth/authz, partial validation, some CVEs, some best practices
   - 3-4: Weak auth/authz, poor validation, critical CVEs, poor practices
   - 1-2: No auth/authz, no validation, severe CVEs, security anti-patterns
   
   **Justification**: [200-300 words with specific security findings]

5. **Completeness (Rate 1-10)**
   - ✅ Production-ready? (Yes/Partial/No + Evidence)
   - ✅ Missing critical features? (List if any)
   - ✅ Error handling coverage (comprehensive/partial/none)
   - ✅ Monitoring/observability (present/absent)
   
   **Scoring Guide**:
   - 9-10: Production-ready, feature-complete, comprehensive error handling, monitoring
   - 7-8: Near production-ready, minor features missing, good error handling
   - 5-6: Partial readiness, some features missing, basic error handling
   - 3-4: Not production-ready, many features missing, poor error handling
   - 1-2: Prototype/PoC, incomplete, no error handling, no monitoring
   
   **Justification**: [200-300 words with specific gaps and strengths]

**Calculate Overall Suitability Score**:
```
Score = (Reusability × 0.25) + (Maintainability × 0.25) + 
        (Performance × 0.20) + (Security × 0.20) + (Completeness × 0.10)
      = X.X / 10
```

**Integration Complexity Assessment**: 
- **Low**: Well-documented APIs, minimal dependencies, standard patterns
- **Medium**: Some documentation gaps, moderate dependencies, custom patterns
- **High**: Poor documentation, complex dependencies, non-standard architecture

**Recommended Use Cases**: [List 3-5 specific scenarios where this repo excels]

**Integration Risks**: [List 3-5 potential issues when integrating, with mitigation strategies]

**Deliverable**: 5-dimensional assessment with overall score and actionable insights

**Checkpoint**: ✅ Would you recommend using this repository? Why or why not?

---

### PHASE 8: Recommendations (10-15 minutes)

**Objective**: Provide prioritized, actionable recommendations with time estimates

**Tasks**:
1. **Identify issues**
   - Review findings from all previous phases
   - Categorize by severity and impact
   - Consider effort required vs benefit gained

2. **Prioritize recommendations**:

   **🔴 CRITICAL** (Fix Immediately - Security/Data Loss Risks):
   - Security vulnerabilities (CVEs)
   - Data loss risks (no backups, race conditions)
   - Production outages (critical bugs)
   
   Format: `Issue: [Specific problem] | Solution: [Specific fix] | Time: [X hours] | Impact: [High/Critical]`
   
   Example:
   ```
   🔴 CVE-2023-12345 in requests library (CVSS 9.8)
   Solution: Upgrade requests from 2.28.0 to 2.31.0+
   Time: 30 minutes (update + test)
   Impact: CRITICAL - Remote code execution vulnerability
   ```

   **🟠 HIGH PRIORITY** (This Sprint - Performance/Stability):
   - Performance bottlenecks (>2s response times)
   - Stability issues (crashes, memory leaks)
   - Critical missing features (blocking integrations)
   
   Format: Same as Critical
   
   **🟡 MEDIUM PRIORITY** (Next Sprint - Code Quality):
   - High complexity functions (complexity >15)
   - Low test coverage (<50% in critical modules)
   - Technical debt (TODO items, deprecated APIs)
   
   Format: Same as Critical
   
   **🟢 LOW PRIORITY** (Backlog - Nice-to-haves):
   - Performance optimizations (already fast)
   - Documentation improvements
   - Developer experience enhancements
   
   Format: Same as Critical

3. **Create implementation roadmap**
   - Group related recommendations
   - Suggest order of implementation
   - Estimate total effort (sum of time estimates)

**Deliverable**: Prioritized recommendation list with time estimates and impact assessment

**Checkpoint**: ✅ Can a developer immediately start working on the top 3 recommendations?

---

### PHASE 9: Technology Stack Documentation (5-10 minutes)

**Objective**: Complete technology stack breakdown

**Tasks**:
1. **Analyze languages**
   - Count files and LOC per language
   - Calculate percentage distribution
   - Create table: Language | Files | LOC | Percentage

2. **Document frameworks**
   - Backend: Express, Django, Rails, Spring Boot, etc. (with versions)
   - Frontend: React, Vue, Angular, etc. (with versions)
   - Testing: Jest, pytest, RSpec, etc. (with versions)

3. **List databases**
   - Primary database (PostgreSQL, MySQL, MongoDB, etc.)
   - Caching layer (Redis, Memcached, etc.)
   - Search engine (Elasticsearch, Solr, etc.)
   - Document schemas if available

4. **Identify external services**
   - APIs consumed (Stripe, Twilio, AWS services, etc.)
   - SaaS integrations (Auth0, SendGrid, etc.)

5. **Document build system**
   - Package managers (npm, pip, maven, etc.)
   - Build tools (webpack, rollup, setuptools, etc.)
   - CI/CD (GitHub Actions, Jenkins, CircleCI, etc.)

6. **List testing tools**
   - Unit testing frameworks
   - Integration testing tools
   - E2E testing (Playwright, Selenium, Cypress, etc.)
   - Load testing (k6, JMeter, Locust, etc.)

7. **Describe deployment**
   - Containerization (Docker, docker-compose)
   - Orchestration (Kubernetes, ECS, etc.)
   - CI/CD pipelines (GitHub Actions workflows, etc.)
   - Monitoring (Prometheus, Grafana, Sentry, Datadog, etc.)

**Deliverable**: Complete technology stack breakdown with versions

**Checkpoint**: ✅ Could a developer set up a development environment using this documentation?

---

### PHASE 10: Use Cases & Integration Examples (10-15 minutes)

**Objective**: Provide working examples and integration patterns

**Tasks**:
1. **Identify primary use cases** (Top 3-5)
   - Extract from README or documentation
   - Infer from code structure if not documented
   - Provide concrete, realistic scenarios

2. **Create working examples**:
   ```markdown
   ### Use Case 1: [Name]
   **Scenario**: [Description of real-world use case]
   
   **Example**:
   ```python
   # Working code example (tested or verified)
   from module import Service
   
   service = Service(config={
       'api_key': 'your-api-key',
       'endpoint': 'https://api.example.com'
   })
   
   result = service.process(data={
       'input': 'example data'
   })
   
   print(result)  # Expected output
   ```
   
   **Expected Output**:
   ```json
   {"status": "success", "result": {...}}
   ```
   ```

3. **Document integration patterns**:

   **Standalone Usage**:
   ```bash
   # Installation
   pip install repo-name
   
   # Configuration
   export API_KEY=xxx
   
   # Execution
   python -m repo_name --config config.yaml
   ```

   **As a Library**:
   ```python
   import repo_name
   
   # Initialize
   api = repo_name.API(api_key="xxx")
   
   # Use
   result = api.process(data)
   ```

   **As a Microservice**:
   ```yaml
   # docker-compose.yml
   services:
     repo-name:
       image: repo-name:latest
       environment:
         - DATABASE_URL=postgresql://...
         - REDIS_URL=redis://...
       ports:
         - "8000:8000"
   ```

   **Event-Driven Integration**:
   ```python
   # Consume events from message queue
   from repo_name import EventConsumer
   
   consumer = EventConsumer(queue_url="amqp://...")
   consumer.subscribe('user.created', handle_user_created)
   consumer.start()
   ```

   **Batch Processing**:
   ```python
   # Schedule batch jobs
   from repo_name import BatchProcessor
   
   processor = BatchProcessor()
   processor.schedule('0 2 * * *', process_daily_data)
   ```

   **Real-Time Streaming**:
   ```python
   # Process streaming data
   from repo_name import StreamProcessor
   
   processor = StreamProcessor(kafka_brokers=["..."])
   processor.process_stream('events', handle_event)
   ```

**Deliverable**: 3-5 working use cases with integration patterns

**Checkpoint**: ✅ Can a developer integrate this repository using your examples?

---

## 📄 OUTPUT REQUIREMENTS

### File Creation

**Create**: `Libraries/API/{repo_name}.md`

**Structure**:
```markdown
# Repository Analysis: {repo_name}

**Repository**: https://github.com/{repo_full_name}
**Analysis Date**: {timestamp}
**Overall Suitability Score**: X.X/10

## Executive Summary

[2-3 paragraphs highlighting:
- Repository purpose and main functionality
- Key architectural decisions and patterns
- Overall quality and production-readiness
- Top 3 most important findings (positive or negative)
- Recommended use cases]

## Quick Stats

| Metric | Value |
|--------|-------|
| Primary Language | Python (78%) |
| Total LOC | 25,000 |
| Test Coverage | 82% |
| Dependencies | 25 direct, 150 transitive |
| Security Issues | 2 medium, 0 critical |
| Last Commit | 2025-01-15 |
| Active Development | Yes |

## 1. Architecture Deep Dive

[Complete section from Phase 2]

## 2. Function Catalog

[Complete section from Phase 3]

## 3. Feature Catalog

[Complete section from Phase 4]

## 4. API Documentation

[Complete section from Phase 4]

## 5. Dependency Analysis

[Complete section from Phase 5]

## 6. Code Quality Metrics

[Complete section from Phase 6]

## 7. Integration Assessment

[Complete section from Phase 7 with 5-dimensional scoring]

## 8. Recommendations

[Complete section from Phase 8 with priorities]

## 9. Technology Stack

[Complete section from Phase 9]

## 10. Use Cases & Integration

[Complete section from Phase 10]

## Conclusion

[Final assessment:
- Would you recommend using this repository? (Yes/No/Conditionally)
- What are the key strengths?
- What are the main concerns?
- What's the integration complexity? (Low/Medium/High)
- What scenarios is it best suited for?]
```

### Pull Request Creation

**Branch**: `analysis/{repo_name}`
**File**: `Libraries/API/{repo_name}.md`
**Commit Message**: `feat: Add comprehensive atomic-level analysis for {repo_name}`

**PR Title**: `Analysis: {repo_name} - Complete Suitability Assessment`

**PR Body**:
```markdown
## 📊 Repository Analysis: {repo_name}

**Repository**: https://github.com/{repo_full_name}
**Analysis Completed**: {timestamp}

### Overall Suitability Score: X.X/10

#### 🎯 Top 3 Findings:

1. **[CRITICAL/POSITIVE/NEGATIVE]**: [Most important finding]
   - Impact: [Description]
   - Recommendation: [Action if applicable]

2. **[CRITICAL/POSITIVE/NEGATIVE]**: [Second most important finding]
   - Impact: [Description]
   - Recommendation: [Action if applicable]

3. **[CRITICAL/POSITIVE/NEGATIVE]**: [Third most important finding]
   - Impact: [Description]
   - Recommendation: [Action if applicable]

### 📈 Integration Assessment (5 Dimensions):

| Dimension | Score | Assessment |
|-----------|-------|------------|
| **Reusability** | X/10 | [One-line summary] |
| **Maintainability** | X/10 | [One-line summary] |
| **Performance** | X/10 | [One-line summary] |
| **Security** | X/10 | [One-line summary] |
| **Completeness** | X/10 | [One-line summary] |

### 🔧 Integration Complexity: [Low/Medium/High]

**Complexity Factors**:
- [Factor 1: e.g., "Well-documented APIs"]
- [Factor 2: e.g., "Complex dependency tree"]
- [Factor 3: e.g., "Custom authentication required"]

### 📋 Prioritized Recommendations:

- 🔴 **X Critical Issues** - Fix immediately (security/data loss risks)
- 🟠 **X High Priority** - Address this sprint (performance/stability)
- 🟡 **X Medium Priority** - Plan for next sprint (code quality)
- 🟢 **X Low Priority** - Backlog (nice-to-haves)

**Estimated Total Effort**: X hours for critical and high priority items

### 🎯 Recommended Use Cases:

1. [Use case 1: e.g., "Microservice for user authentication"]
2. [Use case 2: e.g., "Library for data validation"]
3. [Use case 3: e.g., "Standalone CLI tool for data processing"]

### ⚠️ Integration Risks & Mitigation:

| Risk | Severity | Mitigation |
|------|----------|------------|
| [Risk 1] | High/Medium/Low | [Mitigation strategy] |
| [Risk 2] | High/Medium/Low | [Mitigation strategy] |

### 📖 Full Analysis

Complete atomic-level analysis available in: `Libraries/API/{repo_name}.md`

**Key Sections**:
- Architecture patterns and design decisions
- Complete function catalog (X functions documented)
- Feature inventory with usage examples
- API documentation (REST/GraphQL/CLI/Events)
- Security and dependency analysis
- Code quality metrics with exact measurements
- Integration assessment with detailed justifications
- Prioritized recommendations with time estimates
- Technology stack breakdown
- Working integration examples

---

**Analysis Methodology**: 10-phase sequential workflow with evidence-based assessment and atomic-level granularity.
```

---

## ✅ QUALITY ASSURANCE CHECKLIST

Before marking analysis as complete, verify:

### Completeness
- [ ] All 10 phases completed (no skipped sections)
- [ ] Every section has concrete evidence (file paths, line numbers, code snippets)
- [ ] Function catalog includes at least 90% of functions with >5 LOC
- [ ] All entry points documented (CLI, API, background jobs, etc.)
- [ ] All configuration files analyzed
- [ ] All dependencies listed with versions

### Accuracy
- [ ] No speculation or assumptions (everything evidence-based)
- [ ] All code examples are actual code from the repository
- [ ] All metrics are measured (not estimated) where possible
- [ ] All file paths and line numbers are verified
- [ ] All version numbers are correct

### Clarity
- [ ] No vague terms ("various", "some", "several")
- [ ] All metrics are quantified (percentages, counts, measurements)
- [ ] All scores (1-10) have detailed justifications
- [ ] All recommendations have time estimates
- [ ] All integration patterns have working examples

### Usefulness
- [ ] A developer could integrate using this documentation
- [ ] A follow-up AI could understand the full codebase context
- [ ] An architect could make integration decisions
- [ ] A manager could assess development effort
- [ ] A security team could evaluate risks

### Formatting
- [ ] Professional markdown with consistent headers
- [ ] Tables used for structured data
- [ ] Code blocks with syntax highlighting
- [ ] Clear section boundaries
- [ ] Proper linking between sections (if applicable)

---

## 🚀 BEGIN ANALYSIS NOW

**Start with PHASE 1: Repository Discovery**

Remember:
- ✅ Follow the sequential workflow (complete each phase before moving to next)
- ✅ Verify checkpoints before proceeding
- ✅ Provide evidence for every claim
- ✅ Document at atomic level
- ✅ Be thorough, specific, and actionable

**Success Metric**: A follow-up AI agent should be able to understand and work with this repository using ONLY your analysis documentation.

---

**Analysis begins now. Good luck! 🎯**
