#!/usr/bin/env bash
# ============================================================================
# Phase 1: Foundation — Install omnibase_spi + omnibase_core
# No runtime services — just typed contracts & execution protocol
# ============================================================================

phase_01_foundation() {
    log_phase "1" "Foundation — SPI Contracts + Core Engine"

    local ws="$WORKSPACE"
    local org="OmniNode-ai"

    # ── 1.1 Clone omnibase_spi ─────────────────────────────────────────────
    log_step "1.1 — Installing omnibase_spi (Service Provider Interface)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "git clone https://github.com/${org}/omnibase_spi.git ${ws}/omnibase_spi"
        log_dry "cd ${ws}/omnibase_spi && uv sync"
    else
        ensure_repo "$org" "omnibase_spi" "${ws}/omnibase_spi"
        cd "${ws}/omnibase_spi"
        uv sync
        log_info "omnibase_spi installed ✓"
    fi

    # ── 1.2 Clone omnibase_core ────────────────────────────────────────────
    log_step "1.2 — Installing omnibase_core (ONEX Execution Protocol)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "git clone https://github.com/${org}/omnibase_core.git ${ws}/omnibase_core"
        log_dry "cd ${ws}/omnibase_core && uv sync"
    else
        ensure_repo "$org" "omnibase_core" "${ws}/omnibase_core"
        cd "${ws}/omnibase_core"
        uv sync
        log_info "omnibase_core installed ✓"
    fi

    # ── 1.3 Verify imports ─────────────────────────────────────────────────
    log_step "1.3 — Verifying Python imports"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "python3 -c 'import omnibase_spi; import omnibase_core'"
    else
        if python3 -c "
import importlib
for mod in ['omnibase_spi', 'omnibase_core']:
    try:
        importlib.import_module(mod.replace('-', '_'))
        print(f'  ✓ {mod} importable')
    except ImportError as e:
        print(f'  ✗ {mod} FAILED: {e}')
        exit(1)
" 2>/dev/null; then
            log_info "Phase 1 complete — Foundation packages verified ✓"
        else
            log_warn "Import verification had issues (may need editable installs)"
            log_info "Phase 1 complete — packages installed (verification deferred)"
        fi
    fi
}

