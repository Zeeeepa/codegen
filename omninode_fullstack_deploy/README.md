# OmniNode Full-Stack Deployment Guide

> **Authority**: This guide wraps the deployment tools in `omnibase_infra`. When in doubt, consult `CLAUDE.md` (authoritative rules) → `docs/` (explanations) → this guide.

> ⚠️ **Critical**: Never run `docker compose up` directly from the `docker/` directory — use `scripts/deploy-runtime.sh` instead. Direct compose invocation causes project name collisions (OMN-2233).

---

## Architecture Overview

```
                    ┌──────────────────────────────────────────────────┐
                    │              OmniNode Platform                    │
                    │                                                  │
  Interface ─────── │  OmniClaude ← 90+ skills, 54 agents, FULL_ONEX │
                    │  OmniDash   ← Real-time observability UI        │
                    │                                                  │
  Intelligence ──── │  OmniIntelligence ← 21 ONEX intelligence nodes  │
                    │  OmniMemory      ← Qdrant + Memgraph + Valkey   │
                    │  ONEX CC         ← Cross-repo governance        │
                    │                                                  │
  Runtime ───────── │  omninode-runtime    ← ONEX execution engine    │
                    │  migration-gate      ← Startup sentinel (OMN-3737)│
                    │  intelligence-api    ← Pattern + intent API     │
                    │  contract-resolver   ← HTTP bridge for contracts│
                    │  skill-lifecycle-consumer ← Skill registry      │
                    │  phoenix             ← OTLP observability       │
                    │  + workers, consumers                           │
                    │                                                  │
  Infrastructure ── │  PostgreSQL ← 7 databases, 6 roles              │
                    │  Redpanda   ← Kafka event bus                   │
                    │  Valkey     ← Platform cache                    │
                    │  Infisical  ← Secrets management (opt-in)       │
                    │  Keycloak   ← OIDC authentication (opt-in)      │
                    │                                                  │
  Foundation ────── │  omnibase_spi  ← Protocol interfaces            │
                    │  omnibase_core ← ONEX 4-node framework          │
                    └──────────────────────────────────────────────────┘
```

### Dependency Graph

```
omnibase_spi (contracts)
  └→ omnibase_core (execution protocol)
       └→ omnibase_infra (deployment center — ALL repos deploy through here)
            ├→ omnimemory (Qdrant, Memgraph, Valkey, Kreuzberg)
            ├→ omniintelligence (21 intelligence nodes)
            ├→ onex_change_control (governance)
            ├→ omnidash (React dashboard)
            └→ omniclaude (Claude Code agent — top of stack)
```

**Key insight**: `omnibase_infra` is the deployment center-of-gravity. All services deploy through its compose file and scripts — not through separate per-repo compose files.

---

## Prerequisites

| Tool | Minimum Version | Check Command |
|------|----------------|---------------|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | **v2.20+** (required by deploy-runtime.sh) | `docker compose version` |
| Python | 3.12+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| uv | latest | `uv --version` |
| Git | 2.0+ | `git --version` |
| openssl | any | `openssl version` |
| Disk Space | 10GB+ | `df -h .` |
| RAM | 4GB+ (8GB recommended) | `free -h` |

---

## Quick Start

```bash
# 1. Clone omnibase_infra (the deployment center)
git clone https://github.com/OmniNode-ai/omnibase_infra.git
cd omnibase_infra

# 2. Generate credentials from template
cp docker/.env.example docker/.env
# Generate secure passwords:
openssl rand -hex 32  # Use output for each password field

# 3. Store credentials permanently (survives docker volume rm)
mkdir -p ~/.omnibase
cp docker/.env ~/.omnibase/.env

# 4. Preview what will happen (dry-run)
./docker/scripts/deploy-runtime.sh --dry-run --profile full

# 5. Deploy infrastructure (correct entry point)
./docker/scripts/deploy-runtime.sh --execute --profile full

# 6. Run migrations
uv run python scripts/run-migrations.py --db-url "postgresql://postgres:<password>@localhost:5436/omnibase_infra"

# 7. Verify deployment
./verify_deployment.sh --live
```

---

## Compose Profiles (Actual)

> ⚠️ These are the **real** Docker Compose profiles from `docker/docker-compose.infra.yml`. PR #218's `minimal`/`standard` profiles do NOT exist.

| Profile | Services Included | Use Case |
|---------|-------------------|----------|
| `(default)` | PostgreSQL, Redpanda, Valkey | Core infrastructure only |
| `runtime` | + All ONEX runtime services | API development, service testing |
| `secrets` | + Infisical | When you need centralized secret management |
| `auth` | + Keycloak | When you need OIDC authentication |
| `full` | Everything above combined | Full platform, production-like |
| `bootstrap` | First-time setup sequence | Initial deployment only |

```bash
# Infrastructure only (PostgreSQL + Redpanda + Valkey)
./docker/scripts/deploy-runtime.sh --execute

# Infrastructure + runtime services
./docker/scripts/deploy-runtime.sh --execute --profile runtime

# Everything including secrets + auth
./docker/scripts/deploy-runtime.sh --execute --profile full

# First-time bootstrap (handles circular dependencies)
./docker/scripts/deploy-runtime.sh --execute --profile bootstrap
```

---

## Deployment via deploy-runtime.sh

> **This is THE entry point.** Not `docker compose up`. Not custom scripts. This tool encodes operational knowledge from production incidents.

### What deploy-runtime.sh Provides

| Feature | Description |
|---------|-------------|
| **Versioned deployments** | Each deploy creates `~/.omnibase/infra/deployed/{version}/` |
| **Atomic locks** | Prevents concurrent deploys with stale PID detection |
| **Registry tracking** | `registry.json` tracks which deployment is currently active |
| **Orphan cleanup** | Automatically removes old deployments (keeps max 5) |
| **Full rollback** | On failure, restores previous deployment state |
| **Docker version check** | Requires Compose v2.20+ |
| **Git SHA labeling** | Tags deployed images with VCS_REF for tracking |
| **Dry-run mode** | `--dry-run` previews without executing |
| **Profile validation** | Only allows alphanumeric/hyphen/underscore profile names |
| **OMN-2233 prevention** | Avoids project name collision via controlled project naming |

### Usage

```bash
# Dry run (preview everything)
./docker/scripts/deploy-runtime.sh --dry-run --profile full

# Execute deployment
./docker/scripts/deploy-runtime.sh --execute --profile runtime

# For exact flags and options:
./docker/scripts/deploy-runtime.sh --help
```

---

## Bootstrap Sequence (Correct 6-Step)

> Source: `docker/scripts/bootstrap-infisical.sh` — handles circular dependency where Postgres migrations must run BEFORE Infisical can seal secrets.

```
Step 1:   PostgreSQL starts
Step 1b:  Migrations run (omnibase_infra, omniintelligence, omniclaude)
Step 1c:  Cross-repo provisioning (omnimemory, omnidash databases + roles)
Step 1d:  OmniDash read-model migrations (NON-FATAL — warns and continues)
Step 2:   Valkey starts
Step 3:   Infisical starts
Step 3.5: Keycloak + provisioning (optional, skip with --skip-keycloak)
Step 4:   Identity provisioning
Step 5:   Seed Infisical with secrets
Step 6:   Runtime services start (gated by migration-gate OMN-3737)
```

### Circular Dependency Handling

The bootstrap has a chicken-and-egg problem: Infisical needs Postgres for its own data, but services need Infisical for their secrets. The solution:

1. Bootstrap credentials live in `.env` only (the "bootstrap transport exception")
2. Postgres starts first with those credentials
3. Migrations run using those credentials
4. Infisical starts after Postgres is healthy
5. Runtime services then fetch their config from Infisical via CONFIG_DISCOVERY

### Non-Fatal Error Handling

Step 1d (omnidash read-model migrations) is **advisory during bootstrap**:
- At **bootstrap time**: Warns and continues if DB not available
- At **deploy time** (via deploy-runtime.sh): Fails closed — pod won't start if schema mismatch

---

## Complete Service Inventory

### Infrastructure Services (default profile)

| Service | Port | Health Check |
|---------|------|-------------|
| PostgreSQL | 5436 | `pg_isready -h localhost -p 5436` |
| Redpanda (internal) | 9092 | — |
| Redpanda (external) | **19092** | `rpk cluster health --brokers localhost:19092` |
| Valkey (platform cache) | 16379 | `redis-cli -p 16379 ping` |

### Runtime Services (runtime profile)

| Service | Port | Health Check |
|---------|------|-------------|
| **migration-gate** (OMN-3737) | — | Startup sentinel, gates all runtime services |
| omninode-runtime | 8085 | `curl -sf http://localhost:8085/health` |
| runtime-effects | 8086 | `curl -sf http://localhost:8086/health` |
| agent-actions-consumer | 8087 | — |
| intelligence-api | 8053 | `curl -sf http://localhost:8053/health` |
| contract-resolver | 8091 | `curl -sf http://localhost:8091/health` |
| skill-lifecycle-consumer | 8092 | — |
| Phoenix OTLP | 6006 | `curl -sf http://localhost:6006` |

### Optional Services

| Service | Port | Profile | Health Check |
|---------|------|---------|-------------|
| Infisical | 8880 | `secrets` | `curl -sf http://localhost:8880/api/status` |
| Keycloak | 28080 | `auth` | `curl -sf http://localhost:28080` |
| Consul | 28500 | — | `curl -sf http://localhost:28500/v1/status/leader` |

### Memory/Intelligence Services (deployed separately)

| Service | Port | Health Check |
|---------|------|-------------|
| Qdrant HTTP | 6333 | `curl -sf http://localhost:6333` |
| Qdrant gRPC | 6334 | — |
| Memgraph Bolt | 7687 | — |
| Memgraph HTTP | 7444 | — |
| Valkey (memory-local) | 6379 | `redis-cli -p 6379 ping` |
| Kreuzberg parser | 8090 | `curl -sf http://localhost:8090` |

### Interface Services

| Service | Port | Health Check |
|---------|------|-------------|
| OmniDash | 3000 | `curl -sf http://localhost:3000` |

---

## Configuration Model (CONFIG_DISCOVERY)

> Source: `docs/architecture/CONFIG_DISCOVERY.md`

**Problem**: The `.env` file expanded from 60 to 660 lines, creating maintenance hell.

**Solution**: Contracts declare what they need → runtime auto-fetches from Infisical.

### How It Works

1. Each node's `contract.yaml` declares dependencies:
   ```yaml
   dependencies:
     - type: environment
       key: DATABASE_URL
   ```

2. Three contract fields are scanned:
   - `metadata.transport_type`
   - `handler_routing.handlers[].handler_type`
   - `dependencies[].type == "environment"`

3. Transport slugs: `db`, `kafka`, `consul`, `infisical` (bootstrap only), `http`, `mcp`, `qdrant`, `env`

4. **Key rule**: Environment variables ALWAYS override Infisical (local dev flexibility)

### Credential Storage

| Location | Purpose | Survives Volume Rm? |
|----------|---------|-------------------|
| `docker/.env` | Active compose environment | No |
| `~/.omnibase/.env` | Permanent credential store | Yes |
| Infisical (`/shared/<transport>/KEY`) | Production secrets | Yes |

---

## Claude Code Operator Guide

### 3-Tier Integration

OmniClaude auto-detects available services and sets its tier:

| Tier | Requirements | Capabilities |
|------|-------------|-------------|
| **STANDALONE** | Nothing | 90+ skills, 54 agents, hooks — events silently dropped |
| **EVENT_BUS** | Kafka reachable on 19092 | + routing telemetry, session events, Kafka observability |
| **FULL_ONEX** | + Intelligence API + Memory | + context enrichment, semantic recall, pattern enforcement |

### Deploy Plugin to Claude Code

```bash
# From omniclaude repo:
# Dry run (preview what changes)
/deploy-local-plugin

# Execute deployment (syncs files + builds venv)
/deploy-local-plugin --execute

# With tier filtering
/deploy-local-plugin --execute --level basic        # Daily driver skills only
/deploy-local-plugin --execute --level intermediate  # + intermediate skills
/deploy-local-plugin --execute --include-debug       # Everything including debug
```

Plugin files deploy to: `~/.claude/plugins/cache/omninode-tools/onex/{version}/`

### Performance Budgets

| Hook | Budget | What Blocks |
|------|--------|-------------|
| SessionStart | <50ms | Daemon check, stdin read |
| UserPromptSubmit | <500ms | Routing, injection, advisory |
| PreToolUse | <100ms | stdin read, authorization (Edit/Write) |
| PostToolUse | <100ms | stdin read, quality check |
| SessionEnd | <50ms | stdin read |

---

## Migrations

> Source: `docs/runbooks/apply-migrations.md`

### When to Run

- After pulling new code
- After fresh rebuild
- After incident recovery
- When fingerprint mismatch detected

### Commands

```bash
# Dry run (preview changes)
uv run python scripts/run-migrations.py --db-url "postgresql://postgres:<pw>@localhost:5436/omnibase_infra" --dry-run

# Apply all migrations
uv run python scripts/run-migrations.py --db-url "postgresql://postgres:<pw>@localhost:5436/omnibase_infra"

# Apply to specific target
uv run python scripts/run-migrations.py --db-url "..." --target omniintelligence

# Fingerprint verification
uv run python scripts/run-migrations.py --db-url "..." --verify-fingerprint
```

### OmniDash Special Handling

OmniDash uses **TypeScript migrations** (not Python):
```bash
cd omnidash
npx tsx scripts/run-migrations.ts
```

- **Bootstrap**: Advisory (warn and continue if DB unavailable)
- **Deploy time**: Fail-closed (pod won't start on schema mismatch)

---

## Troubleshooting

### PostgreSQL won't start
```bash
docker logs omninode-infra-postgres-1
# Common: permissions on data volume, insufficient shared memory
# Fix: docker volume rm omninode-infra_postgres_data && redeploy
```

### Redpanda broker unreachable
```bash
docker logs omninode-infra-redpanda-1
# Common: port already in use (check 19092, not 29092)
ss -tlnp | grep 19092
```

### Migrations fail
```bash
# Check migration state:
uv run python scripts/run-migrations.py --db-url "..." --verify-fingerprint

# Emergency rollback:
uv run python scripts/run-migrations.py --db-url "..." --rollback
```

### OmniClaude shows STANDALONE instead of FULL_ONEX
```bash
# Check Kafka (note: port 19092, not 29092):
rpk cluster health --brokers localhost:19092

# Check intelligence-api:
curl -sf http://localhost:8053/health

# Force re-probe:
rm ~/.claude/.onex_capabilities
# Start new Claude Code session
```

### Runtime services won't start
```bash
# Check migration-gate (OMN-3737):
docker logs omninode-infra-migration-gate-1
# Migration gate must be healthy before runtime services can start
```

### Rollback a failed deployment
```bash
# deploy-runtime.sh handles this automatically on failure
# To manually rollback, consult:
./docker/scripts/deploy-runtime.sh --help
# Review active deployment in registry:
cat ~/.omnibase/infra/deployed/registry.json
```

---

## File Structure

```
omninode_fullstack_deploy/
├── deploy_all.sh                    # Wrapper that calls deploy-runtime.sh
├── verify_deployment.sh             # Read-only health check (all services)
├── README.md                        # This guide
├── config/
│   └── .env.template                # Reference environment (all 8 repos)
├── phases/
│   ├── 01_foundation.sh             # SPI + Core (pip/uv install)
│   ├── 02_infrastructure.sh         # Calls deploy-runtime.sh (default profile)
│   ├── 03_runtime_services.sh       # Calls deploy-runtime.sh (runtime profile)
│   ├── 04_intelligence_layer.sh     # Memory + Intelligence + Governance
│   └── 05_interface_layer.sh        # OmniDash + OmniClaude
├── lib/
│   ├── common.sh                    # Logging, health checks, retry logic
│   ├── docker_helpers.sh            # deploy-runtime.sh wrappers
│   └── validation.sh                # Pre-flight checks
├── agent_manifest.yaml              # Machine-readable deployment plan
├── agent_orchestrator.sh            # AI agent wrapper (plan/execute/verify/status)
├── run_sandbox_tests.sh             # TAP test suite (no Docker needed)
└── docs/
    ├── architecture.md              # System architecture details
    ├── troubleshooting.md           # Extended troubleshooting
    └── agent_integration.md         # Claude Code multi-agent guide
```

---

## Key References

| Document | Location | Authority |
|----------|----------|-----------|
| **CLAUDE.md** | `omnibase_infra/CLAUDE.md` | **Highest** — non-negotiable rules |
| **docker/README.md** | `omnibase_infra/docker/README.md` | Deployment authority |
| **deploy-runtime.sh** | `omnibase_infra/docker/scripts/` | Single deployment entry point |
| **bootstrap-infisical.sh** | `omnibase_infra/docker/scripts/` | 6-step bootstrap |
| **CONFIG_DISCOVERY.md** | `omnibase_infra/docs/architecture/` | Config resolution pattern |
| **apply-migrations.md** | `omnibase_infra/docs/runbooks/` | Migration operations |

---

## License

MIT — See individual OmniNode repositories for their respective licenses.

