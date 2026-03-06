#!/usr/bin/env bash
# ============================================================================
# Phase 4: Intelligence Layer — OmniMemory, OmniIntelligence, Change Control
# Memory persistence, 21 ONEX intelligence nodes, governance
# ============================================================================

phase_04_intelligence() {
    log_phase "4" "Intelligence Layer — Memory + Intelligence + Governance"

    local ws="$WORKSPACE"
    local org="OmniNode-ai"

    # ── 4.1 Deploy OmniMemory ──────────────────────────────────────────────
    log_step "4.1 — Deploying OmniMemory (Qdrant, Memgraph, Valkey, Kreuzberg)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "git clone https://github.com/${org}/omnimemory.git ${ws}/omnimemory"
        log_dry "docker compose -f ${ws}/omnimemory/docker-compose.yml up -d"
        log_dry "Services: Qdrant (6333), Memgraph (7687), Valkey (6379), Kreuzberg (8090)"
    else
        ensure_repo "$org" "omnimemory" "${ws}/omnimemory"
        export OMNI_MEMORY_DIR="${ws}/omnimemory"

        cd "${ws}/omnimemory"

        # Install Python package
        uv sync 2>/dev/null || pip install -e "." 2>/dev/null || {
            log_warn "omnimemory Python package install deferred"
        }

        # Start memory data services
        omni_compose_memory "${ws}/omnimemory" up -d

        # Health check memory services
        wait_for_port localhost "${QDRANT_HTTP_PORT:-6333}" "Qdrant" 20 || true
        wait_for_port localhost "${MEMGRAPH_BOLT_PORT:-7687}" "Memgraph" 20 || true
        wait_for_port localhost "${MEMORY_VALKEY_PORT:-6379}" "Valkey (Memory)" 15 || true
        wait_for_port localhost "${KREUZBERG_PORT:-8090}" "Kreuzberg" 15 || true

        log_info "OmniMemory services deployed ✓"
    fi

    # ── 4.2 Install OmniIntelligence ──────────────────────────────────────
    log_step "4.2 — Installing OmniIntelligence (21 ONEX nodes)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "git clone https://github.com/${org}/omniintelligence.git ${ws}/omniintelligence"
        log_dry "cd ${ws}/omniintelligence && uv sync --group all"
        log_dry "Nodes: orchestrators, reducers, compute, effects"
    else
        ensure_repo "$org" "omniintelligence" "${ws}/omniintelligence"
        cd "${ws}/omniintelligence"

        # Install with all dependency groups
        uv sync --group all 2>/dev/null || uv sync 2>/dev/null || {
            pip install -e ".[all]" 2>/dev/null || {
                log_warn "omniintelligence install had issues — some features may be limited"
            }
        }

        # Pre-commit hooks (optional, for development)
        if [[ "$PROFILE" == "full" ]] && command -v pre-commit &>/dev/null; then
            pre-commit install 2>/dev/null || true
        fi

        log_info "OmniIntelligence installed (21 nodes) ✓"
    fi

    # ── 4.2a Validate Plugin Discoverability (Gap #1) ─────────────────────
    log_step "4.2a — Validating PluginIntelligence is importable by runtime"
    validate_plugin_discoverability || log_warn "PluginIntelligence not discoverable — dashboard may be empty"

    # ── 4.3 Verify intelligence-api ────────────────────────────────────────
    log_step "4.3 — Verifying intelligence-api (from Phase 3)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "curl -sf http://localhost:8053/health"
    else
        wait_for_service \
            "http://localhost:${INTELLIGENCE_API_PORT:-8053}/health" \
            "intelligence-api" 10 || {
            log_warn "intelligence-api not responding — started in Phase 3"
        }
    fi

    # ── 4.4 Install ONEX Change Control ───────────────────────────────────
    log_step "4.4 — Installing ONEX Change Control (governance)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "git clone https://github.com/${org}/onex_change_control.git ${ws}/onex_change_control"
        log_dry "cd ${ws}/onex_change_control && uv sync"
    else
        ensure_repo "$org" "onex_change_control" "${ws}/onex_change_control"
        cd "${ws}/onex_change_control"

        # All OmniNode repos use uv as their package manager
        uv sync 2>/dev/null || {
            log_warn "onex_change_control uv sync deferred — falling back to pip"
            pip install -e "." 2>/dev/null || true
        }

        # Install pre-commit hooks (optional)
        if command -v pre-commit &>/dev/null; then
            uv run pre-commit install 2>/dev/null || true
            # Install pre-push hook (Gap #9)
            uv run pre-commit install --hook-type pre-push 2>/dev/null || true
        fi

        log_info "ONEX Change Control installed ✓"
    fi

    # ── 4.4a Validate ONEX Contracts (Gap #7) ─────────────────────────────
    log_step "4.4a — Running contract validators (validate-yaml + check-schema-purity)"
    validate_contracts || log_warn "Contract validation incomplete — check onex_change_control"

    log_info "Phase 4 complete — Intelligence layer deployed ✓"
}
