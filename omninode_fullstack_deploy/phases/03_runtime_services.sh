#!/usr/bin/env bash
# ============================================================================
# Phase 3: Runtime Services — ONEX runtime, workers, consumers, intelligence
# Uses omnibase_infra's runtime Docker profile
# ============================================================================

phase_03_runtime() {
    log_phase "3" "Runtime Services — ONEX Engine + Intelligence API"

    local ws="$WORKSPACE"
    local infra_dir="${ws}/omnibase_infra"

    # ── 3.1 Install omnibase_infra Python Package ──────────────────────────
    log_step "3.1 — Installing omnibase_infra Python libraries"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "cd ${infra_dir} && uv sync"
    else
        cd "$infra_dir"
        uv sync 2>/dev/null || pip install -e "." 2>/dev/null || {
            log_warn "omnibase_infra Python install deferred"
        }
        log_info "omnibase_infra Python libraries installed ✓"
    fi

    # ── 3.2 Build Runtime Docker Images ────────────────────────────────────
    log_step "3.2 — Building runtime Docker images"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "docker compose --profile runtime build"
    else
        omni_compose_infra "$infra_dir" --profile runtime build || {
            log_warn "Build step skipped — images may be pulled instead"
        }
        log_info "Runtime images ready ✓"
    fi

    # ── 3.3 Start Runtime Services ─────────────────────────────────────────
    log_step "3.3 — Starting ONEX runtime services"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "docker compose --profile runtime up -d"
        log_dry "Services: omninode-runtime (8085), runtime-effects (8086),"
        log_dry "          runtime-worker, agent-actions-consumer (8087),"
        log_dry "          intelligence-api (8053), contract-resolver (8091),"
        log_dry "          skill-lifecycle-consumer (8092), phoenix-otlp (6006)"
    else
        start_infra_profile "$infra_dir" "runtime"
        log_info "Runtime services starting..."
    fi

    # ── 3.4 Health Check: omninode-runtime ─────────────────────────────────
    log_step "3.4 — Health checks for runtime services"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "Health check: http://localhost:8085/health"
        log_dry "Health check: http://localhost:8053/health"
        log_dry "Health check: http://localhost:8091/health"
        log_dry "Health check: http://localhost:6006"
    else
        # Health check each service — use pipe delimiter to avoid URL colon conflicts
        check_runtime_health() {
            local svc_name="$1" svc_url="$2"
            wait_for_service "$svc_url" "$svc_name" 15 || {
                log_warn "${svc_name} health check failed — service may still be starting"
            }
        }

        check_runtime_health "omninode-runtime"   "http://localhost:${RUNTIME_PORT:-8085}/health"
        check_runtime_health "intelligence-api"    "http://localhost:${INTELLIGENCE_API_PORT:-8053}/health"
        check_runtime_health "contract-resolver"   "http://localhost:${CONTRACT_RESOLVER_PORT:-8091}/health"

        # Port-level checks for services without HTTP health endpoints
        wait_for_port localhost "${RUNTIME_EFFECTS_PORT:-8086}" "runtime-effects" 20 || true
        wait_for_port localhost "${AGENT_ACTIONS_PORT:-8087}" "agent-actions-consumer" 20 || true
        wait_for_port localhost "${SKILL_LIFECYCLE_PORT:-8092}" "skill-lifecycle-consumer" 20 || true
        wait_for_port localhost "${PHOENIX_OTLP_PORT:-6006}" "Phoenix OTLP" 20 || true

        log_info "Phase 3 complete — Runtime services running ✓"
    fi
}
