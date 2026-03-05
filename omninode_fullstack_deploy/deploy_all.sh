#!/usr/bin/env bash
# ============================================================================
#
#  OmniNode Full-Stack Deployment Orchestrator
#
#  Deploys all 8 OmniNode repositories in dependency order:
#    Phase 1: Foundation   — omnibase_spi + omnibase_core
#    Phase 2: Infrastructure — PostgreSQL, Redpanda, Valkey, Infisical, Keycloak
#    Phase 3: Runtime      — omninode-runtime, workers, consumers, intelligence-api
#    Phase 4: Intelligence — OmniMemory, OmniIntelligence, ONEX Change Control
#    Phase 5: Interface    — OmniDash, OmniClaude (73 skills, 54 agents)
#
#  Usage:
#    ./deploy_all.sh --dry-run                    Preview all actions
#    ./deploy_all.sh --execute --profile full      Deploy everything
#    ./deploy_all.sh --execute --phase 2           Deploy Phase 2 only
#    ./deploy_all.sh --execute --skip-secrets      Skip Infisical
#    ./deploy_all.sh --execute --skip-keycloak     Skip Keycloak
#
# ============================================================================
set -euo pipefail

# ── Resolve Script Directory ──────────────────────────────────────────────
DEPLOY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export DEPLOY_ROOT

# ── Source Libraries ──────────────────────────────────────────────────────
# shellcheck source=lib/common.sh
source "${DEPLOY_ROOT}/lib/common.sh"
# shellcheck source=lib/validation.sh
source "${DEPLOY_ROOT}/lib/validation.sh"
# shellcheck source=lib/docker_helpers.sh
source "${DEPLOY_ROOT}/lib/docker_helpers.sh"

# ── Source Phase Scripts ──────────────────────────────────────────────────
# shellcheck source=phases/01_foundation.sh
source "${DEPLOY_ROOT}/phases/01_foundation.sh"
# shellcheck source=phases/02_infrastructure.sh
source "${DEPLOY_ROOT}/phases/02_infrastructure.sh"
# shellcheck source=phases/03_runtime_services.sh
source "${DEPLOY_ROOT}/phases/03_runtime_services.sh"
# shellcheck source=phases/04_intelligence_layer.sh
source "${DEPLOY_ROOT}/phases/04_intelligence_layer.sh"
# shellcheck source=phases/05_interface_layer.sh
source "${DEPLOY_ROOT}/phases/05_interface_layer.sh"

# ── Defaults ──────────────────────────────────────────────────────────────
DRY_RUN="true"
PROFILE="full"
PHASE=""
WORKSPACE="${HOME}/omninode-workspace"
SKIP_SECRETS="false"
SKIP_KEYCLOAK="false"
SKIP_PORT_CHECK="false"
VERBOSE="false"

export DRY_RUN PROFILE PHASE WORKSPACE SKIP_SECRETS SKIP_KEYCLOAK SKIP_PORT_CHECK VERBOSE

# ── Parse Arguments ───────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  --dry-run                 Preview all actions without executing (default)
  --execute                 Actually deploy services
  --phase N                 Run specific phase only (1-5)
  --profile PROFILE         Service profile: minimal|standard|full (default: full)
  --workspace DIR           Workspace directory (default: ~/omninode-workspace)
  --skip-secrets            Skip Infisical deployment
  --skip-keycloak           Skip Keycloak deployment
  --skip-port-check         Skip pre-flight port scan
  --verbose                 Enable verbose logging
  --stop                    Stop all OmniNode services
  -h, --help                Show this help

Profiles:
  minimal     Core infrastructure only (PostgreSQL, Redpanda, Valkey)
  standard    Infrastructure + runtime services
  full        Everything including intelligence, dashboard, and Claude Code

Phases:
  1  Foundation      — omnibase_spi + omnibase_core (Python packages)
  2  Infrastructure  — PostgreSQL, Redpanda, Valkey, Infisical, Keycloak
  3  Runtime         — ONEX runtime, workers, consumers, intelligence-api
  4  Intelligence    — OmniMemory, OmniIntelligence, Change Control
  5  Interface       — OmniDash (React), OmniClaude (73 skills, 54 agents)

Examples:
  $(basename "$0") --dry-run                              # Preview full deployment
  $(basename "$0") --execute --profile full                # Deploy everything
  $(basename "$0") --execute --phase 2 --skip-secrets      # Deploy infra only, no Infisical
  $(basename "$0") --execute --profile minimal             # Just databases + event bus
  $(basename "$0") --stop                                  # Stop all services
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)       DRY_RUN="true"; shift ;;
        --execute)       DRY_RUN="false"; shift ;;
        --phase)         PHASE="$2"; shift 2 ;;
        --profile)       PROFILE="$2"; shift 2 ;;
        --workspace)     WORKSPACE="$2"; shift 2 ;;
        --skip-secrets)  SKIP_SECRETS="true"; shift ;;
        --skip-keycloak) SKIP_KEYCLOAK="true"; shift ;;
        --skip-port-check) SKIP_PORT_CHECK="true"; shift ;;
        --verbose)       VERBOSE="true"; set -x; shift ;;
        --stop)          stop_all; exit 0 ;;
        -h|--help)       usage ;;
        *) log_error "Unknown option: $1"; usage ;;
    esac
done

# ── Main ──────────────────────────────────────────────────────────────────
main() {
    print_banner

    local start_time
    start_time=$(date +%s)

    # Mode indicator
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}  ⚠  DRY-RUN MODE — No changes will be made${NC}"
        echo -e "${DIM}  Run with --execute to deploy for real${NC}"
    else
        echo -e "${GREEN}  ▶  EXECUTE MODE — Deploying services${NC}"
    fi
    echo -e "  Profile: ${BOLD}${PROFILE}${NC}  |  Workspace: ${DIM}${WORKSPACE}${NC}"
    echo ""

    # Create workspace
    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "mkdir -p ${WORKSPACE}"
    else
        mkdir -p "$WORKSPACE"
    fi

    # Pre-flight checks (skip in dry-run for speed)
    if [[ "$DRY_RUN" != "true" ]]; then
        run_preflight || exit 1
    fi

    # ── Execute Phases Based on Profile + Phase Filter ─────────────────────

    # Phase 1: Foundation (always needed)
    if should_run_phase 1; then
        phase_01_foundation
    fi

    # Phase 2: Infrastructure (always needed for any profile)
    if should_run_phase 2; then
        phase_02_infrastructure
    fi

    # Phase 3: Runtime (standard + full profiles)
    if should_run_phase 3 && [[ "$PROFILE" != "minimal" ]]; then
        phase_03_runtime
    elif should_run_phase 3; then
        log_info "Skipping Phase 3 — Profile '${PROFILE}' does not include runtime services"
    fi

    # Phase 4: Intelligence (full profile only)
    if should_run_phase 4 && [[ "$PROFILE" == "full" ]]; then
        phase_04_intelligence
    elif should_run_phase 4; then
        log_info "Skipping Phase 4 — Profile '${PROFILE}' does not include intelligence layer"
    fi

    # Phase 5: Interface (full profile only)
    if should_run_phase 5 && [[ "$PROFILE" == "full" ]]; then
        phase_05_interface
    elif should_run_phase 5; then
        log_info "Skipping Phase 5 — Profile '${PROFILE}' does not include interface layer"
    fi

    # ── Summary ────────────────────────────────────────────────────────────
    local end_time elapsed
    end_time=$(date +%s)
    elapsed=$((end_time - start_time))

    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Deployment Complete! (${elapsed}s)                     ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"

    if [[ "$DRY_RUN" != "true" ]]; then
        print_service_table
        print_service_row "PostgreSQL"             "${POSTGRES_PORT:-5436}"    "localhost:${POSTGRES_PORT:-5436}"
        print_service_row "Redpanda (Kafka)"       "${REDPANDA_EXTERNAL_PORT:-29092}" "localhost:${REDPANDA_EXTERNAL_PORT:-29092}"
        print_service_row "Valkey"                 "${VALKEY_PORT:-16379}"     "localhost:${VALKEY_PORT:-16379}"

        if [[ "$SKIP_SECRETS" != "true" ]]; then
            print_service_row "Infisical"          "8880"                     "http://localhost:8880"
        fi
        if [[ "$SKIP_KEYCLOAK" != "true" ]]; then
            print_service_row "Keycloak"           "28080"                    "http://localhost:28080"
        fi

        if [[ "$PROFILE" != "minimal" ]]; then
            print_service_row "omninode-runtime"   "${RUNTIME_PORT:-8085}"    "http://localhost:${RUNTIME_PORT:-8085}"
            print_service_row "intelligence-api"   "${INTELLIGENCE_API_PORT:-8053}" "http://localhost:${INTELLIGENCE_API_PORT:-8053}"
            print_service_row "contract-resolver"  "${CONTRACT_RESOLVER_PORT:-8091}" "http://localhost:${CONTRACT_RESOLVER_PORT:-8091}"
            print_service_row "Phoenix OTLP"       "${PHOENIX_OTLP_PORT:-6006}" "http://localhost:${PHOENIX_OTLP_PORT:-6006}"
        fi

        if [[ "$PROFILE" == "full" ]]; then
            print_service_row "Qdrant"             "${QDRANT_HTTP_PORT:-6333}" "http://localhost:${QDRANT_HTTP_PORT:-6333}"
            print_service_row "Memgraph"           "${MEMGRAPH_BOLT_PORT:-7687}" "bolt://localhost:${MEMGRAPH_BOLT_PORT:-7687}"
            print_service_row "Kreuzberg"          "${KREUZBERG_PORT:-8090}"  "http://localhost:${KREUZBERG_PORT:-8090}"
            print_service_row "OmniDash"           "${OMNIDASH_PORT:-3000}"   "http://localhost:${OMNIDASH_PORT:-3000}"
            print_service_row "OmniClaude"         "—"                        "Claude Code Plugin"
        fi

        print_service_table_end
    fi

    echo -e "  ${BOLD}Next Steps:${NC}"
    echo -e "    1. Open OmniDash:  ${CYAN}http://localhost:3000${NC}"
    echo -e "    2. In Claude Code:  ${CYAN}/deploy-local-plugin${NC}"
    echo -e "    3. Verify:          ${CYAN}./verify_deployment.sh${NC}"
    echo ""
}

# ── Phase Filter Helper ───────────────────────────────────────────────────
should_run_phase() {
    local phase_num="$1"
    if [[ -z "$PHASE" ]]; then
        return 0  # No filter = run all
    fi
    [[ "$PHASE" == "$phase_num" ]]
}

# ── Run ───────────────────────────────────────────────────────────────────
main "$@"

