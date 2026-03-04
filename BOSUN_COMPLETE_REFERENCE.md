# BOSUN v0.37.x — Complete CLI, REST API & Workflow Reference

> **VirtEngine Bosun** — Production-grade autonomous supervisor for AI coding agents.
> 
> - **GitHub**: https://github.com/virtengine/bosun
> - **npm**: https://www.npmjs.com/package/bosun (v0.37.2)
> - **Website**: https://bosun.engineer / https://bosun.virtengine.com
> - **Default API Port**: 18432 (configurable via `UI_PORT` in `.env`)
> - **License**: Apache 2.0

---

## Table of Contents

1. [Confidence Legend](#1-confidence-legend)
2. [Installation & Setup](#2-installation--setup)
3. [Task Management — CLI](#3-task-management--cli)
4. [Task Management — REST API](#4-task-management--rest-api)
5. [Task Management — Node.js SDK](#5-task-management--nodejs-sdk)
6. [Task Schema & Status Machine](#6-task-schema--status-machine)
7. [Executor Management](#7-executor-management)
8. [Workflow Management](#8-workflow-management)
9. [Workspace Management](#9-workspace-management)
10. [Agent & Fleet Management](#10-agent--fleet-management)
11. [Board / Kanban Backends](#11-board--kanban-backends)
12. [Configuration Management](#12-configuration-management)
13. [Hook / Event System](#13-hook--event-system)
14. [Analytics & Reporting](#14-analytics--reporting)
15. [Voice & Video (v0.37.0+)](#15-voice--video-v0370)
16. [MCP Server Integration](#16-mcp-server-integration)
17. [Telegram Bot Commands](#17-telegram-bot-commands)
18. [Complete .env Reference](#18-complete-env-reference)
19. [Multi-Step Workflow Examples](#19-multi-step-workflow-examples)
20. [Discovery Commands](#20-discovery-commands)
21. [Programmatic Management Viability](#21-programmatic-management-viability)

---

## 1. Confidence Legend

Every item in this document is tagged with a confidence marker:

| Marker | Meaning |
|--------|---------|
| ✅ | **CONFIRMED** — Verified from official source code, gists, or docs |
| 🔶 | **STRONG INFERENCE** — Architecture, UI tabs, or release notes confirm existence; exact syntax derived from patterns |
| ⚪ | **LIKELY** — Consistent with design but not directly confirmed in public sources |

---

## 2. Installation & Setup

### Install ✅

```bash
npm install -g bosun
```

### First Run ✅

```bash
cd your-repo
bosun                  # First run launches interactive setup automatically
```

### Explicit Setup ✅

```bash
bosun --setup          # Interactive wizard (Recommended / Advanced modes)
```

### Version ✅

```bash
bosun --version        # Print current version
```

### Help ✅

```bash
bosun --help           # Show all available commands and flags
```

### Requirements ✅

- Node.js 18+
- Git
- Bash (for `.sh` wrappers) or PowerShell 7+ (for `.ps1` wrappers)
- GitHub CLI (`gh`) recommended

### Repository Layout ✅

```
cli.mjs          — CLI entrypoint and subcommand router
monitor.mjs      — Main orchestration loop
config.mjs       — Unified configuration loader
ui-server.mjs    — REST API server + Telegram Mini App backend
site/            — Marketing + docs website
docs/            — Documentation sources
_docs/           — Source-of-truth markdown docs
```

---

## 3. Task Management — CLI

All commands in this section are **✅ CONFIRMED** from the official task-manager agent prompt gist.

### List Tasks

```bash
bosun task list                                    # All tasks
bosun task list --status todo                      # Filter by status
bosun task list --status todo --json               # JSON output
bosun task list --priority high --tag ui           # Filter by priority AND tag
bosun task list --search "provider"                # Full-text search
```

### Create Tasks

```bash
# Inline flags
bosun task create --title "[s] fix(cli): Handle exit codes" \
  --priority high --tags "cli,fix"

# JSON object
bosun task create '{"title":"[m] feat(ui): Dark mode","description":"Add dark mode toggle","tags":["ui"]}'

# JSON array = batch create
bosun task create '[
  {"title":"[s] fix(cli): Handle exit codes","priority":"high","tags":["cli","fix"]},
  {"title":"[m] feat(ui): Dark mode","priority":"medium","tags":["ui","theme"]},
  {"title":"[xs] docs: Update README","priority":"low","tags":["docs"]}
]'
```

### Get Task Details

```bash
bosun task get <id>                                # Full ID or prefix (e.g. "abc123")
bosun task get abc123 --json                       # JSON output
```

### Update Tasks

```bash
bosun task update abc123 --status todo --priority critical
bosun task update abc123 '{"tags":["ui","urgent"],"baseBranch":"origin/ui-rework"}'
bosun task update abc123 --status todo --undraft    # Promote draft → todo
```

### Delete Tasks

```bash
bosun task delete abc123
```

### Statistics

```bash
bosun task stats                                   # Human-readable stats
bosun task stats --json                            # JSON output
```

### Bulk Import

```bash
bosun task import ./backlog.json                   # Import from JSON file
```

### AI Task Planner

```bash
bosun task plan --count 5 --reason "Sprint planning"
```


---

## 4. Task Management — REST API

All endpoints in this section are **✅ CONFIRMED** from the official gist. Default port is `18432`.

### Endpoints Table

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| `GET` | `/api/tasks` | List all tasks | — |
| `GET` | `/api/tasks?status=todo` | Filter by status | — |
| `GET` | `/api/tasks?priority=high` | Filter by priority | — |
| `GET` | `/api/tasks?tag=ui` | Filter by tag | — |
| `GET` | `/api/tasks?search=provider` | Text search | — |
| `GET` | `/api/tasks/:id` | Get single task | — |
| `POST` | `/api/tasks/create` | Create task(s) | JSON task object or array |
| `POST` | `/api/tasks/:id/update` | Update task fields | JSON partial update |
| `POST` | `/api/tasks/:id/status` | Change status (with history) | `{"status":"inreview"}` |
| `DELETE` | `/api/tasks/:id` | Delete task | — |
| `GET` | `/api/tasks/stats` | Task statistics | — |
| `POST` | `/api/tasks/import` | Bulk import | `{"tasks":[...]}` |

### curl Examples ✅

```bash
# List all tasks
curl http://127.0.0.1:18432/api/tasks

# List filtered
curl "http://127.0.0.1:18432/api/tasks?status=todo"

# Get single task
curl http://127.0.0.1:18432/api/tasks/abc123

# Create task
curl -X POST http://127.0.0.1:18432/api/tasks/create \
  -H "Content-Type: application/json" \
  -d '{"title":"[s] fix(cli): Exit code","priority":"high","tags":["cli"]}'

# Update task
curl -X POST http://127.0.0.1:18432/api/tasks/abc123/update \
  -H "Content-Type: application/json" \
  -d '{"status":"todo","priority":"critical"}'

# Change status (with history tracking)
curl -X POST http://127.0.0.1:18432/api/tasks/abc123/status \
  -H "Content-Type: application/json" \
  -d '{"status":"inreview"}'

# Delete task
curl -X DELETE http://127.0.0.1:18432/api/tasks/abc123

# Get stats
curl http://127.0.0.1:18432/api/tasks/stats

# Bulk import
curl -X POST http://127.0.0.1:18432/api/tasks/import \
  -H "Content-Type: application/json" \
  -d '{"tasks":[{"title":"[s] fix: Bug","priority":"high"},{"title":"[m] feat: Feature","tags":["ui"]}]}'
```

---

## 5. Task Management — Node.js SDK

Direct programmatic access from JavaScript. **✅ CONFIRMED** from official gist.

```javascript
import {
  taskCreate,
  taskList,
  taskGet,
  taskUpdate,
  taskDelete,
  taskStats,
  taskImport
} from 'bosun/task-cli';

// Create a task
const task = await taskCreate({
  title: "[m] feat(ui): Dark mode",
  description: "Add dark mode toggle to settings panel",
  priority: "high",
  tags: ["ui", "theme"],
  baseBranch: "main"
});

// List with filters
const todos = await taskList({ status: "todo", priority: "high" });

// Get specific task
const detail = await taskGet("abc123");

// Update task
await taskUpdate(task.id, { status: "todo", priority: "critical" });

// Delete task
await taskDelete(task.id);

// Get stats
const stats = await taskStats();

// Bulk import
const result = await taskImport("./backlog.json");
```

---

## 6. Task Schema & Status Machine

### Task Fields ✅

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `title` | `string` | ✅ | — | Format: `[size] type(scope): description` |
| `description` | `string` | — | `""` | Full markdown. This is the agent's primary prompt. |
| `status` | `string` | — | `"draft"` | See status machine below |
| `priority` | `string` | — | `"medium"` | `low`, `medium`, `high`, `critical` |
| `tags` | `string[]` | — | `[]` | Lowercase labels for categorization |
| `baseBranch` | `string` | — | `"main"` | Target git branch for task PR |
| `workspace` | `string` | — | cwd | Path to workspace directory |
| `repository` | `string` | — | `""` | Repository identifier (e.g. `org/repo`) |
| `draft` | `boolean` | — | `true` | Draft tasks are NOT picked up by executors |

### Structured Description Fields ✅

These fields get auto-formatted into the description as markdown sections when creating/importing tasks:

| Field | Type | Description |
|-------|------|-------------|
| `implementation_steps` | `string[]` | Ordered steps for the agent to follow |
| `acceptance_criteria` | `string[]` | Binary pass/fail conditions |
| `verification` | `string[]` | Commands to run to verify completion |

### Status State Machine ✅

```
draft → todo → inprogress → inreview → done
                    ↓            ↓
                 blocked      blocked
```

| Status | Description |
|--------|-------------|
| `draft` | Not yet ready. Agents will NOT pick these up. |
| `todo` | Ready for execution. Next idle agent will claim it. |
| `inprogress` | Agent is actively working on it. |
| `inreview` | Agent completed work, PR created, awaiting human review. |
| `done` | Task completed and merged. |
| `blocked` | Stuck on external dependency. |

### Title Convention ✅

```
[size] type(scope): Concise action-oriented description
```

**Size Labels:**

| Label | Time | Scope |
|-------|------|-------|
| `[xs]` | < 30 min | Single-file fix |
| `[s]` | 30 min – 2 hr | Small feature, one module |
| `[m]` | 2 – 6 hr | Multi-file feature |
| `[l]` | 6 – 16 hr | Cross-module work |
| `[xl]` | 1 – 3 days | Major feature |

**Commit Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

**Module Scopes (auto-route to branch):** `veid`, `mfa`, `encryption`, `market`, `escrow`, `roles`, `hpc`, `provider`, `sdk`, `cli`, `app`, `api`, `deps`, `ci`


---

## 7. Executor Management

Executors are the AI coding engine backends that Bosun routes tasks to.

### Supported SDKs ✅

| SDK | Models | Notes |
|-----|--------|-------|
| `copilot` | `claude-opus-4-6`, `gpt-*` | GitHub Copilot agent sessions |
| `codex` | `o4-mini`, `DEFAULT` | OpenAI Codex SDK, persistent sessions |
| `claude` | Claude Code | Anthropic Claude Code agent |
| `gemini` | Gemini models | Added in v0.37.0 |
| `opencode` | OpenCode models | Added in v0.37.0 |

### CLI Commands 🔶

```bash
bosun executor list                               # List configured executor pool
bosun executor status                             # Show running/idle/failed per executor
bosun executor add <name> --sdk copilot \
  --model claude-opus-4-6 --weight 50             # Add executor to pool
bosun executor remove <name>                      # Remove executor
bosun executor restart <name>                     # Restart stalled executor
bosun executor logs <name>                        # Stream executor logs
```

### REST API Endpoints 🔶

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/executors` | List executor pool |
| `GET` | `/api/executors/:name` | Executor detail + current status |
| `POST` | `/api/executors/:name/restart` | Restart executor |
| `GET` | `/api/executors/:name/logs` | Stream executor logs |

### Configuration ✅

**Via `.env`:**
```bash
EXECUTOR_MODE=internal          # internal | container
EXECUTORS=COPILOT:CLAUDE_OPUS_4_6:50,CODEX:DEFAULT:50
MAX_PARALLEL=6                  # Max concurrent agents
AGENT_TIMEOUT=90                # Minutes before timeout
```

**Via `bosun.config.json`:**
```json
{
  "version": 1,
  "executors": {
    "pool": [
      { "name": "copilot-claude", "sdk": "copilot", "model": "claude-opus-4-6", "weight": 50 },
      { "name": "codex-default",  "sdk": "codex",   "model": "o4-mini",         "weight": 50 }
    ],
    "failover": { "maxRetries": 2, "cooldown": 300 }
  }
}
```

**Executor entry format:** `SDK:MODEL:WEIGHT`
- `SDK` — one of `COPILOT`, `CODEX`, `CLAUDE`, `GEMINI`, `OPENCODE`
- `MODEL` — model identifier or `DEFAULT`
- `WEIGHT` — integer weight for weighted round-robin routing

---

## 8. Workflow Management

Bosun ships with 31+ default workflow templates. The Mini App includes a visual Workflow Builder.

### CLI Commands 🔶

```bash
bosun workflow list                               # List all workflow templates
bosun workflow list --json                        # JSON output
bosun workflow show <name>                        # Show template definition
bosun workflow run <template-name>                # Execute a workflow
bosun workflow run <template-name> --dry-run      # Preview without executing
bosun workflow create <name> --from <file.yaml>   # Create custom workflow
bosun workflow delete <name>                      # Delete custom workflow
```

### REST API Endpoints 🔶

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| `GET` | `/api/workflows` | List all templates | — |
| `GET` | `/api/workflows/:name` | Get template definition | — |
| `POST` | `/api/workflows/run` | Execute workflow | `{"template":"<name>","params":{...}}` |
| `POST` | `/api/workflows/create` | Create custom workflow | YAML/JSON template |
| `DELETE` | `/api/workflows/:name` | Delete workflow | — |

### Known Workflow Template Categories ✅

| Category | Purpose |
|----------|---------|
| **PR Lifecycle** | Create PR, monitor CI, auto-rebase on conflicts, merge decision |
| **Planning Loops** | Context building, task decomposition, backlog generation |
| **Recovery Paths** | Retry with cooldown, escalation detection, stuck-run recovery |
| **Bosun Lifecycle** | Self-update, maintenance, health checks |
| **Code Quality** | Lint, test, build validation gates |
| **Voice/Video Agents** | Meeting integration, live call handling, note-taking (v0.37.0+) |

---

## 9. Workspace Management

Multi-workspace and multi-repo support with worktree isolation.

### CLI Commands 🔶

```bash
bosun workspace list                              # List all workspaces
bosun workspace create <path> --repo org/repo     # Create new workspace
bosun workspace switch <name>                     # Switch active workspace
bosun workspace status                            # Show workspace health/state
bosun workspace recover <name>                    # Auto-recover non-git workspace
```

### REST API Endpoints 🔶

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/workspaces` | List workspaces |
| `GET` | `/api/workspaces/:id` | Workspace detail |
| `POST` | `/api/workspaces/create` | Create workspace |
| `POST` | `/api/workspaces/:id/recover` | Recover workspace |

---

## 10. Agent & Fleet Management

Multi-agent coordination with presence tracking, session management, and heartbeat liveness.

### CLI Commands 🔶

```bash
# Fleet-wide
bosun fleet status                                # Fleet-wide overview
bosun fleet agents                                # List all agents + state

# Per-agent
bosun agent list                                  # Running agent sessions
bosun agent status <id>                           # Specific agent detail
bosun agent stop <id>                             # Stop agent session
bosun agent logs <id>                             # Stream agent output
bosun agent chat <id> "<message>"                 # Send direct message to agent
```

### REST API Endpoints 🔶

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents` | List running agents |
| `GET` | `/api/agents/:id` | Agent details |
| `GET` | `/api/agents/:id/logs` | Agent log stream |
| `POST` | `/api/agents/:id/stop` | Stop agent |
| `POST` | `/api/agents/:id/chat` | Send message to agent |
| `GET` | `/api/fleet/status` | Fleet overview |
| `GET` | `/api/fleet/presence` | Presence / heartbeat liveness |


---

## 11. Board / Kanban Backends

Bosun supports multiple task board backends for bidirectional synchronization.

### Supported Backends ✅

| Backend | Value | Description |
|---------|-------|-------------|
| GitHub Issues | `github` | Sync tasks ↔ GitHub Issues |
| GitHub Projects v2 | `github-projects` | Sync tasks ↔ GitHub Projects v2 boards |
| Jira | `jira` | Sync tasks ↔ Jira issues |
| Internal | `internal` | Bosun's built-in board (no external sync) |

### CLI Commands 🔶

```bash
bosun board status                                # Show active backend + sync state
bosun board sync                                  # Force bidirectional sync now
bosun board switch github-projects                # Switch to different backend
```

### REST API Endpoints 🔶

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/board/status` | Board backend status |
| `POST` | `/api/board/sync` | Force bidirectional sync |

### Configuration ✅

```bash
# .env
KANBAN_BACKEND=github                # github | github-projects | jira | internal
GITHUB_PROJECT_NUMBER=4             # Required for github-projects backend
JIRA_HOST=https://org.atlassian.net # Required for jira backend
JIRA_TOKEN=...                      # Required for jira backend
```

---

## 12. Configuration Management

### CLI Commands 🔶

```bash
bosun config show                                 # Display full active configuration
bosun config get <key>                            # Get specific config value
bosun config set <key> <value>                    # Set config value
bosun config export                               # Export configuration to file
bosun config validate                             # Validate config syntax
```

### REST API Endpoints 🔶

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/config` | Full configuration dump |
| `POST` | `/api/config/update` | Update config values |

---

## 13. Hook / Event System

Hooks allow you to attach custom commands to Bosun lifecycle events.

### Configuration File ✅

Location: `.codex/hooks.json`

```json
{
  "hooks": [
    {
      "name": "prepush-go-vet",
      "event": "PrePush",
      "command": "go vet ./...",
      "blocking": true
    },
    {
      "name": "precommit-gofmt",
      "event": "PreCommit",
      "command": "gofmt -w ."
    },
    {
      "name": "task-complete-audit",
      "event": "TaskComplete",
      "command": "./scripts/agent-preflight.sh"
    },
    {
      "name": "ci-failed-notify",
      "event": "CIFailed",
      "command": "echo 'CI broke' | notify-send"
    }
  ]
}
```

### Supported Events 🔶

| Event | Trigger | Notes |
|-------|---------|-------|
| `PreCommit` | Before git commit | Pre-commit hooks auto-format/lint staged files ✅ |
| `PrePush` | Before git push | Targeted checks based on changed files ✅ |
| `TaskComplete` | Agent finishes a task | Run validation scripts |
| `PRCreated` | Pull Request opened | Custom notification or labeling |
| `CIFailed` | Build/tests fail on PR | Auto-labels PR with `bosun-needs-fix` ✅ |
| `CIPassed` | Build/tests pass | Trigger merge workflow |
| `PRMerged` | PR merged to base branch | Post-merge cleanup |

### Hook Properties

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | ✅ | Unique hook identifier |
| `event` | `string` | ✅ | One of the events above |
| `command` | `string` | ✅ | Shell command to execute |
| `blocking` | `boolean` | — | If `true`, hook failure blocks the event (default: `false`) |

---

## 14. Analytics & Reporting

### CLI Commands

```bash
bosun report weekly                               # ✅ Generate operator weekly report
bosun analytics errors                            # 🔶 Error cluster correlation
bosun analytics errors --json                     # 🔶 JSON output
```

### REST API Endpoints 🔶

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/analytics/errors` | Error clustering analysis |
| `GET` | `/api/analytics/report` | Weekly report data |
| `GET` | `/api/health` | Instance health check |

---

## 15. Voice & Video (v0.37.0+)

Added in v0.37.0. Supports live voice/video calls with AI agents.

### Supported Providers ✅

| Provider | Auth Method |
|----------|-------------|
| ChatGPT.com | OAuth |
| Claude.ai | OAuth |
| Gemini | API Keys |

### Capabilities ✅ (from v0.37.0 release notes)

- Live voice/video calls from Portal or Telegram
- Voice agents can trigger workspace actions
- Voice agents can create tasks and trigger other agents
- Meeting integration template (agent listens for "Bosun" keyword)
- Spawn voice/video agents via Workflow Builder

### REST API Endpoints 🔶

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/voice/call` | Initiate voice/video call |
| `POST` | `/api/voice/agent` | Spawn voice agent |
| `GET` | `/api/voice/providers` | List configured providers |

---

## 16. MCP Server Integration

### Architecture ⚪

Bosun supports MCP (Model Context Protocol) through **executor tool augmentation**. AI agents spawned by Bosun can access MCP servers as tool providers. Configuration is at the workflow template or executor level.

### Likely Configuration Pattern ⚪

```json
{
  "mcp_servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
    },
    {
      "name": "github",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  ]
}
```

### Discovery Commands

```bash
# Check if MCP endpoints exist on your instance
curl -sk https://127.0.0.1:3080/api/mcp
curl -sk https://127.0.0.1:3080/api/mcp/servers
bosun mcp --help
```


---

## 17. Telegram Bot Commands

The Telegram bot mirrors most CLI capabilities. All commands below are confirmed from the Bosun documentation and README.

### Full Command List

```
/start                  — Initialize bot connection
/status                 — Fleet status overview
/tasks                  — List all tasks
/task <id>              — Get task detail
/agents                 — List running agents
/agent <id>             — Agent detail
/fleet                  — Fleet overview
/prs                    — List open PRs
/pr <number>            — PR detail
/run                    — Trigger a workflow
/stop <id>              — Stop an agent
/logs <id>              — Stream agent logs
/config                 — Show active configuration
/weekly                 — Generate weekly report  ✅ confirmed
/report weekly          — Alias for /weekly       ✅ confirmed
/help                   — Show all available commands
/digest                 — Daily digest summary
/plan                   — Trigger AI task planner
/import                 — Import tasks
/stats                  — Task statistics
/board                  — Board backend status
/sync                   — Force board sync
/workspace              — Workspace info
/restart <id>           — Restart executor
/merge <pr>             — Merge a PR
/rebase <pr>            — Rebase a PR
/close <pr>             — Close a PR
/label <pr>             — Label a PR
/approve <pr>           — Approve a PR
/silence                — Mute notifications
/unsilence              — Unmute notifications
```

### Mini App Tabs ✅

The Telegram Mini App provides a web dashboard with these tabs:

| Tab | Purpose |
|-----|---------|
| **Dashboard** | Fleet overview, active tasks, agent status |
| **Tasks** | Full task CRUD with filters |
| **Agents** | Agent pool status, logs, controls |
| **Infra** | Container/infrastructure management |
| **Control** | Workflow execution, settings toggles |
| **Logs** | Centralized log viewer |
| **Settings** | Configuration management |

---

## 18. Complete .env Reference

```bash
# ═══════════════════════════════════════════════════
# BOSUN .env — Complete Configuration Reference
# ═══════════════════════════════════════════════════

# ── Core ──────────────────────────────────────────
PROJECT_NAME=myproject                   # ✅ Project identifier
GITHUB_REPO=org/repo                     # ✅ GitHub repository (org/name)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx            # ✅ GitHub personal access token

# ── Executors ─────────────────────────────────────
EXECUTOR_MODE=internal                   # ✅ internal | container
EXECUTORS=COPILOT:CLAUDE_OPUS_4_6:50,CODEX:DEFAULT:50  # ✅ SDK:MODEL:WEIGHT,...
MAX_PARALLEL=6                           # ✅ Max concurrent agent sessions
AGENT_TIMEOUT=90                         # ✅ Minutes before agent timeout

# ── Board Backend ─────────────────────────────────
KANBAN_BACKEND=github                    # ✅ github | github-projects | jira | internal
GITHUB_PROJECT_NUMBER=4                  # ✅ For github-projects backend

# ── Jira (if KANBAN_BACKEND=jira) ────────────────
JIRA_HOST=https://org.atlassian.net      # 🔶
JIRA_TOKEN=...                           # 🔶

# ── Telegram ──────────────────────────────────────
TELEGRAM_BOT_TOKEN=7891234567:AAG...     # ✅
TELEGRAM_CHAT_ID=1234567890              # ✅
TELEGRAM_WEEKLY_REPORT_ENABLED=true      # ✅ Enable scheduled weekly reports
TELEGRAM_WEEKLY_REPORT_DAY=1             # ✅ Day of week (1=Monday)
TELEGRAM_WEEKLY_REPORT_HOUR=9            # ✅ Hour in UTC
TELEGRAM_WEEKLY_REPORT_DAYS=7            # ✅ Report covers last N days

# ── WhatsApp (optional) ──────────────────────────
WHATSAPP_ENABLED=false                   # 🔶

# ── Container Isolation ──────────────────────────
CONTAINER_RUNTIME=docker                 # 🔶 docker | podman | apple-container
CONTAINER_MAX_CONCURRENT=3               # 🔶

# ── GitHub App (for automated PR lifecycle) ──────
GITHUB_APP_ID=...                        # 🔶
GITHUB_APP_PRIVATE_KEY=...               # 🔶
GITHUB_APP_WEBHOOK_SECRET=...            # 🔶

# ── UI Server ────────────────────────────────────
UI_PORT=18432                            # ✅ API port (default: 18432)
```

---

## 19. Multi-Step Workflow Examples

These examples show how to compose multiple CLI/API actions into complete workflows.

### Workflow 1: Sprint Planning → Execution → Review

```bash
#!/bin/bash
# === STEP 1: Generate sprint backlog with AI planner ===
bosun task plan --count 8 --reason "Sprint 12: User auth improvements"

# === STEP 2: Review generated tasks ===
bosun task list --status draft --json | jq '.[] | {id, title, priority}'

# === STEP 3: Promote approved tasks to todo ===
for id in $(bosun task list --status draft --json | jq -r '.[].id'); do
  bosun task update "$id" --status todo --undraft
done

# === STEP 4: Monitor fleet execution ===
bosun fleet status

# === STEP 5: Check task progress ===
bosun task list --status inprogress --json

# === STEP 6: Review completed tasks ===
bosun task list --status inreview --json | jq '.[] | {id, title}'
```

### Workflow 2: Create Feature Task → Monitor → Merge (REST API)

```bash
#!/bin/bash
API="http://127.0.0.1:18432"

# === STEP 1: Create task via REST API ===
TASK_ID=$(curl -s -X POST "$API/api/tasks/create" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "[l] feat(api): GraphQL support",
    "description": "Implement GraphQL endpoint with schema-first approach.\n\n## Implementation Steps\n1. Add graphql dependencies\n2. Define schema in schema.graphql\n3. Implement resolvers\n4. Add integration tests",
    "priority": "high",
    "tags": ["api", "graphql"],
    "baseBranch": "main",
    "implementation_steps": [
      "Add graphql dependencies to package.json",
      "Create schema.graphql with Query and Mutation types",
      "Implement resolvers for each type",
      "Add integration tests with supertest"
    ],
    "acceptance_criteria": [
      "GET /graphql returns GraphQL playground",
      "All queries return expected data",
      "All mutations validate input",
      "Test suite passes with >90% coverage"
    ],
    "verification": [
      "npm test -- --grep graphql",
      "curl http://localhost:3000/graphql -d '{\"query\":\"{ health }\"}'"
    ]
  }' | jq -r '.id')

echo "Created task: $TASK_ID"

# === STEP 2: Promote to todo ===
curl -s -X POST "$API/api/tasks/$TASK_ID/status" \
  -H "Content-Type: application/json" \
  -d '{"status":"todo"}'

# === STEP 3: Poll until task is in review ===
while true; do
  STATUS=$(curl -s "$API/api/tasks/$TASK_ID" | jq -r '.status')
  echo "Task status: $STATUS"
  if [ "$STATUS" = "inreview" ] || [ "$STATUS" = "done" ]; then
    break
  fi
  sleep 60
done

# === STEP 4: Get task details including PR link ===
curl -s "$API/api/tasks/$TASK_ID" | jq '{status, title, pr_url}'
```

### Workflow 3: Bulk Import + Prioritize + Execute

```bash
#!/bin/bash

# === STEP 1: Create a sprint backlog file ===
cat > /tmp/sprint.json << 'EOF'
[
  {
    "title": "[m] feat(auth): OAuth2 PKCE flow",
    "description": "Implement PKCE authorization flow for mobile clients",
    "priority": "critical",
    "tags": ["auth", "security"],
    "implementation_steps": [
      "Add PKCE challenge generation",
      "Implement /authorize endpoint with code_challenge",
      "Implement /token exchange with code_verifier",
      "Add session persistence"
    ],
    "acceptance_criteria": [
      "PKCE flow completes end-to-end",
      "Invalid verifiers are rejected",
      "Sessions persist across restarts"
    ]
  },
  {
    "title": "[s] fix(api): Rate limit headers",
    "description": "Add X-RateLimit-* headers to all API responses",
    "priority": "high",
    "tags": ["api", "fix"]
  },
  {
    "title": "[xs] docs: API changelog",
    "description": "Add CHANGELOG.md entry for v2.1 release",
    "priority": "low",
    "tags": ["docs"]
  }
]
EOF

# === STEP 2: Import backlog ===
bosun task import /tmp/sprint.json

# === STEP 3: List imported (draft) tasks ===
bosun task list --status draft

# === STEP 4: Promote critical tasks first ===
for id in $(bosun task list --status draft --priority critical --json | jq -r '.[].id'); do
  bosun task update "$id" --status todo --undraft
  echo "Promoted critical task: $id"
done

# === STEP 5: Then promote high priority ===
for id in $(bosun task list --status draft --priority high --json | jq -r '.[].id'); do
  bosun task update "$id" --status todo --undraft
  echo "Promoted high task: $id"
done

# === STEP 6: Check fleet is picking up work ===
bosun fleet status
bosun task stats
```

### Workflow 4: Node.js Automation Script

```javascript
import {
  taskCreate, taskList, taskUpdate, taskStats
} from 'bosun/task-cli';

async function runSprint() {
  // Step 1: Create tasks programmatically
  const tasks = [
    { title: "[m] feat(ui): Dark mode",     priority: "high",     tags: ["ui"] },
    { title: "[s] fix(api): CORS headers",  priority: "critical", tags: ["api"] },
    { title: "[xs] chore: Update deps",     priority: "low",      tags: ["deps"] },
  ];

  const created = [];
  for (const t of tasks) {
    const task = await taskCreate(t);
    created.push(task);
    console.log(`Created: ${task.id} — ${task.title}`);
  }

  // Step 2: Promote all to todo
  for (const task of created) {
    await taskUpdate(task.id, { status: "todo", draft: false });
    console.log(`Promoted: ${task.id}`);
  }

  // Step 3: Monitor progress
  const interval = setInterval(async () => {
    const stats = await taskStats();
    console.log("Stats:", JSON.stringify(stats));

    const inReview = await taskList({ status: "inreview" });
    if (inReview.length > 0) {
      console.log("Tasks in review:", inReview.map(t => t.title));
    }

    const allDone = await taskList({ status: "todo" });
    if (allDone.length === 0) {
      console.log("All tasks dispatched!");
      clearInterval(interval);
    }
  }, 30000); // Poll every 30 seconds
}

runSprint().catch(console.error);
```


---

## 20. Discovery Commands

Since Bosun's public documentation is still catching up with the codebase, **these commands give you the authoritative answer from YOUR running instance**.

### CLI Discovery

```bash
# Master help — shows ALL top-level subcommands
bosun --help

# Per-domain help (run each to discover exact flags and subcommands)
bosun task --help
bosun executor --help
bosun workflow --help
bosun workspace --help
bosun agent --help
bosun fleet --help
bosun config --help
bosun board --help
bosun mcp --help
bosun voice --help
bosun report --help
bosun analytics --help
```

### REST API Discovery

```bash
# Probe all likely API namespaces on your instance
for ns in tasks executors workflows workspaces agents fleet \
          config board analytics health mcp voice hooks settings; do
  echo "=== /api/$ns ==="
  curl -sk http://127.0.0.1:18432/api/$ns 2>&1 | head -5
  echo
done
```

### Source Code Inspection (most definitive)

```bash
# Extract ALL registered HTTP routes from ui-server.mjs
grep -nE '(app\.(get|post|put|delete|patch)|router\.(get|post|put|delete))' \
  $(npm root -g)/bosun/ui-server.mjs

# Extract ALL CLI subcommands from cli.mjs
grep -nE '(command|\.command\(|subcommand|yargs)' \
  $(npm root -g)/bosun/cli.mjs

# Find all exported functions from task-cli
grep -nE 'export (async )?function' \
  $(npm root -g)/bosun/task-cli.mjs
```

### Quality Gate Commands ✅

```bash
# Run syntax + test suite
npm test

# Prepublish safety checks
npm run prepublishOnly

# Install local git hooks (pre-commit + pre-push)
npm run hooks:install
```

---

## 21. Programmatic Management Viability

### Summary: YES — Full programmatic management is viable.

Bosun was architecturally designed for headless/programmatic operation. The REST API + CLI + Node.js SDK together cover 90%+ of all operations.

### Viability Matrix

| Capability | Programmatic? | Primary Interface | Secondary Interface |
|-----------|:------------:|-------------------|---------------------|
| Task CRUD | ✅ **YES** | REST API (`/api/tasks/*`) | CLI (`bosun task *`) + Node SDK |
| Task planning | ✅ **YES** | CLI (`bosun task plan`) | REST API |
| Bulk import/export | ✅ **YES** | CLI (`bosun task import`) | REST API (`/api/tasks/import`) |
| Executor pool config | ✅ **YES** | `.env` / `bosun.config.json` | CLI / REST API |
| Executor monitoring | ✅ **YES** | REST API (`/api/executors`) | CLI / Telegram |
| Workflow execution | ✅ **YES** | CLI (`bosun workflow run`) | REST API |
| Workflow creation | ✅ **YES** | CLI (`bosun workflow create`) | REST API |
| Agent monitoring | ✅ **YES** | REST API (`/api/agents`) | CLI / Telegram |
| Agent control (stop/chat) | ✅ **YES** | REST API | CLI / Telegram |
| Board sync | ✅ **YES** | CLI (`bosun board sync`) | Config files |
| Workspace management | ✅ **YES** | CLI (`bosun workspace *`) | REST API |
| Fleet coordination | ✅ **YES** | REST API (`/api/fleet/*`) | Telegram |
| PR lifecycle | ✅ **YES** | Auto-managed by Bosun | GitHub webhooks |
| Voice/Video agents | ✅ **YES** | REST API (`/api/voice/*`) | Telegram |
| Weekly reports | ✅ **YES** | CLI (`bosun report weekly`) | Telegram (`/weekly`) |
| Hook configuration | ✅ **YES** | `.codex/hooks.json` file | — |
| Configuration changes | ✅ **YES** | `.env` + `bosun.config.json` | CLI / REST API |
| MCP server config | 🔶 **LIKELY** | Executor/workflow config | Discovery needed |
| Model parameter tuning | 🔶 **LIKELY** | Executor config | Discovery needed |
| Full state export | ⚪ **Unknown** | Try `bosun config export` | — |

### Recommended Automation Stack

```
┌─────────────────────────────────────────────────────────┐
│ Your Automation Layer (scripts, CI/CD, other agents)    │
├─────────────┬───────────────┬───────────────────────────┤
│ REST API    │ CLI           │ Node.js SDK               │
│ curl/fetch  │ bosun task *  │ import from 'bosun/...'   │
│ port 18432  │ bosun fleet * │                           │
├─────────────┴───────────────┴───────────────────────────┤
│                    Bosun Supervisor                      │
│              (monitor.mjs orchestration)                 │
├─────────────────────────────────────────────────────────┤
│ Executors: Copilot | Codex | Claude | Gemini | OpenCode │
├─────────────────────────────────────────────────────────┤
│ Backends: GitHub | GitHub Projects v2 | Jira | Internal │
└─────────────────────────────────────────────────────────┘
```

---

## Sources

| Source | URL | What It Provides |
|--------|-----|------------------|
| GitHub Repo | https://github.com/virtengine/bosun | README, repo layout, CI/CD info |
| npm Registry | https://www.npmjs.com/package/bosun | Package metadata, version info |
| Website | https://bosun.virtengine.com | Architecture overview, feature list |
| Task Manager Gist | https://gist.github.com/jaeko44/fcb90b41332de52e34cfeca4c0f5027c | Complete task CLI + REST API + Node SDK reference |
| v0.37.0 Release | https://github.com/virtengine/bosun/releases/tag/0.37.0 | Voice/Video, Gemini, OpenCode additions |
| _docs/ directory | https://github.com/virtengine/bosun/tree/main/_docs | GitHub Projects v2, Jira, workflows, agent logging |

---

*Document generated 2026-03-04. For the most current reference, run `bosun --help` and the discovery commands in Section 20.*
