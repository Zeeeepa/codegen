#!/usr/bin/env bash
# ============================================================================
# OmniNode Full-Stack Deploy — Pre-flight & Post-deploy Validation
# validation.sh: Check all prerequisites + service postconditions
#
# Functions:
#   Pre-flight:  check_tool, check_docker, check_python, check_node,
#                check_uv, check_git, check_all_ports, check_disk_space,
#                check_memory, run_preflight
#
#   Post-deploy: validate_db_roles, validate_kafka_topics,
#                validate_plugin_discoverability, validate_emit_daemon,
#                validate_claude_hooks, validate_infisical_bootstrap,
#                validate_contracts, validate_omnidash_db
# ============================================================================

# ── Tool Version Check ───────────────────────────────────────────────────
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

# ── Docker Version ───────────────────────────────────────────────────────
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
    log_info "Docker version: ${version} [OK]"

    # Check Docker Compose v2
    if ! docker compose version &>/dev/null; then
        log_error "Docker Compose v2 is not available. Install 'docker-compose-plugin'."
        return 1
    fi
    local compose_version
    compose_version=$(docker compose version --short 2>/dev/null || echo "0.0.0")
    log_info "Docker Compose version: ${compose_version} [OK]"
}

# ── Python 3.12+ ─────────────────────────────────────────────────────────
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
    log_info "Python version: ${version} [OK]"
}

# ── Node.js 18+ ──────────────────────────────────────────────────────────
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
    log_info "Node.js version: ${version} [OK]"
}

# ── uv Package Manager ──────────────────────────────────────────────────
check_uv() {
    if ! command -v uv &>/dev/null; then
        log_warn "uv not found. Installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    fi
    log_info "uv version: $(uv --version) [OK]"
}

# ── Git ──────────────────────────────────────────────────────────────────
check_git() {
    check_tool git "2.0" "Git" || return 1
    log_info "Git version: $(git --version) [OK]"
}

# ── Port Conflict Scan ───────────────────────────────────────────────────
check_all_ports() {
    log_step "Scanning for port conflicts..."

    local ports=(
        "5436:PostgreSQL"
        "16379:Valkey (Infra Cache)"
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
        "6333:Qdrant HTTP"
        "6334:Qdrant gRPC"
        "7687:Memgraph Bolt"
        "7444:Memgraph HTTP"
        "6379:Valkey (Memory)"
        "8090:Kreuzberg"
        "3000:OmniDash"
        "28500:Consul"
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

    log_info "All ${#ports[@]} ports are available [OK]"
}

# ── Disk Space ───────────────────────────────────────────────────────────
check_disk_space() {
    local min_gb="${1:-10}"
    local available_kb
    available_kb=$(df -k . | tail -1 | awk '{print $4}')
    local available_gb=$((available_kb / 1024 / 1024))

    if [[ $available_gb -lt $min_gb ]]; then
        log_error "Insufficient disk space: ${available_gb}GB available, ${min_gb}GB required"
        return 1
    fi
    log_info "Disk space: ${available_gb}GB available [OK]"
}

# ── Memory Check ─────────────────────────────────────────────────────────
check_memory() {
    local min_gb="${1:-4}"
    local total_kb
    total_kb=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}')
    if [[ -z "$total_kb" ]]; then
        log_warn "Cannot determine system memory -- skipping check"
        return 0
    fi
    local total_gb=$((total_kb / 1024 / 1024))

    if [[ $total_gb -lt $min_gb ]]; then
        log_warn "Low memory: ${total_gb}GB available, ${min_gb}GB recommended"
    else
        log_info "System memory: ${total_gb}GB [OK]"
    fi
}

# ── Run All Pre-flight Checks ────────────────────────────────────────────
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

    log_info "All pre-flight checks passed [OK]"
}


# ============================================================================
# POST-DEPLOY VALIDATION FUNCTIONS
# ============================================================================

# ── Database Role Validation (Critical Gap #4) ──────────────────────────
# Verifies all 6 least-privilege roles exist after migrations.
# Roles: role_omnibase, role_omniintelligence, role_omniclaude,
#        role_omnimemory, role_omninode, role_omnidash
validate_db_roles() {
    local pg_host="${POSTGRES_HOST:-localhost}"
    local pg_port="${POSTGRES_PORT:-5436}"
    local pg_user="${POSTGRES_USER:-postgres}"

    local roles=(
        "role_omnibase"
        "role_omniintelligence"
        "role_omniclaude"
        "role_omnimemory"
        "role_omninode"
        "role_omnidash"
    )

    if [[ "${DRY_RUN:-true}" == "true" ]]; then
        log_dry "Validate ${#roles[@]} database roles exist in PostgreSQL"
        return 0
    fi

    local missing=0
    for role in "${roles[@]}"; do
        if psql -h "$pg_host" -p "$pg_port" -U "$pg_user" -tAc \
            "SELECT 1 FROM pg_roles WHERE rolname='${role}'" 2>/dev/null | grep -q 1; then
            log_info "  Role '${role}' exists [OK]"
        else
            log_error "  Role '${role}' MISSING -- migration may have failed"
            missing=$((missing + 1))
        fi
    done

    if [[ $missing -gt 0 ]]; then
        log_error "${missing}/${#roles[@]} database roles missing. Check migration logs."
        return 1
    fi
    log_info "All ${#roles[@]} database roles validated [OK]"
}

# ── Kafka Topic Validation (Critical Gap #2) ────────────────────────────
# Creates and validates 4 OmniDash-required Kafka topics.
# Topics: agent-routing-decisions, agent-transformation-events,
#         router-performance-metrics, agent-actions
validate_kafka_topics() {
    local broker="${KAFKA_BOOTSTRAP_SERVERS:-localhost:29092}"
    local topics=(
        "agent-routing-decisions"
        "agent-transformation-events"
        "router-performance-metrics"
        "agent-actions"
    )

    if [[ "${DRY_RUN:-true}" == "true" ]]; then
        log_dry "Create and validate ${#topics[@]} Kafka topics: ${topics[*]}"
        return 0
    fi

    local missing=0
    for topic in "${topics[@]}"; do
        # Create topic idempotently (Redpanda rpk or kafka-topics.sh)
        if command -v rpk &>/dev/null; then
            rpk topic create "$topic" --brokers "$broker" 2>/dev/null || true
        else
            docker exec omninode-redpanda rpk topic create "$topic" 2>/dev/null || true
        fi

        # Verify topic exists
        local exists
        if command -v rpk &>/dev/null; then
            exists=$(rpk topic list --brokers "$broker" 2>/dev/null | grep -c "^${topic}\b" || echo 0)
        else
            exists=$(docker exec omninode-redpanda rpk topic list 2>/dev/null | grep -c "^${topic}\b" || echo 0)
        fi

        if [[ "$exists" -gt 0 ]]; then
            log_info "  Topic '${topic}' exists [OK]"
        else
            log_error "  Topic '${topic}' MISSING after creation attempt"
            missing=$((missing + 1))
        fi
    done

    if [[ $missing -gt 0 ]]; then
        log_error "${missing}/${#topics[@]} Kafka topics missing. Check Redpanda status."
        return 1
    fi
    log_info "All ${#topics[@]} Kafka topics validated [OK]"
}

# ── Plugin Discoverability (Critical Gap #1) ─────────────────────────────
# Verifies OmniIntelligence PluginIntelligence is importable by runtime.
validate_plugin_discoverability() {
    local workspace="${WORKSPACE:-$HOME/omninode-workspace}"
    local module="${OMNIINTELLIGENCE_PLUGIN_MODULE:-omniintelligence.runtime.plugin}"

    if [[ "${DRY_RUN:-true}" == "true" ]]; then
        log_dry "Validate PluginIntelligence import from ${module}"
        return 0
    fi

    if python3 -c "from ${module} import PluginIntelligence; print('OK')" 2>/dev/null | grep -q OK; then
        log_info "PluginIntelligence importable from ${module} [OK]"
    else
        log_error "PluginIntelligence NOT importable from ${module}"
        log_error "  Runtime won't discover intelligence nodes. Check omniintelligence install."
        return 1
    fi
}

# ── Emit Daemon Validation (Critical Gap #3) ─────────────────────────────
# Verifies OmniClaude emit daemon is running and socket is available.
validate_emit_daemon() {
    local socket="${OMNICLAUDE_EMIT_SOCKET:-/tmp/omniclaude-emit.sock}"

    if [[ "${DRY_RUN:-true}" == "true" ]]; then
        log_dry "Validate emit daemon socket at ${socket}"
        return 0
    fi

    if [[ -S "$socket" ]]; then
        log_info "Emit daemon socket present at ${socket} [OK]"
    else
        log_error "Emit daemon socket NOT found at ${socket}"
        log_error "  Hooks won't publish to Kafka. Start the emit daemon."
        return 1
    fi
}

# ── Claude Hooks Validation (High Gap #8) ────────────────────────────────
# Verifies all 5 OmniClaude hook scripts exist and are executable.
validate_claude_hooks() {
    local workspace="${WORKSPACE:-$HOME/omninode-workspace}"
    local hooks_dir="${OMNICLAUDE_HOOKS_DIR:-${workspace}/omniclaude/hooks}"

    local hooks=(
        "session_start.sh"
        "user_prompt_submit.sh"
        "pre_tool_use.sh"
        "post_tool_use.sh"
        "session_end.sh"
    )

    if [[ "${DRY_RUN:-true}" == "true" ]]; then
        log_dry "Validate ${#hooks[@]} Claude hook scripts in ${hooks_dir}"
        return 0
    fi

    local missing=0
    for hook in "${hooks[@]}"; do
        local path="${hooks_dir}/${hook}"
        if [[ -f "$path" && -x "$path" ]]; then
            log_info "  Hook '${hook}' exists and is executable [OK]"
        elif [[ -f "$path" ]]; then
            log_warn "  Hook '${hook}' exists but is NOT executable -- fixing"
            chmod +x "$path"
        else
            log_error "  Hook '${hook}' MISSING at ${path}"
            missing=$((missing + 1))
        fi
    done

    if [[ $missing -gt 0 ]]; then
        log_error "${missing}/${#hooks[@]} hook scripts missing."
        return 1
    fi
    log_info "All ${#hooks[@]} Claude hooks validated [OK]"
}

# ── Infisical Bootstrap Validation (High Gap #6) ─────────────────────────
# Validates the 6-step Infisical bootstrap completed correctly.
validate_infisical_bootstrap() {
    local addr="${INFISICAL_ADDR-http://localhost:8880}"

    if [[ "${DRY_RUN:-true}" == "true" ]]; then
        log_dry "Validate Infisical 6-step bootstrap at ${addr}"
        return 0
    fi

    if [[ -z "$addr" ]]; then
        log_info "Infisical disabled (INFISICAL_ADDR empty) -- skipping validation"
        return 0
    fi

    # Bootstrap chain (from actual bootstrap-infisical.sh, OMN-2287):
    #   Step 1:   PostgreSQL starts (POSTGRES_PASSWORD from .env)
    #   Step 1b:  Pending migrations applied (run-migrations.py)
    #   Step 1c:  Cross-repo tables provisioned (provision-cross-repo-tables.py)
    #   Step 2:   Valkey starts
    #   Step 3:   Infisical starts (depends_on: postgres + valkey healthy)
    #   Step 3.5: Keycloak starts (--profile auth)
    #   Step 4:   Identity provisioning (first-time only)
    #   Step 5:   Seed runs (populates Infisical from contracts + .env values)
    #   Step 6:   Runtime services start (prefetch from Infisical)

    local pass=0
    local total=4

    # Check 1: Health endpoint
    if curl -sf --max-time 5 "${addr}/api/status" >/dev/null 2>&1; then
        log_info "Infisical responding at ${addr} [OK]"
        pass=$((pass + 1))
    else
        log_error "Infisical NOT responding at ${addr}"
        return 1
    fi

    # Check 2: Machine identity configured (Step 4 output)
    if [[ -n "${INFISICAL_CLIENT_ID:-}" && -n "${INFISICAL_CLIENT_SECRET:-}" ]]; then
        log_info "Infisical machine identity configured [OK]"
        pass=$((pass + 1))
    else
        log_warn "Infisical machine identity not configured (INFISICAL_CLIENT_ID/SECRET empty)"
        log_warn "  Run: ${OMNI_INFRA_DIR:-omnibase_infra}/scripts/bootstrap-infisical.sh"
    fi

    # Check 3: ~/.omnibase/.env exists (created by bootstrap Step 4/5)
    if [[ -f "${HOME}/.omnibase/.env" ]]; then
        log_info "~/.omnibase/.env exists (bootstrap credentials file) [OK]"
        pass=$((pass + 1))
    else
        log_warn "~/.omnibase/.env not found — bootstrap may not have completed"
        log_warn "  Expected after running: scripts/bootstrap-infisical.sh"
    fi

    # Check 4: DB connection URI set for Infisical
    if [[ -n "${INFISICAL_DB_CONNECTION_URI:-}" ]]; then
        log_info "INFISICAL_DB_CONNECTION_URI set [OK]"
        pass=$((pass + 1))
    else
        log_warn "INFISICAL_DB_CONNECTION_URI not set"
    fi

    log_info "Infisical bootstrap: ${pass}/${total} checks passed"
    [[ $pass -ge 2 ]]  # At minimum health + one config check
}

# ── Autoheal Validation ──────────────────────────────────────────────────────
# willfarrell/autoheal:1.2.0 watches containers with label autoheal=true
# Active in: runtime and full profiles
validate_autoheal() {
    if [[ "${DRY_RUN:-true}" == "true" ]]; then
        log_dry "Validate autoheal container running"
        return 0
    fi

    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "autoheal"; then
        log_info "Autoheal container running [OK]"

        # Check it has access to docker socket
        if docker inspect omnibase-infra-autoheal 2>/dev/null |            grep -q "/var/run/docker.sock"; then
            log_info "Autoheal has Docker socket access [OK]"
        else
            log_warn "Autoheal may not have Docker socket access"
        fi
        return 0
    else
        log_info "Autoheal not running (only active in runtime/full profiles)"
        return 0
    fi
}

# ── Keycloak Validation ──────────────────────────────────────────────────────
validate_keycloak() {
    local addr="${KEYCLOAK_ADDR:-http://localhost:28080}"

    if [[ "${DRY_RUN:-true}" == "true" ]]; then
        log_dry "Validate Keycloak at ${addr}"
        return 0
    fi

    if [[ "${SKIP_KEYCLOAK:-false}" == "true" ]]; then
        log_info "Keycloak skipped (--skip-keycloak)"
        return 0
    fi

    if curl -sf --max-time 5 "${addr}" >/dev/null 2>&1; then
        log_info "Keycloak responding at ${addr} [OK]"
    else
        log_warn "Keycloak not responding at ${addr} (may need --profile auth)"
    fi
}

# ── Contract Validation (High Gap #7) ────────────────────────────────────
# Runs onex_change_control validators: validate-yaml + check-schema-purity.
validate_contracts() {
    local workspace="${WORKSPACE:-$HOME/omninode-workspace}"
    local cc_dir="${workspace}/onex_change_control"

    if [[ "${DRY_RUN:-true}" == "true" ]]; then
        log_dry "Run onex_change_control contract validators"
        return 0
    fi

    if [[ ! -d "$cc_dir" ]]; then
        log_warn "onex_change_control not found at ${cc_dir} -- skipping"
        return 0
    fi

    cd "$cc_dir" || return 1

    if poetry run validate-yaml 2>/dev/null; then
        log_info "YAML contract validation passed [OK]"
    else
        log_error "YAML contract validation FAILED"
        return 1
    fi

    if poetry run check-schema-purity 2>/dev/null; then
        log_info "Schema purity check passed [OK]"
    else
        log_error "Schema purity check FAILED"
        return 1
    fi
}

# ── OmniDash Analytics DB Validation (Critical Gap #5) ───────────────────
# Verifies omnidash_analytics database exists before OmniDash starts.
validate_omnidash_db() {
    local pg_host="${POSTGRES_HOST:-localhost}"
    local pg_port="${POSTGRES_PORT:-5436}"
    local pg_user="${POSTGRES_USER:-postgres}"
    local db_name="omnidash_analytics"

    if [[ "${DRY_RUN:-true}" == "true" ]]; then
        log_dry "Validate database '${db_name}' exists"
        return 0
    fi

    if psql -h "$pg_host" -p "$pg_port" -U "$pg_user" -lqt 2>/dev/null | \
        cut -d\| -f1 | grep -qw "$db_name"; then
        log_info "Database '${db_name}' exists [OK]"
    else
        log_error "Database '${db_name}' NOT found"
        log_error "  OmniDash db:push/db:migrate will fail. Check migration 000-036."
        return 1
    fi
}

