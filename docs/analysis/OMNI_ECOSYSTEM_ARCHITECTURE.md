# OMNI Ecosystem: Complete Architecture Analysis & Local Windows Orchestrator Blueprint

> **Analysis Date**: 2026-03-04  
> **Packages Analyzed**: 6 | **Files**: 10,071 | **Lines of Code**: 2,625,878 | **YAML Contracts**: 221  
> **Target**: Local Windows Native Multi-Agent Orchestrator / Mission Control

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Package Inventory](#2-package-inventory)
3. [Four-Node Architecture](#3-four-node-architecture)
4. [Core Pipeline: NL → Execution](#4-core-pipeline)
5. [60+ Skill Orchestrators](#5-skill-orchestrators)
6. [MCP Subsystem](#6-mcp-subsystem)
7. [Cross-Agent Memory](#7-cross-agent-memory)
8. [Pattern Learning & Anti-Gaming](#8-pattern-learning)
9. [Strongest Suites Assessment](#9-strongest-suites)
10. [Local Windows Deployment Blueprint](#10-deployment-blueprint)
11. [Infrastructure Replacement Map](#11-infra-replacement)
12. [Implementation Roadmap](#12-implementation-roadmap)

---

## 1. Executive Summary

The **OMNI ecosystem** (by OmniNode.ai) is a **contract-driven, DAG-based multi-agent orchestration framework** comprising 6 Python packages under the MIT license. It implements the **ONEX (Open Node Execution)** protocol — a deterministic execution layer for tools and distributed workflows that standardizes how agents execute, communicate, and share context.

### Why It Matters for a Local Orchestrator

OMNI solves the hardest problems in multi-agent orchestration:
- **Task decomposition**: Natural language → typed intent → dependency DAG → executable tickets
- **Parallel execution**: Topological sort enables maximum parallelism while respecting dependencies
- **Quality control**: Ambiguity gating, anti-gaming guardrails, evidence-tier classification
- **Memory coordination**: Cross-agent memory with subscription model for pattern reuse
- **Tool integration**: Complete MCP (Model Context Protocol) subsystem with registry/discovery

**95% of protocols, 85% of skill contracts, and 80% of core models are directly reusable** for a local Windows deployment with minimal adaptation (primarily replacing Kafka with a local event bus).

---

## 2. Package Inventory

| Package | Version | Files | Lines | YAML Contracts | PyPI Downloads/mo | Role |
|---------|---------|-------|-------|----------------|-------------------|------|
| **omnibase-spi** | 0.15.0 | 477 | 123,525 | 0 | — | Protocol interfaces (SPI) |
| **omnibase-core** | 0.23.0 | 4,619 | 1,085,216 | 3 | — | Execution engine, models, enums |
| **omnibase-infra** | 0.15.0 | 2,416 | 796,926 | 51 | 17,473 | Infrastructure (Kafka, DB, Consul) |
| **omninode-claude** | 0.4.1 | 1,036 | 264,181 | 110 | — | 60+ skill orchestrators, DAG pipeline |
| **omninode-intelligence** | 0.9.3 | 1,109 | 238,411 | 45 | — | Pattern learning, decision store |
| **omninode-memory** | 0.6.1 | 414 | 117,619 | 12 | — | Cross-agent memory coordination |

### Dependency Graph
```
omnibase-spi ← omnibase-core ← omnibase-infra
                    ↑
              omninode-claude
              omninode-intelligence  
              omninode-memory
```

All packages require **Python ≥3.12**, **Pydantic ≥2.11**, and **typing-extensions ≥4.5**.

---

## 3. Four-Node Architecture

ONEX enforces a strict **four-node-type taxonomy** with unidirectional data flow:

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────────┐
│   EFFECT    │──▶│   COMPUTE   │──▶│   REDUCER   │──▶│ ORCHESTRATOR │
│  (I/O)      │   │ (Transform) │   │ (Aggregate) │   │ (Coordinate) │
└─────────────┘   └─────────────┘   └─────────────┘   └──────────────┘
     │                                    │                    │
     ▼                                    ▼                    ▼
 External I/O                     Emits Intents          Issues Actions
 (APIs, DB, Files)                (no direct I/O)        (workflow steps)
```

### Node Type Rules

| Type | Can Do | Cannot Do | Output |
|------|--------|-----------|--------|
| **EFFECT** | API calls, DB ops, file I/O | Pure transforms | `events[]` only |
| **COMPUTE** | Data transforms, validation | Side effects | `result` only |
| **REDUCER** | FSM state transitions | Direct I/O | `intents[]` only |
| **ORCHESTRATOR** | Workflow coordination | Subprocess calls | `actions[]` only |

### Implementation Pattern
Nodes are **thin shells** (~15 lines). All business logic lives in **handlers**:

```python
# Node (thin shell)
class NodeDatabaseEffect(NodeEffect):
    def __init__(self, container: ModelONEXContainer) -> None:
        super().__init__(container)

# Handler (all logic)
class HandlerDatabase:
    async def handle(self, contract, input_envelope_id, correlation_id):
        result = await self._execute_with_retry(contract)
        return ModelHandlerOutput.for_effect(
            input_envelope_id=input_envelope_id,
            correlation_id=correlation_id,
            events=(ModelEventEnvelope(
                event_type="database.operation.completed",
                payload={"result": result}
            ),),
        )
```


---

## 4. Core Pipeline: NL → Execution

The crown jewel — a 4-stage pipeline that converts natural language into parallel executable work:

```
User Request (NL)
    ↓
┌──────────────────────────────┐
│ Stage 1: NL Intent Pipeline  │  Classifies into FEATURE, BUG_FIX, REFACTOR,
│ (node_nl_intent_pipeline)    │  SECURITY, DEBUGGING, INFRASTRUCTURE, etc.
└──────────────────────────────┘
    ↓
┌──────────────────────────────┐
│ Stage 2: Plan DAG Generator  │  Maps intent → dependency DAG of WorkUnits
│ (handler_plan_dag_default)   │  Template-driven: FEATURE→[design→impl→tests→docs]
└──────────────────────────────┘
    ↓
┌──────────────────────────────┐
│ Stage 3: Ambiguity Gate      │  Evaluates each DAG node for unresolved ambiguity
│ (node_ambiguity_gate)        │  Flags for human review without rejecting
└──────────────────────────────┘
    ↓
┌──────────────────────────────┐
│ Stage 4: Ticket Compiler     │  Compiles each WorkUnit → executable ticket/task
│ (node_ticket_compiler)       │  Ready for agent assignment and execution
└──────────────────────────────┘
    ↓
┌──────────────────────────────┐
│ Orchestrator.plan()          │  Topological sort → parallel execution steps
│ Orchestrator.execute()       │  Dependency-aware parallel execution
└──────────────────────────────┘
```

### Intent → DAG Templates (from `handler_plan_dag_default.py`)

| Intent Type | Work Units | Dependencies |
|-------------|-----------|--------------|
| **FEATURE** | design → impl → tests → docs | Sequential chain |
| **BUG_FIX** | investigate → fix → tests | Sequential chain |
| **REFACTOR** | scope → refactor → tests | Sequential chain |
| **SECURITY** | audit → patch → tests | Sequential chain |
| **INFRASTRUCTURE** | design → impl → tests | Sequential chain |
| **EPIC_DECOMPOSITION** | epic → decompose | Parent-child |
| **CODE** | impl → tests | Simple pair |
| **DEBUGGING** | investigate → fix | Simple pair |
| **REVIEW** | review | Single node |

### OmniMemory Cache Integration
The DAG generator integrates with the memory system: if a previous execution produced a promoted pattern for the same intent type, it **short-circuits** template generation and reuses the cached pattern — learning from past executions.

---

## 5. Skill Orchestrators (60+ Ready-Made Agent Behaviors)

`omninode-claude` provides **110 YAML contracts** defining 60+ skill orchestrators. Each follows a common pattern:

```
┌─────────────────────────┐
│ YAML Contract            │  Defines: name, description, input/output schema,
│ (node_skill_X.onex.yaml)│  topics, capabilities, permissions
└─────────────────────────┘
          │
          ▼
┌─────────────────────────┐
│ Thin Shell Node          │  ~15 lines, imports shared handler
│ (node.py)               │
└─────────────────────────┘
          │
          ▼
┌─────────────────────────┐
│ Shared Handler           │  handle_skill_requested() dispatches to
│ (handler_skill_requested)│  "Polly" (polymorphic agent) and parses
└─────────────────────────┘  RESULT: block from output
```

### Key Skill Categories

**Agent Management**:
- `dispatching_parallel_agents_orchestrator` — Spawns 3+ agents for independent tasks
- `node_agent_routing_compute` — Routes requests to optimal agent

**CI/CD Pipeline**:
- `ci_watch`, `ci_failures`, `ci_fix_pipeline` — Monitor and auto-fix CI

**PR Workflows**:
- `pr_review`, `pr_watch`, `pr_polish`, `fix_prs`, `auto_merge`

**Planning & Ticketing**:
- `create_ticket`, `plan_ticket`, `ticket_work`, `decompose_epic`
- `writing_plans`, `executing_plans`, `insights_to_plan`, `gap_analysis`

**Code Quality**:
- `test_driven_development`, `testing_anti_patterns`, `contract_compliance_check`

**Debugging**:
- `systematic_debugging`, `root_cause_tracing`, `crash_recovery`

### Shared Handler Implementation

The `handle_skill_requested` function is the universal dispatcher:

```python
async def handle_skill_requested(
    request: ModelSkillRequest,
    *,
    task_dispatcher: TaskDispatcher,     # Sends prompt to LLM
    event_emitter: EventEmitter | None,  # Lifecycle events
) -> ModelSkillResult:
    # 1. Build prompt with skill path + serialized args
    prompt = f"Execute the skill at {request.skill_path!r}..."
    
    # 2. Emit skill.started event
    # 3. Dispatch to LLM agent (Polly)
    raw_output = await task_dispatcher(prompt)
    
    # 4. Parse RESULT: block from output
    status, error = _parse_result_block(raw_output)
    
    # 5. Emit skill.completed event
    return ModelSkillResult(skill_name=..., status=status, output=raw_output)
```

---

## 6. MCP Subsystem (Model Context Protocol)

A complete tool management subsystem with 20+ protocol definitions:

### Core MCP Protocols (from `omnibase_spi`)

| Protocol | Purpose |
|----------|---------|
| `ProtocolMCPToolDefinition` | Tool metadata, parameters, schemas |
| `ProtocolMCPToolExecution` | Execution state, results, timing |
| `ProtocolMCPSubsystemRegistration` | Lifecycle, health, heartbeats, TTL |
| `ProtocolMCPRegistryMetrics` | Subsystem counts, peak concurrency, uptime |
| `ProtocolMCPRegistryConfig` | Max subsystems, tools, timeouts |
| `ProtocolMCPHealthCheck` | Per-subsystem diagnostics |
| `ProtocolMCPDiscoveryInfo` | Service discovery with capabilities |
| `ProtocolMCPValidationResult` | Input validation with errors/warnings |
| `ProtocolEventBusConfig` | Kafka/event bus configuration |
| `ProtocolToolClass` / `ProtocolToolInstance` | Tool classification and instances |

### MCP Registry Capabilities
- **Register/deregister tools** with schema validation
- **Health monitoring** with configurable heartbeat intervals
- **Discovery service** — agents can discover available tools dynamically
- **Execution tracking** — success/failure counts, timing, peak concurrency
- **Maintenance mode** — graceful tool unavailability

This maps perfectly to a local orchestrator where you register local tools, LLM endpoints, and file system operations.


---

## 7. Cross-Agent Memory Coordination

`omninode-memory` implements a **subscription-based memory system** for agent coordination:

### Agent Coordinator (Orchestrator Node)
**Actions**: SUBSCRIBE, UNSUBSCRIBE, LIST_SUBSCRIPTIONS, NOTIFY

```python
# Agent subscribes to memory events
coordinator.subscribe(
    agent_id="code-review-agent",
    topic="memory.item.created",
    filter={"category": "bug_pattern"}
)

# When a new pattern is discovered...
coordinator.notify(
    topic="memory.item.created",
    payload={"item_id": "pat-123", "category": "bug_pattern"}
)
# → code-review-agent receives notification via event bus
```

### Memory Lifecycle
```
Create → Update → Promote → Archive
  ↓         ↓         ↓
memory_lifecycle_orchestrator
  ↓
semantic_analyzer_compute → similarity_compute
  ↓
memory_consolidator_reducer (merge related items)
  ↓
memory_storage_effect → intent_storage_effect (graph DB)
```

### Key Models
- `ModelMemoryItem`: Content, tags, category, relationships, embeddings
- `ModelSubscription`: Agent ID, topic, filter, delivery status
- `ModelConsolidationResult`: Merged items with provenance

---

## 8. Pattern Learning & Anti-Gaming

`omninode-intelligence` provides continuous improvement via pattern recognition:

### Pattern Lifecycle
```
Execution Trace → Pattern Discovery → Validation → Promotion → Archival
                                          ↓
                              Anti-Gaming Guardrails
                              (exploitation detection)
```

### Evidence-Tier Classification
| Tier | Strength | Requirements |
|------|----------|-------------|
| TIER_0 | Strongest | Multiple confirmed sources, high confidence |
| TIER_1 | Strong | Validated pattern with evidence |
| TIER_2 | Moderate | Statistical correlation |
| TIER_3 | Weak | Single observation |
| TIER_4 | Anecdotal | Unvalidated signal |

### Decision Store
Records **every major decision** with:
- Input context, alternative options considered
- Decision rationale, confidence level
- Outcome (when available), replay capability

### Model Selector
Dynamically selects the optimal LLM for each task based on:
- Task complexity and type
- Historical performance on similar tasks
- Cost/latency budget constraints
- Available model capabilities

---

## 9. Strongest Suites Assessment

### Suite 1: Contract-Driven DAG Orchestration ⭐⭐⭐⭐⭐
**Reusability: 95%** | No infrastructure assumptions
- `omnibase_spi/protocols/advanced/protocol_orchestrator.py`
- `omnibase_spi/protocols/advanced/protocol_graph_model.py`
- **Best for**: Task decomposition, dependency resolution, parallel execution
- **Unique value**: Topological sort with cycle detection and orphan flagging

### Suite 2: NL → Execution Pipeline ⭐⭐⭐⭐⭐
**Reusability: 85%** | Intent templates are universal
- `omninode_claude/nodes/node_nl_intent_pipeline/`
- `omninode_claude/nodes/node_plan_dag_generator/handler_plan_dag_default.py`
- **Best for**: Requirement decomposition, work planning, quality gates
- **Unique value**: Template-driven DAG generation with OmniMemory cache

### Suite 3: 60+ Skill Orchestrators ⭐⭐⭐⭐
**Reusability: 90%** | Shared handler pattern is LLM-agnostic
- `omninode_claude/nodes/shared/handler_skill_requested.py` + 60 skill nodes
- **Best for**: Rapid capability deployment, agent behavior library
- **Unique value**: Ready-made skills for CI/CD, PR, debugging, planning

### Suite 4: MCP Tool Management ⭐⭐⭐⭐⭐
**Reusability: 100%** | No infrastructure assumptions
- `omnibase_spi/protocols/mcp/*.py`
- **Best for**: Tool registration, discovery, health monitoring
- **Unique value**: Complete protocol suite with validation and metrics

### Suite 5: Cross-Agent Memory ⭐⭐⭐⭐
**Reusability: 75%** | Replace Kafka with local event bus
- `omninode_memory/nodes/agent_coordinator_orchestrator/`
- **Best for**: Pattern reuse, agent communication, feedback loops
- **Unique value**: Subscription model with topic filtering

### Suite 6: Pattern Learning ⭐⭐⭐⭐
**Reusability: 75%** | Pure algorithms, no infrastructure lock-in
- `omninode_intelligence/nodes/node_pattern_compiler_reducer/`
- **Best for**: Continuous improvement, quality control
- **Unique value**: Anti-gaming guardrails with evidence tiers

### Suite 7: Type System (200+ Enums) ⭐⭐⭐⭐⭐
**Reusability: 100%** | Universal definitions
- `omnibase_core/enums/` (200+ files)
- **Best for**: Schema consistency, IDE support, type safety

### Suite 8: Service Registry & DI ⭐⭐⭐⭐⭐
**Reusability: 100%** | Protocol-based design
- `omnibase_core/models/container/model_onex_container.py`
- **Best for**: Runtime handler resolution, backend swapping

---

## 10. Local Windows Deployment Blueprint

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    MISSION CONTROL UI                         │
│              (FastAPI + WebSocket + Browser)                  │
│   ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐│
│   │ DAG Viewer │ │ Agent Pool │ │ Log Stream │ │ Controls ││
│   │ (real-time)│ │ (health)   │ │ (search)   │ │ (pause/  ││
│   └────────────┘ └────────────┘ └────────────┘ │  resume) ││
│                                                  └──────────┘│
├──────────────────────────────────────────────────────────────┤
│                     ORCHESTRATOR CORE                         │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ NL Intent │→ │ Plan DAG Gen │→ │ Ambiguity Gate       │  │
│  │ Parser    │  │ (templates)  │  │ (confidence scoring) │  │
│  └───────────┘  └──────────────┘  └──────────────────────┘  │
│                         ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │          Ticket Compiler & Scheduler                     │ │
│  │    (topological sort, dependency resolution, FIFO)       │ │
│  └─────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│              LOCAL EVENT BUS (asyncio.Queue + SQLite WAL)     │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│    │agent.cmd │  │skill.done│  │memory.new│  │dag.status│  │
│    └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├──────────────────────────────────────────────────────────────┤
│                   AGENT EXECUTION LAYER                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
│  │ COMPUTE  │ │ EFFECT   │ │ REDUCER  │ │ ORCHESTRATOR   │ │
│  │ (async   │ │ (sub-    │ │ (async   │ │ (async task,   │ │
│  │  task)   │ │ process) │ │  task)   │ │  workflow mgr) │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ MCP Registry │ │ Pattern      │ │ LLM Backend Adapter  │ │
│  │ (in-process) │ │ Learning     │ │ ┌──────┐ ┌────────┐ │ │
│  │ • tools      │ │ Store        │ │ │Claude│ │ Ollama │ │ │
│  │ • health     │ │ • decisions  │ │ │ API  │ │ local  │ │ │
│  │ • discovery  │ │ • anti-game  │ │ └──────┘ └────────┘ │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│           SQLite (WAL mode) — Unified Persistence             │
│  ┌─────────────┐┌────────────┐┌──────────┐┌───────────────┐ │
│  │ dag_history  ││ decisions  ││ events   ││ agent_state   │ │
│  │ (executions) ││ (audit)    ││ (bus log)││ (health/sub)  │ │
│  └─────────────┘└────────────┘└──────────┘└───────────────┘ │
├──────────────────────────────────────────────────────────────┤
│           YAML Contract Store (filesystem)                    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ 221 .onex.yaml contracts (skill definitions, schemas)│    │
│  │ Hot-reload via filesystem watcher (watchdog)          │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### Process Model

| Component | Execution Model | Why |
|-----------|----------------|-----|
| Orchestrator Core | Main async process | Low latency, direct access to all state |
| COMPUTE nodes | `asyncio.Task` in main process | Pure transforms, no isolation needed |
| EFFECT nodes | `subprocess` (Python) | I/O isolation, crash containment |
| REDUCER nodes | `asyncio.Task` in main process | FSM transitions are lightweight |
| ORCHESTRATOR nodes | `asyncio.Task` in main process | Workflow coordination needs shared state |
| Mission Control UI | FastAPI in same process (separate thread) | WebSocket needs access to orchestrator state |
| LLM Backend | Network calls (API) or subprocess (local) | Depends on backend choice |

### IPC Design (Agent ↔ Orchestrator)

```python
class LocalEventBus:
    """In-process event bus with SQLite durability."""
    
    def __init__(self, db_path: Path):
        self._topics: dict[str, list[asyncio.Queue]] = {}
        self._db = sqlite3.connect(db_path, isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at REAL NOT NULL,
                consumed BOOLEAN DEFAULT FALSE
            )
        """)
    
    async def publish(self, topic: str, payload: dict) -> None:
        # Persist for durability
        self._db.execute(
            "INSERT INTO events (topic, payload, created_at) VALUES (?, ?, ?)",
            (topic, json.dumps(payload), time.time())
        )
        # In-memory fan-out for speed
        for queue in self._topics.get(topic, []):
            await queue.put(payload)
    
    async def subscribe(self, topic: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._topics.setdefault(topic, []).append(queue)
        return queue
```


---

## 11. Infrastructure Replacement Map

| Cloud Component | Local Replacement | Rationale | Risk |
|----------------|-------------------|-----------|------|
| **Kafka** (event bus) | `asyncio.Queue` + SQLite WAL | In-process for speed; SQLite for persistence across restarts | No consumer groups; OK for single-machine |
| **Distributed DB** | SQLite (WAL mode, single-writer) | Handles all persistence at local scale; zero setup | Single-writer bottleneck at extreme scale |
| **Container orchestration** (K8s) | Python `multiprocessing` + `subprocess` | Agent process management; Windows `spawn` start method | No auto-restart; implement watchdog |
| **Cloud LLM APIs** | Adapter interface → Claude API / Ollama / LM Studio | Must be pluggable; start with API, add local later | Local LLMs: GPU requirements, quality trade-offs |
| **Service discovery** (Consul) | In-process MCP registry | Already protocol-based; perfect for local | No multi-machine; fine for target use case |
| **Distributed tracing** | Structured logging + SQLite event log | Queryable from mission control UI; `structlog` recommended | No distributed correlation; fine for local |
| **Health checks** (HTTP) | Local heartbeat loop per agent task | Report to mission control via event bus | Process crash detection needs watchdog |
| **Idempotency/DLQ** | SQLite deduplication table + dead letter table | Track event IDs to prevent reprocessing | Simpler than Kafka exactly-once semantics |
| **Graph DB** (memory storage) | SQLite FTS5 + JSON columns | Full-text search + structured queries | No native graph queries; use recursive CTEs |

### Adapter Pattern for LLM Backends

```python
class LLMBackendAdapter(Protocol):
    """Pluggable LLM backend for the orchestrator."""
    
    async def complete(
        self,
        prompt: str,
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tools: list[ProtocolMCPToolDefinition] | None = None,
    ) -> LLMResponse: ...
    
    async def health_check(self) -> ProtocolMCPHealthCheck: ...
    
    @property
    def capabilities(self) -> list[str]: ...


class ClaudeAPIBackend(LLMBackendAdapter):
    """Claude API via anthropic SDK."""
    ...

class OllamaBackend(LLMBackendAdapter):
    """Local LLM via Ollama REST API (http://localhost:11434)."""
    ...

class LMStudioBackend(LLMBackendAdapter):
    """Local LLM via LM Studio OpenAI-compatible API."""
    ...
```

---

## 12. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2) 🏗️

| Task | Source Package | Effort | Output |
|------|---------------|--------|--------|
| Python project setup (Windows asyncio, poetry/uv) | — | 1d | `pyproject.toml`, CI |
| Port SPI protocols (95% copy) | `omnibase-spi` | 1d | All protocol interfaces |
| Port core enums (200+ types) | `omnibase-core` | 0.5d | Type system |
| Implement LocalEventBus | New | 1d | `asyncio.Queue` + SQLite |
| Port ModelONEXContainer (DI) | `omnibase-core` | 0.5d | Service registry |
| SQLite persistence layer | New | 1d | DAG history, decisions, events |
| Port YAML contract loader | `omnibase-core` | 0.5d | Contract parsing + validation |

**Milestone**: Contracts load, events flow, types validate

### Phase 2: Core Pipeline (Weeks 3-4) ⚡

| Task | Source Package | Effort | Output |
|------|---------------|--------|--------|
| Port NL Intent Parser | `omninode-claude` | 1d | Intent classification |
| Port Plan DAG Generator | `omninode-claude` | 1d | Intent → DAG conversion |
| Port Ambiguity Gate | `omninode-claude` | 0.5d | Quality gate |
| Port Ticket Compiler | `omninode-claude` | 0.5d | DAG → executable tickets |
| Port ProtocolOrchestrator (plan/execute) | `omnibase-spi` | 1d | Topological execution |
| Implement LLM Backend Adapter | New | 1d | Claude API adapter first |
| Wire pipeline end-to-end | New | 1d | NL → execution working |

**Milestone**: "Add login form validation" → spawns 4 agents (design, impl, tests, docs)

### Phase 3: Agent Execution (Weeks 5-6) 🤖

| Task | Source Package | Effort | Output |
|------|---------------|--------|--------|
| Implement 4 node-type executors | `omnibase-core` | 2d | COMPUTE/EFFECT/REDUCER/ORCHESTRATOR |
| Subprocess management for EFFECT nodes | New | 1d | Windows `spawn` + watchdog |
| Port MCP Registry (local) | `omnibase-spi` | 1d | Tool registration/discovery |
| Port 15 highest-value skills | `omninode-claude` | 2d | Agent behaviors |
| Port Agent Routing | `omninode-claude` | 1d | Optimal agent selection |
| Cross-agent memory via event bus | `omninode-memory` | 1d | Subscription model |

**Milestone**: Full agent pool with 15 skills, memory coordination, tool discovery

### Phase 4: Mission Control UI (Weeks 7-8) 🎯

| Task | Source Package | Effort | Output |
|------|---------------|--------|--------|
| FastAPI backend + WebSocket | New | 1d | Real-time state streaming |
| DAG visualization (live status) | New | 2d | Node states, edges, progress |
| Agent pool dashboard | New | 1d | Health, active tasks, history |
| Log viewer with structured search | New | 1d | SQLite FTS5 queries |
| Manual intervention controls | New | 1d | Pause/resume/abort/retry |
| Request composer (NL input) | New | 0.5d | Text box + intent preview |
| Ticket/work unit detail view | New | 0.5d | Per-node execution details |

**Milestone**: Full mission control with real-time DAG visualization

### Phase 5: Intelligence Layer (Weeks 9-10) 🧠

| Task | Source Package | Effort | Output |
|------|---------------|--------|--------|
| Port Decision Store | `omninode-intelligence` | 1d | Audit trail + replay |
| Port Pattern Learning | `omninode-intelligence` | 2d | Pattern discovery + promotion |
| Port Anti-Gaming Guardrails | `omninode-intelligence` | 1d | Exploitation detection |
| OmniMemory cache integration | `omninode-memory` | 1d | DAG generation short-circuits |
| Feedback loops | New | 1d | Execution results → patterns |
| Model Selector (local) | `omninode-intelligence` | 1d | LLM routing per task |
| Permission model enforcement | New | 0.5d | Per-skill contract gates |

**Milestone**: Self-improving orchestrator with pattern learning and decision audit

---

## Appendix A: Windows-Specific Considerations

1. **AsyncIO Event Loop**: Windows uses `ProactorEventLoop` by default. Verify all `asyncio.subprocess` operations work correctly.
2. **Path Normalization**: Use `pathlib.Path` consistently; OMNI may have POSIX path assumptions.
3. **Process Management**: No `fork()`. Use `multiprocessing.Process(start_method='spawn')`.
4. **File Locking**: SQLite WAL mode handles this well on Windows via `LockFileEx`.
5. **GPU Access**: For local LLMs (llama.cpp), CUDA or DirectML. Test with `torch.cuda.is_available()`.
6. **Filesystem Watcher**: Use `watchdog` library for YAML contract hot-reload.

## Appendix B: Complete File Reference

### Critical Files to Port First

```
# Protocols (copy verbatim)
omnibase_spi/protocols/advanced/protocol_orchestrator.py
omnibase_spi/protocols/advanced/protocol_graph_model.py
omnibase_spi/protocols/advanced/protocol_node_model.py
omnibase_spi/protocols/mcp/*.py  (20+ files)

# Core Pipeline
omninode_claude/nodes/node_nl_intent_pipeline/
omninode_claude/nodes/node_plan_dag_generator/handler_plan_dag_default.py
omninode_claude/nodes/node_plan_dag_generator/models/*.py
omninode_claude/nodes/node_ambiguity_gate/
omninode_claude/nodes/node_ticket_compiler/

# Skill Handler
omninode_claude/nodes/shared/handler_skill_requested.py

# Memory Coordination
omninode_memory/nodes/agent_coordinator_orchestrator/
omninode_memory/handlers/handler_subscription.py

# Intelligence
omninode_intelligence/decision_store/
omninode_intelligence/nodes/node_pattern_compiler_reducer/
omninode_intelligence/nodes/node_anti_gaming_guardrails_compute/

# Container / DI
omnibase_core/models/container/model_onex_container.py

# Enums (all)
omnibase_core/enums/**/*.py
```

---

*Generated from analysis of 6 OMNI packages (10,071 files, 2,625,878 LOC, 221 YAML contracts)*