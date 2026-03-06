#!/usr/bin/env bash
# ============================================================================
# OmniNode Full-Stack Deploy — Docker / Compose Helpers
# docker_helpers.sh: Wrappers for consistent Docker Compose usage
# ============================================================================

# ── Constants ──────────────────────────────────────────────────────────────
OMNI_COMPOSE_PROJECT="omninode"
OMNI_NETWORK="omninode-network"

# ── Ensure Docker Network ─────────────────────────────────────────────────
ensure_network() {
    if ! docker network inspect "$OMNI_NETWORK" &>/dev/null; then
        log_step "Creating Docker network: ${OMNI_NETWORK}"
        docker network create "$OMNI_NETWORK" 2>/dev/null || true
    fi
}

# ── Compose Wrapper for omnibase_infra ─────────────────────────────────────
# CRITICAL: Never run `docker compose up` directly from docker/ directory
# Always invoke from the project root with explicit --project-directory
omni_compose_infra() {
    local infra_dir="$1"; shift
    local env_file="${infra_dir}/docker/.env"
    local compose_file="${infra_dir}/docker/docker-compose.infra.yml"

    docker compose \
        --project-name "${OMNI_COMPOSE_PROJECT}-infra" \
        --project-directory "${infra_dir}" \
        -f "$compose_file" \
        --env-file "$env_file" \
        "$@"
}

# ── Compose Wrapper for omnimemory ─────────────────────────────────────────
omni_compose_memory() {
    local memory_dir="$1"; shift
    local compose_file="${memory_dir}/docker-compose.yml"

    docker compose \
        --project-name "${OMNI_COMPOSE_PROJECT}-memory" \
        --project-directory "${memory_dir}" \
        -f "$compose_file" \
        "$@"
}

# ── Profile-Aware Service Start ────────────────────────────────────────────
# Profiles from docker-compose.infra.yml:
#   (default)  → PostgreSQL, Redpanda, Valkey
#   runtime    → ONEX runtime services
#   secrets    → Infisical
#   auth       → Keycloak
#   consul     → Consul
#   full       → All services
#   bootstrap  → Infrastructure + secrets

start_infra_profile() {
    local infra_dir="$1"
    local profile="$2"

    log_step "Starting infrastructure with profile: ${profile}"

    if [[ "$profile" == "default" ]]; then
        omni_compose_infra "$infra_dir" up -d
    else
        omni_compose_infra "$infra_dir" --profile "$profile" up -d
    fi
}

# ── Container Health Status ────────────────────────────────────────────────
check_container_health() {
    local container_name="$1"
    local status
    status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "missing")

    case "$status" in
        healthy)   log_info "${container_name}: healthy ✓"; return 0 ;;
        unhealthy) log_error "${container_name}: unhealthy ✗"; return 1 ;;
        starting)  log_warn "${container_name}: starting..."; return 2 ;;
        missing)   log_error "${container_name}: not found"; return 1 ;;
        *)         log_warn "${container_name}: status=${status}"; return 2 ;;
    esac
}

# ── Wait for Container to be Healthy ───────────────────────────────────────
wait_container_healthy() {
    local container_name="$1"
    local max_attempts="${2:-30}"
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if check_container_health "$container_name"; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 3
    done

    log_error "${container_name} did not become healthy in time"
    return 1
}

# ── Stop All OmniNode Services ─────────────────────────────────────────────
stop_all() {
    log_step "Stopping all OmniNode services..."

    # Stop infra
    if [[ -n "${OMNI_INFRA_DIR:-}" ]]; then
        omni_compose_infra "$OMNI_INFRA_DIR" --profile full down 2>/dev/null || true
    fi

    # Stop memory
    if [[ -n "${OMNI_MEMORY_DIR:-}" ]]; then
        omni_compose_memory "$OMNI_MEMORY_DIR" down 2>/dev/null || true
    fi

    log_info "All OmniNode services stopped"
}

# ── Docker Image Build with Labels ─────────────────────────────────────────
build_with_labels() {
    local context_dir="$1"
    local image_name="$2"
    local vcs_ref
    vcs_ref=$(git -C "$context_dir" rev-parse --short HEAD 2>/dev/null || echo "unknown")

    log_step "Building Docker image: ${image_name} (VCS_REF=${vcs_ref})"

    docker build \
        --build-arg "VCS_REF=${vcs_ref}" \
        --build-arg "BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        -t "$image_name" \
        "$context_dir"
}

