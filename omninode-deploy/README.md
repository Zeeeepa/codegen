# OmniNode AI — Full Stack Deployment Guide v2.0

> Multi-agent, single-script deployment for the complete OmniNode AI platform.

## Architecture Overview

```
┌─────────────────────────── OmniNode Platform ────────────────────────────┐
│                                                                            │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │ omnibase_spi│←→│ omnibase_core│─→│ omnibase_infra│─→│ Docker Infra │ │
│  │  (Protocol) │  │  (Core/CLI)  │  │  (Infra/DB)   │  │ PG/Kafka/    │ │
│  │  SPI v0.15  │  │  Core v0.23  │  │  Infra v0.15  │  │ Qdrant/Valkey│ │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘  └──────────────┘ │
│         │                │                   │                            │
│  ┌──────┴──────────────┬─┴───────────────────┴──────────┐                │
│  │                     │                                │                │
│  ▼                     ▼                                ▼                │
│  ┌───────────────┐  ┌────────────────────┐  ┌──────────────────┐        │
│  │ omnimemory    │  │ omniintelligence   │  │ omniclaude       │        │
│  │ Vector Memory │  │ 816 Python modules │  │ Claude Code Ops  │        │
│  │ MCP + Qdrant  │  │ 8 effect nodes     │  │ 10 hook endpoints│        │
│  │ + Supabase    │  │ Contract topics    │  │ 72 hook lib mods │        │
│  │ + Redis       │  │ FSM + patterns     │  │ 53 agents (YAML) │        │
│  └───────────────┘  └────────────────────┘  │ 80 skills        │        │
│                                              │ 6 commands       │        │
│  ┌────────────────────┐                     └──────────────────┘        │
│  │ onex_change_control│                                                  │
│  │ Governance/Drift   │  ┌────────────────────────────┐                 │
│  │ Schema Purity      │  │ omnidash                   │                 │
│  └────────────────────┘  │ Real-time Dashboard (Vite) │                 │
│                           │ 35+ npm scripts            │                 │
│                           │ Drizzle ORM → PG           │                 │
│                           │ Kafka topic validation     │                 │
│                           └────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone deployment scripts
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/omninode-deploy

# Full deploy (all 8 repos + infrastructure + Claude Code)
./deploy.sh

# Or with options
./deploy.sh --profile full      # All Docker profiles
./deploy.sh --seed-demo          # Seed demo data
./deploy.sh --python-only        # Just Python env
./deploy.sh --infra-only         # Just Docker services
./deploy.sh --skip-clone         # Repos already cloned
```

## Repository Map

| # | Repository | Type | Key Metrics |
|---|-----------|------|-------------|
| 1 | `omnibase_spi` | Python | Protocol definitions, SPI v0.15.0 |
| 2 | `omnibase_core` | Python | Core framework v0.23.0, CLI (`onex`), DI container |
| 3 | `omnibase_infra` | Python+Docker | Canonical docker-compose, 2 PG migrations, env template |
| 4 | `omniintelligence` | Python | 816 Python modules, 8 effect nodes, contract-driven topics |
| 5 | `omnimemory` | Python | MCP integration, Qdrant vectors, Redis cache, Supabase |
| 6 | `omniclaude` | Python+Shell | 10 hook endpoints, 72 lib modules, 53 agents, 80 skills |
| 7 | `onex_change_control` | Python | Governance, drift detection, schema purity |
| 8 | `omnidash` | TypeScript | Vite+React, 35 npm scripts, Drizzle ORM, Kafka validation |

## Infrastructure

| Service | Port | Notes |
|---------|------|-------|
| PostgreSQL | 5436 | 7 databases, per-service roles |
| Redpanda (Kafka) | 19092 | Contract-driven topics from 8 effect nodes |
| Qdrant | 6333 | 5 vector collections |
| Valkey (Redis) | 16379 | Session cache |

### PostgreSQL Databases

Created by canonical migrations (`omnibase_infra/docker/migrations/forward/`):

| Database | Service | Schema |
|----------|---------|--------|
| `omnibase_infra` | Core infrastructure | — |
| `omniintelligence` | Intelligence engine | FSM state, workflows, taxonomy, patterns, attributions |
| `omniclaude` | Claude Code ops | Session tracking |
| `omnimemory` | Memory service | Vector store metadata |
| `omninode_cloud` | Cloud platform | — |
| `omnidash_analytics` | Dashboard | Drizzle ORM managed |
| `infisical_db` | Secrets (optional) | Infisical secrets manager |

## Python Dependency Chain

⚠️ **Critical**: `omnibase_spi` and `omnibase_core` have a circular dependency.

```
                 ┌──────────────┐
            ┌───→│ omnibase_spi │──────┐
            │    │  v0.15.0     │      │ depends on
            │    └──────────────┘      │ omnibase_core>=0.19.0
depends on  │                          │
omnibase-   │    ┌──────────────┐      │
spi==0.15.0 └────│ omnibase_core│←─────┘
                 │  v0.23.0     │
                 └──────────────┘

Solution: Bootstrap both with --no-deps, then resolve transitive deps.
```

**Install sequence** (encoded in `deploy.sh`):
1. `uv pip install --no-deps -e omnibase_core`
2. `uv pip install --no-deps -e omnibase_spi`
3. Install shared external deps (pydantic, pyyaml, httpx, etc.)
4. `uv pip install --no-deps -e omnibase_infra omniintelligence omnimemory omniclaude`
5. Pin `qdrant-client>=1.7.0,<1.18.0` (PEP 604 bug on Python 3.12)

## Claude Code Integration

### Hook Event Types (hooks.json v1.2.0)

| Event | Endpoints | Scripts | Purpose |
|-------|-----------|---------|---------|
| `SessionStart` | 1 | `session-start.sh` | Initialize session tracking |
| `SessionEnd` | 1 | `session-end.sh` | Finalize session, emit event |
| `Stop` | 1 | `stop.sh` | Graceful shutdown |
| `UserPromptSubmit` | 2 | `user-prompt-submit.sh`, `user-prompt-delegation-rule.sh` | Intent classification + delegation |
| `PreCompact` | 1 | `pre-compact.sh` | Context probe before compaction |
| `PreToolUse` | 2 | `pre_tool_use_authorization_shim.sh` (Edit/Write), `pre_tool_use_bash_guard.sh` (Bash) | Authorization + guard |
| `PostToolUse` | 5 | quality, ruff, CI reminder, skill delegation, tool counter | Enforcement pipeline |

### Hook Library (72 modules)

The `hooks/lib/` directory contains the runtime library that hook scripts depend on:

- **Routing**: `agent_router.py`, `delegation_orchestrator.py`, `local_delegation_handler.py`
- **Auth**: `auth_gate_adapter.py`, `pr_claim_registry.py`, `promotion_gater.py`
- **Metrics**: `metrics_aggregator.py`, `metrics_emitter.py`, `post_tool_metrics.py`
- **Pattern**: `pattern_enforcement.py`, `pattern_cache.py`, `pattern_advisory_formatter.py`
- **Session**: `session_intelligence.py`, `session_marker.py`, `session_outcome.py`
- **Events**: `emit_client_wrapper.py`, `hook_event_adapter.py`, `hook_event_logger.py`
- **Observability**: `phoenix_otel_exporter.py`, `phase_instrumentation.py`

### Commands

| Command | Description |
|---------|-------------|
| `/authorize` | Grant elevated permissions |
| `/bus-audit` | Audit Kafka event bus |
| `/crash-recovery` | Recover from crashed session |
| `/deauthorize` | Revoke permissions |
| `/gap-fix` | Run gap analysis and fix |
| `/set-active-run` | Set active deployment run |

## Validation

```bash
# Full validation (70+ checks)
./validate.sh

# With type checking (mypy)
./validate.sh --typecheck

# With shell linting (shellcheck)
./validate.sh --lint

# Machine-readable JSON output for CI
./validate.sh --json

# Quick mode (skip slow checks)
./validate.sh --quick

# Integration tests
./scripts/test-integration.sh
```

### Validation Sections

1. **Repository Structure** — 8 repos, pyproject.toml/package.json
2. **Docker Infrastructure** — 4 containers, 7 databases, 5 Qdrant collections
3. **Python Environment** — virtualenv, imports, qdrant-client constraint
4. **Claude Code Operator** — hooks, lib modules, agents, skills, commands
5. **OmniDash Frontend** — node_modules, build artifacts, npm scripts
6. **OmniIntelligence Nodes** — node count, Python modules, topics
7. **Type Checking & Linting** — mypy, shellcheck
8. **Environment & Configuration** — .env validation, required vars

## Files

```
omninode-deploy/
├── deploy.sh                          # Main deployment script (v2.0)
├── validate.sh                        # 70+ check validation suite
├── docker-compose.yml                 # Fallback compose (prefer canonical)
├── .env.example                       # Canonical env vars (30+)
├── README.md                          # This file
├── config/
│   ├── postgres-init.sh               # Fallback DB init
│   ├── create-kafka-topics.sh         # Topic creation
│   └── create-qdrant-collections.sh   # Vector collection setup
└── scripts/
    ├── setup-claude-operator.sh       # Claude Code operator (v2.0)
    └── test-integration.sh            # Integration test suite
```

