#!/usr/bin/env bash
# ============================================================================
# OmniNode Full-Stack Deploy — Shared Library
# common.sh: Logging, health checks, retry logic, utility functions
# ============================================================================
set -euo pipefail

# ── Color Palette ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ── Logging ────────────────────────────────────────────────────────────────
log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${CYAN}[STEP]${NC}  ${BOLD}$*${NC}"; }
log_phase() {
    local phase_num="$1"; shift
    echo ""
    echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║  Phase ${phase_num}: $*${NC}"
    echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}
log_dry() { echo -e "${DIM}[DRY-RUN]${NC} $*"; }

# ── Banner ─────────────────────────────────────────────────────────────────
print_banner() {
    echo -e "${CYAN}"
    cat <<'BANNER'
   ____                  _ _   _           _
  / __ \                (_) \ | |         | |
 | |  | |_ __ ___  _ __  _|  \| | ___  __| | ___
 | |  | | '_ ` _ \| '_ \| | . ` |/ _ \/ _` |/ _ \
 | |__| | | | | | | | | | | |\  | (_) | (_| |  __/
  \____/|_| |_| |_|_| |_|_|_| \_|\___/ \__,_|\___|
    Full-Stack Deployment Orchestrator
BANNER
    echo -e "${NC}"
    echo -e "${DIM}  8 repositories • 17+ services • 5 phases • 1 command${NC}"
    echo ""
}

# ── Health Check with Exponential Backoff ──────────────────────────────────
# Usage: wait_for_service <url> <service_name> [max_attempts] [interval_secs]
wait_for_service() {
    local url="$1"
    local name="$2"
    local max_attempts="${3:-15}"
    local interval="${4:-4}"
    local attempt=0

    log_step "Waiting for ${name} at ${url}..."

    while [[ $attempt -lt $max_attempts ]]; do
        if curl -sf --max-time 5 "$url" >/dev/null 2>&1; then
            log_info "${name} is healthy ✓"
            return 0
        fi
        attempt=$((attempt + 1))
        local wait_time=$((interval + (attempt / 3)))
        echo -e "  ${DIM}Attempt ${attempt}/${max_attempts} — retrying in ${wait_time}s...${NC}"
        sleep "$wait_time"
    done

    log_error "${name} failed health check after ${max_attempts} attempts at ${url}"
    return 1
}

# ── TCP Port Check ─────────────────────────────────────────────────────────
# Usage: wait_for_port <host> <port> <name> [max_attempts]
wait_for_port() {
    local host="$1"
    local port="$2"
    local name="$3"
    local max_attempts="${4:-30}"
    local attempt=0

    log_step "Waiting for ${name} on ${host}:${port}..."

    while [[ $attempt -lt $max_attempts ]]; do
        if (echo >/dev/tcp/"$host"/"$port") 2>/dev/null; then
            log_info "${name} is listening on port ${port} ✓"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    log_error "${name} not listening on ${host}:${port} after ${max_attempts} attempts"
    return 1
}

# ── Retry Wrapper ──────────────────────────────────────────────────────────
# Usage: retry <max_attempts> <command> [args...]
retry() {
    local max="$1"; shift
    local attempt=1

    while [[ $attempt -le $max ]]; do
        if "$@"; then
            return 0
        fi
        log_warn "Attempt ${attempt}/${max} failed for: $*"
        attempt=$((attempt + 1))
        sleep 3
    done

    log_error "All ${max} attempts failed for: $*"
    return 1
}

# ── Generate Secure Random Password ───────────────────────────────────────
gen_password() {
    local length="${1:-32}"
    openssl rand -hex "$((length / 2))"
}

# ── Clone or Update a Repository ──────────────────────────────────────────
# Usage: ensure_repo <org> <repo_name> <dest_dir>
ensure_repo() {
    local org="$1"
    local repo="$2"
    local dest="$3"

    if [[ -d "$dest/.git" ]]; then
        log_info "${repo} already cloned at ${dest} — pulling latest"
        git -C "$dest" pull --ff-only 2>/dev/null || true
    else
        log_step "Cloning ${org}/${repo}..."
        git clone --depth 1 "https://github.com/${org}/${repo}.git" "$dest"
    fi
}

# ── Check Port Availability ───────────────────────────────────────────────
check_port_free() {
    local port="$1"
    local name="${2:-unknown}"
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        log_error "Port ${port} (${name}) is already in use!"
        return 1
    fi
    return 0
}

# ── Summary Table Printer ─────────────────────────────────────────────────
print_service_table() {
    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║                    Service Summary                              ║${NC}"
    echo -e "${BOLD}╠═══════════════════════════╦════════╦═══════════════════════════╣${NC}"
    printf  "${BOLD}║ %-25s ║ %-6s ║ %-25s ║${NC}\n" "Service" "Port" "URL"
    echo -e "${BOLD}╠═══════════════════════════╬════════╬═══════════════════════════╣${NC}"
}

print_service_row() {
    local name="$1"
    local port="$2"
    local url="$3"
    printf "║ %-25s ║ %-6s ║ %-25s ║\n" "$name" "$port" "$url"
}

print_service_table_end() {
    echo -e "${BOLD}╚═══════════════════════════╩════════╩═══════════════════════════╝${NC}"
    echo ""
}

# ── Timestamp ──────────────────────────────────────────────────────────────
timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

# ── Trap Handler ───────────────────────────────────────────────────────────
cleanup_on_exit() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        echo ""
        log_error "Deployment failed at $(timestamp) with exit code ${exit_code}"
        log_error "Review the logs above for details."
        echo ""
    fi
}

trap cleanup_on_exit EXIT

