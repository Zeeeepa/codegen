#!/usr/bin/env bash
# ============================================================================
#
#  OmniNode Agent Orchestrator (Corrected v3)
#
#  A wrapper for Claude Code operator and AI agents to drive the OmniNode
#  full-stack deployment. Provides:
#
#    - JSON-line output for structured agent parsing
#    - Decision points with agent-injectable environment variables
#    - Phase-level execution with pre/postcondition verification
#    - Manifest-aware deployment planning
#
#  CRITICAL CORRECTIONS from v2:
#    - Entry point: deploy-runtime.sh (NOT docker compose up)
#    - Compose file: docker/docker-compose.infra.yml (NOT docker-compose.yml)
#    - Profiles: (default)/runtime/secrets/auth/full/bootstrap (NOT minimal/standard)
#    - Redpanda external port: 19092 (NOT 29092)
#    - Migrations: uv run python scripts/run-migrations.py (NOT ./run_migrations.sh)
#    - Topics: auto-created by TopicProvisioner (NOT manual rpk)
#    - Missing services added: migration-gate, skill-lifecycle-consumer,
#      contract-resolver, phoenix OTLP
#
#  Usage:
#    ./agent_orchestrator.sh --execute --profile full     # Deploy with JSON output
#    ./agent_orchestrator.sh --plan                        # Emit plan without executing
#    ./agent_orchestrator.sh --verify                      # Run all postcondition checks
#    ./agent_orchestrator.sh --status                      # Current deployment status
#
#  Agent Integration:
#    export AGENT_MODE=true
#    ./agent_orchestrator.sh --execute 2>/dev/null | jq .
#
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${SCRIPT_DIR}/agent_manifest.yaml"
DEPLOY_SCRIPT="${SCRIPT_DIR}/deploy_all.sh"
VERIFY_SCRIPT="${SCRIPT_DIR}/verify_deployment.sh"
LOG_FILE="${AGENT_LOG_FILE:-/tmp/omninode-agent-deploy.jsonl}"

# ── JSON Output Helpers ──────────────────────────────────────────────────
emit_json() {
    local event_type="$1"
    shift
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    printf '{"timestamp":"%s","type":"%s"' "$timestamp" "$event_type"
    while [[ $# -gt 0 ]]; do
        local key="$1"
        local value="$2"
        # Escape special characters for valid JSON output
        value="${value//\\/\\\\}"      # Escape backslashes first
        value="${value//\"/\\\"}"        # Escape double quotes
        value="${value//$'\n'/\\n}"       # Escape newlines
        value="${value//$'\t'/\\t}"       # Escape tabs
        value="${value//$'\r'/\\r}"       # Escape carriage returns
        printf ',"%s":"%s"' "$key" "$value"
        shift 2
    done
    printf '}\n'
}

emit_phase_start() {
    emit_json "phase_start" \
        "phase" "$1" \
        "name" "$2" \
        "description" "$3"
}

emit_phase_end() {
    emit_json "phase_end" \
        "phase" "$1" \
        "status" "$2" \
        "duration_seconds" "$3"
}

emit_step() {
    emit_json "step" \
        "phase" "$1" \
        "step_id" "$2" \
        "action" "$3" \
        "status" "$4" \
        "detail" "$5"
}

emit_validation() {
    emit_json "validation" \
        "check" "$1" \
        "status" "$2" \
        "detail" "$3"
}

emit_plan_step() {
    emit_json "plan" \
        "phase" "$1" \
        "step_id" "$2" \
        "action" "$3" \
        "description" "$4"
}

emit_status() {
    emit_json "status" \
        "component" "$1" \
        "state" "$2" \
        "detail" "$3"
}

# ── Plan Mode ────────────────────────────────────────────────────────────
# Emit the deployment plan without executing anything.
# CORRECTED: Uses actual compose profiles and deploy-runtime.sh
cmd_plan() {
    emit_json "plan_start" \
        "version" "3.0.0" \
        "repositories" "8" \
        "phases" "5" \
        "profile" "${PROFILE:-full}" \
        "entry_point" "scripts/deploy-runtime.sh" \
        "compose_file" "docker/docker-compose.infra.yml" \
        "authority" "CLAUDE.md > docs/ > this-plan"

    # Phase 1: Foundation
    emit_plan_step "1" "1.1" "clone_and_install" "Install omnibase_spi (contracts)"
    emit_plan_step "1" "1.2" "clone_and_install" "Install omnibase_core (4-node engine)"
    emit_plan_step "1" "1.3" "validate" "Verify Python imports (spi + core)"

    # Phase 2: Infrastructure (via deploy-runtime.sh, NOT docker compose up)
    emit_plan_step "2" "2.0" "generate_credentials" "Generate .env from template + store to ~/.omnibase/.env"
    emit_plan_step "2" "2.1" "deploy_via_script" "Run deploy-runtime.sh --execute (NOT docker compose up — OMN-2233)"
    emit_plan_step "2" "2.2" "wait_for_service" "Wait for PostgreSQL on port 5436"
    emit_plan_step "2" "2.3" "run_migrations" "Run: uv run python scripts/run-migrations.py --db-url ..."
    emit_plan_step "2" "2.4" "validate" "Validate 6 database roles exist"
    emit_plan_step "2" "2.5" "validate" "Validate omnidash_analytics database exists"
    emit_plan_step "2" "2.6" "wait_for_service" "Wait for Redpanda on port 19092 (NOT 29092)"
    emit_plan_step "2" "2.7" "note" "Topics auto-created by TopicProvisioner on kernel boot (NOT manual rpk)"

    # Phase 3: Runtime (via deploy-runtime.sh --profile runtime)
    # CORRECTED: No "minimal" profile exists — check against actual profiles
    if [[ "${PROFILE:-full}" == "runtime" || "${PROFILE:-full}" == "full" ]]; then
        emit_plan_step "3" "3.1" "deploy_via_script" "Run deploy-runtime.sh --execute --profile runtime"
        emit_plan_step "3" "3.1b" "wait_for_service" "Wait for migration-gate (OMN-3737 — startup sentinel)"
        emit_plan_step "3" "3.2" "wait_for_service" "Wait for omninode-runtime on port 8085"
        emit_plan_step "3" "3.3" "wait_for_service" "Wait for intelligence-api on port 8053"
        emit_plan_step "3" "3.4" "wait_for_service" "Wait for contract-resolver on port 8091"
        emit_plan_step "3" "3.5" "wait_for_service" "Wait for skill-lifecycle-consumer on port 8092"
        emit_plan_step "3" "3.6" "wait_for_service" "Wait for phoenix OTLP on port 6006"
    fi

    # Phase 4: Intelligence
    if [[ "${PROFILE:-full}" == "full" ]]; then
        emit_plan_step "4" "4.1" "clone_and_install" "Install OmniMemory (Qdrant + Memgraph + Valkey + Kreuzberg)"
        emit_plan_step "4" "4.1b" "run_migrations" "Run omnimemory migrations"
        emit_plan_step "4" "4.2" "clone_and_install" "Install OmniIntelligence (22 migration files)"
        emit_plan_step "4" "4.2b" "run_migrations" "Run omniintelligence 22 migrations"
        emit_plan_step "4" "4.3" "validate" "Verify PluginIntelligence discoverable by RuntimeHostProcess"
        emit_plan_step "4" "4.4" "clone_and_install" "Install ONEX Change Control"
        emit_plan_step "4" "4.5" "validate" "Run validate-yaml + check-schema-purity"
    fi

    # Phase 5: Interface
    if [[ "${PROFILE:-full}" == "full" ]]; then
        emit_plan_step "5" "5.1" "clone_and_build" "Build OmniDash (npm install)"
        emit_plan_step "5" "5.1b" "run_migrations" "Run OmniDash TypeScript migrations (npx tsx, NOT Python)"
        emit_plan_step "5" "5.2" "start_service" "Start OmniDash on port 3000"
        emit_plan_step "5" "5.3" "clone_and_install" "Install OmniClaude"
        emit_plan_step "5" "5.4" "start_daemon" "Start emit daemon (Unix socket → Kafka bridge)"
        emit_plan_step "5" "5.5" "deploy_plugin" "Deploy to ~/.claude/plugins/cache/ via deploy-local-plugin"
        emit_plan_step "5" "5.6" "capability_probe" "Detect tier: STANDALONE / EVENT_BUS / FULL_ONEX"
    fi

    emit_json "plan_end" "total_steps" "$(count_plan_steps)"
}

count_plan_steps() {
    local count=3  # Phase 1 always
    count=$((count + 7))  # Phase 2 always (7 steps with credential gen)
    if [[ "${PROFILE:-full}" == "runtime" || "${PROFILE:-full}" == "full" ]]; then
        count=$((count + 7))  # Phase 3 (with migration-gate + new services)
    fi
    if [[ "${PROFILE:-full}" == "full" ]]; then
        count=$((count + 7))  # Phase 4
        count=$((count + 7))  # Phase 5
    fi
    echo "$count"
}

# ── Execute Mode ─────────────────────────────────────────────────────────
# Run deploy_all.sh with agent-mode output wrapping.
# NOTE: deploy_all.sh should internally call deploy-runtime.sh
cmd_execute() {
    emit_json "deploy_start" \
        "profile" "${PROFILE:-full}" \
        "dry_run" "${DRY_RUN:-false}" \
        "workspace" "${WORKSPACE:-$HOME/omninode-workspace}" \
        "entry_point" "scripts/deploy-runtime.sh" \
        "compose_file" "docker/docker-compose.infra.yml"

    local args=("--profile" "${PROFILE:-full}")
    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        args+=("--dry-run")
    else
        args+=("--execute")
    fi

    # Add optional flags
    [[ "${SKIP_SECRETS:-false}" == "true" ]] && args+=("--skip-secrets")
    [[ "${SKIP_KEYCLOAK:-false}" == "true" ]] && args+=("--skip-keycloak")
    [[ -n "${PHASE:-}" ]] && args+=("--phase" "$PHASE")

    local start_time
    start_time=$(date +%s)
    local exit_code=0

    # Execute with output capture
    if bash "$DEPLOY_SCRIPT" "${args[@]}" 2>&1 | while IFS= read -r line; do
        emit_json "output" "line" "$line"
    done; then
        exit_code=0
    else
        exit_code=$?
    fi

    local end_time elapsed
    end_time=$(date +%s)
    elapsed=$((end_time - start_time))

    if [[ $exit_code -eq 0 ]]; then
        emit_json "deploy_end" "status" "success" "duration_seconds" "$elapsed"
    else
        emit_json "deploy_end" "status" "failed" "duration_seconds" "$elapsed" "exit_code" "$exit_code"
    fi

    return $exit_code
}

# ── Verify Mode ──────────────────────────────────────────────────────────
# Run all postcondition checks with structured output.
cmd_verify() {
    emit_json "verify_start" "mode" "${VERIFY_MODE:-sandbox}"

    local exit_code=0

    if bash "$VERIFY_SCRIPT" "--${VERIFY_MODE:-sandbox}" 2>&1 | while IFS= read -r line; do
        # Parse check results from verification output
        if echo "$line" | grep -qF '[OK]'; then
            local check_name
            check_name=$(echo "$line" | sed 's/.*\] //' | sed 's/ \[OK\]//')
            emit_validation "$check_name" "pass" ""
        elif echo "$line" | grep -q 'MISSING\|FAILED\|not responding'; then
            local check_name
            check_name=$(echo "$line" | sed 's/.*\] //')
            emit_validation "$check_name" "fail" "$line"
        fi
        echo "$line" >&2  # Pass through to stderr for human viewing
    done; then
        exit_code=0
    else
        exit_code=$?
    fi

    emit_json "verify_end" "status" "$( [[ $exit_code -eq 0 ]] && echo 'pass' || echo 'fail' )"
    return $exit_code
}

# ── Status Mode ──────────────────────────────────────────────────────────
# Check current state of all services (corrected ports).
cmd_status() {
    emit_json "status_check_start" "timestamp" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    # Docker containers
    local containers
    containers=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -c 'omninode' || echo 0)
    emit_status "docker" "$([ "$containers" -gt 0 ] && echo 'running' || echo 'stopped')" "${containers} containers"

    # Deploy-runtime.sh registry status
    local registry="${HOME}/.omnibase/infra/deployed/registry.json"
    if [[ -f "$registry" ]]; then
        emit_status "deploy_registry" "present" "Active deployment tracked in registry.json"
    else
        emit_status "deploy_registry" "absent" "No deploy-runtime.sh deployment registered"
    fi

    # PostgreSQL
    if pg_isready -h localhost -p "${POSTGRES_PORT:-5436}" -U postgres &>/dev/null; then
        emit_status "postgresql" "healthy" "Port ${POSTGRES_PORT:-5436}"
    else
        emit_status "postgresql" "down" "Not responding on port ${POSTGRES_PORT:-5436}"
    fi

    # Redpanda (CORRECTED: port 19092, NOT 29092)
    if (echo >/dev/tcp/localhost/"${REDPANDA_EXTERNAL_PORT:-19092}") 2>/dev/null; then
        emit_status "redpanda" "healthy" "Port ${REDPANDA_EXTERNAL_PORT:-19092}"
    else
        emit_status "redpanda" "down" "Not responding on port ${REDPANDA_EXTERNAL_PORT:-19092}"
    fi

    # Valkey (infra cache)
    if redis-cli -h localhost -p "${VALKEY_PORT:-16379}" ping 2>/dev/null | grep -q PONG; then
        emit_status "valkey_infra" "healthy" "Port ${VALKEY_PORT:-16379}"
    else
        emit_status "valkey_infra" "down" "Not responding on port ${VALKEY_PORT:-16379}"
    fi

    # Migration gate (OMN-3737) — NEW CHECK
    local mg_container
    mg_container=$(docker ps --format '{{.Names}}' 2>/dev/null | grep 'migration-gate' || echo "")
    if [[ -n "$mg_container" ]]; then
        emit_status "migration_gate" "running" "OMN-3737 startup sentinel active"
    else
        emit_status "migration_gate" "not_running" "Migration gate container not found"
    fi

    # Runtime
    if curl -sf --max-time 3 "http://localhost:${RUNTIME_PORT:-8085}/health" >/dev/null 2>&1; then
        emit_status "runtime" "healthy" "Port ${RUNTIME_PORT:-8085}"
    else
        emit_status "runtime" "down" "Not responding on port ${RUNTIME_PORT:-8085}"
    fi

    # Intelligence API
    if curl -sf --max-time 3 "http://localhost:${INTELLIGENCE_PORT:-8053}/health" >/dev/null 2>&1; then
        emit_status "intelligence_api" "healthy" "Port ${INTELLIGENCE_PORT:-8053}"
    else
        emit_status "intelligence_api" "down" "Not responding on port ${INTELLIGENCE_PORT:-8053}"
    fi

    # Contract Resolver — NEW CHECK
    if curl -sf --max-time 3 "http://localhost:${CONTRACT_RESOLVER_PORT:-8091}/health" >/dev/null 2>&1; then
        emit_status "contract_resolver" "healthy" "Port ${CONTRACT_RESOLVER_PORT:-8091}"
    else
        emit_status "contract_resolver" "down" "Not responding on port ${CONTRACT_RESOLVER_PORT:-8091}"
    fi

    # Skill Lifecycle Consumer — NEW CHECK
    local slc_container
    slc_container=$(docker ps --format '{{.Names}}' 2>/dev/null | grep 'skill-lifecycle' || echo "")
    if [[ -n "$slc_container" ]]; then
        emit_status "skill_lifecycle_consumer" "running" "Port 8092"
    else
        emit_status "skill_lifecycle_consumer" "not_running" "Container not found"
    fi

    # Phoenix OTLP — NEW CHECK
    if curl -sf --max-time 3 "http://localhost:${PHOENIX_PORT:-6006}" >/dev/null 2>&1; then
        emit_status "phoenix_otlp" "healthy" "Port ${PHOENIX_PORT:-6006}"
    else
        emit_status "phoenix_otlp" "down" "Not responding on port ${PHOENIX_PORT:-6006}"
    fi

    # OmniDash
    if curl -sf --max-time 3 "http://localhost:${OMNIDASH_PORT:-3000}" >/dev/null 2>&1; then
        emit_status "omnidash" "healthy" "Port ${OMNIDASH_PORT:-3000}"
    else
        emit_status "omnidash" "down" "Not responding on port ${OMNIDASH_PORT:-3000}"
    fi

    # Emit daemon
    if [[ -S "${OMNICLAUDE_EMIT_SOCKET:-/tmp/omniclaude-emit.sock}" ]]; then
        emit_status "emit_daemon" "running" "Socket present"
    else
        emit_status "emit_daemon" "stopped" "No socket at ${OMNICLAUDE_EMIT_SOCKET:-/tmp/omniclaude-emit.sock}"
    fi

    # OmniClaude tier
    local cap_file="${HOME}/.claude/.onex_capabilities"
    if [[ -f "$cap_file" ]]; then
        local tier
        tier=$(head -1 "$cap_file" 2>/dev/null || echo "unknown")
        emit_status "omniclaude" "active" "Tier: ${tier}"
    else
        emit_status "omniclaude" "not_probed" "Start a Claude Code session to trigger probe"
    fi

    emit_json "status_check_end"
}

# ── Argument Parsing ─────────────────────────────────────────────────────
COMMAND=""
PROFILE="${PROFILE:-full}"
DRY_RUN="${DRY_RUN:-false}"
WORKSPACE="${WORKSPACE:-$HOME/omninode-workspace}"
VERIFY_MODE="sandbox"
SKIP_SECRETS="${SKIP_SECRETS:-false}"
SKIP_KEYCLOAK="${SKIP_KEYCLOAK:-false}"
PHASE="${PHASE:-}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --plan)      COMMAND="plan"; shift ;;
        --execute)   COMMAND="execute"; DRY_RUN="false"; shift ;;
        --dry-run)   COMMAND="execute"; DRY_RUN="true"; shift ;;
        --verify)    COMMAND="verify"; shift ;;
        --status)    COMMAND="status"; shift ;;
        --profile)   PROFILE="$2"; shift 2 ;;
        --workspace) WORKSPACE="$2"; shift 2 ;;
        --live)      VERIFY_MODE="live"; shift ;;
        --sandbox)   VERIFY_MODE="sandbox"; shift ;;
        --skip-secrets)  SKIP_SECRETS="true"; shift ;;
        --skip-keycloak) SKIP_KEYCLOAK="true"; shift ;;
        --phase)     PHASE="$2"; shift 2 ;;
        -h|--help)
            cat <<'HELP'
OmniNode Agent Orchestrator v3 - AI-driven deployment coordinator

  CRITICAL: Uses deploy-runtime.sh as entry point (NOT docker compose up).
  See omnibase_infra/docker/README.md for why.

Commands:
  --plan          Emit deployment plan as JSON (no execution)
  --execute       Run deployment with JSON-line output
  --dry-run       Preview deployment with JSON-line output
  --verify        Run postcondition checks with structured output
  --status        Check current service status (21 services)

Options:
  --profile P     Deployment profile (ACTUAL profiles):
                    (default) - PostgreSQL + Redpanda + Valkey only
                    runtime   - + all ONEX runtime services
                    secrets   - + Infisical
                    auth      - + Keycloak
                    full      - everything (default)
                    bootstrap - first-time setup
  --workspace D   Workspace directory (default: ~/omninode-workspace)
  --phase N       Run specific phase only (1-5)
  --live          Use live verification (requires running services)
  --sandbox       Use sandbox verification (no Docker required)
  --skip-secrets  Skip Infisical deployment
  --skip-keycloak Skip Keycloak deployment

Agent Integration:
  Pipe stdout to jq for structured parsing:
    ./agent_orchestrator.sh --plan | jq .
    ./agent_orchestrator.sh --execute 2>/dev/null | jq -c 'select(.type=="step")'
    ./agent_orchestrator.sh --status | jq -c 'select(.type=="status")'

Key Corrections (v3):
  - Entry point: scripts/deploy-runtime.sh (NOT docker compose up)
  - Compose file: docker/docker-compose.infra.yml
  - Redpanda external: port 19092 (NOT 29092)
  - Migrations: uv run python scripts/run-migrations.py (NOT ./run_migrations.sh)
  - Topics: auto-created by TopicProvisioner (NOT manual rpk)
  - Added: migration-gate, skill-lifecycle-consumer, contract-resolver, phoenix
HELP
            exit 0
            ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

export PROFILE DRY_RUN WORKSPACE SKIP_SECRETS SKIP_KEYCLOAK PHASE

# ── Dispatch ─────────────────────────────────────────────────────────────
case "${COMMAND:-plan}" in
    plan)    cmd_plan ;;
    execute) cmd_execute ;;
    verify)  cmd_verify ;;
    status)  cmd_status ;;
    *)       echo "Unknown command: $COMMAND" >&2; exit 1 ;;
esac

