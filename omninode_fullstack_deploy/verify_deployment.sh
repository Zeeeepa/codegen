#!/usr/bin/env bash
# ============================================================================
#
#  OmniNode Full-Stack — Deployment Verification
#
#  Two modes:
#    --live     Check running services (health, DB, Kafka, endpoints)
#    --sandbox  Validate configs & scripts without Docker (syntax, structure)
#
#  Usage:
#    ./verify_deployment.sh --live                    # Full health checks
#    ./verify_deployment.sh --sandbox                 # Config & syntax only
#    ./verify_deployment.sh --live --workspace DIR    # Custom workspace
#
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Colors ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check_pass() { echo -e "  ${GREEN}✓${NC} $*"; PASS=$((PASS + 1)); }
check_fail() { echo -e "  ${RED}✗${NC} $*"; FAIL=$((FAIL + 1)); }
check_warn() { echo -e "  ${YELLOW}△${NC} $*"; WARN=$((WARN + 1)); }

# ── Defaults ──────────────────────────────────────────────────────────────
MODE="live"
WORKSPACE="${HOME}/omninode-workspace"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --live)      MODE="live"; shift ;;
        --sandbox)   MODE="sandbox"; shift ;;
        --workspace) WORKSPACE="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $(basename "$0") [--live|--sandbox] [--workspace DIR]"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ============================================================================
# SANDBOX MODE — No Docker required
# ============================================================================
verify_sandbox() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║          Sandbox Verification (No Docker Required)          ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # ── 1. Shell Script Syntax ─────────────────────────────────────────────
    echo -e "${BOLD}1. Shell Script Syntax${NC}"
    for script in "${SCRIPT_DIR}"/{deploy_all,verify_deployment}.sh \
                  "${SCRIPT_DIR}"/lib/*.sh \
                  "${SCRIPT_DIR}"/phases/*.sh; do
        if [[ -f "$script" ]]; then
            if bash -n "$script" 2>/dev/null; then
                check_pass "$(basename "$script"): valid syntax"
            else
                check_fail "$(basename "$script"): syntax error!"
            fi
        fi
    done
    echo ""

    # ── 2. Configuration Validation ────────────────────────────────────────
    echo -e "${BOLD}2. Configuration Files${NC}"

    local env_template="${SCRIPT_DIR}/config/.env.template"
    if [[ -f "$env_template" ]]; then
        check_pass ".env.template exists"

        # Check for placeholder leaks
        if grep -q '__REPLACE_WITH__' "$env_template"; then
            check_fail ".env.template contains __REPLACE_WITH__ placeholders"
        else
            check_pass "No placeholder leaks in .env.template"
        fi

        # Count defined variables
        local var_count
        var_count=$(grep -cE '^[A-Z_]+=' "$env_template" || echo 0)
        check_pass "${var_count} environment variables defined"
    else
        check_fail ".env.template not found"
    fi
    echo ""

    # ── 3. Port Allocation (Conflict Check) ────────────────────────────────
    echo -e "${BOLD}3. Port Allocation${NC}"

    declare -A port_map
    local conflicts=0
    local ports=(
        5436 16379 19092 29092 8880 28080
        8085 8086 8087 8053 8091 8092 6006
        6333 6334 7687 7444 6379 8090 3000
    )

    for port in "${ports[@]}"; do
        if [[ -n "${port_map[$port]:-}" ]]; then
            check_fail "Port ${port} assigned multiple times!"
            conflicts=$((conflicts + 1))
        else
            port_map[$port]=1
        fi
    done

    if [[ $conflicts -eq 0 ]]; then
        check_pass "All ${#ports[@]} ports unique — no conflicts"
    fi
    echo ""

    # ── 4. Repository Structure Check ──────────────────────────────────────
    echo -e "${BOLD}4. Repository Structure${NC}"

    local repos=(
        omnibase_spi omnibase_core omnibase_infra
        omniintelligence omnimemory onex_change_control
        omnidash omniclaude
    )

    if [[ -d "$WORKSPACE" ]]; then
        for repo in "${repos[@]}"; do
            if [[ -d "${WORKSPACE}/${repo}" ]]; then
                check_pass "${repo} directory exists"
            else
                check_warn "${repo} not yet cloned"
            fi
        done
    else
        check_warn "Workspace ${WORKSPACE} does not exist — repos not yet cloned"
    fi
    echo ""

    # ── 5. File Structure Validation ───────────────────────────────────────
    echo -e "${BOLD}5. Deploy Package Structure${NC}"

    local required_files=(
        "deploy_all.sh"
        "verify_deployment.sh"
        "config/.env.template"
        "lib/common.sh"
        "lib/validation.sh"
        "lib/docker_helpers.sh"
        "phases/01_foundation.sh"
        "phases/02_infrastructure.sh"
        "phases/03_runtime_services.sh"
        "phases/04_intelligence_layer.sh"
        "phases/05_interface_layer.sh"
    )

    for f in "${required_files[@]}"; do
        if [[ -f "${SCRIPT_DIR}/${f}" ]]; then
            check_pass "${f}"
        else
            check_fail "${f} MISSING"
        fi
    done
    echo ""

    # ── 6. Script Executability ────────────────────────────────────────────
    echo -e "${BOLD}6. Script Permissions${NC}"

    for script in "${SCRIPT_DIR}/deploy_all.sh" "${SCRIPT_DIR}/verify_deployment.sh"; do
        if [[ -x "$script" ]]; then
            check_pass "$(basename "$script") is executable"
        else
            check_warn "$(basename "$script") is not executable — run: chmod +x $(basename "$script")"
        fi
    done
    echo ""

    # ── 7. Dry-Run Test ────────────────────────────────────────────────────
    echo -e "${BOLD}7. Dry-Run Smoke Test${NC}"

    if bash "${SCRIPT_DIR}/deploy_all.sh" --dry-run 2>/dev/null; then
        check_pass "deploy_all.sh --dry-run completed successfully"
    else
        check_fail "deploy_all.sh --dry-run failed!"
    fi
    echo ""
}

# ============================================================================
# LIVE MODE — Requires Running Services
# ============================================================================
verify_live() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           Live Deployment Verification                      ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # ── 1. Docker Status ───────────────────────────────────────────────────
    echo -e "${BOLD}1. Docker Status${NC}"

    if docker info &>/dev/null; then
        check_pass "Docker daemon running"
    else
        check_fail "Docker daemon not running"
        return 1
    fi

    local running_containers
    running_containers=$(docker ps --format '{{.Names}}' | grep -c 'omninode' || echo 0)
    if [[ "$running_containers" -gt 0 ]]; then
        check_pass "${running_containers} OmniNode containers running"
    else
        check_warn "No OmniNode containers found"
    fi
    echo ""

    # ── 2. Database Connectivity ───────────────────────────────────────────
    echo -e "${BOLD}2. Database Connectivity${NC}"

    local pg_port="${POSTGRES_PORT:-5436}"
    if pg_isready -h localhost -p "$pg_port" -U postgres &>/dev/null; then
        check_pass "PostgreSQL accepting connections on port ${pg_port}"

        # Check all 7 databases
        local databases=(
            omnibase_infra omniintelligence omniclaude omnimemory
            omninode_cloud omnidash_analytics
        )
        for db in "${databases[@]}"; do
            if psql -h localhost -p "$pg_port" -U postgres -d "$db" \
                -c "SELECT 1" &>/dev/null; then
                check_pass "Database '${db}' accessible"
            else
                check_warn "Database '${db}' not accessible"
            fi
        done
    else
        check_fail "PostgreSQL not responding on port ${pg_port}"
    fi
    echo ""

    # ── 3. Event Bus ──────────────────────────────────────────────────────
    echo -e "${BOLD}3. Event Bus (Redpanda/Kafka)${NC}"

    if (echo >/dev/tcp/localhost/"${REDPANDA_EXTERNAL_PORT:-29092}") 2>/dev/null; then
        check_pass "Redpanda broker reachable on port ${REDPANDA_EXTERNAL_PORT:-29092}"
    else
        check_fail "Redpanda not reachable"
    fi
    echo ""

    # ── 4. Cache ──────────────────────────────────────────────────────────
    echo -e "${BOLD}4. Cache (Valkey)${NC}"

    if redis-cli -h localhost -p "${VALKEY_PORT:-16379}" ping 2>/dev/null | grep -q PONG; then
        check_pass "Valkey responding (PONG) on port ${VALKEY_PORT:-16379}"
    else
        check_warn "Valkey not responding on port ${VALKEY_PORT:-16379}"
    fi
    echo ""

    # ── 5. Runtime Services ───────────────────────────────────────────────
    echo -e "${BOLD}5. Runtime Services${NC}"

    local services=(
        "8085:omninode-runtime"
        "8053:intelligence-api"
        "8091:contract-resolver"
        "6006:Phoenix OTLP"
    )

    for entry in "${services[@]}"; do
        local port="${entry%%:*}"
        local name="${entry#*:}"
        if curl -sf --max-time 3 "http://localhost:${port}/health" >/dev/null 2>&1 || \
           curl -sf --max-time 3 "http://localhost:${port}" >/dev/null 2>&1; then
            check_pass "${name} healthy on port ${port}"
        else
            check_warn "${name} not responding on port ${port}"
        fi
    done
    echo ""

    # ── 6. Memory Services ────────────────────────────────────────────────
    echo -e "${BOLD}6. Memory Services${NC}"

    if curl -sf --max-time 3 "http://localhost:${QDRANT_HTTP_PORT:-6333}" >/dev/null 2>&1; then
        check_pass "Qdrant healthy on port ${QDRANT_HTTP_PORT:-6333}"
    else
        check_warn "Qdrant not responding"
    fi

    if (echo >/dev/tcp/localhost/"${MEMGRAPH_BOLT_PORT:-7687}") 2>/dev/null; then
        check_pass "Memgraph reachable on port ${MEMGRAPH_BOLT_PORT:-7687}"
    else
        check_warn "Memgraph not reachable"
    fi

    if curl -sf --max-time 3 "http://localhost:${KREUZBERG_PORT:-8090}" >/dev/null 2>&1; then
        check_pass "Kreuzberg healthy on port ${KREUZBERG_PORT:-8090}"
    else
        check_warn "Kreuzberg not responding"
    fi
    echo ""

    # ── 7. OmniDash ──────────────────────────────────────────────────────
    echo -e "${BOLD}7. OmniDash${NC}"

    if curl -sf --max-time 5 "http://localhost:${OMNIDASH_PORT:-3000}" >/dev/null 2>&1; then
        check_pass "OmniDash accessible on port ${OMNIDASH_PORT:-3000}"
    else
        check_warn "OmniDash not responding on port ${OMNIDASH_PORT:-3000}"
    fi
    echo ""

    # ── 8. OmniClaude Tier ────────────────────────────────────────────────
    echo -e "${BOLD}8. OmniClaude Capability Tier${NC}"

    local cap_file="${HOME}/.claude/.onex_capabilities"
    if [[ -f "$cap_file" ]]; then
        local tier
        tier=$(cat "$cap_file" 2>/dev/null | head -1)
        check_pass "OmniClaude capability tier: ${tier}"
    else
        check_warn "Capability file not found — start a Claude Code session to trigger probe"
    fi
    echo ""
}

# ============================================================================
# SUMMARY
# ============================================================================
print_summary() {
    echo -e "${BOLD}══════════════════════════════════════════════════════════════${NC}"
    echo -e "  ${GREEN}✓ Passed: ${PASS}${NC}  |  ${RED}✗ Failed: ${FAIL}${NC}  |  ${YELLOW}△ Warnings: ${WARN}${NC}"
    echo -e "${BOLD}══════════════════════════════════════════════════════════════${NC}"
    echo ""

    if [[ $FAIL -gt 0 ]]; then
        echo -e "  ${RED}DEPLOYMENT HAS ISSUES — review failures above${NC}"
        exit 1
    elif [[ $WARN -gt 0 ]]; then
        echo -e "  ${YELLOW}DEPLOYMENT OK with warnings — review above${NC}"
        exit 0
    else
        echo -e "  ${GREEN}ALL CHECKS PASSED ✓${NC}"
        exit 0
    fi
}

# ── Main ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  OmniNode Deployment Verifier — Mode: ${MODE}${NC}"

case "$MODE" in
    sandbox) verify_sandbox ;;
    live)    verify_live ;;
    *)       echo "Unknown mode: $MODE"; exit 1 ;;
esac

print_summary

