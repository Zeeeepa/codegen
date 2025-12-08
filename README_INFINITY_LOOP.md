# 🔄 Infinity CICD Loop System

An autonomous, self-improving continuous research and development system that never stops learning.

## Quick Start

```python
from codegen.infinity_loop import InfinityLoopOrchestrator

# Initialize
orchestrator = InfinityLoopOrchestrator(
    api_key="your-api-key",
    org_id=323
)

# Define context
context = """
Current System: My application
Goal: Continuously improve performance and features
Repository: org/repo
"""

# Run single loop iteration
execution = await orchestrator.run_loop(context)

# Or run continuous loop
await orchestrator.run_continuous_loop(context, max_iterations=10)
```

## The Infinity Loop

```
┌─────────────────────────────────────────────────────┐
│  INFINITY CICD LOOP                                 │
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │ RESEARCH │───▶│ ANALYZE  │───▶│IMPLEMENT │     │
│  └──────────┘    └──────────┘    └──────────┘     │
│       ▲                                   │         │
│       │          ┌──────────┐    ┌──────────┐     │
│       └──────────│INTEGRATE │◀───│BENCHMARK │     │
│                  └──────────┘    └──────────┘     │
│                        ▲               ▲           │
│                        │               │           │
│                  ┌─────┴───┐     ┌────┴────┐      │
│                  │  TEST   │────▶│   FIX   │      │
│                  │ (loop)  │◀────│ (loop)  │      │
│                  └─────────┘     └─────────┘      │
└─────────────────────────────────────────────────────┘
```

## Stages

### 1. 🔬 Research Agent
**Purpose**: Discover improvement opportunities

**Process**:
- Analyzes current system state
- Researches SOTA (state of the art) solutions
- Searches academic papers, GitHub repos, blogs
- Identifies specific optimization opportunities
- Generates detailed PRD

**Output**: Research Report + PRD

### 2. 📊 Analysis Agent
**Purpose**: Validate feasibility and plan implementation

**Process**:
- Validates technical feasibility
- Estimates implementation cost/effort
- Identifies risks and blockers
- Designs implementation strategy
- Defines success metrics

**Output**: Analysis Report with Implementation Plan

### 3. 💻 Implementation Agent
**Purpose**: Generate code changes

**Process**:
- Generates all necessary code changes
- Writes comprehensive tests
- Creates clear documentation
- Prepares PR description

**Output**: Implementation ready for PR creation

### 4. 🧪 Test Agent
**Purpose**: Validate changes work correctly

**Process**:
- Runs full test suite
- Runs performance benchmarks
- Runs security scans (trufflehog, etc.)
- Checks code quality (linting, type checking)

**Output**: Test Report (PASS/FAIL)

### 5. 🔧 Fix Agent (Conditional Loop)
**Purpose**: Resolve test failures

**Process**:
- Analyzes all test failures
- Identifies root causes
- Generates fixes
- Re-runs tests

**Loop**: Repeats up to 5 times until tests pass

**Output**: Fixed PR

### 6. 📈 Benchmark Agent
**Purpose**: Compare performance vs baseline

**Process**:
- Runs performance profiling
- Measures resource usage (CPU, memory, etc.)
- Compares against baseline metrics
- Calculates improvement percentages

**Output**: Benchmark Report with comparison

### 7. 🎯 Integration Agent
**Purpose**: Decide whether to integrate changes

**Decision Logic**:
```python
if improvement > 5% and no_regressions:
    merge_pr()
    update_baseline()
    record_success()
    continue_loop()
else:
    close_pr()
    record_failure()
    learn_from_failure()
    continue_loop()
```

**Output**: Integration decision + learnings

## State Persistence

All loop executions are persisted to SQLite database at `~/.codegen/infinity_loop.db`.

**Schema**:
```sql
CREATE TABLE loop_executions (
    loop_id TEXT PRIMARY KEY,
    stage TEXT NOT NULL,
    iteration INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    research_report TEXT,
    analysis_report TEXT,
    pr_number INTEGER,
    test_report TEXT,
    benchmark_report TEXT,
    integration_decision INTEGER,
    baseline_metrics TEXT,
    new_metrics TEXT,
    improvement_pct REAL,
    error_count INTEGER,
    last_error TEXT,
    created_at TEXT,
    updated_at TEXT
)
```

## Configuration

Configure via environment variables:

```bash
export CODEGEN_API_KEY="sk-..."
export CODEGEN_ORG_ID="323"
```

Or pass to constructor:

```python
orchestrator = InfinityLoopOrchestrator(
    api_key="sk-...",
    org_id=323
)
```

**Constants**:
- `MAX_FIX_ITERATIONS = 5` - Max test/fix cycles
- `IMPROVEMENT_THRESHOLD = 0.05` - 5% improvement required
- `STATE_DB_PATH = ~/.codegen/infinity_loop.db` - State database location

## Examples

### Single Loop Iteration

```python
import asyncio
from codegen.infinity_loop import InfinityLoopOrchestrator

async def run_single():
    orchestrator = InfinityLoopOrchestrator()
    
    context = """
    Current System: E-commerce API
    Goal: Improve response times and reduce database queries
    Repository: myorg/ecommerce-api
    """
    
    execution = await orchestrator.run_loop(context)
    
    print(f"Loop ID: {execution.loop_id}")
    print(f"Stage: {execution.stage.value}")
    print(f"Integrated: {execution.integration_decision}")
    print(f"Improvement: {execution.improvement_pct}%")

asyncio.run(run_single())
```

### Continuous Loop (10 iterations)

```python
import asyncio
from codegen.infinity_loop import InfinityLoopOrchestrator

async def run_continuous():
    orchestrator = InfinityLoopOrchestrator()
    
    context = """
    Current System: Machine Learning Pipeline
    Goal: Continuously optimize model performance and inference speed
    Repository: myorg/ml-pipeline
    """
    
    # Run 10 iterations
    await orchestrator.run_continuous_loop(context, max_iterations=10)

asyncio.run(run_continuous())
```

### Query Loop History

```python
from codegen.infinity_loop import LoopStateManager

state_mgr = LoopStateManager()

# Get recent executions
executions = state_mgr.list_executions(limit=10)

for exec in executions:
    print(f"{exec.loop_id}: {exec.stage.value} - {exec.improvement_pct}%")

# Get specific execution
execution = state_mgr.get_execution("loop_1733598523")
print(execution.research_report)
```

## Benefits

✅ **Fully Autonomous** - No human intervention required  
✅ **Self-Healing** - Automatically fixes test failures  
✅ **Continuous Learning** - Each iteration improves on the last  
✅ **Persistent State** - Survives restarts and crashes  
✅ **Quality Gates** - Only integrates if improvement > 5%  
✅ **Risk Mitigation** - Tests, benchmarks, and validates before merging  
✅ **Audit Trail** - Full history of all decisions and changes  

## Architecture

Built on top of:
- **Codegen Agent Execution** - All agents use Codegen SDK
- **Async/Await** - Non-blocking parallel execution
- **SQLite** - Lightweight persistent state
- **Modular Agents** - Each stage is independent and replaceable

## Future Enhancements

- [ ] Actual PR creation/merging via GitHub API
- [ ] Real performance benchmarking integration
- [ ] Multi-repository support
- [ ] Web dashboard for monitoring
- [ ] Slack/email notifications
- [ ] Advanced learning from past iterations
- [ ] Cost optimization and caching
- [ ] Parallel multi-loop execution

## Comparison: Orchestration vs Infinity Loop

| Feature | Multi-Agent Orchestration | Infinity CICD Loop |
|---------|--------------------------|---------------------|
| **Purpose** | Get better answers | Continuous improvement |
| **Pattern** | Council/Pro Mode synthesis | Research → Apply → Integrate |
| **Duration** | Single run | Infinite iterations |
| **State** | Stateless | Persistent database |
| **Output** | Final synthesized answer | Merged PRs + metrics |
| **Learning** | Per-query | Accumulates over time |
| **Use Case** | Complex questions | Autonomous development |

## When to Use

**Use Infinity Loop when:**
- You want continuous autonomous improvement
- You have clear metrics to benchmark
- You want a self-healing development process
- You want to accumulate learnings over time

**Use Orchestration when:**
- You need a single high-quality answer
- You want consensus from multiple perspectives
- You're exploring solution space with many candidates
- You don't need persistent state

## License

Same as Codegen - see main LICENSE file.

## See Also

- `src/codegen/infinity_loop.py` - Full implementation
- `src/codegen/orchestration.py` - Multi-agent orchestration
- DevOps Research: Continuous Delivery and improvement loops

