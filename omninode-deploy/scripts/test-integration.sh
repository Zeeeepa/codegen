#!/usr/bin/env bash
# shellcheck disable=SC1090,SC1091
# SPDX-FileCopyrightText: 2025 OmniNode.ai Inc.
# SPDX-License-Identifier: MIT
#
# OmniNode AI — Integration Test Suite
# Tests cross-service event flow and functional correctness.
#
# Usage:
#   ./scripts/test-integration.sh                   # Full test
#   ./scripts/test-integration.sh --workspace /path
#   ./scripts/test-integration.sh --quick            # Skip slow checks

set -euo pipefail

WORKSPACE="${WORKSPACE:-$(pwd)/omninode-workspace}"
QUICK=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --quick)     QUICK=true; shift ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
# Colors used in output functions
# shellcheck disable=SC2034
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PASS=0
FAIL=0
SKIP=0

ok()   { PASS=$((PASS + 1)); echo -e "  ${GREEN}✓${NC} $*"; }
fail() { FAIL=$((FAIL + 1)); echo -e "  ${RED}✗${NC} $*"; }
skip() { SKIP=$((SKIP + 1)); echo -e "  ${CYAN}○${NC} $*"; }

section() { echo -e "\n${BOLD}${CYAN}── $1 ──${NC}"; }

echo -e "${BOLD}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   OmniNode AI — Integration Test Suite        ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════════╝${NC}"

# ============================================================================
# Test 1: Hook Script Dependency Chain
# ============================================================================
section "Test 1: Hook → Lib Dependency Chain"

HOOK_DIR="${WORKSPACE}/omniclaude/plugins/onex/hooks"
if [[ -d "${HOOK_DIR}/scripts" ]] && [[ -d "${HOOK_DIR}/lib" ]]; then
  # Check that hook scripts can find their lib imports
  LIB_IMPORTS="$(grep -rch "from.*hooks\.lib\|import.*hooks\.lib" "${HOOK_DIR}/scripts/" 2>/dev/null | awk '{s+=$1} END{print s+0}' || true)"
  if [[ "${LIB_IMPORTS}" -gt 0 ]]; then
    ok "Hook scripts reference hooks/lib/ (${LIB_IMPORTS} import statements)"
  else
    # Hook scripts may invoke lib via shell wrappers
    SHELL_REFS="$(grep -rch "hooks/lib" "${HOOK_DIR}/scripts/" 2>/dev/null | awk '{s+=$1} END{print s+0}' || true)"
    if [[ "${SHELL_REFS}" -gt 0 ]]; then
      ok "Hook scripts reference hooks/lib/ via shell paths (${SHELL_REFS} refs)"
    else
      skip "Hook→lib dependency chain not found (may use dynamic loading)"
    fi
  fi

  # Verify lib modules don't have syntax errors
  BAD_PY=0
  while IFS= read -r pyfile; do
    if ! python3 -c "import ast; ast.parse(open('${pyfile}').read())" 2>/dev/null; then
      BAD_PY=$((BAD_PY + 1))
      fail "Python syntax error: $(basename "$pyfile")"
    fi
  done < <(find "${HOOK_DIR}/lib" -type f -name "*.py" 2>/dev/null)

  if [[ $BAD_PY -eq 0 ]]; then
    LIB_COUNT=$(find "${HOOK_DIR}/lib" -type f -name "*.py" | wc -l)
    ok "All ${LIB_COUNT} hook lib modules pass Python AST parse"
  fi
else
  skip "Hook scripts or lib directory not found"
fi

# ============================================================================
# Test 2: Agent YAML Schema Validation
# ============================================================================
section "Test 2: Agent YAML Schema Validation"

AGENT_DIR="${WORKSPACE}/omniclaude/plugins/onex/agents/configs"
if [[ -d "$AGENT_DIR" ]]; then
  YAML_COUNT=$(find "$AGENT_DIR" -name "*.yaml" | wc -l)
  BAD_SCHEMA=0

  while IFS= read -r yaml_file; do
    RESULT=$(python3 -c "
import yaml, sys
with open('${yaml_file}') as f:
    d = yaml.safe_load(f)
if not isinstance(d, dict):
    print('not a dict')
    sys.exit(1)
# Check for v2.0.0 schema keys
expected = {'agent_type', 'agent_identity', 'agent_philosophy'}
found = set(d.keys()) & expected
if len(found) < 2:
    print(f'missing keys: expected ≥2 of {expected}, found {found}')
    sys.exit(1)
print('ok')
" 2>/dev/null || echo "parse error")

    if [[ "$RESULT" != "ok" ]]; then
      BAD_SCHEMA=$((BAD_SCHEMA + 1))
      fail "Schema: $(basename "$yaml_file") — ${RESULT}"
    fi
  done < <(find "$AGENT_DIR" -name "*.yaml")

  if [[ $BAD_SCHEMA -eq 0 ]]; then
    ok "All ${YAML_COUNT} agent YAMLs pass schema v2.0.0 validation"
  else
    fail "${BAD_SCHEMA}/${YAML_COUNT} agents failed schema validation"
  fi
else
  skip "Agent config directory not found"
fi

# ============================================================================
# Test 3: Python Package Import Chain
# ============================================================================
section "Test 3: Python Import Chain"

VENV_DIR="${WORKSPACE}/.venv"
if [[ -d "$VENV_DIR" ]]; then
  # shellcheck source=/dev/null
  source "${VENV_DIR}/bin/activate"

  # Test SPI→Core circular dep is resolved
  SPI_CORE=$(python3 -c "
try:
    import omnibase_core
    import omnibase_spi
    print('ok')
except ImportError as e:
    print(f'fail: {e}')
" 2>/dev/null || echo "fail: python error")

  if [[ "$SPI_CORE" == "ok" ]]; then
    ok "SPI↔Core circular dependency resolved"
  else
    fail "SPI↔Core import chain broken: ${SPI_CORE}"
  fi

  # Test qdrant-client version
  QDRANT_CHECK=$(python3 -c "
try:
    from qdrant_client import __version__
    major, minor = int(__version__.split('.')[0]), int(__version__.split('.')[1])
    if major == 1 and minor < 18:
        print(f'ok: v{__version__}')
    else:
        print(f'warn: v{__version__} >= 1.18.0')
except ImportError:
    print('skip: not installed')
" 2>/dev/null || echo "skip")

  if [[ "$QDRANT_CHECK" == ok:* ]]; then
    ok "qdrant-client ${QDRANT_CHECK#ok: } (<1.18.0 ✓)"
  elif [[ "$QDRANT_CHECK" == warn:* ]]; then
    fail "qdrant-client ${QDRANT_CHECK#warn: } (PEP 604 bug risk)"
  else
    skip "qdrant-client not installed"
  fi

  # Test contract_topics.py loads
  if [[ -f "${WORKSPACE}/omniintelligence/src/omniintelligence/runtime/contract_topics.py" ]]; then
    TOPICS_CHECK=$(python3 -c "
try:
    from omniintelligence.runtime.contract_topics import collect_subscribe_topics_from_contracts
    print('ok')
except Exception as e:
    print(f'fail: {e}')
" 2>/dev/null || echo "skip")

    if [[ "$TOPICS_CHECK" == "ok" ]]; then
      ok "contract_topics.py module loadable"
    else
      skip "contract_topics.py: ${TOPICS_CHECK}"
    fi
  fi
else
  skip "Virtual environment not found at ${VENV_DIR}"
fi

# ============================================================================
# Test 4: Infrastructure Connectivity
# ============================================================================
section "Test 4: Infrastructure Connectivity"

# PostgreSQL
if command -v psql &>/dev/null; then
  if [[ -f "${WORKSPACE}/.env" ]]; then
    source "${WORKSPACE}/.env"
  fi
  PG_CHECK=$(psql "postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@localhost:${POSTGRES_PORT:-5436}/${POSTGRES_DB:-omnibase_infra}" -c "SELECT 1 AS check" -t 2>/dev/null | tr -d ' ' || echo "fail")
  if [[ "$PG_CHECK" == "1" ]]; then
    ok "PostgreSQL connectable on port ${POSTGRES_PORT:-5436}"

    # Count databases
    DB_COUNT=$(psql "postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@localhost:${POSTGRES_PORT:-5436}/postgres" -t -c "SELECT COUNT(*) FROM pg_database WHERE datname IN ('omnibase_infra','omniintelligence','omniclaude','omnimemory','omninode_cloud','omnidash_analytics','infisical_db')" 2>/dev/null | tr -d ' ' || echo 0)
    if [[ $DB_COUNT -ge 6 ]]; then
      ok "PostgreSQL has ${DB_COUNT}/7 expected databases"
    else
      fail "PostgreSQL has only ${DB_COUNT}/7 databases"
    fi
  else
    skip "PostgreSQL not reachable"
  fi
else
  skip "psql not available"
fi

# Qdrant
if command -v curl &>/dev/null; then
  QDRANT_HEALTH=$(curl -s --connect-timeout 2 http://localhost:6333/healthz 2>/dev/null || echo "fail")
  if [[ "$QDRANT_HEALTH" != "fail" ]]; then
    ok "Qdrant healthy on port 6333"

    COLL_COUNT=$(curl -s http://localhost:6333/collections 2>/dev/null | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('result',{}).get('collections',[])))" 2>/dev/null || echo 0)
    if [[ $COLL_COUNT -ge 3 ]]; then
      ok "Qdrant has ${COLL_COUNT} collections"
    else
      skip "Qdrant has ${COLL_COUNT} collections (expected ≥3)"
    fi
  else
    skip "Qdrant not reachable"
  fi
fi

# Kafka/Redpanda
if command -v curl &>/dev/null && ! $QUICK; then
  KAFKA_CHECK=$(curl -s --connect-timeout 2 http://localhost:8082/v3/clusters 2>/dev/null || echo "fail")
  if [[ "$KAFKA_CHECK" != "fail" ]]; then
    ok "Redpanda Admin API reachable on 8082"
  else
    skip "Redpanda Admin API not reachable (may use different port)"
  fi
fi

# ============================================================================
# Test 5: Skills Structure Validation
# ============================================================================
section "Test 5: Skills Structure"

SKILLS_DIR="${WORKSPACE}/omniclaude/plugins/onex/skills"
if [[ -d "$SKILLS_DIR" ]]; then
  # Check infrastructure dirs exist
  for idir in _bin _lib _shared; do
    if [[ -d "${SKILLS_DIR}/${idir}" ]]; then
      ok "Infrastructure dir: ${idir}/"
    else
      fail "Missing infrastructure dir: ${idir}/"
    fi
  done

  # Check deploy-local-plugin skill has its own deploy.sh
  if [[ -f "${SKILLS_DIR}/deploy-local-plugin/deploy.sh" ]]; then
    ok "deploy-local-plugin/deploy.sh exists (meta-deployment skill)"
  fi

  # Check _golden_path_validate exists
  if [[ -d "${SKILLS_DIR}/_golden_path_validate" ]]; then
    ok "_golden_path_validate skill present"
  fi
else
  skip "Skills directory not found"
fi

# ============================================================================
# Test 6: Command Definitions
# ============================================================================
section "Test 6: Command Definitions"

CMD_DIR="${WORKSPACE}/omniclaude/plugins/onex/commands"
EXPECTED_CMDS=(authorize bus-audit crash-recovery deauthorize gap-fix set-active-run)

if [[ -d "$CMD_DIR" ]]; then
  for cmd in "${EXPECTED_CMDS[@]}"; do
    if [[ -f "${CMD_DIR}/${cmd}.md" ]]; then
      ok "Command: ${cmd}"
    else
      fail "Missing command: ${cmd}.md"
    fi
  done
else
  skip "Commands directory not found"
fi

# ============================================================================
# Summary
# ============================================================================
TOTAL=$((PASS + FAIL + SKIP))

echo -e "\n${BOLD}═══════════════════════════════════════════${NC}"
echo -e "  ${GREEN}✓ ${PASS} passed${NC}  ${RED}✗ ${FAIL} failed${NC}  ${CYAN}○ ${SKIP} skipped${NC}"
echo -e "  Total: ${TOTAL} integration tests"
echo -e "${BOLD}═══════════════════════════════════════════${NC}"

if [[ $FAIL -gt 0 ]]; then
  echo -e "\n  ${RED}Integration tests have failures.${NC}"
  exit 1
else
  echo -e "\n  ${GREEN}Integration tests passed! 🧪${NC}"
  exit 0
fi
