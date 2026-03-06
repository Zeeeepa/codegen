# OmniNode Platform — Full Static Analysis

> **Scope**: All 8 OmniNode repositories  
> **Primary focus**: `omnibase_infra` (infrastructure layer)  
> **Analysis date**: 2026-03-06  
> **Source verification**: docker-compose.infra.yml, deploy-runtime.sh, docker/README.md, .env.example, OmniNode org profile README

---

## 1. Repository Structure and Components

### 1.1 Top-Level Repositories (8 total)

| Repository | Layer | Type | Purpose |
|------------|-------|------|---------|
| `omnibase_spi` | Foundation | Python library | Service Provider Interface — typed protocols and contracts |
| `omnibase_core` | Foundation | Python library | ONEX 4-node execution model: Effect → Compute → Reducer → Orchestrator |
| `omnibase_infra` | Infrastructure | Python + Docker | Kafka/Redpanda event bus, PostgreSQL, Valkey cache, session management, runtime services |
| `omnimemory` | Infrastructure | Docker Compose | Qdrant vector DB, Memgraph graph DB, Valkey (memory-local), Kreuzberg parser |
| `omniintelligence` | Intelligence | Python | 21 ONEX intelligence nodes: intent classification, drift detection, semantic review |
| `onex_change_control` | Governance | Python | Schema governance, drift detection, cross-repo contract enforcement |
| `omnidash` | Interface | Node/React | Real-time observability dashboard for agents, patterns, and code analysis |
| `omniclaude` | Interface | Python | Claude Code plugin — 90+ skills, 54 agents, 5 hooks, agent routing |

### 1.2 Dependency Layers

```text
Layer 3 — Interface (User-Facing)
├── omnidash (React dashboard, port 3000)
└── omniclaude (Claude Code plugin, no exposed port)
       ↓ depends on ↓
Layer 2 — Infrastructure + Intelligence (Deployable Services)
├── omnibase_infra (PostgreSQL, Redpanda, Valkey, runtime services)
├── omnimemory (Qdrant, Memgraph, Valkey, Kreuzberg)
├── omniintelligence (21 intelligence nodes)
└── onex_change_control (Schema governance)
       ↓ depends on ↓
Layer 1 — Foundation (Python Libraries, Non-Deployable)
├── omnibase_spi (Protocol interfaces)
└── omnibase_core (Typed models, contracts, ONEX base types)
```

### 1.3 omnibase_infra Internal Structure

Key directories within `omnibase_infra`:

| Directory | Purpose |
|-----------|---------|
| `docker/` | Docker Compose configuration (`docker-compose.infra.yml`), `.env.example` |
| `docker/docker-entrypoint-initdb.d/` | PostgreSQL initialization scripts (7 databases, 6 roles, 22 SQL migrations) |
| `scripts/` | `deploy-runtime.sh` (canonical entry point), `run-migrations.py`, `bootstrap-infisical.sh` |
| `src/omnibase_infra/` | Python source: event bus, topics, session management, runtime kernel |
| `src/omnibase_infra/topics/` | `platform_topic_suffixes.py` — single source of truth for Kafka topic names |

---

## 2. Entrypoints and Execution Flow

### 2.1 Primary Entry Point: `scripts/deploy-runtime.sh`

**Purpose**: Canonical, stable, versioned deployment of omnibase_infra runtime.

**Invocation**:
```bash
./scripts/deploy-runtime.sh --execute              # Deploy with defaults
./scripts/deploy-runtime.sh --execute --restart     # Restart runtime services only
./scripts/deploy-runtime.sh --execute --profile full  # Full profile
./scripts/deploy-runtime.sh --print-compose-cmd     # Print compose command and exit
```

**Control Flow**:
```text
1. Validate prerequisites (Docker 20.10+, Compose 2.20+, rsync, git, jq, curl)
2. Resolve repo root (walk up from script location to find pyproject.toml)
3. Read version from [project] section of pyproject.toml
4. Read git SHA (12-char abbreviated)
5. Acquire mkdir-based lock at ~/.omnibase/infra/.deploy.lock
6. Rsync repository to versioned deployment root:
   ~/.omnibase/infra/deployed/{version}/
7. Create/update registry: ~/.omnibase/infra/registry.json
8. Run docker compose from stable directory with fixed project name
9. Poll health checks (15 retries × 4s = 60s max)
10. Clean up stale deployments (keep MAX_DEPLOYMENTS=5 most recent)
```

**Why This Exists**: Prevents "invisible deployments" (OMN-2233). Multiple repo copies sharing the same compose project name would run containers from the wrong directory. `deploy-runtime.sh` uses fixed project name `omnibase-infra-runtime` from a stable location.

**Default mode**: Dry-run (preview). Use `--execute` to deploy.

### 2.2 Docker Compose Profiles

| Profile | Services | Command |
|---------|----------|---------|
| (default) | PostgreSQL, Redpanda, Valkey | `docker compose -f docker-compose.infra.yml up -d` |
| `runtime` | + migration-gate, omninode-runtime, effects, workers, consumers, intelligence-api, phoenix | `--profile runtime` |
| `consul` | + Consul service discovery | `--profile consul` |
| `secrets` | + Infisical secrets manager | `--profile secrets` |
| `auth` | + Keycloak OIDC | `--profile auth` |
| `full` | All of the above | `--profile full` |
| `bootstrap` | Infrastructure + secrets (initial bootstrap) | `--profile bootstrap` |

### 2.3 PostgreSQL Initialization (Auto on First Start)

Docker entrypoint runs scripts from `docker-entrypoint-initdb.d/`:
1. `000_create_multiple_databases.sh` — Creates 7 databases + 6 least-privilege roles
2. `001_create_omniintelligence_schema.sh` — Full schema (tables, triggers, views, indexes)
3. `001_registration_projection.sql` ... `036_create_schema_migrations.sql` — 22 SQL migrations
4. `02-keycloak-db.sql` — Keycloak database

On subsequent starts, entrypoint is skipped (data directory exists). Incremental migrations via `run-migrations.py`.

### 2.4 Topic Provisioning

- **Automatic**: `TopicProvisioner` on runtime boot (`service_kernel.py`)
- **Source of truth**: `ALL_PLATFORM_TOPIC_SPECS` in `src/omnibase_infra/topics/platform_topic_suffixes.py`
- **Manual**: `uv run python -m omnibase_infra.event_bus.service_topic_manager`

---

## 3. Data Flows and Architecture Diagrams

### 3.1 Component Diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│                     OmniNode Platform                           │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │PostgreSQL│  │ Redpanda │  │  Valkey   │  │ Infisical│       │
│  │  :5436   │  │  :19092  │  │  :16379  │  │  :8880   │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │              │             │
│       └──────────────┴──────┬───────┴──────────────┘             │
│                             │                                    │
│  ┌──────────────────────────┴────────────────────────────┐      │
│  │              omnibase-infra-network (bridge)           │      │
│  └──────────────────────────┬────────────────────────────┘      │
│                             │                                    │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │omninode-  │  │runtime-   │  │runtime-   │  │intelligence│   │
│  │runtime    │  │effects    │  │worker ×N  │  │-api        │   │
│  │ :8085     │  │ :8086     │  │(parallel) │  │ :8053      │   │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │
│                                                                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │contract-  │  │skill-life │  │agent-act  │  │ phoenix   │   │
│  │resolver   │  │-cycle-con │  │-consumer  │  │ (OTLP)    │   │
│  │ :8091     │  │ :8092     │  │ :8087     │  │ :6006     │   │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │
│                                                                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │  Qdrant   │  │ Memgraph  │  │ Kreuzberg │  │  Keycloak │   │
│  │  :6333    │  │  :7687    │  │  :8090    │  │  :28080   │   │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │
│                                                                 │
│  ┌───────────┐  ┌───────────┐                                   │
│  │ OmniDash  │  │OmniClaude │                                   │
│  │  :3000    │  │ (plugin)  │                                   │
│  └───────────┘  └───────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 ONEX 4-Node Request Processing Flow

```text
Client Request (via Kafka topic: requests)
    │
    ▼
[omninode-runtime] ── Effect Node ──────────────────
    │  Receives request from Kafka topic
    │  Passes to processing pipeline
    ▼
[runtime-effects / runtime-worker] ── Compute Node ─
    │  Applies business logic
    │  May call external services (PostgreSQL, Infisical, etc.)
    │  Emits side effect events (NodeLlmInferenceEffect → LLM costs)
    ▼
[intelligence-api] ── Reducer Node (async) ─────────
    │  Reduces intermediate results
    │  Applies learned patterns from OmniIntelligence
    │  Performs drift detection
    ▼
[omninode-runtime] ── Orchestrator Node ────────────
    │  Coordinates aggregated result
    │  Publishes to response topic
    ▼
Client Response (via Kafka topic: responses)
```

### 3.3 Database Schema (7 Databases, 6 Roles)

| Database | Role | Purpose |
|----------|------|---------|
| `omnibase_infra` | `role_omnibase` | Events, ledger, projections, migrations, session state |
| `omniintelligence` | `role_omniintelligence` | Intelligence node state, patterns, drift detection |
| `omniclaude` | `role_omniclaude` | Claude agent routing, skill registry, hook lifecycle |
| `omnimemory` | `role_omnimemory` | Semantic memory embeddings, intent graphs (PG side) |
| `omninode_cloud` | `role_omninode` | Multi-tenant node registry, routing, capability discovery |
| `omnidash_analytics` | `role_omnidash` | Dashboard: cost aggregates, metrics, skill executions |
| `keycloak` | `postgres` (shared) | OIDC realm, users, clients (auth profile only) |

### 3.4 Kafka Addressing Invariant (OMN-3431)

```text
┌─────────────────────┐     ┌──────────────────────────┐
│  Host Scripts/Tools  │     │  Docker Containers       │
│                      │     │                          │
│  localhost:19092     │     │  redpanda:9092           │
│  (external port)     │     │  (Docker-internal)       │
│                      │     │                          │
│  NEVER set           │     │  Hardcoded in compose    │
│  KAFKA_BOOTSTRAP_    │     │  DO NOT override from    │
│  SERVERS for         │     │  host environment        │
│  containers          │     │                          │
└─────────────────────┘     └──────────────────────────┘
```

---

## 4. APIs, Interfaces, and Key Abstractions

### 4.1 Runtime HTTP Endpoints

| Service | Port | Key Endpoints | Purpose |
|---------|------|---------------|---------|
| omninode-runtime | 8085 | `GET /health` | Health check, readiness probe |
| runtime-effects | 8086 | (port-level) | External I/O processing |
| agent-actions-consumer | 8087 | (port-level) | Observability event persistence |
| intelligence-api | 8053 | `GET /health` | Pattern detection, intent classification |
| contract-resolver | 8091 | `GET /health` | HTTP bridge for contract resolution |
| skill-lifecycle-consumer | 8092 | (port-level) | Skill registry management |
| phoenix | 6006 | OTLP collector | OpenTelemetry observability |

### 4.2 Infrastructure APIs

| Service | Port | API | Purpose |
|---------|------|-----|---------|
| Redpanda | 19092 | Kafka protocol | Event streaming |
| Redpanda | 18082 | Pandaproxy REST | HTTP-based Kafka access |
| Redpanda | 18081 | Schema Registry | Avro/JSON schema management |
| PostgreSQL | 5436 | PostgreSQL wire | Relational data storage |
| Valkey | 16379 | Redis protocol | Caching, pub/sub |
| Consul | 28500 | HTTP API + UI | Service discovery (optional) |
| Infisical | 8880 | REST API | Secrets management (optional) |
| Keycloak | 28080 | OIDC/REST | Authentication (optional) |

### 4.3 OmniMemory Service APIs

| Service | Port | API | Purpose |
|---------|------|-----|---------|
| Qdrant | 6333 | HTTP REST | Vector search |
| Qdrant | 6334 | gRPC | High-performance vector ops |
| Memgraph | 7687 | Bolt protocol | Graph database |
| Memgraph | 7444 | HTTP | Graph DB management |
| Kreuzberg | 8090 | HTTP | Document parsing/processing |

### 4.4 Key Abstractions

- **ONEX 4-Node Pattern**: Effect → Compute → Reducer → Orchestrator. All processing follows this pipeline.
- **TopicProvisioner**: Auto-creates Kafka topics from `ALL_PLATFORM_TOPIC_SPECS` at runtime boot.
- **Migration-Gate (OMN-3737)**: Boot-order sentinel that queries `db_metadata.migrations_complete` before allowing runtime services to start.
- **ContractConfigExtractor (OMN-2287)**: Optional Infisical-based config prefetch. Activates when `INFISICAL_ADDR` is non-empty.
- **DB-SPLIT-05**: Least-privilege database role pattern — 6 separate roles, one per logical service.

---

## 5. Important Files, Functions, and Data Structures

### 5.1 Central Files

| File | Purpose |
|------|---------|
| `docker/docker-compose.infra.yml` | Complete service definitions for all profiles |
| `scripts/deploy-runtime.sh` | Canonical deployment entry point |
| `docker/.env.example` | Template for all environment variables |
| `docker/docker-entrypoint-initdb.d/000_create_multiple_databases.sh` | 7 databases + 6 roles creation |
| `src/omnibase_infra/topics/platform_topic_suffixes.py` | Topic name source of truth |
| `scripts/run-migrations.py` | Incremental migration runner |
| `scripts/bootstrap-infisical.sh` | 6-step Infisical bootstrap |

### 5.2 Configuration & Environment

**Required environment variables** (no defaults, fail if missing):

| Variable | Method |
|----------|--------|
| `POSTGRES_PASSWORD` | `openssl rand -hex 32` |
| `ROLE_OMNIBASE_PASSWORD` | `openssl rand -hex 32` |
| `ROLE_OMNICLAUDE_PASSWORD` | `openssl rand -hex 32` |
| `ROLE_OMNIDASH_PASSWORD` | `openssl rand -hex 32` |
| `ROLE_OMNIINTELLIGENCE_PASSWORD` | `openssl rand -hex 32` |
| `ROLE_OMNIMEMORY_PASSWORD` | `openssl rand -hex 32` |
| `ROLE_OMNINODE_PASSWORD` | `openssl rand -hex 32` |
| `OMNIBASE_INFRA_DB_URL` | Full PostgreSQL DSN |

**Required if using secrets profile**:

| Variable | Method |
|----------|--------|
| `INFISICAL_ENCRYPTION_KEY` | `openssl rand -hex 16` or `32` |
| `INFISICAL_AUTH_SECRET` | `openssl rand -hex 32` |
| `INFISICAL_DB_CONNECTION_URI` | PostgreSQL DSN |
| `INFISICAL_REDIS_URL` | Redis/Valkey URL |

### 5.3 Critical Invariants

| Invariant ID | Description |
|-------------|-------------|
| OMN-3431 | Docker-internal Kafka addressing: containers use `redpanda:9092`, host uses `localhost:19092` |
| OMN-3737 | Migration-gate boot-order sentinel — runtime waits for `db_metadata.migrations_complete` |
| OMN-2287 | Infisical config prefetch — only when `INFISICAL_ADDR` is non-empty |
| OMN-2233 | Invisible deployments — fixed by `deploy-runtime.sh` versioned directories |
| DB-SPLIT-05 | 6 least-privilege database roles, created only when password env var is non-empty |

---

## 6. Frameworks, Libraries, and Tech Stack

### 6.1 Languages & Runtimes

| Language | Usage |
|----------|-------|
| Python 3.11+ | All backend services, libraries, scripts |
| TypeScript/React | OmniDash frontend |
| Bash | Deployment scripts, Docker entrypoints |
| SQL | PostgreSQL migrations, schema definitions |

### 6.2 Package Management

| Tool | Scope |
|------|-------|
| **uv** | All Python repos (NOT poetry, NOT pip) |
| **npm** | OmniDash frontend |
| **Docker Compose V2** | Service orchestration |

### 6.3 Key Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.20+ (V2) | Service orchestration |
| Redpanda | latest | Kafka-compatible event streaming |
| PostgreSQL | 16+ | Primary relational database |
| Valkey | latest | Redis-compatible cache |
| Qdrant | latest | Vector database for embeddings |
| Memgraph | latest | Graph database |
| Infisical | latest | Secrets management (optional) |
| Keycloak | latest | OIDC authentication (optional) |
| Consul | latest | Service discovery (optional) |
| Phoenix | latest | OpenTelemetry observability |

### 6.4 Build & Test

- **Build**: `docker compose --profile runtime build` (BuildKit required)
- **Test**: `uv sync && uv run pytest` (Python), `npm test` (OmniDash)
- **CI**: Pre-commit hooks via `uv run pre-commit install`
- **Container Registry**: Images built locally via compose build

---

## 7. Capabilities, Features, and Use-Cases

### 7.1 Core Features

1. **Contract-Driven Event Bus**: Typed Kafka topics with schema validation via Redpanda
2. **ONEX 4-Node Pattern**: Structured Effect → Compute → Reducer → Orchestrator pipeline
3. **21 Intelligence Nodes**: Intent classification, drift detection, semantic review, pattern learning
4. **Semantic Memory**: Vector search (Qdrant) + knowledge graphs (Memgraph) + embedding storage
5. **Real-Time Dashboard**: Agent monitoring, cost tracking, skill execution analytics
6. **Claude Code Integration**: 90+ skills, 54 agents, hooks, routing via omniclaude plugin
7. **Schema Governance**: Automated drift detection and cross-repo contract enforcement
8. **Secrets Management**: Centralized via Infisical with bootstrap automation

### 7.2 Example Use-Cases

**Use-Case 1: AI Agent Task Execution**
```
User invokes Claude Code skill → omniclaude routes to agent →
Agent publishes to Kafka → omninode-runtime (Effect) picks up →
runtime-worker (Compute) processes → intelligence-api (Reducer) 
applies patterns → runtime (Orchestrator) returns result
```

**Use-Case 2: Pattern Detection & Drift Alert**
```
Code change committed → onex_change_control detects schema drift →
omniintelligence drift detection node analyzes impact →
omnidash displays drift alert with suggested fixes
```

**Use-Case 3: Semantic Memory Recall**
```
Agent needs context → queries omnimemory →
Qdrant vector search finds similar embeddings →
Memgraph knowledge graph provides relationships →
Combined context returned to agent for response
```

**Use-Case 4: Infrastructure Deployment**
```
Developer runs: ./scripts/deploy-runtime.sh --execute --profile full
→ Versioned copy created at ~/.omnibase/infra/deployed/{version}/
→ PostgreSQL starts, migrations run, migration-gate validates
→ Runtime services start after gate passes
→ Health checks confirm all services running
```

**Use-Case 5: Cost & Performance Monitoring**
```
Runtime emits NodeLlmInferenceEffect events →
agent-actions-consumer persists to omnidash_analytics →
OmniDash renders real-time cost aggregates and performance metrics →
intelligence-api provides pattern insights
```

---

## 8. Program Strengths and Best Use

### 8.1 Strengths

| Aspect | Rating | Details |
|--------|--------|---------|
| **Architecture** | ★★★★★ | Clean layer separation, well-defined 4-node pattern |
| **Extensibility** | ★★★★★ | Plugin system (omniclaude), typed contracts (SPI), profile-based deployment |
| **Operability** | ★★★★☆ | Canonical deploy script, health checks, versioned deployments |
| **Security** | ★★★★☆ | Least-privilege DB roles, optional secrets management, boot-order gating |
| **Documentation** | ★★★★☆ | Comprehensive README, inline invariant comments (OMN-*), architecture diagrams |
| **Observability** | ★★★★☆ | Phoenix OTLP, real-time dashboard, Kafka-based event streaming |

### 8.2 Best Suited For

- **AI agent orchestration** with structured pipelines
- **Multi-model inference** with cost tracking and pattern optimization
- **Teams using Claude Code** who want structured agent routing and skill management
- **Organizations requiring governance** over AI agent behavior and schema contracts

### 8.3 Less Appropriate For

- Simple single-model API wrappers (over-engineered for simple use cases)
- Teams without Docker expertise (complex multi-service deployment)
- Ultra-low-latency requirements (Kafka adds milliseconds of latency)
- Projects needing lightweight deployment (13+ services in full profile)

---

## 9. Code Quality and Comprehensiveness Level

### 9.1 Code Quality Assessment

| Metric | Rating | Notes |
|--------|--------|-------|
| **Consistency** | ★★★★★ | All repos follow same patterns: uv, ONEX 4-node, typed contracts |
| **Modularity** | ★★★★★ | Clean SPI separation, profile-based services, plugin architecture |
| **Naming** | ★★★★☆ | Descriptive names, OMN-* invariant IDs, clear file organization |
| **Test Coverage** | ★★★☆☆ | Pre-commit hooks present, pytest configured, but coverage percentage unknown |
| **Documentation** | ★★★★☆ | Excellent README, inline comments, but some cross-repo dependencies underdocumented |
| **Error Handling** | ★★★★☆ | Migration-gate pattern, health checks, graceful fallbacks |

### 9.2 Developer Onboarding

- **Entry point clarity**: `deploy-runtime.sh` is well-documented with clear WARNING in README
- **Environment setup**: `.env.example` with `__REPLACE_WITH_*__` placeholders, generation instructions
- **Architecture understanding**: Docker README provides multi-profile architecture diagrams
- **Complexity barrier**: High — 8 repos, 13+ services, 7 databases requires significant ramp-up time
- **Quick start path**: `omniclaude QUICKSTART.md` provides fastest path to working system

### 9.3 Comprehensiveness Rating

**Production-Ready System: 85/100**

**Justification**:
- ✅ Complete multi-service architecture with proper separation of concerns
- ✅ Versioned deployment with collision prevention (OMN-2233)
- ✅ Boot-order safety (migration-gate, OMN-3737)
- ✅ Least-privilege security (DB-SPLIT-05, 6 roles)
- ✅ Contract-driven event bus with schema validation
- ✅ Comprehensive observability (Phoenix OTLP, OmniDash)
- ✅ Plugin ecosystem (omniclaude, 90+ skills)
- ⚠️ Some cross-repo deployment coordination requires external tooling
- ⚠️ Full-stack deployment of all 8 repos not automated in a single script (this PR addresses that gap)
- ⚠️ Test coverage metrics not readily available across all repos

---

## 10. Complete Port Allocation Map

### Infrastructure (Always On)

| Port | Service | Protocol | Notes |
|------|---------|----------|-------|
| 5436 | PostgreSQL | PostgreSQL wire | Host port (internal: 5432) |
| 16379 | Valkey | Redis protocol | Host port (internal: 6379) |
| 19092 | Redpanda | Kafka external | Host port (internal: 9092) |
| 18082 | Pandaproxy | HTTP REST | Kafka HTTP bridge |
| 18081 | Schema Registry | HTTP REST | Avro/JSON schemas |

### Optional Infrastructure

| Port | Service | Profile | Notes |
|------|---------|---------|-------|
| 28500 | Consul | `consul` | Service discovery UI + API |
| 8880 | Infisical | `secrets` | Secrets management |
| 28080 | Keycloak | `auth` | OIDC authentication |

### Runtime Services (--profile runtime)

| Port | Service | Notes |
|------|---------|-------|
| 8085 | omninode-runtime | ONEX kernel, HTTP health endpoint |
| 8086 | runtime-effects | Effect node processing |
| 8087 | agent-actions-consumer | Observability persistence |
| 8053 | intelligence-api | Pattern detection, intent classification |
| 8091 | contract-resolver | HTTP bridge for contracts |
| 8092 | skill-lifecycle-consumer | Skill registry management |
| 6006 | Phoenix | OTLP observability collector |

### OmniMemory Services (separate compose)

| Port | Service | Notes |
|------|---------|-------|
| 6333 | Qdrant HTTP | Vector database |
| 6334 | Qdrant gRPC | High-performance vector ops |
| 7687 | Memgraph Bolt | Graph database |
| 7444 | Memgraph HTTP | Graph management |
| 6379 | Valkey (memory-local) | Separate from infra Valkey |
| 8090 | Kreuzberg | Document parser/processor |

### Interface Layer

| Port | Service | Notes |
|------|---------|-------|
| 3000 | OmniDash | React observability dashboard |
| — | OmniClaude | Claude Code plugin (no exposed port) |

---

*Analysis verified against source: docker-compose.infra.yml, deploy-runtime.sh, docker/README.md, .env.example, OmniNode org profile README*

