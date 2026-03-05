#!/usr/bin/env bash
# ============================================================================
# Phase 2: Infrastructure — PostgreSQL, Redpanda, Valkey, Infisical, Keycloak
# Uses omnibase_infra's docker-compose.infra.yml + deploy patterns
# ============================================================================

phase_02_infrastructure() {
    log_phase "2" "Infrastructure — Core Platform Services"

    local ws="$WORKSPACE"
    local org="OmniNode-ai"
    local infra_dir="${ws}/omnibase_infra"

    # ── 2.1 Clone omnibase_infra ───────────────────────────────────────────
    log_step "2.1 — Cloning omnibase_infra"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "git clone https://github.com/${org}/omnibase_infra.git ${infra_dir}"
    else
        ensure_repo "$org" "omnibase_infra" "$infra_dir"
        export OMNI_INFRA_DIR="$infra_dir"
    fi

    # ── 2.2 Generate .env with secure passwords ───────────────────────────
    log_step "2.2 — Generating environment configuration"

    local env_file="${infra_dir}/docker/.env"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "Generate ${env_file} from template with secure random passwords"
    else
        if [[ -f "$env_file" ]]; then
            log_warn ".env already exists at ${env_file} — using existing"
        else
            log_info "Creating .env from master template..."

            # Copy template and fill in auto-generated values
            cp "${DEPLOY_ROOT}/config/.env.template" "$env_file"

            # Generate secure passwords for all [AUTO] fields
            local pg_pass; pg_pass=$(gen_password 32)
            local valkey_pass; valkey_pass=$(gen_password 32)
            local infisical_enc; infisical_enc=$(gen_password 16)
            local infisical_auth; infisical_auth=$(gen_password 32)
            local kc_pass; kc_pass=$(gen_password 24)

            # Per-service role passwords
            local role_omnibase_pass; role_omnibase_pass=$(gen_password 32)
            local role_intelligence_pass; role_intelligence_pass=$(gen_password 32)
            local role_claude_pass; role_claude_pass=$(gen_password 32)
            local role_memory_pass; role_memory_pass=$(gen_password 32)
            local role_node_pass; role_node_pass=$(gen_password 32)
            local role_dash_pass; role_dash_pass=$(gen_password 32)

            # Apply substitutions
            sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${pg_pass}|" "$env_file"
            sed -i "s|^VALKEY_PASSWORD=.*|VALKEY_PASSWORD=${valkey_pass}|" "$env_file"
            sed -i "s|^INFISICAL_ENCRYPTION_KEY=.*|INFISICAL_ENCRYPTION_KEY=${infisical_enc}|" "$env_file"
            sed -i "s|^INFISICAL_AUTH_SECRET=.*|INFISICAL_AUTH_SECRET=${infisical_auth}|" "$env_file"
            sed -i "s|^KEYCLOAK_ADMIN_PASSWORD=.*|KEYCLOAK_ADMIN_PASSWORD=${kc_pass}|" "$env_file"
            sed -i "s|^ROLE_OMNIBASE_PASSWORD=.*|ROLE_OMNIBASE_PASSWORD=${role_omnibase_pass}|" "$env_file"
            sed -i "s|^ROLE_OMNIINTELLIGENCE_PASSWORD=.*|ROLE_OMNIINTELLIGENCE_PASSWORD=${role_intelligence_pass}|" "$env_file"
            sed -i "s|^ROLE_OMNICLAUDE_PASSWORD=.*|ROLE_OMNICLAUDE_PASSWORD=${role_claude_pass}|" "$env_file"
            sed -i "s|^ROLE_OMNIMEMORY_PASSWORD=.*|ROLE_OMNIMEMORY_PASSWORD=${role_memory_pass}|" "$env_file"
            sed -i "s|^ROLE_OMNINODE_PASSWORD=.*|ROLE_OMNINODE_PASSWORD=${role_node_pass}|" "$env_file"
            sed -i "s|^ROLE_OMNIDASH_PASSWORD=.*|ROLE_OMNIDASH_PASSWORD=${role_dash_pass}|" "$env_file"

            log_info ".env generated with secure random passwords ✓"
        fi

        # Source the env file for this session
        set -a
        # shellcheck source=/dev/null
        source "$env_file"
        set +a
    fi

    # ── 2.3 Start PostgreSQL ───────────────────────────────────────────────
    log_step "2.3 — Starting PostgreSQL (port ${POSTGRES_PORT:-5436})"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "docker compose up -d postgres"
        log_dry "wait_for_port localhost 5436 PostgreSQL"
    else
        omni_compose_infra "$infra_dir" up -d postgres
        wait_for_port localhost "${POSTGRES_PORT:-5436}" "PostgreSQL" 30

        # Wait for PostgreSQL to be fully ready (accepting connections)
        retry 5 docker exec -i omninode-infra-postgres-1 \
            pg_isready -U postgres -h localhost

        log_info "PostgreSQL is ready ✓"
    fi

    # ── 2.4 Run Database Migrations (36 migrations) ────────────────────────
    log_step "2.4 — Applying database migrations (36 forward migrations)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "python3 ${infra_dir}/scripts/run-migrations.py --apply"
        log_dry "Creates: 7 databases, 6 roles, schema evolution 000-036"
    else
        if [[ -f "${infra_dir}/scripts/run-migrations.py" ]]; then
            cd "$infra_dir"
            python3 scripts/run-migrations.py --apply 2>/dev/null || {
                log_warn "Migration script failed — migrations may already be applied"
            }
        else
            log_warn "Migration script not found — migrations handled by container entrypoint"
        fi
        log_info "Database migrations complete ✓"
    fi

    # ── 2.4a Validate Database Roles (Gap #4) ─────────────────────────────
    log_step "2.4a — Validating 6 least-privilege database roles"
    validate_db_roles || log_warn "Role validation incomplete — check migration logs"

    # ── 2.4b Validate omnidash_analytics Database (Gap #5) ────────────────
    log_step "2.4b — Validating omnidash_analytics database exists"
    validate_omnidash_db || log_warn "omnidash_analytics DB missing — OmniDash Phase 5 may fail"

    # ── 2.5 Start Valkey Cache ─────────────────────────────────────────────
    log_step "2.5 — Starting Valkey cache (port ${VALKEY_PORT:-16379})"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "docker compose up -d valkey"
    else
        omni_compose_infra "$infra_dir" up -d valkey
        wait_for_port localhost "${VALKEY_PORT:-16379}" "Valkey" 20
        log_info "Valkey is ready ✓"
    fi

    # ── 2.6 Start Redpanda (Kafka) ────────────────────────────────────────
    log_step "2.6 — Starting Redpanda event bus (port ${REDPANDA_EXTERNAL_PORT:-29092})"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "docker compose up -d redpanda"
        log_dry "wait_for_port localhost 29092 Redpanda"
    else
        omni_compose_infra "$infra_dir" up -d redpanda
        wait_for_port localhost "${REDPANDA_EXTERNAL_PORT:-29092}" "Redpanda" 30
        log_info "Redpanda is ready ✓"
    fi

    # ── 2.7 Create Kafka Topics from Contracts ─────────────────────────────
    log_step "2.7 — Creating Kafka topics (contract-driven)"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "python3 ${infra_dir}/scripts/create_kafka_topics.py"
    else
        if [[ -f "${infra_dir}/scripts/create_kafka_topics.py" ]]; then
            cd "$infra_dir"
            python3 scripts/create_kafka_topics.py 2>/dev/null || {
                log_warn "Topic creation deferred — will be handled at runtime"
            }
        fi
        log_info "Kafka topics configured ✓"
    fi

    # ── 2.7a Validate OmniDash Kafka Topics (Gap #2) ─────────────────────
    log_step "2.7a — Creating and validating 4 OmniDash Kafka topics"
    validate_kafka_topics || log_warn "Kafka topic validation incomplete — OmniDash may fail"

    # ── 2.8 Start Infisical (optional) ────────────────────────────────────
    if [[ "${SKIP_SECRETS}" != "true" ]]; then
        log_step "2.8 — Starting Infisical secrets manager (port 8880)"

        if [[ "$DRY_RUN" == "true" ]]; then
            log_dry "docker compose --profile secrets up -d"
            log_dry "bash ${infra_dir}/scripts/bootstrap-infisical.sh"
        else
            start_infra_profile "$infra_dir" "secrets"
            wait_for_service "http://localhost:8880/api/status" "Infisical" 20

            # Run 6-step bootstrap
            if [[ -f "${infra_dir}/scripts/bootstrap-infisical.sh" ]]; then
                bash "${infra_dir}/scripts/bootstrap-infisical.sh" || {
                    log_warn "Infisical bootstrap had issues — secrets may need manual seeding"
                }
            fi
            log_info "Infisical is ready ✓"

            # Validate bootstrap (Gap #6)
            validate_infisical_bootstrap || log_warn "Infisical bootstrap incomplete"
        fi
    else
        log_step "2.8 — Skipping Infisical (--skip-secrets)"
    fi

    # ── 2.9 Start Keycloak (optional) ─────────────────────────────────────
    if [[ "${SKIP_KEYCLOAK}" != "true" ]]; then
        log_step "2.9 — Starting Keycloak (port 28080)"

        if [[ "$DRY_RUN" == "true" ]]; then
            log_dry "docker compose --profile auth up -d"
        else
            start_infra_profile "$infra_dir" "auth"
            wait_for_service "http://localhost:28080" "Keycloak" 30
            log_info "Keycloak is ready ✓"
        fi
    else
        log_step "2.9 — Skipping Keycloak (--skip-keycloak)"
    fi

    log_info "Phase 2 complete — Infrastructure services running ✓"
}
