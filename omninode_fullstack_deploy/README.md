# OmniNode Full-Stack Deployment Guide

> **One command to deploy all 8 OmniNode repositories — 17+ services, 5 phases, FULL_ONEX tier.**

```bash
./deploy_all.sh --execute --profile full
```

---

## Architecture Overview

```
                    ┌──────────────────────────────────────────────┐
                    │              OmniNode Platform                │
                    │                                              │
  Phase 5 ──────── │  OmniClaude ← 73 skills, 54 agents, FULL_ONEX│
  (Interface)       │  OmniDash   ← Real-time observability UI    │
                    │                                              │
  Phase 4 ──────── │  OmniIntelligence ← 21 ONEX intelligence nodes│
  (Intelligence)    │  OmniMemory      ← Qdrant + Memgraph + Valkey│
                    │  ONEX CC         ← Cross-repo governance     │
                    │                                              │
  Phase 3 ──────── │  omninode-runtime  ← ONEX execution engine    │
  (Runtime)         │  intelligence-api ← Pattern + intent API     │
                    │  7 more services  ← workers, consumers, OTLP │
                    │                                              │
  Phase 2 ──────── │  PostgreSQL ← 7 databases, 6 roles, 36 migrations│
  (Infrastructure)  │  Redpanda   ← Kafka event bus                │
                    │  Valkey     ← Platform cache                 │
                    │  Infisical  ← Secrets management (opt-in)    │
                    │  Keycloak   ← OIDC authentication (opt-in)   │
                    │                                              │
  Phase 1 ──────── │  omnibase_spi  ← Protocol interfaces         │
  (Foundation)      │  omnibase_core ← ONEX 4-node framework       │
                    └──────────────────────────────────────────────┘
```

### Dependency Graph

```
omnibase_spi (contracts)
  └→ omnibase_core (execution protocol)
       └→ omnibase_infra (deployment + infrastructure)
            ├→ omnimemory (Qdrant, Memgraph, Valkey, Kreuzberg)
            ├→ omniintelligence (21 intelligence nodes)
            ├→ onex_change_control (governance)
            ├→ omnidash (React dashboard)
            └→ omniclaude (Claude Code agent — top of stack)
```

---

## Prerequisites

| Tool | Minimum Version | Check Command |
|------|----------------|---------------|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | v2.20+ | `docker compose version` |
| Python | 3.12+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| uv | latest | `uv --version` |
| Git | 2.0+ | `git --version` |
| Disk Space | 10GB+ | `df -h .` |
| RAM | 4GB+ (8GB recommended) | `free -h` |

---

## Quick Start

```bash
# 1. Clone this deploy package
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/omninode_fullstack_deploy

# 2. Make scripts executable
chmod +x deploy_all.sh verify_deployment.sh

# 3. Preview what will happen
./deploy_all.sh --dry-run

# 4. Deploy everything
./deploy_all.sh --execute --profile full

# 5. Verify deployment
./verify_deployment.sh --live
```

---

## Deployment Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| `minimal` | PostgreSQL, Redpanda, Valkey | Backend development, testing infra |
| `standard` | + Runtime services (8 containers) | API development, service testing |
| `full` | + Intelligence + Dashboard + Claude Code | Full platform, production-like |

```bash
./deploy_all.sh --execute --profile minimal     # Just databases + event bus
./deploy_all.sh --execute --profile standard     # + runtime services
./deploy_all.sh --execute --profile full          # Everything
```

---

## Phase-by-Phase Walkthrough

### Phase 1: Foundation

Installs the Python packages that everything else depends on:

- **omnibase_spi** — Service Provider Interface protocols (typed contracts)
- **omnibase_core** — ONEX 4-node execution protocol (Effect → Compute → Reducer → Orchestrator)

```bash
./deploy_all.sh --execute --phase 1
```

### Phase 2: Infrastructure

Deploys core platform services via `omnibase_infra`:

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5436 | 7 databases, 6 roles, 36 migrations |
| Redpanda | 19092 / 29092 | Kafka-compatible event bus |
| Valkey | 16379 | Platform-wide cache |
| Infisical | 8880 | Secrets management (opt-in) |
| Keycloak | 28080 | OIDC authentication (opt-in) |

```bash
./deploy_all.sh --execute --phase 2
./deploy_all.sh --execute --phase 2 --skip-secrets --skip-keycloak  # Minimal infra
```

**Databases created:**
- `omnibase_infra`, `omniintelligence`, `omniclaude`, `omnimemory`
- `omninode_cloud`, `omnidash_analytics`

**Roles created (least-privilege):**
- `role_omnibase`, `role_omniintelligence`, `role_omniclaude`
- `role_omnimemory`, `role_omninode`, `role_omnidash`

### Phase 3: Runtime Services

Starts the ONEX execution engine and supporting consumers:

| Service | Port | Purpose |
|---------|------|---------|
| omninode-runtime | 8085 | ONEX execution engine |
| runtime-effects | 8086 | Effect node execution |
| runtime-worker | — | Background task processing |
| agent-actions-consumer | 8087 | Agent action handling |
| intelligence-api | 8053 | Intelligence + pattern API |
| contract-resolver | 8091 | HTTP bridge for contracts |
| skill-lifecycle-consumer | 8092 | Skill registry management |
| Phoenix OTLP | 6006 | OpenTelemetry observability |

```bash
./deploy_all.sh --execute --phase 3
```

### Phase 4: Intelligence Layer

Deploys memory, intelligence, and governance:

| Component | Services | Ports |
|-----------|----------|-------|
| OmniMemory | Qdrant, Memgraph, Valkey, Kreuzberg | 6333, 7687, 6379, 8090 |
| OmniIntelligence | 21 ONEX nodes (FastAPI) | Uses :8053 |
| ONEX Change Control | Governance tooling | — |

```bash
./deploy_all.sh --execute --phase 4
```

### Phase 5: Interface Layer

Deploys the dashboard and Claude Code integration:

| Component | Port | Description |
|-----------|------|-------------|
| OmniDash | 3000 | Real-time observability dashboard (React + Drizzle) |
| OmniClaude | — | Claude Code plugin with 73 skills, 54 agents |

```bash
./deploy_all.sh --execute --phase 5
```

---

## Claude Code Operator Guide

### 3-Tier Integration

OmniClaude auto-detects available services and sets its tier:

| Tier | Requirements | Capabilities |
|------|-------------|-------------|
| **STANDALONE** | Nothing | 73 skills, 54 agents, hooks — events silently dropped |
| **EVENT_BUS** | Kafka reachable | + routing telemetry, session events, Kafka observability |
| **FULL_ONEX** | + Intelligence API + Memory | + context enrichment, semantic recall, pattern enforcement |

With all 5 phases deployed, OmniClaude reaches **FULL_ONEX**:

```
─── OmniClaude: FULL_ONEX (73 skills, 54 agents) (probe: 2s ago) ───
```

### Multi-Agent Orchestration

Within FULL_ONEX tier, the system supports:

1. **Skill Routing** — Prompts are classified and routed to the best-match agent
2. **Context Injection** — Learned patterns injected into prompts automatically
3. **Pattern Enforcement** — Code patterns enforced via intelligence-api
4. **Cost Tracking** — LLM inference costs tracked through OmniDash
5. **Memory Retrieval** — Semantic memory from Qdrant enriches responses
6. **Intent Classification** — OmniIntelligence classifies user intents

### Agent Dispatch Pattern

```python
# Dispatch to polymorphic-agent for ONEX capabilities
Task(
    subagent_type="onex:polymorphic-agent",
    description="Review PR #30",
    prompt="..."
)
```

### Performance Budgets

| Hook | Budget | What Blocks |
|------|--------|-------------|
| SessionStart | <50ms | Daemon check, stdin read |
| UserPromptSubmit | <500ms | Routing, injection, advisory |
| PostToolUse | <100ms | stdin read, quality check |
| SessionEnd | <50ms | stdin read |

---

## Port Allocation Map

```
Infrastructure (Phase 2):
  5436   PostgreSQL
  16379  Valkey (platform cache)
  19092  Redpanda (internal)
  29092  Redpanda (external/client)
  8880   Infisical (opt-in)
  28080  Keycloak (opt-in)

Runtime (Phase 3):
  8085   omninode-runtime
  8086   runtime-effects
  8087   agent-actions-consumer
  8053   intelligence-api
  8091   contract-resolver
  8092   skill-lifecycle-consumer
  6006   Phoenix OTLP

Intelligence (Phase 4):
  6333   Qdrant HTTP
  6334   Qdrant gRPC
  7687   Memgraph Bolt
  7444   Memgraph HTTP
  6379   Valkey (memory-local)
  8090   Kreuzberg parser

Interface (Phase 5):
  3000   OmniDash
```

**Zero port conflicts** — all allocations are unique.

---

## Environment Configuration

All configuration lives in a single `.env.template`. The deploy script auto-generates secure passwords.

Key variable groups:

| Group | Count | Purpose |
|-------|-------|---------|
| PostgreSQL | ~12 | Host, port, passwords, 6 role passwords |
| Kafka/Redpanda | ~4 | Bootstrap servers, ports |
| Valkey | ~3 | Host, port, password |
| Infisical | ~6 | Bootstrap credentials (circular dep) |
| Keycloak | ~4 | Admin credentials, DB URL |
| Runtime | ~8 | Service ports |
| Memory | ~8 | Qdrant, Memgraph, Kreuzberg |
| OmniDash | ~5 | DB URL, Kafka config |
| OmniClaude | ~6 | DB URL, service URLs |

---

## Troubleshooting

### PostgreSQL won't start
```bash
docker logs omninode-infra-postgres-1
# Common: permissions on data volume, insufficient shared memory
# Fix: docker volume rm omninode-infra_postgres_data && redeploy Phase 2
```

### Redpanda broker unreachable
```bash
docker logs omninode-infra-redpanda-1
# Common: port already in use, insufficient memory (needs 512M+)
# Fix: check `ss -tlnp | grep 29092` and kill conflicting process
```

### Migrations fail
```bash
# Check migration state:
psql -h localhost -p 5436 -U postgres -d omnibase_infra \
  -c "SELECT * FROM schema_migrations ORDER BY version DESC LIMIT 5"
```

### OmniClaude shows STANDALONE instead of FULL_ONEX
```bash
# Check if Kafka is reachable:
echo "KAFKA_BOOTSTRAP_SERVERS=localhost:29092" >> ~/omninode-workspace/omniclaude/.env

# Check if intelligence-api is reachable:
curl -sf http://localhost:8053/health

# Delete cached capabilities to force re-probe:
rm ~/.claude/.onex_capabilities
# Start new Claude Code session
```

### Port already in use
```bash
# Find what's using a port:
ss -tlnp | grep :8085
# Kill the process or change the port in .env
```

### OmniDash database error
```bash
cd ~/omninode-workspace/omnidash
npm run db:push   # Push Drizzle schema
npm run db:migrate # Run SQL migrations
```

---

## Verification

```bash
# Sandbox mode (no Docker required):
./verify_deployment.sh --sandbox

# Live mode (checks all running services):
./verify_deployment.sh --live
```

---

## Stopping Services

```bash
./deploy_all.sh --stop
```

---

## File Structure

```
omninode_fullstack_deploy/
├── deploy_all.sh                    # Master orchestration (single entry point)
├── verify_deployment.sh             # Health check + sandbox validation
├── README.md                        # This guide
├── config/
│   └── .env.template                # Master environment (all 8 repos)
├── phases/
│   ├── 01_foundation.sh             # SPI + Core
│   ├── 02_infrastructure.sh         # PostgreSQL, Redpanda, Valkey, Infisical, Keycloak
│   ├── 03_runtime_services.sh       # 7 runtime services
│   ├── 04_intelligence_layer.sh     # Memory + Intelligence + Governance
│   └── 05_interface_layer.sh        # OmniDash + OmniClaude
├── lib/
│   ├── common.sh                    # Logging, health checks, retry logic
│   ├── docker_helpers.sh            # Compose wrappers
│   └── validation.sh               # Pre-flight checks
└── docs/
    ├── architecture.md              # System architecture details
    ├── troubleshooting.md           # Extended troubleshooting
    └── agent_integration.md         # Claude Code multi-agent guide
```

---

## License

MIT — See individual OmniNode repositories for their respective licenses.

