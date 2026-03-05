# Multi-Agent Integration Guide

## OmniClaude — The Claude Code Operator

OmniClaude is the top-of-stack agent system that bridges Claude Code with the entire OmniNode platform. It provides:

- **73 skills** — Reusable capabilities invokable by agents
- **54 agent configurations** — Specialized agents for different tasks
- **4 hooks** — SessionStart, UserPromptSubmit, PostToolUse, SessionEnd
- **3-tier integration** — Automatic capability detection

## Integration Tiers

### Tier 0: STANDALONE (Zero Config)

```bash
cd omniclaude && uv sync
# In Claude Code: /deploy-local-plugin
```

**What works:** All 73 skills, 54 agents, hooks fire normally.
**What doesn't:** Events silently dropped (no Kafka), no intelligence enrichment.

### Tier 1: EVENT_BUS (15 min)

Requires: Kafka (Redpanda) reachable.

```bash
# Set in .env:
KAFKA_BOOTSTRAP_SERVERS=localhost:29092
```

**What works:** Everything in Standalone + routing telemetry, session events, Kafka-backed observability through OmniDash.

### Tier 2: FULL_ONEX (Full Deployment)

Requires: Kafka + intelligence-api + memory services.

```bash
# All these must be reachable:
KAFKA_BOOTSTRAP_SERVERS=localhost:29092
INTELLIGENCE_SERVICE_URL=http://localhost:8053
QDRANT_HOST=localhost
QDRANT_HTTP_PORT=6333
MEMGRAPH_HOST=localhost
MEMGRAPH_BOLT_PORT=7687
```

**What works:** Everything + context enrichment, semantic memory retrieval, pattern enforcement, intent classification.

## Hook Architecture

### SessionStart Hook (<50ms budget)

```
Trigger → daemon check → stdin read → [background: Kafka emit, Postgres log]
                                     → capability probe
                                     → inject tier banner
```

### UserPromptSubmit Hook (<500ms budget)

```
Trigger → stdin read → agent routing (5s timeout)
                     → context injection (1s timeout)
                     → pattern advisory (1s timeout)
                     → candidate formatting
                     → [background: Kafka emit, intelligence requests]
```

### PostToolUse Hook (<100ms budget)

```
Trigger → stdin read → quality assessment
                     → [background: Kafka emit, content capture]
```

### SessionEnd Hook (<50ms budget)

```
Trigger → stdin read → [background: Kafka emit, session summary]
```

## Agent Routing

When a user submits a prompt, OmniClaude:

1. **Classifies intent** via intelligence-api
2. **Matches candidates** from 54 agent configs
3. **Scores relevance** for each candidate
4. **Selects best match** and formats the agent's instructions
5. **Injects context** from learned patterns (semantic memory)

### Dispatch Pattern

For automated workflows, dispatch to `polymorphic-agent`:

```python
Task(
    subagent_type="onex:polymorphic-agent",
    description="Review PR #30",
    prompt="..."
)
```

This ensures:
- ONEX capabilities are available
- Intelligence integration is active
- Observability traces are emitted
- Cost tracking is enabled

## Skill Library

OmniClaude includes 73 skills organized by category. Skills are automatically registered with the skill-lifecycle-consumer (port 8092) in FULL_ONEX tier.

Key skill categories:
- **Code Analysis** — Static analysis, complexity metrics, refactoring suggestions
- **Testing** — Test generation, coverage analysis, mutation testing
- **Documentation** — Doc generation, API documentation, README creation
- **Architecture** — Dependency analysis, pattern detection, design review
- **Intelligence** — Pattern learning, drift detection, semantic search

## Observability Flow

```
OmniClaude (hooks)
    │
    ├──→ Kafka: onex.evt.session.* (preview-safe)
    │       │
    │       └──→ OmniDash consumer → Real-time dashboard
    │
    ├──→ Kafka: onex.cmd.omniintelligence.* (full prompt)
    │       │
    │       └──→ intelligence-api → Pattern learning → PostgreSQL
    │
    └──→ Phoenix OTLP :6006 (OTEL spans)
            │
            └──→ OmniDash :3000 → Trace visualization
```

### OmniDash Routes

| Route | Purpose |
|-------|---------|
| `/category/speed` | Cache hit rate, latency, pipeline health |
| `/category/success` | A/B comparison, injection effectiveness |
| `/category/intelligence` | Pattern utilization, intent classification |
| `/category/health` | Validation counts, node registry, health |
| `/events` | Real-time Kafka event stream |
| `/cost-trends` | LLM cost trends, budget alerts |
| `/patterns` | Code pattern discovery and learning |
| `/intents` | Intent classification analysis |

## Environment Variables Reference

### Required for FULL_ONEX

```bash
# Event Bus
KAFKA_BOOTSTRAP_SERVERS=localhost:29092

# Intelligence
INTELLIGENCE_SERVICE_URL=http://localhost:8053

# Database
ENABLE_POSTGRES=true
OMNICLAUDE_DB_URL=postgresql://role_omniclaude:xxx@localhost:5436/omniclaude

# Memory
QDRANT_HOST=localhost
QDRANT_HTTP_PORT=6333
MEMGRAPH_HOST=localhost
MEMGRAPH_BOLT_PORT=7687

# Observability
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
```

### Optional

```bash
# LLM API keys (for enriched responses)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Logging
LOG_LEVEL=INFO
LOG_FILE=~/.claude/hooks.log
```

## Failure Modes

OmniClaude is designed to **never block Claude Code**. Data loss is acceptable; UI freeze is not.

| Failure | Behavior | Data Loss |
|---------|----------|-----------|
| Emit daemon down | Events dropped, hook continues | Yes (events) |
| Kafka unavailable | Brief buffer then drop | Yes (events) |
| PostgreSQL down | Logging skipped | Yes (logs) |
| Routing timeout (5s) | Fallback to polymorphic-agent | No |
| Context injection timeout (1s) | Proceed without patterns | No |
| Agent YAML not found | Use default agent | No |
| No valid Python | Hard fail (exit 1) | No |

## Headless Mode

OmniClaude supports headless execution via `claude -p`:

```bash
# Non-interactive execution
claude -p "Analyze this codebase for security issues"
```

In headless mode, all hooks fire normally and events are emitted to Kafka. The capability probe runs at SessionStart as usual.

