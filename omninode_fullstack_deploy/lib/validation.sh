#!/usr/bin/env bash
# ============================================================================
# OmniNode Full-Stack Deploy — Pre-flight Validation
# validation.sh: Check all prerequisites before deployment
# ============================================================================

# ── Tool Version Check ─────────────────────────────────────────────────────
check_tool() {
    local cmd="$1"
    local min_version="$2"
    local label="${3:-$cmd}"

    if ! command -v "$cmd" &>/dev/null; then
        log_error "${label} is not installed. Please install it first."
        return 1
    fi
    log_info "${label} found: $(command -v "$cmd")"
    return 0
}

# ── Docker Version ─────────────────────────────────────────────────────────
check_docker() {
    check_tool docker "20.10" "Docker" || return 1

    local version
    version=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "0.0.0")
    local major minor
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)

    if [[ "$major" -lt 20 ]] || { [[ "$major" -eq 20 ]] && [[ "$minor" -lt 10 ]]; }; then
        log_error "Docker ${version} is too old. Minimum required: 20.10"
        return 1
    fi
    log_info "Docker version: ${version} ✓"

    # Check Docker Compose v2
    if ! docker compose version &>/dev/null; then
        log_error "Docker Compose v2 is not available. Install 'docker-compose-plugin'."
        return 1
    fi
    local compose_version
    compose_version=$(docker compose version --short 2>/dev/null || echo "0.0.0")
    log_info "Docker Compose version: ${compose_version} ✓"
}

# ── Python 3.12+ ───────────────────────────────────────────────────────────
check_python() {
    check_tool python3 "3.12" "Python 3" || return 1

    local version
    version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    local major minor
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)

    if [[ "$major" -lt 3 ]] || { [[ "$major" -eq 3 ]] && [[ "$minor" -lt 12 ]]; }; then
        log_error "Python ${version} is too old. Minimum required: 3.12"
        return 1
    fi
    log_info "Python version: ${version} ✓"
}

# ── Node.js 18+ ────────────────────────────────────────────────────────────
check_node() {
    check_tool node "18" "Node.js" || return 1

    local version
    version=$(node --version | sed 's/^v//')
    local major
    major=$(echo "$version" | cut -d. -f1)

    if [[ "$major" -lt 18 ]]; then
        log_error "Node.js ${version} is too old. Minimum required: 18"
        return 1
    fi
    log_info "Node.js version: ${version} ✓"
}

# ── uv Package Manager ────────────────────────────────────────────────────
check_uv() {
    if ! command -v uv &>/dev/null; then
        log_warn "uv not found. Installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    fi
    log_info "uv version: $(uv --version) ✓"
}

# ── Git ────────────────────────────────────────────────────────────────────
check_git() {
    check_tool git "2.0" "Git" || return 1
    log_info "Git version: $(git --version) ✓"
}

# ── Port Conflict Scan ─────────────────────────────────────────────────────
check_all_ports() {
    log_step "Scanning for port conflicts..."

    local ports=(
        "5436:PostgreSQL"
        "16379:Valkey (Infra)"
        "19092:Redpanda (Internal)"
        "29092:Redpanda (External)"
        "8880:Infisical"
        "28080:Keycloak"
        "8085:omninode-runtime"
        "8086:runtime-effects"
        "8087:agent-actions-consumer"
        "8053:intelligence-api"
        "8091:contract-resolver"
        "8092:skill-lifecycle-consumer"
        "6006:Phoenix OTLP"
        "6333:Qdrant"
        "6334:Qdrant gRPC"
        "7687:Memgraph"
        "6379:Valkey (Memory)"
        "8090:Kreuzberg"
        "3000:OmniDash"
    )

    local conflicts=0
    for entry in "${ports[@]}"; do
        local port="${entry%%:*}"
        local name="${entry#*:}"
        if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
            log_error "Port ${port} (${name}) is already in use!"
            conflicts=$((conflicts + 1))
        fi
    done

    if [[ $conflicts -gt 0 ]]; then
        log_error "${conflicts} port conflict(s) detected. Resolve before deploying."
        return 1
    fi

    log_info "All ${#ports[@]} ports are available ✓"
}

# ── Disk Space ─────────────────────────────────────────────────────────────
check_disk_space() {
    local min_gb="${1:-10}"
    local available_kb
    available_kb=$(df -k . | tail -1 | awk '{print $4}')
    local available_gb=$((available_kb / 1024 / 1024))

    if [[ $available_gb -lt $min_gb ]]; then
        log_error "Insufficient disk space: ${available_gb}GB available, ${min_gb}GB required"
        return 1
    fi
    log_info "Disk space: ${available_gb}GB available ✓"
}

# ── Memory Check ───────────────────────────────────────────────────────────
check_memory() {
    local min_gb="${1:-4}"
    local total_kb
    total_kb=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}')
    if [[ -z "$total_kb" ]]; then
        log_warn "Cannot determine system memory — skipping check"
        return 0
    fi
    local total_gb=$((total_kb / 1024 / 1024))

    if [[ $total_gb -lt $min_gb ]]; then
        log_warn "Low memory: ${total_gb}GB available, ${min_gb}GB recommended"
    else
        log_info "System memory: ${total_gb}GB ✓"
    fi
}

# ── Run All Pre-flight Checks ─────────────────────────────────────────────
run_preflight() {
    log_step "Running pre-flight checks..."
    echo ""

    local failures=0

    check_git        || failures=$((failures + 1))
    check_python     || failures=$((failures + 1))
    check_uv         || failures=$((failures + 1))
    check_docker     || failures=$((failures + 1))
    check_node       || failures=$((failures + 1))
    check_disk_space || failures=$((failures + 1))
    check_memory     || true  # non-fatal

    if [[ "$SKIP_PORT_CHECK" != "true" ]]; then
        check_all_ports || failures=$((failures + 1))
    fi

    echo ""
    if [[ $failures -gt 0 ]]; then
        log_error "${failures} pre-flight check(s) failed. Fix issues above before deploying."
        return 1
    fi

    log_info "All pre-flight checks passed ✓"
}

