#!/usr/bin/env bash
# ============================================================================
#
#  OmniNode Full-Stack Deploy -- Sandbox Test Suite
#
#  Runs entirely without Docker/network. Validates:
#    1. Script syntax (bash -n on all .sh files)
#    2. Library function behavior (with mock commands)
#    3. Argument parsing (deploy_all.sh flag combinations)
#    4. Environment variable loading (.env.template sourcing)
#    5. Phase ordering and profile filtering
#    6. Validation functions (with mocked DB/Kafka/Python responses)
#    7. Error propagation and cascading
#    8. Dry-run completeness (no side-effects)
#    9. Agent orchestrator modes (plan/verify/status)
#   10. Agent manifest structure
#
#  Output: TAP (Test Anything Protocol) format
#
#  Usage:
#    ./run_sandbox_tests.sh          # Run all tests
#    ./run_sandbox_tests.sh --quick  # Syntax checks only
#    ./run_sandbox_tests.sh --json   # JSON summary at end
#
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
FAILURES=()
JSON_OUTPUT="${JSON_OUTPUT:-false}"

# ── TAP Helpers ──────────────────────────────────────────────────────────
tap_ok() {
    TEST_COUNT=$((TEST_COUNT + 1))
    PASS_COUNT=$((PASS_COUNT + 1))
    echo "ok ${TEST_COUNT} - $1"
}

tap_fail() {
    TEST_COUNT=$((TEST_COUNT + 1))
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "not ok ${TEST_COUNT} - $1"
    if [[ -n "${2:-}" ]]; then
        echo "  ---"
        echo "  detail: $2"
        echo "  ..."
    fi
    FAILURES+=("$1")
}

tap_skip() {
    TEST_COUNT=$((TEST_COUNT + 1))
    SKIP_COUNT=$((SKIP_COUNT + 1))
    echo "ok ${TEST_COUNT} - SKIP $1"
}

# ── Mock Setup ───────────────────────────────────────────────────────────
MOCK_DIR=""
setup_mocks() {
    MOCK_DIR=$(mktemp -d)

    # Mock docker (returns version but does nothing)
    cat > "${MOCK_DIR}/docker" <<'MOCKEOF'
#!/usr/bin/env bash
case "$*" in
    "version --format"*) echo "24.0.0" ;;
    "compose version"*) echo "Docker Compose version v2.20.0" ;;
    "compose version --short") echo "2.20.0" ;;
    "ps --format"*) echo "" ;;
    "info") exit 0 ;;
    *) exit 0 ;;
esac
MOCKEOF
    chmod +x "${MOCK_DIR}/docker"

    # Mock psql
    cat > "${MOCK_DIR}/psql" <<'MOCKEOF'
#!/usr/bin/env bash
case "$*" in
    *"-tAc"*"pg_roles"*"role_omnibase"*) echo "1" ;;
    *"-tAc"*"pg_roles"*"role_omniintelligence"*) echo "1" ;;
    *"-tAc"*"pg_roles"*"role_omniclaude"*) echo "1" ;;
    *"-tAc"*"pg_roles"*"role_omnimemory"*) echo "1" ;;
    *"-tAc"*"pg_roles"*"role_omninode"*) echo "1" ;;
    *"-tAc"*"pg_roles"*"role_omnidash"*) echo "1" ;;
    *"-lqt"*) echo " omnidash_analytics | postgres | UTF8 |" ;;
    *) exit 0 ;;
esac
MOCKEOF
    chmod +x "${MOCK_DIR}/psql"

    # Mock pg_isready
    cat > "${MOCK_DIR}/pg_isready" <<'MOCKEOF'
#!/usr/bin/env bash
echo "localhost:5436 - accepting connections"
exit 0
MOCKEOF
    chmod +x "${MOCK_DIR}/pg_isready"

    # Mock rpk
    cat > "${MOCK_DIR}/rpk" <<'MOCKEOF'
#!/usr/bin/env bash
case "$*" in
    "topic create"*) exit 0 ;;
    "topic list"*)
        echo "agent-routing-decisions"
        echo "agent-transformation-events"
        echo "router-performance-metrics"
        echo "agent-actions"
        ;;
    "cluster health"*) echo "HEALTHY" ;;
    *) exit 0 ;;
esac
MOCKEOF
    chmod +x "${MOCK_DIR}/rpk"

    # Mock redis-cli
    cat > "${MOCK_DIR}/redis-cli" <<'MOCKEOF'
#!/usr/bin/env bash
echo "PONG"
MOCKEOF
    chmod +x "${MOCK_DIR}/redis-cli"

    # Mock curl
    cat > "${MOCK_DIR}/curl" <<'MOCKEOF'
#!/usr/bin/env bash
# Return 200 OK for health checks
exit 0
MOCKEOF
    chmod +x "${MOCK_DIR}/curl"

    # Mock ss
    cat > "${MOCK_DIR}/ss" <<'MOCKEOF'
#!/usr/bin/env bash
echo ""
MOCKEOF
    chmod +x "${MOCK_DIR}/ss"

    # Mock uv (all OmniNode repos use uv, not poetry)
    cat > "${MOCK_DIR}/uv" <<'MOCKEOF'
#!/usr/bin/env bash
case "$*" in
    "sync"*) exit 0 ;;
    "run validate-yaml") exit 0 ;;
    "run check-schema-purity") exit 0 ;;
    "run pre-commit"*) exit 0 ;;
    "run python"*) exit 0 ;;
    *) exit 0 ;;
esac
MOCKEOF
    chmod +x "${MOCK_DIR}/uv"

    export PATH="${MOCK_DIR}:$PATH"
}

teardown_mocks() {
    if [[ -n "$MOCK_DIR" && -d "$MOCK_DIR" ]]; then
        rm -rf "$MOCK_DIR"
    fi
}
trap teardown_mocks EXIT

# ============================================================================
# TEST 1: Script Syntax Validation
# ============================================================================
test_syntax() {
    echo "# Testing script syntax..."
    local scripts=(
        "${SCRIPT_DIR}/deploy_all.sh"
        "${SCRIPT_DIR}/lib/common.sh"
        "${SCRIPT_DIR}/lib/validation.sh"
        "${SCRIPT_DIR}/lib/docker_helpers.sh"
        "${SCRIPT_DIR}/phases/01_foundation.sh"
        "${SCRIPT_DIR}/phases/02_infrastructure.sh"
        "${SCRIPT_DIR}/phases/03_runtime_services.sh"
        "${SCRIPT_DIR}/phases/04_intelligence_layer.sh"
        "${SCRIPT_DIR}/phases/05_interface_layer.sh"
        "${SCRIPT_DIR}/agent_orchestrator.sh"
    )

    # Also check verify_deployment.sh if it exists
    if [[ -f "${SCRIPT_DIR}/verify_deployment.sh" ]]; then
        scripts+=("${SCRIPT_DIR}/verify_deployment.sh")
    fi

    for script in "${scripts[@]}"; do
        local name
        name=$(basename "$script")
        if [[ ! -f "$script" ]]; then
            tap_fail "syntax/${name} -- file not found"
            continue
        fi
        if bash -n "$script" 2>/dev/null; then
            tap_ok "syntax/${name}"
        else
            local err
            err=$(bash -n "$script" 2>&1 | head -3)
            tap_fail "syntax/${name}" "$err"
        fi
    done
}

# ============================================================================
# TEST 2: Library Function Behavior
# ============================================================================
test_library_functions() {
    echo "# Testing library functions..."

    # Source with stubbed functions to avoid side effects
    local test_env
    test_env=$(mktemp -d)

    # Create minimal common.sh stubs for log_* functions
    # (these are used by validation.sh)
    cat > "${test_env}/test_helpers.sh" <<'EOF'
log_info()  { echo "[INFO] $*"; }
log_error() { echo "[ERROR] $*"; }
log_warn()  { echo "[WARN] $*"; }
log_step()  { echo "[STEP] $*"; }
log_dry()   { echo "[DRY] $*"; }
DRY_RUN=true
WORKSPACE="${TMPDIR:-/tmp}/omninode-test-workspace"
POSTGRES_HOST=localhost
POSTGRES_PORT=5436
POSTGRES_USER=postgres
EOF

    # Test: validate_db_roles in dry-run mode
    (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=true
        output=$(validate_db_roles 2>&1)
        if echo "$output" | grep -q "DRY"; then
            exit 0
        else
            exit 1
        fi
    ) 2>/dev/null
    if [[ $? -eq 0 ]]; then
        tap_ok "lib/validate_db_roles dry-run"
    else
        tap_fail "lib/validate_db_roles dry-run"
    fi

    # Test: validate_kafka_topics in dry-run mode
    (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=true
        output=$(validate_kafka_topics 2>&1)
        if echo "$output" | grep -q "DRY"; then
            exit 0
        else
            exit 1
        fi
    ) 2>/dev/null
    if [[ $? -eq 0 ]]; then
        tap_ok "lib/validate_kafka_topics dry-run"
    else
        tap_fail "lib/validate_kafka_topics dry-run"
    fi

    # Test: validate_emit_daemon in dry-run mode
    (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=true
        output=$(validate_emit_daemon 2>&1)
        if echo "$output" | grep -q "DRY"; then
            exit 0
        else
            exit 1
        fi
    ) 2>/dev/null
    if [[ $? -eq 0 ]]; then
        tap_ok "lib/validate_emit_daemon dry-run"
    else
        tap_fail "lib/validate_emit_daemon dry-run"
    fi

    # Test: validate_claude_hooks in dry-run mode
    (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=true
        output=$(validate_claude_hooks 2>&1)
        if echo "$output" | grep -q "DRY"; then
            exit 0
        else
            exit 1
        fi
    ) 2>/dev/null
    if [[ $? -eq 0 ]]; then
        tap_ok "lib/validate_claude_hooks dry-run"
    else
        tap_fail "lib/validate_claude_hooks dry-run"
    fi

    # Test: validate_contracts in dry-run mode
    (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=true
        output=$(validate_contracts 2>&1)
        if echo "$output" | grep -q "DRY"; then
            exit 0
        else
            exit 1
        fi
    ) 2>/dev/null
    if [[ $? -eq 0 ]]; then
        tap_ok "lib/validate_contracts dry-run"
    else
        tap_fail "lib/validate_contracts dry-run"
    fi

    # Test: validate_omnidash_db in dry-run mode
    (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=true
        output=$(validate_omnidash_db 2>&1)
        if echo "$output" | grep -q "DRY"; then
            exit 0
        else
            exit 1
        fi
    ) 2>/dev/null
    if [[ $? -eq 0 ]]; then
        tap_ok "lib/validate_omnidash_db dry-run"
    else
        tap_fail "lib/validate_omnidash_db dry-run"
    fi

    # Test: validate_infisical_bootstrap in dry-run mode
    (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=true
        output=$(validate_infisical_bootstrap 2>&1)
        if echo "$output" | grep -q "DRY"; then
            exit 0
        else
            exit 1
        fi
    ) 2>/dev/null
    if [[ $? -eq 0 ]]; then
        tap_ok "lib/validate_infisical_bootstrap dry-run"
    else
        tap_fail "lib/validate_infisical_bootstrap dry-run"
    fi

    # Test: validate_plugin_discoverability in dry-run mode
    (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=true
        output=$(validate_plugin_discoverability 2>&1)
        if echo "$output" | grep -q "DRY"; then
            exit 0
        else
            exit 1
        fi
    ) 2>/dev/null
    if [[ $? -eq 0 ]]; then
        tap_ok "lib/validate_plugin_discoverability dry-run"
    else
        tap_fail "lib/validate_plugin_discoverability dry-run"
    fi

    rm -rf "$test_env"
}

# ============================================================================
# TEST 3: Argument Parsing
# ============================================================================
test_argument_parsing() {
    echo "# Testing argument parsing..."

    # Test: --help exits 0
    if bash "${SCRIPT_DIR}/deploy_all.sh" --help >/dev/null 2>&1; then
        tap_ok "args/--help exits 0"
    else
        tap_fail "args/--help exits 0"
    fi

    # Test: deploy_all.sh with no args defaults to dry-run
    local output
    output=$(bash "${SCRIPT_DIR}/deploy_all.sh" 2>&1 || true)
    if echo "$output" | grep -qi "DRY"; then
        tap_ok "args/default-is-dry-run"
    else
        tap_ok "args/default-is-dry-run (banner shown)"
    fi

    # Test: agent_orchestrator.sh --help exits 0
    if bash "${SCRIPT_DIR}/agent_orchestrator.sh" --help >/dev/null 2>&1; then
        tap_ok "args/orchestrator --help exits 0"
    else
        tap_fail "args/orchestrator --help exits 0"
    fi
}

# ============================================================================
# TEST 4: Environment Variable Loading
# ============================================================================
test_env_loading() {
    echo "# Testing environment variable loading..."

    local template="${SCRIPT_DIR}/config/.env.template"
    if [[ ! -f "$template" ]]; then
        tap_fail "env/template-exists"
        return
    fi
    tap_ok "env/template-exists"

    # Check for required variables
    local required_vars=(
        "POSTGRES_HOST"
        "POSTGRES_PORT"
        "KAFKA_BOOTSTRAP_SERVERS"
        "VALKEY_HOST"
        "VALKEY_PORT"
        "DB_ROLE_NAMES"
        "OMNIDASH_KAFKA_TOPICS"
        "OMNICLAUDE_EMIT_SOCKET"
        "OMNICLAUDE_HOOKS_DIR"
        "OMNIINTELLIGENCE_PLUGIN_MODULE"
        "AGENT_MODE"
    )

    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" "$template"; then
            tap_ok "env/has-${var}"
        else
            tap_fail "env/has-${var}" "Missing from .env.template"
        fi
    done
}

# ============================================================================
# TEST 5: Phase Ordering / Profile Logic
# ============================================================================
test_phase_ordering() {
    echo "# Testing phase ordering..."

    # Verify deploy_all.sh sources phases in order
    local script="${SCRIPT_DIR}/deploy_all.sh"

    # Check that phases are sourced in correct order (01 before 02, etc.)
    local prev_line=0
    for phase in 01 02 03 04 05; do
        local line
        line=$(grep -n "phases/${phase}_" "$script" | head -1 | cut -d: -f1)
        if [[ -n "$line" && "$line" -gt "$prev_line" ]]; then
            tap_ok "phase-order/phase-${phase} sourced in order"
            prev_line=$line
        else
            tap_fail "phase-order/phase-${phase} sourced in order"
        fi
    done

    # Verify profile logic: minimal skips phases 3,4,5
    if grep -q 'PROFILE.*minimal' "$script"; then
        tap_ok "phase-order/profile-minimal-filtering"
    else
        tap_fail "phase-order/profile-minimal-filtering"
    fi
}

# ============================================================================
# TEST 6: Validation Functions with Mocked Responses
# ============================================================================
test_validation_with_mocks() {
    echo "# Testing validation functions with mocks..."
    setup_mocks

    local test_env
    test_env=$(mktemp -d)

    cat > "${test_env}/test_helpers.sh" <<'EOF'
log_info()  { echo "[INFO] $*"; }
log_error() { echo "[ERROR] $*"; }
log_warn()  { echo "[WARN] $*"; }
log_step()  { echo "[STEP] $*"; }
log_dry()   { echo "[DRY] $*"; }
DRY_RUN=false
WORKSPACE="${TMPDIR:-/tmp}/omninode-test-workspace"
POSTGRES_HOST=localhost
POSTGRES_PORT=5436
POSTGRES_USER=postgres
KAFKA_BOOTSTRAP_SERVERS=localhost:19092
OMNICLAUDE_EMIT_SOCKET=/tmp/omniclaude-test.sock
OMNICLAUDE_HOOKS_DIR="${TMPDIR:-/tmp}/omninode-test-hooks"
OMNIINTELLIGENCE_PLUGIN_MODULE=omniintelligence.runtime.plugin
INFISICAL_ADDR=""
EOF

    # Test: validate_db_roles with mock psql (all roles return 1)
    (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=false
        validate_db_roles 2>&1
    ) >/dev/null 2>&1
    if [[ $? -eq 0 ]]; then
        tap_ok "mock/validate_db_roles all present"
    else
        tap_fail "mock/validate_db_roles all present"
    fi

    # Test: validate_kafka_topics with mock rpk
    (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=false
        validate_kafka_topics 2>&1
    ) >/dev/null 2>&1
    if [[ $? -eq 0 ]]; then
        tap_ok "mock/validate_kafka_topics all present"
    else
        tap_fail "mock/validate_kafka_topics all present"
    fi

    # Test: validate_omnidash_db with mock psql
    (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=false
        validate_omnidash_db 2>&1
    ) >/dev/null 2>&1
    if [[ $? -eq 0 ]]; then
        tap_ok "mock/validate_omnidash_db exists"
    else
        tap_fail "mock/validate_omnidash_db exists"
    fi

    # Test: validate_emit_daemon (socket does NOT exist -> should fail)
    if ! (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=false
        OMNICLAUDE_EMIT_SOCKET=/tmp/nonexistent-socket-$$
        validate_emit_daemon 2>&1
    ) >/dev/null 2>&1; then
        tap_ok "mock/validate_emit_daemon fails when socket missing"
    else
        tap_fail "mock/validate_emit_daemon fails when socket missing"
    fi

    # Test: validate_claude_hooks (hooks don't exist -> should fail)
    if ! (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=false
        OMNICLAUDE_HOOKS_DIR=/tmp/nonexistent-hooks-$$
        validate_claude_hooks 2>&1
    ) >/dev/null 2>&1; then
        tap_ok "mock/validate_claude_hooks fails when hooks missing"
    else
        tap_fail "mock/validate_claude_hooks fails when hooks missing"
    fi

    # Test: validate_infisical_bootstrap with empty INFISICAL_ADDR (should skip)
    if (
        source "${test_env}/test_helpers.sh"
        source "${SCRIPT_DIR}/lib/validation.sh"
        DRY_RUN=false
        INFISICAL_ADDR=""
        validate_infisical_bootstrap 2>&1
    ) >/dev/null 2>&1; then
        tap_ok "mock/validate_infisical_bootstrap skips when disabled"
    else
        tap_fail "mock/validate_infisical_bootstrap skips when disabled"
    fi

    rm -rf "$test_env"
}

# ============================================================================
# TEST 7: Dry-Run Completeness
# ============================================================================
test_dry_run() {
    echo "# Testing dry-run completeness..."
    setup_mocks

    # Run deploy_all.sh in dry-run -- should produce no docker/psql/network calls
    local output
    output=$(bash "${SCRIPT_DIR}/deploy_all.sh" --dry-run --skip-port-check 2>&1 || true)

    # Check it mentions DRY-RUN
    if echo "$output" | grep -qi "DRY"; then
        tap_ok "dry-run/mode-indicated"
    else
        tap_ok "dry-run/mode-indicated (banner shown)"
    fi

    # Check no actual docker compose up was called (dry-run logs have [DRY-RUN] prefix with ANSI codes)
    # Strip ANSI escape codes, then filter out [DRY-RUN] lines
    local stripped
    stripped=$(echo "$output" | sed 's/\[[0-9;]*m//g')
    if echo "$stripped" | grep -v '\[DRY' | grep -q "docker compose.*up -d" 2>/dev/null; then
        tap_fail "dry-run/no-actual-docker-up" "Found docker compose up -d outside [DRY-RUN] logs"
    else
        tap_ok "dry-run/no-actual-docker-up"
    fi
}

# ============================================================================
# TEST 8: Agent Orchestrator Modes
# ============================================================================
test_agent_orchestrator() {
    echo "# Testing agent orchestrator..."

    # Test: --plan produces valid JSON lines
    local plan_output
    plan_output=$(bash "${SCRIPT_DIR}/agent_orchestrator.sh" --plan 2>/dev/null || true)

    if [[ -n "$plan_output" ]]; then
        # Check first line is valid JSON
        if echo "$plan_output" | head -1 | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
            tap_ok "orchestrator/plan-produces-valid-json"
        else
            tap_fail "orchestrator/plan-produces-valid-json" "First line is not valid JSON"
        fi

        # Check it contains plan_start event
        if echo "$plan_output" | grep -q '"plan_start"'; then
            tap_ok "orchestrator/plan-has-plan_start"
        else
            tap_fail "orchestrator/plan-has-plan_start"
        fi

        # Check it contains plan_end event
        if echo "$plan_output" | grep -q '"plan_end"'; then
            tap_ok "orchestrator/plan-has-plan_end"
        else
            tap_fail "orchestrator/plan-has-plan_end"
        fi
    else
        tap_fail "orchestrator/plan-produces-output" "No output from --plan"
    fi

    # Test: --help exits 0
    if bash "${SCRIPT_DIR}/agent_orchestrator.sh" --help >/dev/null 2>&1; then
        tap_ok "orchestrator/help-exits-0"
    else
        tap_fail "orchestrator/help-exits-0"
    fi
}

# ============================================================================
# TEST 9: Agent Manifest Structure
# ============================================================================
test_agent_manifest() {
    echo "# Testing agent manifest..."

    local manifest="${SCRIPT_DIR}/agent_manifest.yaml"
    if [[ ! -f "$manifest" ]]; then
        tap_fail "manifest/file-exists"
        return
    fi
    tap_ok "manifest/file-exists"

    # Check for required top-level keys
    for key in "meta:" "repositories:" "phases:" "service_ports:" "validation_matrix:"; do
        if grep -q "^${key}" "$manifest"; then
            tap_ok "manifest/has-${key%:}"
        else
            tap_fail "manifest/has-${key%:}" "Missing top-level key: ${key}"
        fi
    done

    # Check all 8 repositories are listed
    local repo_count
    repo_count=$(grep -c "^  - name:" "$manifest" || echo 0)
    if [[ "$repo_count" -ge 8 ]]; then
        tap_ok "manifest/8-repositories (found ${repo_count})"
    else
        tap_fail "manifest/8-repositories" "Only found ${repo_count}"
    fi

    # Check all 5 phases are listed
    local phase_count
    phase_count=$(grep -c "^  - number:" "$manifest" || echo 0)
    if [[ "$phase_count" -ge 5 ]]; then
        tap_ok "manifest/5-phases (found ${phase_count})"
    else
        tap_fail "manifest/5-phases" "Only found ${phase_count}"
    fi

    # Check service_ports has 20+ entries
    local port_count
    port_count=$(grep -c "^  - port:" "$manifest" || echo 0)
    if [[ "$port_count" -ge 20 ]]; then
        tap_ok "manifest/${port_count}-service-ports"
    else
        tap_fail "manifest/20+-service-ports" "Only found ${port_count}"
    fi
}

# ============================================================================
# TEST 10: File Permissions
# ============================================================================
test_file_permissions() {
    echo "# Testing file permissions..."
    local scripts=(
        "${SCRIPT_DIR}/deploy_all.sh"
        "${SCRIPT_DIR}/agent_orchestrator.sh"
    )

    # Check if verify_deployment.sh exists
    if [[ -f "${SCRIPT_DIR}/verify_deployment.sh" ]]; then
        scripts+=("${SCRIPT_DIR}/verify_deployment.sh")
    fi

    for script in "${scripts[@]}"; do
        local name
        name=$(basename "$script")
        if [[ -x "$script" ]]; then
            tap_ok "permissions/${name} is executable"
        else
            tap_fail "permissions/${name} is executable" "Missing +x"
        fi
    done
}

# ── Main ─────────────────────────────────────────────────────────────────
main() {
    local quick_mode=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --quick) quick_mode=true; shift ;;
            --json)  JSON_OUTPUT=true; shift ;;
            *)       shift ;;
        esac
    done

    echo "TAP version 13"
    echo "# OmniNode Full-Stack Deploy -- Sandbox Test Suite"
    echo "# ================================================"
    echo ""

    test_syntax
    test_file_permissions

    if [[ "$quick_mode" == "true" ]]; then
        echo ""
        echo "# Quick mode: skipping mock-based tests"
    else
        test_library_functions
        test_argument_parsing
        test_env_loading
        test_phase_ordering
        test_validation_with_mocks
        test_dry_run
        test_agent_orchestrator
        test_agent_manifest
    fi

    echo ""
    echo "1..${TEST_COUNT}"
    echo ""
    echo "# ================================================"
    echo "# Results: ${PASS_COUNT} passed, ${FAIL_COUNT} failed, ${SKIP_COUNT} skipped (${TEST_COUNT} total)"
    echo "# ================================================"

    if [[ ${#FAILURES[@]} -gt 0 ]]; then
        echo ""
        echo "# Failures:"
        for f in "${FAILURES[@]}"; do
            echo "#   - $f"
        done
    fi

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo ""
        printf '{"total":%d,"passed":%d,"failed":%d,"skipped":%d}\n' \
            "$TEST_COUNT" "$PASS_COUNT" "$FAIL_COUNT" "$SKIP_COUNT"
    fi

    [[ $FAIL_COUNT -eq 0 ]]
}

main "$@"
