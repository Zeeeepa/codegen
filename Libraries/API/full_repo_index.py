#!/usr/bin/env python3
"""
Comprehensive Repository Indexer for Codegen API
Analyzes all repositories with extensive indexing prompts for AI context
"""

import os, sys, json, time, requests, argparse
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
ORG_ID = "323"
API_TOKEN = "sk-92083737-4e5b-4a48-a2a1-f870a3a096a6"
BASE_URL = "https://api.codegen.com"
RATE_LIMIT = 6  # 10 req/min = 1 req per 6 seconds

# Load comprehensive prompt from external file
def load_prompt_template():
    try:
        # Try ENHANCED_PROMPT.md first, fallback to PROMPT.md
        for prompt_file in ['/tmp/ENHANCED_PROMPT.md', '/tmp/PROMPT.md']:
            if os.path.exists(prompt_file):
                with open(prompt_file, 'r') as f:
            return f.read()
                break
    except FileNotFoundError:
        return get_default_prompt()

def get_default_prompt():
    """Comprehensive indexing prompt for repository analysis"""
    return """
# 🔬 COMPREHENSIVE REPOSITORY ANALYSIS

Analyze this repository with maximum detail for AI context knowledge transfer.

## Required Analysis (10 Sections):

### 1. Architecture Overview
- Design patterns (Singleton, Factory, MVC, Observer, Strategy, etc.)
- Module hierarchy and dependency trees
- Entry points (main functions, CLI, API endpoints, event handlers, cron jobs)
- Data flow paths (Request → Processing → Storage → Response)
- State management mechanisms
- Concurrency models (threading, async/await, event loops, message queues)

### 2. Function Catalog (Atomic Level)
For EVERY function with >5 lines of code:
- Fully qualified name (module.Class.method)
- Complete signature with type annotations
- Purpose (1-2 sentences)
- Parameters (type, description, default values)
- Return type and meaning
- Side effects (file I/O, network, database, state mutations)
- Dependencies (internal function calls)
- Called by (reverse dependencies)
- Complexity (Big-O time/space)
- Error handling (exceptions raised/caught)
- Performance notes (bottlenecks, optimizations, caching)

### 3. Feature Catalog
For EACH feature:
- Feature name and description
- Implementation location (file:line)
- Dependencies (packages/modules required)
- Configuration options (env vars, config files)
- Usage examples (working code snippets)
- Known limitations and edge cases
- Status (Stable/Beta/Experimental/Deprecated)

### 4. API Surface Documentation
Document ALL external interfaces:
- REST endpoints (method, path, params, request/response schemas, status codes, auth)
- GraphQL (queries, mutations, subscriptions with full schemas)
- CLI commands (subcommands, flags, arguments, examples)
- Events emitted/consumed (event names, payload schemas, triggers)
- Webhooks (incoming/outgoing, URL patterns, payloads)
- RPC/gRPC (service definitions, protobuf schemas)

### 5. Dependency Analysis
- Direct dependencies (package, version, purpose, license, security status)
- Transitive dependency tree visualization
- Security vulnerabilities (CVE IDs, severity, affected versions, fixed versions, exploitability, impact)
- License compliance (GPL, MIT, Apache, proprietary, conflicts)
- Update recommendations (current vs latest, breaking changes)
- Dependency health (maintenance status, last commit, open issues, security response time)

### 6. Code Quality Metrics
- Test coverage (overall %, per-module %, uncovered critical paths)
- Cyclomatic complexity (average, top 10 most complex functions)
- Code duplication (duplicate blocks, locations, similarity %)
- Documentation coverage (% with docstrings, missing docs)
- Linting issues (errors, warnings by category)
- Type safety (type coverage %, Any/unknown usage count)
- Security scan results (SAST findings, hardcoded secrets, SQL injection risks, XSS vulnerabilities)

### 7. Integration Assessment (5 Dimensions - Rate 1-10)
**Reusability (X/10)**:
- Clear, documented APIs?
- Modular design with separation of concerns?
- Dependency injection vs hard-coded dependencies?
- Configuration externalized?
**Justification**: [detailed explanation]

**Maintainability (X/10)**:
- Code quality (clean, readable, conventions followed)
- Documentation quality (comprehensive/partial/minimal)
- Test coverage (high/medium/low)
- Technical debt indicators
**Justification**: [detailed explanation]

**Performance (X/10)**:
- Response times (avg, p95, p99)
- Resource usage (CPU, memory, I/O)
- Scalability potential (horizontal/vertical)
- Bottleneck analysis
**Justification**: [detailed explanation]

**Security (X/10)**:
- Authentication/authorization implementation
- Input validation coverage
- Known CVEs and severity
- Security best practices followed
**Justification**: [detailed explanation]

**Completeness (X/10)**:
- Production-ready? (Yes/Partial/No)
- Missing critical features?
- Error handling coverage
- Monitoring/observability
**Justification**: [detailed explanation]

**OVERALL SUITABILITY SCORE**:
```
Score = (Reusability × 0.25) + (Maintainability × 0.25) + 
        (Performance × 0.20) + (Security × 0.20) + (Completeness × 0.10)
      = X.X / 10
```

**Integration Complexity**: Low/Medium/High
**Recommended Use Cases**: [specific scenarios]
**Integration Risks**: [potential issues]

### 8. Prioritized Recommendations
**🔴 CRITICAL** (Fix Immediately - Security/Data Loss):
1. [Issue] - [Solution] (Time estimate: X hours)

**🟠 HIGH PRIORITY** (This Sprint - Performance/Stability):
1. [Issue] - [Solution] (Time estimate: X hours)

**🟡 MEDIUM PRIORITY** (Next Sprint - Code Quality):
1. [Issue] - [Solution] (Time estimate: X hours)

**🟢 LOW PRIORITY** (Backlog - Nice-to-haves):
1. [Issue] - [Solution] (Time estimate: X hours)

### 9. Technology Stack (Complete Breakdown)
**Languages**:
| Language | Files | LOC | Percentage |
|----------|-------|-----|------------|
| Python   | 145   | 23,456 | 78% |

**Frameworks**: Backend, Frontend, Testing with versions
**Databases**: Primary, Cache, Search with schemas
**External Services**: APIs, SaaS integrations
**Build System**: Package managers, build tools, CI/CD
**Testing**: Unit, Integration, E2E, Load testing frameworks
**Deployment**: Containerization, Orchestration, CI/CD, Monitoring

### 10. Use Cases & Integration Examples
**Primary Use Cases** (Top 3-5):
1. [Use case name]
```python
# Working code example
```

**Integration Patterns**:
- Standalone usage (installation, configuration, execution)
- As a library (import, initialization, usage)
- As a microservice (deployment, communication, scaling)
- Event-driven integration (message queues, webhooks)
- Batch processing (scheduling, data processing)
- Real-time streaming (data ingestion, processing)

## Output Requirements

**Create**: `Libraries/API/{repo_name}.md`

**Include**:
- Executive summary (2-3 paragraphs highlighting key findings)
- Quick stats table (language, LOC, test coverage, dependencies, last commit)
- All 10 sections above with detailed analysis
- Overall suitability score with breakdown
- Integration complexity assessment (Low/Medium/High)

**Format**: Professional markdown with tables, code blocks, clear headers

## Pull Request Requirements

**Branch**: `analysis/{repo_name}`
**File**: `Libraries/API/{repo_name}.md`
**Commit**: `feat: Add comprehensive atomic-level analysis for {repo_name}`
**Title**: `Analysis: {repo_name} - Complete Suitability Assessment`

**PR Body Template**:
```markdown
## 📊 Repository Analysis: {repo_name}

### Overall Suitability Score: X.X/10

### 🎯 Top 3 Findings:
1. [Critical/Important finding]
2. [Important finding]
3. [Notable finding]

### 📈 Integration Assessment:
- **Reusability:** X/10
- **Maintainability:** X/10
- **Performance:** X/10
- **Security:** X/10
- **Completeness:** X/10

### 🔧 Integration Complexity: [Low/Medium/High]

### 📋 Recommendations:
- 🔴 X critical issues
- 🟠 X high priority items
- 🟡 X medium priority items

**Full analysis**: `Libraries/API/{repo_name}.md`
```

---

**Begin comprehensive atomic-level analysis now. Be thorough, specific, and provide actionable insights for AI context knowledge transfer.**
"""

class CodegenRepoIndexer:
    def __init__(self, org_id: str, api_token: str, base_url: str = BASE_URL):
        self.org_id = org_id
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.prompt_template = load_prompt_template()
    
    def fetch_all_repos(self) -> List[Dict]:
        """Fetch all repositories from Codegen API with pagination"""
        repos = []
        page = 0
        
        while True:
            skip = page * 100
            url = f"{self.base_url}/v1/organizations/{self.org_id}/repos?limit=100&skip={skip}"
            
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                items = data.get('items', [])
                repos.extend(items)
                
                if len(items) < 100:
                    break
                
                page += 1
                time.sleep(0.5)
                
            except requests.RequestException as e:
                print(f"Error fetching repos: {e}", file=sys.stderr)
                break
        
        return repos
    
    def create_agent_run(self, repo_id: int, repo_name: str, repo_full_name: str) -> Optional[Dict]:
        """Create an agent run for repository analysis"""
        prompt = self.prompt_template.format(
            repo_name=repo_name,
            repo_full_name=repo_full_name,
            timestamp=datetime.now().isoformat()
        )
        
        url = f"{self.base_url}/v1/organizations/{self.org_id}/agent/run"
        payload = {
            "prompt": prompt,
            "repo_id": repo_id
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating agent run for {repo_name}: {e}", file=sys.stderr)
            return None
    
    def index_repository(self, repo: Dict, retry_count: int = 3) -> Optional[Dict]:
        """Index a single repository with retry logic"""
        repo_id = repo['id']
        repo_name = repo['name']
        repo_full_name = repo['full_name']
        
        for attempt in range(retry_count):
            result = self.create_agent_run(repo_id, repo_name, repo_full_name)
            
            if result and result.get('id'):
                return {
                    'repo_id': repo_id,
                    'repo_name': repo_name,
                    'repo_full_name': repo_full_name,
                    'run_id': result['id'],
                    'status': result.get('status'),
                    'web_url': result.get('web_url'),
                    'timestamp': datetime.now().isoformat()
                }
            
            if attempt < retry_count - 1:
                time.sleep(RATE_LIMIT * 2)  # Wait longer on retry
        
        return None
    
    def index_all_sequential(self, repos: List[Dict]) -> Dict:
        """Index all repositories sequentially with rate limiting"""
        results = {'success': [], 'failed': []}
        total = len(repos)
        
        print(f"
🚀 Starting sequential indexing of {total} repositories...")
        print(f"⏱️  Rate: 1 request every {RATE_LIMIT} seconds (10 per minute)")
        print(f"⏱️  Estimated time: {(total * RATE_LIMIT) // 60} minutes
")
        
        start_time = time.time()
        
        for idx, repo in enumerate(repos, 1):
            repo_name = repo['name']
            print(f"[{idx:4d}/{total:4d}] {repo_name:<50}", end=' ', flush=True)
            
            result = self.index_repository(repo)
            
            if result:
                results['success'].append(result)
                print(f"✅ RUN #{result['run_id']}")
            else:
                results['failed'].append({'repo_id': repo['id'], 'repo_name': repo_name})
                print(f"❌ FAILED")
            
            # Progress update every 50 repos
            if idx % 50 == 0:
                elapsed = time.time() - start_time
                rate = idx / (elapsed / 60)  # repos per minute
                remaining = total - idx
                eta = (remaining / rate) if rate > 0 else 0
                
                print(f"
  📊 Progress: {idx}/{total} | ✅ {len(results['success'])} | ❌ {len(results['failed'])}")
                print(f"  ⏱️  ETA: {int(eta)} minutes
")
            
            # Official rate limit: 10 requests per minute
            time.sleep(RATE_LIMIT)
        
        duration = time.time() - start_time
        return {
            'results': results,
            'stats': {
                'total': total,
                'success': len(results['success']),
                'failed': len(results['failed']),
                'duration_seconds': int(duration),
                'duration_minutes': int(duration / 60)
            }
        }
    
    def index_all_parallel(self, repos: List[Dict], max_workers: int = 5) -> Dict:
        """Index all repositories in parallel (respecting rate limits)"""
        results = {'success': [], 'failed': []}
        total = len(repos)
        
        print(f"
🚀 Starting parallel indexing of {total} repositories...")
        print(f"🔀 Workers: {max_workers}")
        print(f"⏱️  Estimated time: {(total * RATE_LIMIT) // (60 * max_workers)} minutes
")
        
        start_time = time.time()
        completed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_repo = {executor.submit(self.index_repository, repo): repo for repo in repos}
            
            for future in as_completed(future_to_repo):
                repo = future_to_repo[future]
                completed += 1
                
                try:
                    result = future.result()
                    if result:
                        results['success'].append(result)
                        print(f"[{completed:4d}/{total:4d}] {repo['name']:<50} ✅ RUN #{result['run_id']}")
                    else:
                        results['failed'].append({'repo_id': repo['id'], 'repo_name': repo['name']})
                        print(f"[{completed:4d}/{total:4d}] {repo['name']:<50} ❌ FAILED")
                except Exception as e:
                    results['failed'].append({'repo_id': repo['id'], 'repo_name': repo['name'], 'error': str(e)})
                    print(f"[{completed:4d}/{total:4d}] {repo['name']:<50} ❌ ERROR: {e}")
                
                # Progress update
                if completed % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = completed / (elapsed / 60)
                    remaining = total - completed
                    eta = (remaining / rate) if rate > 0 else 0
                    
                    print(f"
  📊 Progress: {completed}/{total} | ✅ {len(results['success'])} | ❌ {len(results['failed'])}")
                    print(f"  ⏱️  ETA: {int(eta)} minutes
")
        
        duration = time.time() - start_time
        return {
            'results': results,
            'stats': {
                'total': total,
                'success': len(results['success']),
                'failed': len(results['failed']),
                'duration_seconds': int(duration),
                'duration_minutes': int(duration / 60)
            }
        }

def main():
    parser = argparse.ArgumentParser(description='Comprehensive Repository Indexer for Codegen API')
    parser.add_argument('--parallel', type=int, metavar='N', help='Enable parallel execution with N workers (default: sequential)')
    parser.add_argument('--output', '-o', default='indexing_results.json', help='Output file for results (default: indexing_results.json)')
    parser.add_argument('--limit', type=int, help='Limit number of repositories to process (for testing)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🔬 COMPREHENSIVE REPOSITORY INDEXER")
    print("=" * 80)
    print(f"Organization ID: {ORG_ID}")
    print(f"Mode: {'Parallel' if args.parallel else 'Sequential'}")
    if args.parallel:
        print(f"Workers: {args.parallel}")
    print("=" * 80)
    
    # Initialize indexer
    indexer = CodegenRepoIndexer(ORG_ID, API_TOKEN)
    
    # Fetch all repositories
    print("
📥 Fetching all repositories...")
    repos = indexer.fetch_all_repos()
    
    if not repos:
        print("❌ No repositories found or error fetching repos", file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Fetched {len(repos)} repositories")
    
    # Apply limit if specified
    if args.limit:
        repos = repos[:args.limit]
        print(f"⚠️  Limited to {len(repos)} repositories for testing")
    
    # Index repositories
    if args.parallel:
        final_results = indexer.index_all_parallel(repos, max_workers=args.parallel)
    else:
        final_results = indexer.index_all_sequential(repos)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    # Print summary
    stats = final_results['stats']
    print("
" + "=" * 80)
    print("✅ INDEXING COMPLETE")
    print("=" * 80)
    print(f"Total: {stats['total']}")
    print(f"✅ Success: {stats['success']} ({stats['success'] * 100 // stats['total']}%)")
    print(f"❌ Failed: {stats['failed']}")
    print(f"⏱️  Duration: {stats['duration_minutes']} minutes ({stats['duration_seconds']} seconds)")
    print(f"📁 Results saved to: {args.output}")
    print("
🔗 Track runs: https://codegen.com/runs")
    print("=" * 80)

if __name__ == '__main__':
    main()
