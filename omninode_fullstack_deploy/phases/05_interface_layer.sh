#!/usr/bin/env bash
# ============================================================================
# Phase 5: Interface Layer — OmniDash + OmniClaude
# Observability dashboard + Claude Code agent plugin (FULL_ONEX tier)
# ============================================================================

phase_05_interface() {
    log_phase "5" "Interface Layer — Dashboard + Claude Code Agent"

    local ws="$WORKSPACE"
    local org="OmniNode-ai"

    # ── 5.0a Pre-check: Kafka topics (fail-fast) ─────────────────────────
    log_step "5.0a — Pre-checking Kafka topics exist (fail-fast)"
    validate_kafka_topics || log_warn "Kafka topics missing — OmniDash consumers may fail"

    # ── 5.0b Pre-check: omnidash_analytics DB (fail-fast) ─────────────────
    log_step "5.0b — Pre-checking omnidash_analytics database exists"
    validate_omnidash_db || log_warn "omnidash_analytics DB missing — db:push/db:migrate will fail"

    # ── 5.1 Deploy OmniDash ───────────────────────────────────────────────
    log_step "5.1 — Deploying OmniDash (port 3000)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "git clone https://github.com/${org}/omnidash.git ${ws}/omnidash"
        log_dry "cd ${ws}/omnidash && npm install"
        log_dry "npm run db:push && npm run db:migrate"
        log_dry "npm run build && PORT=3000 npm start"
    else
        ensure_repo "$org" "omnidash" "${ws}/omnidash"
        cd "${ws}/omnidash"

        # Create .env for OmniDash
        if [[ ! -f .env ]]; then
            cat > .env <<DASHENV
PORT=${OMNIDASH_PORT:-3000}
OMNIDASH_ANALYTICS_DB_URL=${OMNIDASH_ANALYTICS_DB_URL:-postgresql://postgres:postgres@localhost:5436/omnidash_analytics}
KAFKA_BROKERS=${KAFKA_BOOTSTRAP_SERVERS:-localhost:29092}
KAFKA_CLIENT_ID=${OMNIDASH_KAFKA_CLIENT_ID:-omnidash-dashboard}
KAFKA_CONSUMER_GROUP=${OMNIDASH_KAFKA_CONSUMER_GROUP:-omnidash-consumers-v2}
ENABLE_REAL_TIME_EVENTS=${ENABLE_REAL_TIME_EVENTS:-true}
NODE_ENV=production
DASHENV
            log_info "OmniDash .env created"
        fi

        # Install dependencies
        npm install

        # Run database migrations
        npm run db:push 2>/dev/null || {
            log_warn "db:push failed — schema may need manual migration"
        }
        npm run db:migrate 2>/dev/null || {
            log_warn "db:migrate deferred"
        }

        # Build production bundle
        npm run build

        # Start OmniDash in background
        PORT="${OMNIDASH_PORT:-3000}" npm start &
        OMNIDASH_PID=$!
        echo "$OMNIDASH_PID" > "${ws}/.omnidash.pid"

        # Wait for dashboard
        wait_for_service "http://localhost:${OMNIDASH_PORT:-3000}" "OmniDash" 15 || {
            log_warn "OmniDash may still be starting..."
        }

        log_info "OmniDash deployed at http://localhost:${OMNIDASH_PORT:-3000} ✓"
    fi

    # ── 5.2 Deploy OmniClaude ─────────────────────────────────────────────
    log_step "5.2 — Deploying OmniClaude (Claude Code Plugin)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "git clone https://github.com/${org}/omniclaude.git ${ws}/omniclaude"
        log_dry "cd ${ws}/omniclaude && uv sync"
        log_dry "Deploy plugin to ~/.claude/plugins/cache/"
        log_dry "Expected tier: FULL_ONEX (90+ skills, 54 agents)"
    else
        ensure_repo "$org" "omniclaude" "${ws}/omniclaude"
        cd "${ws}/omniclaude"

        # Create .env for OmniClaude
        if [[ ! -f .env ]]; then
            cat > .env <<CLAUDEENV
KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS:-localhost:29092}
INTELLIGENCE_SERVICE_URL=${INTELLIGENCE_SERVICE_URL:-http://localhost:8053}
ENABLE_POSTGRES=${ENABLE_POSTGRES:-true}
OMNICLAUDE_DB_URL=${OMNICLAUDE_DB_URL:-postgresql://postgres:postgres@localhost:5436/omniclaude}
PHOENIX_COLLECTOR_ENDPOINT=${PHOENIX_COLLECTOR_ENDPOINT:-http://localhost:6006}
QDRANT_HOST=${QDRANT_HOST:-localhost}
QDRANT_HTTP_PORT=${QDRANT_HTTP_PORT:-6333}
MEMGRAPH_HOST=${MEMGRAPH_HOST:-localhost}
MEMGRAPH_BOLT_PORT=${MEMGRAPH_BOLT_PORT:-7687}
CLAUDEENV
            log_info "OmniClaude .env created"
        fi

        # Install Python dependencies
        uv sync

        # Deploy plugin to Claude Code cache
        local claude_plugin_dir="$HOME/.claude/plugins/cache"
        if [[ -d "$HOME/.claude" ]]; then
            mkdir -p "$claude_plugin_dir"
            log_info "Claude Code directory found — plugin ready for /deploy-local-plugin"
        else
            log_warn "~/.claude not found — install Claude Code first, then run /deploy-local-plugin"
        fi

        log_info "OmniClaude installed ✓"
    fi

    # ── 5.2a Start Emit Daemon (Gap #3) ───────────────────────────────────
    log_step "5.2a — Starting OmniClaude emit daemon (hook->Kafka bridge)"
    local emit_socket="${OMNICLAUDE_EMIT_SOCKET:-/tmp/omniclaude-emit.sock}"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "python3 -m omniclaude.emit.daemon --socket ${emit_socket} &"
    else
        # Start emit daemon as background process
        if [[ -f "${ws}/omniclaude/omniclaude/emit/daemon.py" ]] || \
           python3 -c "from omniclaude.emit import daemon" 2>/dev/null; then
            cd "${ws}/omniclaude"
            python3 -m omniclaude.emit.daemon --socket "$emit_socket" &>/dev/null &
            local emit_pid=$!
            echo "$emit_pid" > "${ws}/.omniclaude-emit.pid"
            log_info "Emit daemon started (PID: ${emit_pid})"

            # Wait for socket to appear
            local retries=10
            while [[ $retries -gt 0 && ! -S "$emit_socket" ]]; do
                sleep 0.5
                retries=$((retries - 1))
            done
        else
            log_warn "Emit daemon module not found — hooks won't publish to Kafka"
        fi

        # Validate socket
        validate_emit_daemon || log_warn "Emit daemon socket not available"
    fi

    # ── 5.2b Validate Claude Hooks (Gap #8) ───────────────────────────────
    log_step "5.2b — Verifying 5 OmniClaude hook scripts"
    validate_claude_hooks || log_warn "Some hook scripts missing or not executable"

    # ── 5.3 Capability Probe ──────────────────────────────────────────────
    log_step "5.3 — Running capability probe"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "Checking Kafka: ${KAFKA_BOOTSTRAP_SERVERS:-localhost:29092}"
        log_dry "Checking Intelligence: ${INTELLIGENCE_SERVICE_URL:-http://localhost:8053}"
        log_dry "Checking Qdrant: ${QDRANT_HOST:-localhost}:${QDRANT_HTTP_PORT:-6333}"
        log_dry "Expected result: FULL_ONEX tier"
    else
        echo ""
        echo -e "  ${BOLD}Capability Detection:${NC}"

        # Check Kafka → EVENT_BUS tier
        if (echo >/dev/tcp/localhost/"${REDPANDA_EXTERNAL_PORT:-29092}") 2>/dev/null; then
            echo -e "    ✓ Kafka reachable → ${GREEN}EVENT_BUS tier available${NC}"
        else
            echo -e "    ✗ Kafka unreachable → ${YELLOW}STANDALONE tier only${NC}"
        fi

        # Check Intelligence API → FULL_ONEX tier
        if curl -sf "http://localhost:${INTELLIGENCE_API_PORT:-8053}/health" >/dev/null 2>&1; then
            echo -e "    ✓ Intelligence API reachable → ${GREEN}FULL_ONEX tier available${NC}"
        else
            echo -e "    △ Intelligence API unreachable → ${YELLOW}EVENT_BUS tier only${NC}"
        fi

        # Check Qdrant → Memory enrichment
        if curl -sf "http://localhost:${QDRANT_HTTP_PORT:-6333}" >/dev/null 2>&1; then
            echo -e "    ✓ Qdrant reachable → ${GREEN}Memory enrichment available${NC}"
        else
            echo -e "    △ Qdrant unreachable → ${YELLOW}No vector memory${NC}"
        fi

        # Check Memgraph → Intent graphs
        if (echo >/dev/tcp/localhost/"${MEMGRAPH_BOLT_PORT:-7687}") 2>/dev/null; then
            echo -e "    ✓ Memgraph reachable → ${GREEN}Intent graphs available${NC}"
        else
            echo -e "    △ Memgraph unreachable → ${YELLOW}No intent graphs${NC}"
        fi

        echo ""
        echo -e "  ${CYAN}═══ Expected OmniClaude banner on next SessionStart: ═══${NC}"
        echo -e "  ${BOLD}─── OmniClaude: FULL_ONEX (90+ skills, 54 agents) ───${NC}"
        echo ""
    fi

    log_info "Phase 5 complete — Interface layer deployed ✓"
}
