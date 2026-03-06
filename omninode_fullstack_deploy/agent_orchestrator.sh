#!/usr/bin/env bash
# ============================================================================
#
#  OmniNode Agent Orchestrator
#
#  A wrapper for Claude Code operator and AI agents to drive the OmniNode
#  full-stack deployment. Provides:
#
#    - JSON-line output for structured agent parsing
#    - Decision points with agent-injectable environment variables
#    - Phase-level execution with pre/postcondition verification
#    - Manifest-aware deployment planning
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
        # Order matters: backslashes first, then quotes, then control chars
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
cmd_plan() {
    emit_json "plan_start" \
        "version" "2.0.0" \
        "repositories" "8" \
        "phases" "5" \
        "profile" "${PROFILE:-full}"

    # Phase 1: Foundation
    emit_plan_step "1" "1.1" "clone_and_install" "Install omnibase_spi"
    emit_plan_step "1" "1.2" "clone_and_install" "Install omnibase_core"
    emit_plan_step "1" "1.3" "validate" "Verify Python imports"

    # Phase 2: Infrastructure
    emit_plan_step "2" "2.1" "docker_compose_up" "Start PostgreSQL, Redpanda, Valkey"
    emit_plan_step "2" "2.2" "wait_for_service" "Wait for PostgreSQL"
    emit_plan_step "2" "2.3" "run_migrations" "Run migrations 000-036"
    emit_plan_step "2" "2.4" "validate" "Validate 6 database roles"
    emit_plan_step "2" "2.5" "validate" "Validate omnidash_analytics DB"
    emit_plan_step "2" "2.6" "wait_for_service" "Wait for Redpanda"
    emit_plan_step "2" "2.7" "create_kafka_topics" "Create 4 OmniDash topics"
    emit_plan_step "2" "2.8" "validate" "Verify Kafka topics"

    # Phase 3: Runtime
    if [[ "${PROFILE:-full}" != "minimal" ]]; then
        emit_plan_step "3" "3.1" "docker_compose_up" "Start runtime services"
        emit_plan_step "3" "3.2" "wait_for_service" "Wait for omninode-runtime"
        emit_plan_step "3" "3.3" "wait_for_service" "Wait for intelligence-api"
    fi

    # Phase 4: Intelligence
    if [[ "${PROFILE:-full}" == "full" ]]; then
        emit_plan_step "4" "4.1" "docker_compose_up" "Start OmniMemory"
        emit_plan_step "4" "4.2" "clone_and_install" "Install OmniIntelligence"
        emit_plan_step "4" "4.3" "validate" "Verify PluginIntelligence discoverable"
        emit_plan_step "4" "4.4" "clone_and_install" "Install ONEX Change Control"
        emit_plan_step "4" "4.5" "validate" "Run contract validators"
        emit_plan_step "4" "4.6" "install_hooks" "Install pre-commit + pre-push hooks"
    fi

    # Phase 5: Interface
    if [[ "${PROFILE:-full}" == "full" ]]; then
        emit_plan_step "5" "5.1" "validate" "Pre-check Kafka topics"
        emit_plan_step "5" "5.2" "validate" "Pre-check omnidash_analytics DB"
        emit_plan_step "5" "5.3" "clone_and_build" "Build and start OmniDash"
        emit_plan_step "5" "5.4" "clone_and_install" "Install OmniClaude"
        emit_plan_step "5" "5.5" "start_daemon" "Start emit daemon"
        emit_plan_step "5" "5.6" "validate" "Verify emit daemon socket"
        emit_plan_step "5" "5.7" "validate" "Verify 5 Claude hooks"
        emit_plan_step "5" "5.8" "deploy_plugin" "Deploy to ~/.claude/plugins/cache/"
        emit_plan_step "5" "5.9" "capability_probe" "Detect integration tier"
    fi

    emit_json "plan_end" "total_steps" "$(count_plan_steps)"
}

count_plan_steps() {
    local count=3  # Phase 1 always
    count=$((count + 8))  # Phase 2 always
    if [[ "${PROFILE:-full}" != "minimal" ]]; then
        count=$((count + 3))  # Phase 3
    fi
    if [[ "${PROFILE:-full}" == "full" ]]; then
        count=$((count + 6))  # Phase 4
        count=$((count + 9))  # Phase 5
    fi
    echo "$count"
}

# ── Execute Mode ─────────────────────────────────────────────────────────
# Run deploy_all.sh with agent-mode output wrapping.
cmd_execute() {
    emit_json "deploy_start" \
        "profile" "${PROFILE:-full}" \
        "dry_run" "${DRY_RUN:-false}" \
        "workspace" "${WORKSPACE:-$HOME/omninode-workspace}"

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
# Check current state of all services.
cmd_status() {
    emit_json "status_check_start" "timestamp" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    # Docker containers
    local containers
    containers=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -c 'omninode' || echo 0)
    emit_status "docker" "$([ "$containers" -gt 0 ] && echo 'running' || echo 'stopped')" "${containers} containers"

    # PostgreSQL
    if pg_isready -h localhost -p "${POSTGRES_PORT:-5436}" -U postgres &>/dev/null; then
        emit_status "postgresql" "healthy" "Port ${POSTGRES_PORT:-5436}"
    else
        emit_status "postgresql" "down" "Not responding"
    fi

    # Kafka
    if (echo >/dev/tcp/localhost/"${REDPANDA_EXTERNAL_PORT:-29092}") 2>/dev/null; then
        emit_status "redpanda" "healthy" "Port ${REDPANDA_EXTERNAL_PORT:-29092}"
    else
        emit_status "redpanda" "down" "Not responding"
    fi

    # Valkey
    if redis-cli -h localhost -p "${VALKEY_PORT:-16379}" ping 2>/dev/null | grep -q PONG; then
        emit_status "valkey_infra" "healthy" "Port ${VALKEY_PORT:-16379}"
    else
        emit_status "valkey_infra" "down" "Not responding"
    fi

    # Runtime
    if curl -sf --max-time 3 "http://localhost:${RUNTIME_PORT:-8085}/health" >/dev/null 2>&1; then
        emit_status "runtime" "healthy" "Port ${RUNTIME_PORT:-8085}"
    else
        emit_status "runtime" "down" "Not responding"
    fi

    # OmniDash
    if curl -sf --max-time 3 "http://localhost:${OMNIDASH_PORT:-3000}" >/dev/null 2>&1; then
        emit_status "omnidash" "healthy" "Port ${OMNIDASH_PORT:-3000}"
    else
        emit_status "omnidash" "down" "Not responding"
    fi

    # Emit daemon
    if [[ -S "${OMNICLAUDE_EMIT_SOCKET:-/tmp/omniclaude-emit.sock}" ]]; then
        emit_status "emit_daemon" "running" "Socket present"
    else
        emit_status "emit_daemon" "stopped" "No socket"
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
OmniNode Agent Orchestrator - AI-driven deployment coordinator

Commands:
  --plan          Emit deployment plan as JSON (no execution)
  --execute       Run deployment with JSON-line output
  --dry-run       Preview deployment with JSON-line output
  --verify        Run postcondition checks with structured output
  --status        Check current service status

Options:
  --profile P     Deployment profile: minimal|standard|full (default: full)
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

