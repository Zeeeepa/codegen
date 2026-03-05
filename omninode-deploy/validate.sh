#!/usr/bin/env bash
# shellcheck disable=SC1090,SC1091
# SPDX-FileCopyrightText: 2025 OmniNode.ai Inc.
# SPDX-License-Identifier: MIT
#
# OmniNode AI — Deployment Validation Suite v2.0
# 70+ automated checks across 8 sections.
#
# Usage:
#   ./validate.sh                          # Full validation
#   ./validate.sh --workspace /path        # Custom workspace
#   ./validate.sh --json                   # Machine-readable JSON output
#   ./validate.sh --quick                  # Skip slow checks
#   ./validate.sh --typecheck              # Run mypy on Python packages
#   ./validate.sh --lint                   # Run shellcheck on scripts

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${WORKSPACE:-$(pwd)/omninode-workspace}"
JSON_OUTPUT=false
QUICK_MODE=false
RUN_TYPECHECK=false
RUN_LINT=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Counters
PASS=0
FAIL=0
WARN=0
SKIP=0

# JSON results array
declare -a JSON_RESULTS=()

# ============================================================================
# CLI
# ============================================================================
while [[ $# -gt 0 ]]; do
  case $1 in
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --json)      JSON_OUTPUT=true; shift ;;
    --quick)     QUICK_MODE=true; export QUICK_MODE; shift ;;
    --typecheck) RUN_TYPECHECK=true; shift ;;
    --lint)      RUN_LINT=true; shift ;;
    --help|-h)   sed -n '2,/^$/p' "$0" | grep '^#' | sed 's/^# \?//'; exit 0 ;;
    *)           echo "Unknown: $1"; exit 1 ;;
  esac
done

# ============================================================================
# Check helpers
# ============================================================================
check_pass() {
  local section="$1" name="$2" detail="${3:-}"
  PASS=$((PASS + 1))
  if ! $JSON_OUTPUT; then
    echo -e "  ${GREEN}✓${NC} ${name}${detail:+ — ${detail}}"
  fi
  JSON_RESULTS+=("{\"section\":\"${section}\",\"name\":\"${name}\",\"status\":\"pass\",\"detail\":\"${detail}\"}")
}

check_fail() {
  local section="$1" name="$2" detail="${3:-}"
  FAIL=$((FAIL + 1))
  if ! $JSON_OUTPUT; then
    echo -e "  ${RED}✗${NC} ${name}${detail:+ — ${detail}}"
  fi
  JSON_RESULTS+=("{\"section\":\"${section}\",\"name\":\"${name}\",\"status\":\"fail\",\"detail\":\"${detail}\"}")
}

check_warn() {
  local section="$1" name="$2" detail="${3:-}"
  WARN=$((WARN + 1))
  if ! $JSON_OUTPUT; then
    echo -e "  ${YELLOW}⚠${NC} ${name}${detail:+ — ${detail}}"
  fi
  JSON_RESULTS+=("{\"section\":\"${section}\",\"name\":\"${name}\",\"status\":\"warn\",\"detail\":\"${detail}\"}")
}

check_skip() {
  local section="$1" name="$2" detail="${3:-}"
  SKIP=$((SKIP + 1))
  if ! $JSON_OUTPUT; then
    echo -e "  ${CYAN}○${NC} ${name}${detail:+ — ${detail}}"
  fi
  JSON_RESULTS+=("{\"section\":\"${section}\",\"name\":\"${name}\",\"status\":\"skip\",\"detail\":\"${detail}\"}")
}

section() {
  if ! $JSON_OUTPUT; then
    echo -e "\n${BOLD}${CYAN}── $1 ──${NC}"
  fi
}

# ============================================================================
# Section 1: Repository Structure
# ============================================================================
section "1. Repository Structure"

declare -a EXPECTED_REPOS=(
  "omnibase_spi" "omnibase_core" "omnibase_infra"
  "omniintelligence" "omnimemory" "omniclaude"
  "onex_change_control" "omnidash"
)

for repo in "${EXPECTED_REPOS[@]}"; do
  if [[ -d "${WORKSPACE}/${repo}/.git" ]]; then
    check_pass "repos" "${repo}" "git repo present"
  else
    check_fail "repos" "${repo}" "missing or not a git repo"
  fi
done

# Check each repo has pyproject.toml (except omnidash which has package.json)
for repo in "${EXPECTED_REPOS[@]}"; do
  if [[ "$repo" == "omnidash" ]]; then
    if [[ -f "${WORKSPACE}/${repo}/package.json" ]]; then
      check_pass "repos" "${repo}/package.json" "exists"
    else
      check_fail "repos" "${repo}/package.json" "missing"
    fi
  else
    if [[ -f "${WORKSPACE}/${repo}/pyproject.toml" ]]; then
      check_pass "repos" "${repo}/pyproject.toml" "exists"
    else
      check_fail "repos" "${repo}/pyproject.toml" "missing"
    fi
  fi
done

# ============================================================================
# Section 2: Docker Infrastructure
# ============================================================================
section "2. Docker Infrastructure"

declare -a INFRA_CONTAINERS=("postgres" "redpanda" "qdrant" "valkey")
declare -a INFRA_PORTS=(5436 19092 6333 16379)

for i in "${!INFRA_CONTAINERS[@]}"; do
  name="${INFRA_CONTAINERS[$i]}"
  port="${INFRA_PORTS[$i]}"

  # Check container running
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -qi "$name"; then
    check_pass "infra" "container:${name}" "running"
  else
    check_warn "infra" "container:${name}" "not running (may need --skip-infra=false)"
  fi

  # Check port listening
  if command -v nc &>/dev/null && nc -z localhost "$port" 2>/dev/null; then
    check_pass "infra" "port:${port}" "${name} reachable"
  elif command -v curl &>/dev/null && curl -s --connect-timeout 2 "localhost:${port}" &>/dev/null; then
    check_pass "infra" "port:${port}" "${name} reachable"
  else
    check_warn "infra" "port:${port}" "${name} not reachable"
  fi
done

# Check PostgreSQL databases (canonical: 7 databases)
declare -a EXPECTED_DBS=(
  "omnibase_infra" "omniintelligence" "omniclaude"
  "omnimemory" "omninode_cloud" "omnidash_analytics"
  "infisical_db"
)

if command -v psql &>/dev/null; then
  for db in "${EXPECTED_DBS[@]}"; do
    if psql "postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@localhost:5436/${db}" \
       -c "SELECT 1" &>/dev/null; then
      check_pass "infra" "database:${db}" "exists and connectable"
    else
      check_warn "infra" "database:${db}" "not connectable"
    fi
  done
else
  check_skip "infra" "database checks" "psql not available"
fi

# Check Qdrant collections
if command -v curl &>/dev/null; then
  QDRANT_COLLECTIONS=$(curl -s http://localhost:6333/collections 2>/dev/null || echo '{"result":{"collections":[]}}')
  declare -a EXPECTED_COLLECTIONS=("session_vectors" "code_embeddings" "pattern_embeddings" "memory_vectors" "intent_vectors")
  for coll in "${EXPECTED_COLLECTIONS[@]}"; do
    if echo "$QDRANT_COLLECTIONS" | grep -q "\"$coll\""; then
      check_pass "infra" "qdrant:${coll}" "collection exists"
    else
      check_warn "infra" "qdrant:${coll}" "collection not found"
    fi
  done
fi

# ============================================================================
# Section 3: Python Environment
# ============================================================================
section "3. Python Environment"

VENV_DIR="${WORKSPACE}/.venv"
if [[ -d "$VENV_DIR" ]]; then
  check_pass "python" "virtualenv" "exists at .venv/"

  # Activate and check
  # shellcheck source=/dev/null
  source "${VENV_DIR}/bin/activate"

  PY_VER=$(python --version 2>&1)
  check_pass "python" "python version" "$PY_VER"

  # Check package imports
  declare -a PYTHON_MODULES=(
    "omnibase_spi"
    "omnibase_core"
    "omnibase_infra"
    "omniintelligence"
    "omnimemory"
    "omniclaude"
  )

  for mod in "${PYTHON_MODULES[@]}"; do
    if python -c "import ${mod}" 2>/dev/null; then
      # Try to get version
      ver=$(python -c "import ${mod}; print(getattr(${mod}, '__version__', 'ok'))" 2>/dev/null || echo "ok")
      check_pass "python" "import ${mod}" "v${ver}"
    else
      check_warn "python" "import ${mod}" "failed (may need infrastructure)"
    fi
  done

  # Check qdrant-client version constraint
  QDRANT_VER=$(python -c "import qdrant_client; print(qdrant_client.__version__)" 2>/dev/null || echo "not installed")
  if [[ "$QDRANT_VER" != "not installed" ]]; then
    # Check if < 1.18.0
    QDRANT_MINOR=$(echo "$QDRANT_VER" | cut -d. -f2)
    if [[ "$QDRANT_MINOR" -lt 18 ]]; then
      check_pass "python" "qdrant-client version" "v${QDRANT_VER} (<1.18.0 ✓)"
    else
      check_warn "python" "qdrant-client version" "v${QDRANT_VER} (≥1.18.0 — PEP 604 bug on Python 3.12)"
    fi
  else
    check_skip "python" "qdrant-client version" "not installed"
  fi

else
  check_fail "python" "virtualenv" "not found at ${VENV_DIR}"
fi

# ============================================================================
# Section 4: Claude Code Operator
# ============================================================================
section "4. Claude Code Operator"

CLAUDE_DIR="${WORKSPACE}/omniclaude"
PLUGIN_DIR="${CLAUDE_DIR}/plugins/onex"

if [[ -d "$PLUGIN_DIR" ]]; then
  check_pass "claude" "plugin directory" "exists"

  # Hooks validation (10 endpoints across 7 event types)
  HOOKS_JSON="${PLUGIN_DIR}/hooks/hooks.json"
  if [[ -f "$HOOKS_JSON" ]]; then
    # Count hook event types
    HOOK_TYPES=$(python3 -c "
import json
with open('${HOOKS_JSON}') as f:
    d = json.load(f)
hooks = d.get('hooks', {})
total_endpoints = sum(len(v) for v in hooks.values())
print(f'{len(hooks)} event types, {total_endpoints} endpoints')
" 2>/dev/null || echo "parse error")
    check_pass "claude" "hooks.json" "${HOOK_TYPES}"

    # Validate hooks version
    HOOKS_VER=$(python3 -c "import json; print(json.load(open('${HOOKS_JSON}')).get('version','?'))" 2>/dev/null || echo "?")
    check_pass "claude" "hooks version" "v${HOOKS_VER}"
  else
    check_fail "claude" "hooks.json" "missing"
  fi

  # Hook scripts
  HOOK_SCRIPTS_DIR="${PLUGIN_DIR}/hooks/scripts"
  if [[ -d "$HOOK_SCRIPTS_DIR" ]]; then
    SCRIPT_COUNT=$(find "$HOOK_SCRIPTS_DIR" -type f -name "*.sh" | wc -l)
    check_pass "claude" "hook scripts" "${SCRIPT_COUNT} scripts in hooks/scripts/"

    # Bash syntax check on hook scripts
    BAD_SYNTAX=0
    while IFS= read -r script; do
      if ! bash -n "$script" 2>/dev/null; then
        BAD_SYNTAX=$((BAD_SYNTAX + 1))
        check_fail "claude" "syntax:$(basename "$script")" "bash -n failed"
      fi
    done < <(find "$HOOK_SCRIPTS_DIR" -type f -name "*.sh")

    if [[ $BAD_SYNTAX -eq 0 ]]; then
      check_pass "claude" "hook script syntax" "all ${SCRIPT_COUNT} pass bash -n"
    fi
  else
    check_fail "claude" "hooks/scripts/" "directory missing"
  fi

  # Hook lib modules (72 Python modules)
  HOOK_LIB="${PLUGIN_DIR}/hooks/lib"
  if [[ -d "$HOOK_LIB" ]]; then
    LIB_COUNT=$(find "$HOOK_LIB" -type f -name "*.py" | wc -l)
    if [[ $LIB_COUNT -ge 50 ]]; then
      check_pass "claude" "hooks/lib/ modules" "${LIB_COUNT} Python modules"
    else
      check_warn "claude" "hooks/lib/ modules" "only ${LIB_COUNT} (expected ~72)"
    fi
  else
    check_fail "claude" "hooks/lib/" "directory missing — hooks will fail at runtime"
  fi

  # Hooks config.yaml
  if [[ -f "${PLUGIN_DIR}/hooks/config.yaml" ]]; then
    check_pass "claude" "hooks/config.yaml" "present"
  else
    check_warn "claude" "hooks/config.yaml" "missing (autofix/pattern config)"
  fi

  # Agent configs (53 YAML files)
  AGENTS_DIR="${PLUGIN_DIR}/agents/configs"
  if [[ -d "$AGENTS_DIR" ]]; then
    AGENT_COUNT=$(find "$AGENTS_DIR" -type f -name "*.yaml" | wc -l)
    if [[ $AGENT_COUNT -ge 50 ]]; then
      check_pass "claude" "agent configs" "${AGENT_COUNT} YAML definitions"
    else
      check_warn "claude" "agent configs" "only ${AGENT_COUNT} (expected ~53)"
    fi

    # YAML parse validation
    BAD_YAML=0
    while IFS= read -r yaml_file; do
      if ! python3 -c "import yaml; yaml.safe_load(open('${yaml_file}'))" 2>/dev/null; then
        BAD_YAML=$((BAD_YAML + 1))
        check_fail "claude" "yaml:$(basename "$yaml_file")" "invalid YAML"
      fi
    done < <(find "$AGENTS_DIR" -type f -name "*.yaml" | head -10)  # Sample first 10

    if [[ $BAD_YAML -eq 0 ]]; then
      check_pass "claude" "agent YAML validation" "sample of 10 files valid"
    fi
  else
    check_fail "claude" "agents/configs/" "directory missing"
  fi

  # Skills (80 skill dirs + 3 infrastructure)
  SKILLS_DIR="${PLUGIN_DIR}/skills"
  if [[ -d "$SKILLS_DIR" ]]; then
    TOTAL_SKILLS=$(find "$SKILLS_DIR" -maxdepth 1 -mindepth 1 -type d | wc -l)
    INFRA_DIRS=$(find "$SKILLS_DIR" -maxdepth 1 -mindepth 1 -type d -name "_*" | wc -l)
    ACTUAL_SKILLS=$((TOTAL_SKILLS - INFRA_DIRS))
    check_pass "claude" "skills" "${ACTUAL_SKILLS} skills + ${INFRA_DIRS} infrastructure dirs"
  else
    check_fail "claude" "skills/" "directory missing"
  fi

  # Commands (6 definitions)
  COMMANDS_DIR="${PLUGIN_DIR}/commands"
  if [[ -d "$COMMANDS_DIR" ]]; then
    CMD_COUNT=$(find "$COMMANDS_DIR" -type f -name "*.md" | wc -l)
    check_pass "claude" "commands" "${CMD_COUNT} command definitions"
  else
    check_warn "claude" "commands/" "directory missing"
  fi

else
  check_fail "claude" "plugin directory" "not found at ${PLUGIN_DIR}"
fi

# ============================================================================
# Section 5: OmniDash Frontend
# ============================================================================
section "5. OmniDash Frontend"

DASH_DIR="${WORKSPACE}/omnidash"
if [[ -d "$DASH_DIR" ]]; then
  # node_modules
  if [[ -d "${DASH_DIR}/node_modules" ]]; then
    check_pass "omnidash" "node_modules" "installed"
  else
    check_warn "omnidash" "node_modules" "not installed (run npm install)"
  fi

  # Build artifacts
  if [[ -d "${DASH_DIR}/dist" ]]; then
    check_pass "omnidash" "build artifacts" "dist/ exists"
  else
    check_warn "omnidash" "build artifacts" "dist/ missing (run npm run build)"
  fi

  # Package.json scripts count
  if [[ -f "${DASH_DIR}/package.json" ]]; then
    SCRIPT_COUNT=$(python3 -c "import json; print(len(json.load(open('${DASH_DIR}/package.json')).get('scripts',{})))" 2>/dev/null || echo 0)
    check_pass "omnidash" "npm scripts" "${SCRIPT_COUNT} scripts defined"
  fi
else
  check_skip "omnidash" "frontend" "omnidash directory not present"
fi

# ============================================================================
# Section 6: OmniIntelligence
# ============================================================================
section "6. OmniIntelligence Nodes"

INTEL_DIR="${WORKSPACE}/omniintelligence"
if [[ -d "$INTEL_DIR" ]]; then
  # Count nodes
  NODE_COUNT=$(find "${INTEL_DIR}/src" -type d -name "node_*" 2>/dev/null | wc -l)
  check_pass "intelligence" "intelligence nodes" "${NODE_COUNT} nodes found"

  # Count Python files
  PY_COUNT=$(find "${INTEL_DIR}/src" -name "*.py" -not -path "*__pycache__*" 2>/dev/null | wc -l)
  check_pass "intelligence" "Python modules" "${PY_COUNT} .py files"

  # Check topics StrEnum
  if [[ -f "${INTEL_DIR}/src/omniintelligence/hooks/topics.py" ]]; then
    TOPIC_COUNT=$(grep -c "onex\." "${INTEL_DIR}/src/omniintelligence/hooks/topics.py" 2>/dev/null || echo 0)
    check_pass "intelligence" "Kafka topics" "${TOPIC_COUNT} topics in StrEnum"
  fi

  # Check contract_topics.py
  if [[ -f "${INTEL_DIR}/src/omniintelligence/runtime/contract_topics.py" ]]; then
    EFFECT_NODES=$(grep -c "omniintelligence.nodes" "${INTEL_DIR}/src/omniintelligence/runtime/contract_topics.py" 2>/dev/null || echo 0)
    check_pass "intelligence" "contract-driven topics" "${EFFECT_NODES} effect nodes discovered"
  fi
else
  check_skip "intelligence" "omniintelligence" "not present"
fi

# ============================================================================
# Section 7: Type Checking & Linting
# ============================================================================
section "7. Type Checking & Linting"

if $RUN_TYPECHECK; then
  if command -v mypy &>/dev/null || python -m mypy --version &>/dev/null 2>&1; then
    for pkg in omnibase_spi omnibase_core; do
      PKG_DIR="${WORKSPACE}/${pkg}"
      if [[ -d "${PKG_DIR}/src" ]]; then
        info "Running mypy on ${pkg}..."
        MYPY_OUT=$(cd "$PKG_DIR" && python -m mypy src/ --ignore-missing-imports --no-error-summary 2>&1 | tail -5)
        MYPY_ERRORS=$(echo "$MYPY_OUT" | grep -c "error:" || true)
        if [[ $MYPY_ERRORS -eq 0 ]]; then
          check_pass "typecheck" "mypy:${pkg}" "no errors"
        else
          check_warn "typecheck" "mypy:${pkg}" "${MYPY_ERRORS} error(s)"
        fi
      fi
    done
  else
    check_skip "typecheck" "mypy" "not installed (pip install mypy)"
  fi
else
  check_skip "typecheck" "Python type checking" "use --typecheck to enable"
fi

if $RUN_LINT; then
  if command -v shellcheck &>/dev/null; then
    for script in "${SCRIPT_DIR}/deploy.sh" "${SCRIPT_DIR}/validate.sh" \
                  "${SCRIPT_DIR}/scripts/setup-claude-operator.sh" \
                  "${SCRIPT_DIR}/config/create-kafka-topics.sh" \
                  "${SCRIPT_DIR}/config/create-qdrant-collections.sh"; do
      if [[ -f "$script" ]]; then
        SC_OUT=$(shellcheck -S warning "$script" 2>&1)
        SC_ISSUES=$(echo "$SC_OUT" | grep -c "warning\|error" || true)
        if [[ $SC_ISSUES -eq 0 ]]; then
          check_pass "lint" "shellcheck:$(basename "$script")" "0 warnings"
        else
          check_warn "lint" "shellcheck:$(basename "$script")" "${SC_ISSUES} issue(s)"
        fi
      fi
    done
  else
    check_skip "lint" "shellcheck" "not installed (apt install shellcheck)"
  fi
else
  check_skip "lint" "shell linting" "use --lint to enable"
fi

# ============================================================================
# Section 8: Environment & Configuration
# ============================================================================
section "8. Environment & Configuration"

ENV_FILE="${WORKSPACE}/.env"
if [[ -f "$ENV_FILE" ]]; then
  check_pass "env" ".env file" "exists"

  # Count defined vars
  VAR_COUNT=$(grep -cE "^[A-Z_]+=.+" "$ENV_FILE" || echo 0)
  check_pass "env" "env vars defined" "${VAR_COUNT} variables"

  # Check critical vars
  for var in POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB; do
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    if [[ -n "${!var:-}" ]]; then
      check_pass "env" "var:${var}" "set"
    else
      check_fail "env" "var:${var}" "not set"
    fi
  done

  # Check for placeholder passwords
  if grep -q "__REPLACE_WITH_" "$ENV_FILE"; then
    check_fail "env" "placeholder passwords" "unreplaced __REPLACE_WITH_* values found"
  else
    check_pass "env" "placeholder passwords" "all replaced"
  fi
else
  check_fail "env" ".env file" "missing"
fi

# ============================================================================
# Summary
# ============================================================================
TOTAL=$((PASS + FAIL + WARN + SKIP))

if $JSON_OUTPUT; then
  echo "{"
  echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
  echo "  \"workspace\": \"${WORKSPACE}\","
  echo "  \"summary\": {"
  echo "    \"total\": ${TOTAL},"
  echo "    \"pass\": ${PASS},"
  echo "    \"fail\": ${FAIL},"
  echo "    \"warn\": ${WARN},"
  echo "    \"skip\": ${SKIP}"
  echo "  },"
  echo "  \"results\": ["
  for i in "${!JSON_RESULTS[@]}"; do
    if [[ $i -lt $((${#JSON_RESULTS[@]} - 1)) ]]; then
      echo "    ${JSON_RESULTS[$i]},"
    else
      echo "    ${JSON_RESULTS[$i]}"
    fi
  done
  echo "  ]"
  echo "}"
else
  echo -e "\n${BOLD}═══════════════════════════════════════════${NC}"
  echo -e "  ${GREEN}✓ ${PASS} passed${NC}  ${RED}✗ ${FAIL} failed${NC}  ${YELLOW}⚠ ${WARN} warnings${NC}  ${CYAN}○ ${SKIP} skipped${NC}"
  echo -e "  Total: ${TOTAL} checks"
  echo -e "${BOLD}═══════════════════════════════════════════${NC}"

  if [[ $FAIL -gt 0 ]]; then
    echo -e "\n  ${RED}Some checks failed. Review issues above.${NC}"
    exit 1
  elif [[ $WARN -gt 0 ]]; then
    echo -e "\n  ${YELLOW}Warnings present — deployment may be partial.${NC}"
    exit 0
  else
    echo -e "\n  ${GREEN}All checks passed! 🎉${NC}"
    exit 0
  fi
fi
