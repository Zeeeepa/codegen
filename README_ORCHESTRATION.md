# 🚀 Multi-Agent Orchestration for Codegen

A sophisticated multi-agent orchestration framework that enables parallel agent execution, consensus building, and self-healing workflows.

## Quick Start

```python
from codegen.orchestration import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator(
    api_key="sk-92083737-4e5b-4a48-a2a1-f870a3a096a6",
    org_id=323
)

# Council Pattern: 3-stage consensus
result = await orchestrator.run_council(
    "What are best practices for REST API authentication?"
)
print(result['stage3']['response'])

# Pro Mode: Tournament synthesis
result = await orchestrator.run_pro_mode(
    "Write a binary search function",
    num_runs=20
)
print(result['final'])

# Basic Orchestration: N agents + synthesis
result = await orchestrator.orchestrate(
    "Create email validation function",
    num_agents=9
)
print(result['final'])
```

## Patterns

### 1. Council Pattern (3-Stage Consensus)

```
Stage 1: Individual responses → Stage 2: Peer rankings → Stage 3: Chairman synthesis
```

**When to use:** Complex questions, consensus needed, peer validation

### 2. Pro Mode (Tournament Synthesis)

```
N candidates → Group synthesis → Final synthesis
```

**When to use:** High-quality code generation, exploring solution space

### 3. Basic Orchestration

```
N agents in parallel → Vote/synthesize → Final response
```

**When to use:** Simple tasks, quick results

## Features

✅ **Parallel Multi-Agent Execution** - Run multiple Codegen agents simultaneously  
✅ **3-Stage Council Pattern** - Consensus building with peer rankings  
✅ **Tournament-Style Synthesis** - Efficient for large agent counts  
✅ **Automatic Error Recovery** - Built-in retry and fallback logic  
✅ **Cost Optimization** - Smart caching and early termination  

## Architecture

Based on patterns from:
- **LLM Council** - Multi-stage consensus building
- **Pro Mode** - Tournament-style synthesis

Adapted to use **Codegen agent execution** instead of direct API calls.

## Configuration

```python
# Set via environment or constructor
CODEGEN_API_KEY = "sk-..."
CODEGEN_ORG_ID = 323
COUNCIL_MODELS = ["gpt-4o", "claude-sonnet-4.5", "gemini-3-pro"]
MAX_PARALLEL_AGENTS = 9
AGENT_TIMEOUT_SECONDS = 300
```

## Full Example

```python
import asyncio
from codegen.orchestration import MultiAgentOrchestrator

async def main():
    orchestrator = MultiAgentOrchestrator()
    
    # Run council for complex question
    result = await orchestrator.run_council(
        "Design a scalable microservices architecture"
    )
    
    # Access stages
    print("Individual responses:", len(result['stage1']))
    print("Peer rankings:", len(result['stage2']))
    print("Final synthesis:", result['stage3']['response'])

asyncio.run(main())
```

## See Also

- `src/codegen/orchestration.py` - Full implementation
- Council Pattern: https://arxiv.org/abs/2305.14867
- Pro Mode: Tournament-style LLM synthesis

## License

Same as Codegen - see main LICENSE file.

