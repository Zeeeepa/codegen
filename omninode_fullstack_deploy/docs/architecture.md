# OmniNode Platform Architecture

## System Topology

```
                            ┌─────────────────────┐
                            │    Claude Code IDE   │
                            │   (OmniClaude Plugin)│
                            │  90+ skills, 54 agents│
                            └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │     OmniDash :3000   │
                            │  Real-time Dashboard │
                            └──────────┬──────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
    ┌─────────▼──────────┐  ┌─────────▼──────────┐  ┌─────────▼──────────┐
    │  OmniIntelligence   │  │    OmniMemory       │  │  ONEX Change       │
    │  21 ONEX Nodes      │  │  Vector + Graph DB   │  │  Control           │
    │  Pattern Learning   │  │  Semantic Retrieval  │  │  Governance        │
    └─────────┬──────────┘  └─────────┬──────────┘  └─────────┬──────────┘
              │                        │                        │
    ┌─────────▼────────────────────────▼────────────────────────▼──────────┐
    │                      ONEX Runtime Layer                               │
    │  omninode-runtime:8085 │ intelligence-api:8053 │ effects:8086         │
    │  contract-resolver:8091│ agent-actions:8087    │ skill-lifecycle:8092 │
    │  runtime-worker        │ Phoenix OTLP:6006     │                      │
    └─────────┬────────────────────────┬────────────────────────┬──────────┘
              │                        │                        │
    ┌─────────▼──────────┐  ┌─────────▼──────────┐  ┌─────────▼──────────┐
    │  PostgreSQL :5436   │  │  Redpanda :29092    │  │  Valkey :16379     │
    │  7 databases        │  │  Kafka event bus    │  │  Platform cache    │
    │  6 roles            │  │  Contract topics    │  │                    │
    │  36 migrations      │  │                     │  │                    │
    └────────────────────┘  └─────────────────────┘  └────────────────────┘
              │
    ┌─────────▼──────────┐  ┌─────────────────────┐
    │  Infisical :8880    │  │  Keycloak :28080     │
    │  Secrets (opt-in)   │  │  Auth/OIDC (opt-in)  │
    └────────────────────┘  └─────────────────────┘
```

## ONEX 4-Node Pattern

Every processing unit in the platform follows the ONEX 4-node architecture:

```
EFFECT (I/O) → COMPUTE (transform) → REDUCER (aggregate) → ORCHESTRATOR (coordinate)
```

| Node Type | Responsibility | Side Effects | Examples |
|-----------|---------------|-------------|---------|
| **Effect** | External I/O (DB, API, file) | Yes | memory_storage, memory_retrieval |
| **Compute** | Pure data transformation | No | semantic_analyzer, similarity_compute |
| **Reducer** | State aggregation (FSM) | Minimal | memory_consolidator, statistics_reducer |
| **Orchestrator** | Multi-step coordination | Via sub-nodes | memory_lifecycle, agent_coordinator |

## Data Flow

```
User Prompt
  │
  ▼
SessionStart hook (OmniClaude)
  │ - Capability probe (STANDALONE / EVENT_BUS / FULL_ONEX)
  │ - Daemon health check
  ▼
UserPromptSubmit hook
  │ - Agent routing (prompt → best agent match)
  │ - Context injection (learned patterns → prompt)
  │ - Pattern advisory (enforcement check)
  │
  ├──→ Kafka: onex.evt.session.* (preview-safe telemetry)
  ├──→ Kafka: onex.cmd.omniintelligence.* (full prompt, restricted)
  │
  ▼
ONEX Runtime (omninode-runtime:8085)
  │ - Skill execution
  │ - Contract resolution
  │ - Effect processing
  │
  ├──→ intelligence-api:8053 (pattern learning, intent classification)
  ├──→ Qdrant:6333 (vector similarity, memory retrieval)
  ├──→ Memgraph:7687 (intent graphs, relationship queries)
  ├──→ PostgreSQL:5436 (state persistence)
  │
  ▼
PostToolUse hook
  │ - Quality assessment
  │ - Content capture
  │ - Emit events
  ▼
SessionEnd hook
  │ - Session summary
  │ - Final event emission
  ▼
OmniDash:3000 (real-time visualization)
```

## Event Bus Topics

Topics are **contract-driven** — extracted from node `contract.yaml` files at startup.

### ONEX Event Topics (Preview-Safe)

| Topic Pattern | Access | Purpose |
|--------------|--------|---------|
| `onex.evt.*` | Broad | Preview-safe observability events |
| `onex.cmd.omniintelligence.*` | Restricted | Full prompts for intelligence processing |
| `onex.cmd.omnimemory.*` | Restricted | Memory operations |

### OmniDash Observability Topics

OmniDash consumes these application-level Kafka topics for real-time dashboard visualization:

| Topic | Purpose |
|-------|---------|
| `agent-routing-decisions` | Agent selection with confidence scores |
| `agent-transformation-events` | Polymorphic agent transformations |
| `router-performance-metrics` | Routing performance and latency data |
| `agent-actions` | Tool calls, decisions, execution errors |

Topics are created dynamically by services based on their `contract.yaml` declarations at runtime.

## Database Schema

### 7 Databases (created by migrations 000-036)

| Database | Owner Role | Purpose |
|----------|-----------|---------|
| `omnibase_infra` | `role_omnibase` | Platform metadata, sessions, Kafka state |
| `omniintelligence` | `role_omniintelligence` | Intelligence state, patterns, learning |
| `omniclaude` | `role_omniclaude` | Plugin state, agent configs, session logs |
| `omnimemory` | `role_omnimemory` | Memory metadata, indices, embeddings |
| `omninode_cloud` | `role_omninode` | Cloud deployment state, provisioning |
| `omnidash_analytics` | `role_omnidash` | Dashboard analytics, read model |
| `system` | `postgres` | PostgreSQL system state |

### DB-SPLIT-05 / OMN-2056

The database split ensures each service has:
- Its own database (isolation)
- Its own role (least-privilege)
- Schema fingerprint validation (SHA256)
- Migration state tracking
