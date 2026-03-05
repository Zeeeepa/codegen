# 🧠 OmniNode AI — Full Stack Deployment Guide

> **Single-command deployment** of the entire OmniNode AI multi-agent platform: 8 repositories, 54 AI agents, 90+ skills, 21 intelligence nodes, Kafka event bus, semantic memory, live dashboard, and Claude Code operator integration.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Claude Code (Operator)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   5 Hooks    │  │  54 Agents   │  │  90+ Skills  │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         └──────────────────┴─────────────────┘                      │
│                            │                                        │
│                     OmniClaude Plugin                                │
│                (Unix Socket Emit Daemon)                             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ Kafka Events
┌─────────────────────────────┼───────────────────────────────────────┐
│                       Event Bus (Redpanda)                          │
│              22+ Topics • 3 Partitions Each • 7d Retention         │
└──────────┬──────────────────┼──────────────────┬────────────────────┘
           │                  │                  │
┌──────────▼──────┐ ┌────────▼────────┐ ┌──────▼────────────┐
│ Intelligence    │ │ Semantic Memory │ │ Dashboard          │
│ omniintelligence│ │ omnimemory      │ │ omnidash           │
│                 │ │                 │ │                    │
│ 21 ONEX Nodes   │ │ MCP Integration │ │ React + TypeScript │
│ Intent Classify │ │ Qdrant Vectors  │ │ Real-time Kafka    │
│ Pattern Learn   │ │ Supabase/PG     │ │ SSE Streaming      │
│ Compliance      │ │ Embedding       │ │ Cost/Agent/Skill   │
│ FastAPI :8053   │ │ FastAPI :8054   │ │ Next.js :3000     │
└──────┬──────────┘ └───────┬─────────┘ └───────┬────────────┘
       │                    │                    │
┌──────▼────────────────────▼────────────────────▼────────────────────┐
│                      Foundation Layer                                │
│  ┌────────────────┐ ┌──────────────┐ ┌─────────────────────────┐   │
│  │ omnibase_core  │ │ omnibase_spi │ │ onex_change_control     │   │
│  │ Pydantic Models│ │ 180+ Protocols│ │ Schema Governance       │   │
│  │ DI Container   │ │ Zero-dep     │ │ Drift Detection         │   │
│  │ 4-Node Arch    │ │              │ │                         │   │
│  └────────┬───────┘ └──────┬───────┘ └─────────────────────────┘   │
│           └────────────────┘                                        │
│                    │                                                │
│  ┌─────────────────▼──────────────────────────────────────────────┐ │
│  │                    omnibase_infra                               │ │
│  │  Kafka Adapters • PostgreSQL Adapters • Service Kernel         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────────┐
│                    Docker Infrastructure                            │
│  PostgreSQL 16 │ Redpanda (Kafka) │ Qdrant │ Valkey (Redis)       │
│  :5436         │ :19092           │ :6333  │ :16379               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Docker | 24.0+ | Latest |
| Docker Compose | v2.20+ | Latest |
| Python | 3.12+ | 3.12.x |
| Node.js | 20+ | 22 LTS |
| RAM | 8 GB | 16 GB |
| Disk | 10 GB free | 20 GB free |
| uv | 0.4+ | Latest |
| OS | Linux/macOS | Any |

---

## 🚀 Quick Start (One Command)

```bash
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/omninode-deploy
chmod +x deploy.sh validate.sh config/*.sh scripts/*.sh
./deploy.sh
```

This single command will:
1. ✅ Check all prerequisites
2. ✅ Clone all 8 OmniNode repositories
3. ✅ Generate secure `.env` configuration
4. ✅ Start Docker infrastructure (PostgreSQL, Redpanda, Qdrant, Valkey)
5. ✅ Create 22+ Kafka topics
6. ✅ Create 5 Qdrant vector collections
7. ✅ Set up Python 3.12 virtual environment
8. ✅ Install all packages in dependency order (SPI → Core → Infra → Intelligence → Memory → Claude)
9. ✅ Build OmniDash React frontend
10. ✅ Deploy Claude Code operator (hooks, agents, skills)
11. ✅ Generate service launcher script

---

## Deployment Options

```bash
# Full deployment (everything)
./deploy.sh

# Infrastructure only (Docker services)
./deploy.sh --infra-only

# Python environment only (skip Docker + frontend)
./deploy.sh --python-only

# Skip repository cloning (repos already present)
./deploy.sh --skip-clone

# Skip specific components
./deploy.sh --skip-infra      # No Docker
./deploy.sh --skip-frontend   # No OmniDash build
./deploy.sh --skip-claude     # No Claude Code integration

# Custom workspace directory
./deploy.sh --workspace /path/to/workspace
```

---

## Validation

```bash
# Full validation (50+ checks)
./validate.sh

# Quick check (infra + imports only)
./validate.sh --quick

# Section-specific
./validate.sh --infra     # Docker services health
./validate.sh --python    # Package imports
./validate.sh --services  # API endpoints
./validate.sh --smoke     # Kafka/PG/Qdrant functional tests

# CI/CD JSON output
./validate.sh --json
```

### Validation Sections

| Section | Checks | What It Tests |
|---------|--------|---------------|
| Infrastructure | 18 | PostgreSQL connections, databases, tables; Redpanda health, topics; Qdrant collections; Valkey PING |
| Python | 12 | Version, venv, all 6 package imports, sub-module imports, repo existence |
| Services | 4 | Intelligence API, OmniDash, Redpanda Console, emit daemon socket |
| Smoke Tests | 6 | Kafka produce/consume, PG write, Qdrant upsert, pytest suites |
| Claude Code | 7 | Plugin directory, hooks, agents (≥50), skills, CLAUDE.md, .env |

---

## Repository Map

| # | Repository | Package | Layer | Purpose |
|---|-----------|---------|-------|---------|
| 1 | `omnibase_spi` | `omnibase-spi` v0.15.0 | Protocol | 180+ interfaces, zero implementation deps |
| 2 | `omnibase_core` | `omnibase-core` v0.23.0 | Model | Pydantic models, DI container, 4-node architecture |
| 3 | `omnibase_infra` | `omnibase-infra` v0.15.0 | Infrastructure | Kafka adapters, PostgreSQL adapters, service kernel |
| 4 | `omniintelligence` | `omninode-intelligence` v0.9.3 | Intelligence | 21 ONEX nodes, intent classification, pattern learning |
| 5 | `omnimemory` | `omninode-memory` v0.6.2 | Memory | Semantic retrieval, MCP integration, Qdrant vectors |
| 6 | `omniclaude` | `omninode-claude` v0.4.2 | Agent | Claude Code plugin, 54 agents, 90+ skills, 5 hooks |
| 7 | `omnidash` | omnidash | Frontend | React dashboard, Kafka consumer, real-time events |
| 8 | `onex_change_control` | `onex-change-control` v0.1.0 | Governance | Schema governance, drift detection, enforcement |

### Dependency Graph

```
omnibase_spi (L1: Protocols)
     │
     ▼
omnibase_core (L2: Models) ──depends──▶ omnibase_spi
     │
     ▼
omnibase_infra (L3: Infrastructure) ──depends──▶ core + spi
     │
     ├──▶ omniintelligence (L4) ──depends──▶ infra
     ├──▶ omnimemory (L4) ──depends──▶ core (via pydantic)
     └──▶ omniclaude (L5) ──depends──▶ core + spi + infra + intelligence
              │
              ▼
         omnidash (L6: Frontend) ←── Kafka events from all layers
```

---

## Infrastructure Services

### Ports

| Service | Internal | External (Host) | Protocol |
|---------|----------|-----------------|----------|
| PostgreSQL | 5432 | **5436** | TCP |
| Redpanda Kafka | 9092 | **19092** | Kafka |
| Redpanda Schema Registry | 8081 | 18081 | HTTP |
| Redpanda Admin | 9644 | 9644 | HTTP |
| Qdrant HTTP | 6333 | **6333** | HTTP |
| Qdrant gRPC | 6334 | 6334 | gRPC |
| Valkey | 6379 | **16379** | RESP |
| Redpanda Console | 8080 | **8080** | HTTP |
| Intelligence API | 8053 | **8053** | HTTP |
| OmniDash | 3000 | **3000** | HTTP |

### Databases (PostgreSQL)

| Database | Service | Key Tables |
|----------|---------|------------|
| `omnibase_infra` | Core infra | node_registrations, contracts_topics, agent_routing_decisions, agent_execution_logs |
| `omniintelligence` | Intelligence | patterns, pattern_feedback, intent_classifications |
| `omnimemory` | Memory | (managed by Supabase/SQLAlchemy) |
| `omnidash_analytics` | Dashboard | llm_cost_aggregates, skill_executions, injection_effectiveness |

### Kafka Topics (22+)

| Domain | Topics |
|--------|--------|
| Session | session-started, session-ended |
| Prompt | prompt-submitted |
| Hook | claude-hook-event |
| Tool | tool-executed |
| Agent | agent-routing-decision, agent-status |
| Intelligence | intent-classified, pattern-extracted, pattern-promoted, pattern-demoted, compliance-evaluated, llm-call-completed |
| Memory | document-ingested, retrieval-completed |
| Registration | node-registered, node-heartbeat |
| Skill | skill-execution-started, skill-execution-completed |
| Observability | metrics |

### Qdrant Collections (5)

| Collection | Purpose | Dimensions |
|------------|---------|-----------|
| `omninode_patterns` | Intelligence pattern storage | 1536 |
| `omnimemory_documents` | Semantic memory documents | 1536 |
| `omninode_code_patterns` | Code pattern matching | 1536 |
| `omninode_intents` | Intent classification | 1536 |
| `omninode_session_context` | Session context embeddings | 1536 |

---

## Claude Code Operator

### Integration Tiers

OmniClaude auto-detects available infrastructure at every `SessionStart`:

| Tier | Requirements | Capabilities |
|------|-------------|--------------|
| **STANDALONE** | None | 90+ skills, 54 agents, all hooks (events silently dropped) |
| **EVENT_BUS** | Kafka reachable | + Agent routing, session telemetry, Kafka observability |
| **FULL_ONEX** | Kafka + PostgreSQL + Qdrant | + Context enrichment, semantic memory, pattern compliance |

### 5 Claude Code Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `SessionStart` | Claude session begins | Probe services, detect tier, inject banner |
| `UserPromptSubmit` | User sends prompt | Classify intent, route to agent, emit event |
| `PreToolUse` | Before tool execution | Compliance check, enrichment injection |
| `PostToolUse` | After tool execution | Extract patterns, update feedback |
| `SessionEnd` | Claude session ends | Emit session summary, aggregate metrics |

### Key Skills

| Skill | Description |
|-------|-------------|
| `onex:ticket-work` | Contract-driven ticket execution with phases |
| `onex:ticket-pipeline` | Autonomous per-ticket pipeline (work → review → PR → CI → merge) |
| `onex:pr-review` | Comprehensive PR review with priority organization |
| `onex:systematic-debugging` | Four-phase debugging methodology |
| `onex:gap-analysis` | Cross-repo integration audit (Kafka drift, type mismatches) |
| `onex:golden-path-validate` | End-to-end event chain validation |
| `onex:system-status` | Full system health monitoring |
| `onex:brainstorming` | Collaborative idea refinement |
| `onex:writing-plans` | Implementation planning with file paths |
| `onex:decision-store` | Architectural decision recording |

---

## File Structure

```
omninode-deploy/
├── README.md                          # This guide
├── deploy.sh                          # 🚀 Main deployment script
├── validate.sh                        # 🔍 Validation suite (50+ checks)
├── docker-compose.yml                 # 🐳 Infrastructure services
├── .env.example                       # ⚙️ Unified configuration template
├── config/
│   ├── postgres-init.sh               # 🗄️ Database schema initialization
│   ├── create-kafka-topics.sh         # 📨 Kafka topic creation
│   └── create-qdrant-collections.sh   # 🔍 Vector collection setup
└── scripts/
    └── setup-claude-operator.sh       # 🤖 Claude Code integration
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `Docker Compose v2 not found` | Old Docker version | Update Docker Desktop or install compose v2 plugin |
| `Python 3.12+ required` | Wrong Python version | Install Python 3.12: `uv python install 3.12` |
| `STANDALONE tier unexpected` | Kafka not reachable | Check `KAFKA_BOOTSTRAP_SERVERS` in `.env`, restart Claude session |
| `omnibase_spi import fails` | Circular dependency | Run `./deploy.sh --python-only` to reinstall in correct order |
| `PostgreSQL health timeout` | Slow startup | Wait longer or check Docker resources |
| `Qdrant collection not found` | Collections not created | Run `bash config/create-qdrant-collections.sh` |

### Docker Commands

```bash
# View all containers
docker compose ps

# View logs
docker compose logs -f postgres
docker compose logs -f redpanda

# Restart a service
docker compose restart postgres

# Full reset (destroys data!)
docker compose down -v && ./deploy.sh
```

### Validate Specific Components

```bash
# Check just infrastructure
./validate.sh --infra

# Check just Python
./validate.sh --python

# Run smoke tests
./validate.sh --smoke

# Machine-readable output
./validate.sh --json | jq '.fail'
```

---

## Development Workflow

### Daily Start

```bash
cd omninode-deploy

# Start infrastructure (idempotent)
docker compose up -d

# Activate Python environment
source workspace/.venv/bin/activate

# Start services
./workspace/start-services.sh

# Open dashboard
open http://localhost:3000
```

### After Code Changes

```bash
# Reinstall a specific package after changes
cd workspace/omniintelligence
uv pip install -e .

# Rerun tests
python -m pytest tests/ -x
```

### Full Reset

```bash
docker compose down -v
rm -rf workspace/.venv
./deploy.sh
```

---

## License

Each OmniNode repository is licensed under MIT. See individual repos for details.

