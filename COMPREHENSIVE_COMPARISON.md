# 🏗️ Super Comprehensive 6-Codebase Comparison for CoWork-OS

## Building a Local Windows Native Assistant Orchestrator / Control Plane / Mission Control

> **Goal**: Multi-coding-agent spawning → task decomposition → sub-agent assignment → completions tracking → temporal top layer

---

## 📊 At-a-Glance Matrix

| Dimension | TheiaOS | Lattice | Attune AI | Taskbrew | ZERG | **Bosun** |
|---|---|---|---|---|---|---|
| **Version** | 2026.3.17 | 1.2.1 | 3.9.0 | 1.0.6 | latest | feat/portal |
| **Language** | TypeScript | TypeScript/React | Python | Python (FastAPI) | Python | JavaScript (ESM) |
| **LOC** | 587K | 56K | 517K | 30K | 155K | 294K |
| **Files** | 3,625 | 1,371 | 2,718 | 189 | 1,118 | 565 |
| **Dependencies** | 52 | 43 | moderate | 9 | moderate | moderate |
| **License** | MIT | Apache 2.0 | Apache 2.0 | MIT | MIT | Apache 2.0 |
| **Primary Domain** | AI Messaging Gateway | Session Dashboard | Workflow OS for Claude | Agent Team Orchestrator | Parallel Swarm Executor | Control Plane |

---

## 🎯 Requirement-by-Requirement Scoring (1-10)

| Requirement | TheiaOS | Lattice | Attune | Taskbrew | ZERG | **Bosun** |
|---|---|---|---|---|---|---|
| **Windows Native Desktop** | 2 | 3 | 1 | 1 | 1 | **9** |
| **Multi-Agent Spawning** | 6 | 5 | 7 | 6 | **9** | 8 |
| **Task Decomposition** | 3 | 3 | **9** | 7 | 7 | 7 |
| **Sub-Agent Assignment/Routing** | 4 | 4 | 8 | 6 | 6 | **9** |
| **Completions Tracking** | 5 | **8** | 7 | 6 | 7 | 8 |
| **Temporal/DAG Management** | 3 | 3 | 6 | 5 | 7 | **9** |
| **MCP Tools Ecosystem** | 4 | 5 | **9** | 5 | 2 | 6 |
| **Skills/Plugin System** | **9** | 5 | 7 | 4 | 3 | 6 |
| **Context Engineering** | 5 | 4 | 7 | 4 | **9** | 5 |
| **Cost Management** | 3 | 4 | **9** | 6 | 2 | 4 |
| **Real-time Streaming/UI** | 5 | **9** | 3 | 5 | 2 | 7 |
| **Production Testing** | 5 | 5 | **10** | 3 | 5 | 7 |
| **Multi-Executor Support** | 4 | 6 | 4 | 5 | 3 | **9** |
| **Git Worktree Isolation** | 2 | 2 | 3 | 5 | **10** | 4 |
| **Workflow Visual Builder** | 3 | 3 | 2 | 2 | 1 | **8** |
| **TOTAL** | 63 | 69 | 92 | 70 | 74 | **106** |

---

## 🔬 Deep Dive: Each Codebase

---

### 1️⃣ TheiaOS (v2026.3.17) — "The Nervous System"

**What it is**: Multi-channel AI gateway — your personal AI's operating system that connects to every messaging channel through a single unified system.

**Architecture**:
```
Gateway → Channels (iMessage/WhatsApp/Discord/Telegram/Signal/35+)
       → Agent (Memory/Cron/Hooks)
       → Skills (60+ plugins)
       → Browser Automation
       → Nodes (remote device control)
       → Sub-agents (background workers)
```

**Key Structures**:
- `dist/plugin-sdk/` — Comprehensive SDK with agents, tools, channels, commands, gateway
- `extensions/` — 35+ channel integrations (bluebubbles, discord, telegram, slack, etc.)
- `skills/` — 60+ skills (coding-agent, github, notion, obsidian, voice-call, etc.)
- `dist/plugin-sdk/agents/tools/` — browser-tool, memory-tool, message-tool, canvas-tool, cron-tool, etc.
- `dist/plugin-sdk/agents/cli-runner.d.ts` — Runs Claude CLI and custom CLI agents

**Strongest Suites**:
- 🏆 **Plugin/Skills ecosystem** — Largest, most extensible skill system of all 6
- 🏆 **Channel diversity** — 35+ messaging integrations, nothing else comes close
- 🏆 **Sub-agent spawning** — Background workers with session isolation
- Voice (ElevenLabs TTS/STT), Browser automation, Device pairing

**For CoWork-OS**: TheiaOS solves a **different problem** (messaging gateway, not orchestration). However, its **plugin SDK architecture** is exemplary — the pattern of skills, tools, hooks, and channels could inform CoWork-OS's extension system. The sub-agent spawning mechanism is also relevant.

**Verdict**: **Extract patterns, don't fork** — wrong domain for orchestrator, but has the best extensibility model.

---

### 2️⃣ Lattice Orchestrator (v1.2.1) — "The Session Dashboard"

**What it is**: Dashboard for orchestrating Claude Code sessions with real-time streaming, AI-powered insights, and session persistence.

**Architecture**:
```
Express Server → PTY Session Manager → Claude/Codex Process Managers
             → Insights Engine (Anthropic-powered)
             → SQLite Persistence
             → WebSocket Streaming
             → React Dashboard (Vite)
```

**Key Structures**:
- `dist/services/process/` — claude-process-manager, codex-process-manager, codex-unified-manager, process-lifecycle-service
- `dist/services/sessions/` — conversation-service, message-store, session-analysis, turn-capture
- `dist/services/insights/` — insight-queue, insights-coordinator, insight-patch-executor
- `dist/services/infrastructure/` — config-service, cost-tracker, database-provider, stream-manager
- `dist/routes/` — 25+ route files (streaming, sessions, insights, threads, teams, plugins, etc.)
- `dist/web/` — Full React SPA with 50+ component prototypes

**Strongest Suites**:
- 🏆 **Real-time streaming** — PTY-based output with instant feedback, best live monitoring
- 🏆 **AI Insights** — Sees what the model is doing: assumptions, progress, uncertainties
- 🏆 **Session persistence** — Sessions survive server restarts, full conversation history
- Beautiful UI with design system prototypes, voice input (Gemini), push notifications
- Both Claude and Codex support with unified process management

**For CoWork-OS**: Lattice provides the **best monitoring/visibility layer** of all 6 codebases. Its PTY streaming, insight computation, and session management patterns are directly applicable to the "completions tracking" requirement. However, it's a **dashboard** (read-mostly), not a **control plane** (read-write orchestration).

**Verdict**: **Borrow streaming and insight patterns** — excellent monitoring layer to graft onto a control plane.

---

### 3️⃣ Attune AI (v3.9.0) — "Workflow OS for Claude"

**What it is**: AI-powered developer workflows with cost optimization, intelligent routing, Socratic discovery, and multi-agent teams.

**Architecture**:
```
CLI/MCP Entry → Socratic Discovery (guided prompts)
            → Workflow Router (17 built-in workflows)
            → Tier Router (CHEAP → CAPABLE → PREMIUM)
            → Agent Factory (14 templates, 4 strategies)
            → MCP Tool Handler (33 tools)
            → Quality Gates / Feedback Loop
```

**Key Structures**:
- `src/attune/agent_factory/` — Base, adapters (AutoGen, CrewAI, Haystack, LangChain, LangGraph, native), crews (code_review, health_check, refactoring, security_audit)
- `src/attune/mcp/handlers/` — auth, context, memory, telemetry, workflow handlers
- `src/attune/workflows/` — 17 production workflows
- `plugin/` — Claude plugin with skills, commands, agents
- `agents/` — code_inspection agent, book_production agent pipeline

**Strongest Suites**:
- 🏆 **MCP ecosystem** — 33 tools, richest MCP integration by far
- 🏆 **Cost optimization** — 3-tier auto-routing saves 34-86% on LLM costs
- 🏆 **Multi-agent teams** — 4 strategies (parallel, sequential, two-phase, delegation), 14 templates
- 🏆 **Testing** — 16,600+ tests at 84% coverage, most production-hardened
- Agent state persistence with checkpoints and recovery
- Inter-agent communication (heartbeats, signals, events, approval gates, 6 coordination patterns)
- Semantic caching (~57% hit rate on workflows)

**For CoWork-OS**: Attune has the **richest task decomposition intelligence** and the **best MCP tool ecosystem**. The agent factory pattern (with adapters for multiple frameworks) and the cost routing strategy are directly reusable. However, it's **Python-only** (no desktop shell), and oriented toward **pre-defined workflow templates** rather than dynamic, real-time orchestration of live coding sessions.

**Verdict**: **The intelligence engine to graft onto a desktop control plane** — take the MCP tools, cost routing, and agent factory patterns.

---

### 4️⃣ Taskbrew (v1.0.6) — "Multi-Agent Team Orchestrator"

**What it is**: Multi-agent AI team orchestrator coordinating Claude Code, Gemini CLI, and custom AI agents into collaborative development workflows.

**Architecture**:
```
FastAPI Server → WebSocket Dashboard
             → Orchestrator (Event Bus + Task Board + Cost Manager)
             → Agent Provider (Claude SDK + Gemini CLI)
             → Intelligence Layer (30+ modules)
             → Git Worktree Manager
```

**Key Structures**:
- `orchestrator/` — task_board.py (CRUD + dependencies), event_bus.py, cost_manager.py, artifact_store.py, notification_service.py, webhook_manager.py
- `agents/` — agent_loop.py, auto_scaler.py, instance_manager.py, provider_base.py, roles.py, gemini_cli.py
- `intelligence/` — 30+ modules: planning, code_reasoning, knowledge_graph, verification, coordination, escalation, memory, quality, security_intel, specialization, etc.
- `dashboard/routers/` — agents, analytics, collaboration, costs, intelligence, pipelines, search, tasks, usage, ws
- `tools/` — git_tools, intelligence_tools, task_tools, worktree_manager

**Strongest Suites**:
- 🏆 **Intelligence layer** — Most comprehensive analytical capabilities (30+ intelligence modules)
- 🏆 **Task board** — Full CRUD with dependency management, priority ordering, role-based prefix routing
- Dual agent support (Claude SDK + Gemini CLI)
- Auto-scaling and instance management
- Knowledge graph, code reasoning, security intelligence

**For CoWork-OS**: Taskbrew is the most **compact and focused** orchestrator. The intelligence layer (planning, code reasoning, knowledge management, verification) is sophisticated relative to its size. The task board's dependency management pattern with role-based prefixes directly maps to the sub-agent assignment requirement. However, it's the **smallest codebase** (30K LOC) and lacks desktop/UI maturity.

**Verdict**: **Good patterns for task board + intelligence layer** — compact, well-structured, borrow the task dependency and intelligence modules.

---

### 5️⃣ ZERG — "Zero-Effort Rapid Growth"

**What it is**: Parallel Claude Code execution system — coordinates multiple Claude Code instances with git worktree isolation, spec-driven execution, and per-worker context engineering.

**Architecture**:
```
/zerg:init → Auto-detect stack → Fetch security rules
/zerg:plan → Capture requirements → Generate spec
/zerg:design → Architecture → Task graph with levels
/zerg:rush → Orchestrator → Worker Fleet (5-10 Claude instances)
          → Git Worktrees (isolated per worker)
          → Quality Gates (per-level)
          → Merge (level-by-level)
```

**Key Structures**:
- `orchestrator.py` — Central coordination: OrchestratorState (IDLE→RUNNING→COMPLETE), WorkerInfo, LevelResult, worker fleet management, task queue
- `rush.py` — Task graph execution with worker count, dry-run, resume
- `task_graph.py` — Level-based task ordering with dependencies
- `spawn.py` — Worker process spawning into git worktrees
- `state.py` — Persistent execution state with checkpoints
- `session.py` — Worker session management
- `container.py` / `devcontainer.py` — Docker container generation
- `security.py` — Auto-fetched OWASP/language-specific rules
- `template_engine.py` — Context template generation per worker
- `quality_tools.py` — Quality gate enforcement

**Strongest Suites**:
- 🏆 **Parallel safety** — File ownership exclusivity prevents merge conflicts (unique!)
- 🏆 **Context engineering** — Per-worker context budgets, core/reference splitting (30%/70%), extension-filtered security rules
- 🏆 **Git worktree isolation** — Each worker gets its own worktree, level-by-level merge
- 🏆 **Spec-driven execution** — Workers read specs, not conversation history (solves context rot)
- Auto stack detection + security rules auto-fetch from TikiTribe
- Dev container generation with MCP configs baked in
- State machine orchestrator with clean lifecycle

**For CoWork-OS**: ZERG solves the **hardest technical problem** in multi-agent coding: **preventing agents from stepping on each other**. The file ownership exclusivity, worktree isolation, and per-worker context engineering are the most sophisticated solutions of all 6 codebases. No UI layer exists — it's CLI/spec-only. But its core execution patterns are the gold standard for the "agent spawning and coordination" layer.

**Verdict**: **The execution engine gold standard** — extract worktree isolation, file ownership, context engineering patterns.

---

### 6️⃣ Bosun — "Production-Grade Control Plane"

**What it is**: Control plane for autonomous software engineering — plans and routes work across executors, automates PR lifecycles, visual workflow builder, desktop app.

**Architecture**:
```
Desktop (Electron) / Web / Telegram Mini App
    → Workflow Engine (DAG-based, JSON definitions)
    → VE Orchestrator (Kanban Runtime + Shared State)
    → Agent Pool + Supervisor
    → Multi-Executor Router (Claude/Codex/Copilot/OpenCode)
    → Task Executor (with orphan recovery + commit)
    → PR Lifecycle (auto-label, auto-merge, review gates)
    → Notification Layer (Telegram/WhatsApp)
```

**Key Structures**:
- `workflow-engine.mjs` — Full DAG engine with: trigger/condition/action/validation/transform/loop node types, back-edges for convergence loops, JSON-definable, iteration limits
- `ve-orchestrator.mjs` — VeKanbanRuntime, shared state management, stale sweep, retry logic
- `task-executor.mjs` — Task execution with orphan recovery and commit handling
- `agent-pool.mjs` — Agent pool management
- `agent-supervisor.mjs` — Agent supervision and monitoring
- `conflict-resolver.mjs` — Merge conflict resolution
- `anomaly-detector.mjs` — Anomaly detection in agent behavior
- `workflow-templates/` — 10 template categories (agents, CI/CD, GitHub, planning, reliability, research, security, task-batch, task-lifecycle)
- `ui/` — Full MUI-based dashboard with kanban board, chat view, diff viewer, command palette, agent selector, session list
- `desktop/` — Electron launcher with Windows/Linux/macOS support

**Key Files (337 .mjs files total)**:
- Agent management: `agent-pool`, `agent-supervisor`, `agent-hook-bridge`, `agent-prompts`, `agent-sdk`, `agent-work-analyzer`
- Workflow: `workflow-engine`, `workflow-nodes`, `workflow-templates`, `workflow-migration`
- Shells: `claude-shell`, `codex-shell`, `copilot-shell`
- Intelligence: `context-indexer`, `context-cache`, `context-shredding-config`
- Tools: `agent-custom-tools`, `agent-tool-config`, `bosun-skills`

**Strongest Suites**:
- 🏆 **Desktop app** — Working Electron app, only codebase with native Windows support
- 🏆 **DAG Workflow Engine** — Most sophisticated workflow system: JSON-definable, visual builder, back-edges, convergence loops, node types (trigger/condition/action/validation/transform/loop)
- 🏆 **Multi-executor routing** — Routes across Codex, Copilot, Claude, OpenCode with weighted distribution, failover
- 🏆 **Visual workflow builder UI** — MUI components, kanban board, command palette
- 🏆 **PR lifecycle automation** — Auto-label, auto-merge, review gates
- Agent supervisor + anomaly detector
- Conflict resolver for merge conflicts
- Shared state management with stale sweep and retry
- 10 workflow template categories

**For CoWork-OS**: Bosun is architecturally the **closest match** to the CoWork-OS vision. It already has the desktop shell, the DAG-based temporal management, the multi-executor routing, the visual workflow builder, and the agent supervision layer. Its workflow engine supports the exact patterns needed: decompose (planning templates) → assign (agent pool routing) → execute (shells per executor) → track (kanban runtime) → merge (PR lifecycle).

**Verdict**: ⭐ **PRIMARY RECOMMENDATION as foundation** — has the most expensive-to-build pieces already working.

---

## 🏆 Final Ranking for CoWork-OS

| Rank | Codebase | Score | Role in CoWork-OS |
|---|---|---|---|
| 🥇 **#1** | **Bosun** | 106/150 | **Foundation** — Desktop shell + DAG engine + multi-executor + UI |
| 🥈 **#2** | **Attune AI** | 92/150 | **Intelligence Graft** — MCP tools + cost routing + agent factory |
| 🥉 **#3** | **ZERG** | 74/150 | **Execution Engine Graft** — Worktree isolation + context engineering |
| **#4** | **Taskbrew** | 70/150 | **Task Intelligence Graft** — Task board + intelligence modules |
| **#5** | **Lattice** | 69/150 | **Streaming/Monitoring Graft** — PTY streaming + real-time insights |
| **#6** | **TheiaOS** | 63/150 | **Extension Model Reference** — Plugin SDK architecture patterns |

---

## 🔧 Recommended CoWork-OS Architecture (Composite)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CoWork-OS Desktop (from Bosun)                │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐  │
│  │ Visual       │ │ Kanban Board │ │ Real-time Streaming    │  │
│  │ Workflow     │ │ (Bosun)      │ │ (Lattice patterns)     │  │
│  │ Builder      │ │              │ │                        │  │
│  │ (Bosun)      │ │              │ │                        │  │
│  └──────┬───────┘ └──────┬───────┘ └────────────┬───────────┘  │
│         │                │                       │              │
│  ┌──────┴────────────────┴───────────────────────┴───────────┐  │
│  │              DAG Workflow Engine (Bosun)                    │  │
│  │   temporal ordering · back-edges · convergence loops        │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
│                            │                                     │
│  ┌─────────────────────────┴─────────────────────────────────┐  │
│  │           Task Decomposition Layer                         │  │
│  │   Attune Socratic Discovery + Taskbrew Intelligence        │  │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐   │  │
│  │   │ Planning │ │ Code     │ │ Knowledge│ │ Cost      │   │  │
│  │   │ Engine   │ │ Reasoning│ │ Graph    │ │ Router    │   │  │
│  │   └──────────┘ └──────────┘ └──────────┘ └───────────┘   │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
│                            │                                     │
│  ┌─────────────────────────┴─────────────────────────────────┐  │
│  │           Agent Pool + Multi-Executor Router (Bosun)       │  │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐   │  │
│  │   │ Claude   │ │ Codex    │ │ Copilot  │ │ OpenCode  │   │  │
│  │   │ Shell    │ │ Shell    │ │ Shell    │ │ Shell     │   │  │
│  │   └──────────┘ └──────────┘ └──────────┘ └───────────┘   │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
│                            │                                     │
│  ┌─────────────────────────┴─────────────────────────────────┐  │
│  │      Execution Safety Layer (from ZERG)                    │  │
│  │   ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐   │  │
│  │   │ Git Worktree │ │ File         │ │ Per-Worker       │   │  │
│  │   │ Isolation    │ │ Ownership    │ │ Context          │   │  │
│  │   │              │ │ Exclusivity  │ │ Engineering      │   │  │
│  │   └──────────────┘ └──────────────┘ └─────────────────┘   │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
│                            │                                     │
│  ┌─────────────────────────┴─────────────────────────────────┐  │
│  │              MCP Tools + Skills (from Attune/TheiaOS)      │  │
│  │   33 MCP tools · Plugin SDK · Skill registry               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💡 What Each Codebase Should Be Used For

| Codebase | Take From It | Don't Take |
|---|---|---|
| **Bosun** | Desktop shell, DAG engine, multi-executor routing, workflow builder UI, agent pool, kanban runtime, PR automation | Telegram-centric notification model (replace with native desktop notifications) |
| **Attune** | MCP tool handlers (33), cost routing strategy, agent factory pattern, Socratic discovery UX, quality gates | Python runtime (translate patterns to TypeScript), workflow templates (too rigid) |
| **ZERG** | Worktree isolation, file ownership exclusivity, per-worker context engineering, spec-driven execution, quality gates | CLI-only interface, monolithic Python architecture |
| **Taskbrew** | Task board CRUD with dependency tracking, intelligence modules (planning, code reasoning, knowledge graph), auto-scaler | Dashboard (too basic), overall scale (too small for production) |
| **Lattice** | PTY-based streaming, session persistence, AI insight computation, conversation caching, cost tracking | Architecture (monitoring-only, not control plane) |
| **TheiaOS** | Plugin SDK architecture, skill system patterns, sub-agent spawning mechanism, channel integration patterns | Messaging gateway (wrong problem domain entirely) |

---

## 📈 Implementation Priority for CoWork-OS

### Phase 1: Foundation (Week 1-2)
1. Fork Bosun → strip Telegram-specific code → enhance Electron desktop shell
2. Validate workflow engine DAG capabilities
3. Validate multi-executor routing with local Claude + Codex

### Phase 2: Execution Safety (Week 3-4)
4. Port ZERG's git worktree isolation pattern into Bosun's task executor
5. Implement file ownership exclusivity map
6. Add per-agent context engineering (core/reference splitting)

### Phase 3: Intelligence (Week 5-6)
7. Integrate Attune's 3-tier cost routing into agent pool
8. Port Taskbrew's task decomposition + dependency management
9. Add planning intelligence (from Taskbrew's intelligence layer)

### Phase 4: Monitoring (Week 7-8)
10. Graft Lattice's PTY streaming into desktop UI panels
11. Add real-time completion tracking with quality metrics
12. Implement AI insight computation for each active session

### Phase 5: Tools (Week 9-10)
13. Build MCP tool registry (from Attune's 33-tool patterns)
14. Add skill/plugin system (from TheiaOS SDK patterns)
15. Implement tool-based sub-agent routing

---

## ⚡ The Bottom Line

**Bosun is the most effective foundation** for CoWork-OS because it's the **only codebase that already solves the desktop + orchestration intersection**. Building a quality Electron app with a DAG workflow engine and multi-executor routing from scratch is 3-6 months of work. Bosun gives you that for free.

The **execution safety layer** (preventing agents from conflicting) should come from **ZERG** — its worktree isolation and file ownership patterns are the most sophisticated solution.

The **intelligence layer** (what tasks to create, which agent to assign, what it'll cost) should come from **Attune** and **Taskbrew** — they have the deepest thinking about task decomposition and cost optimization.

The **monitoring layer** (seeing what agents are doing in real-time) should come from **Lattice** — its PTY streaming and insight engine are the most polished.

The **extensibility model** should reference **TheiaOS** — its plugin SDK with skills, tools, hooks, and channels is the most mature extension architecture.

**No single codebase is perfect. The winning strategy is a composite.**

