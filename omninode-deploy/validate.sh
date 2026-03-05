#!/usr/bin/env bash
# =============================================================================
# OmniNode AI — Validation & Test Suite
# =============================================================================
# Comprehensive validation of every component in the deployed OmniNode platform.
# Runs infrastructure health checks, Python import verification, service endpoint
# tests, functional smoke tests, and Claude Code integration checks.
#
# Usage:
#   ./validate.sh              # Full validation
#   ./validate.sh --quick      # Infrastructure + imports only
#   ./validate.sh --infra      # Infrastructure checks only
#   ./validate.sh --python     # Python checks only
#   ./validate.sh --services   # Service endpoint checks only
#   ./validate.sh --smoke      # Functional smoke tests only
#   ./validate.sh --json       # Output results as JSON
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${OMNINODE_WORKSPACE:-$SCRIPT_DIR/workspace}"
VENV_DIR="${WORKSPACE}/.venv"

# Source env
if [[ -f "${SCRIPT_DIR}/.env" ]]; then
  set -a; source "${SCRIPT_DIR}/.env"; set +a
fi

# =============================================================================
# Colors & Counters
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0
TOTAL=0
RESULTS=()

# CLI flags
RUN_INFRA=true
RUN_PYTHON=true
RUN_SERVICES=true
RUN_SMOKE=true
RUN_CLAUDE=true
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --quick)    RUN_SMOKE=false; RUN_SERVICES=false; RUN_CLAUDE=false; shift ;;
    --infra)    RUN_PYTHON=false; RUN_SERVICES=false; RUN_SMOKE=false; RUN_CLAUDE=false; shift ;;
    --python)   RUN_INFRA=false; RUN_SERVICES=false; RUN_SMOKE=false; RUN_CLAUDE=false; shift ;;
    --services) RUN_INFRA=false; RUN_PYTHON=false; RUN_SMOKE=false; RUN_CLAUDE=false; shift ;;
    --smoke)    RUN_INFRA=false; RUN_PYTHON=false; RUN_SERVICES=false; RUN_CLAUDE=false; shift ;;
    --json)     JSON_OUTPUT=true; shift ;;
    *) shift ;;
  esac
done

check() {
  local name="$1"
  local cmd="$2"
  local expected="${3:-0}"

  TOTAL=$((TOTAL + 1))

  if eval "$cmd" &>/dev/null; then
    PASS=$((PASS + 1))
    RESULTS+=("PASS|$name")
    if [[ "$JSON_OUTPUT" != "true" ]]; then
      echo -e "  ${GREEN}✓ PASS${NC}  $name"
    fi
  else
    FAIL=$((FAIL + 1))
    RESULTS+=("FAIL|$name")
    if [[ "$JSON_OUTPUT" != "true" ]]; then
      echo -e "  ${RED}✗ FAIL${NC}  $name"
    fi
  fi
}

check_warn() {
  local name="$1"
  local cmd="$2"

  TOTAL=$((TOTAL + 1))

  if eval "$cmd" &>/dev/null; then
    PASS=$((PASS + 1))
    RESULTS+=("PASS|$name")
    if [[ "$JSON_OUTPUT" != "true" ]]; then
      echo -e "  ${GREEN}✓ PASS${NC}  $name"
    fi
  else
    WARN=$((WARN + 1))
    RESULTS+=("WARN|$name")
    if [[ "$JSON_OUTPUT" != "true" ]]; then
      echo -e "  ${YELLOW}⚠ WARN${NC}  $name"
    fi
  fi
}

# =============================================================================
# Banner
# =============================================================================
if [[ "$JSON_OUTPUT" != "true" ]]; then
  echo -e "${BOLD}"
  echo "╔══════════════════════════════════════════════════════════════════╗"
  echo "║           🔍 OmniNode AI — Validation Suite 🔍                 ║"
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo -e "${NC}"
fi

# =============================================================================
# Section 1: Infrastructure Health
# =============================================================================
if [[ "$RUN_INFRA" == "true" ]]; then
  [[ "$JSON_OUTPUT" != "true" ]] && echo -e "\n${BOLD}${CYAN}━━━ Infrastructure Health ━━━${NC}"

  # PostgreSQL
  check "PostgreSQL: container running" \
    "docker ps --format '{{.Names}}' | grep -q omninode-postgres"

  check "PostgreSQL: connection" \
    "docker exec omninode-postgres pg_isready -U ${POSTGRES_USER:-postgres}"

  check "PostgreSQL: omnibase_infra database" \
    "docker exec omninode-postgres psql -U ${POSTGRES_USER:-postgres} -d ${OMNIBASE_INFRA_DB:-omnibase_infra} -c 'SELECT 1'"

  check "PostgreSQL: omniintelligence database" \
    "docker exec omninode-postgres psql -U ${POSTGRES_USER:-postgres} -d ${OMNIINTELLIGENCE_DB:-omniintelligence} -c 'SELECT 1'"

  check "PostgreSQL: omnidash_analytics database" \
    "docker exec omninode-postgres psql -U ${POSTGRES_USER:-postgres} -d ${OMNIDASH_ANALYTICS_DB:-omnidash_analytics} -c 'SELECT 1'"

  check "PostgreSQL: node_registrations table" \
    "docker exec omninode-postgres psql -U ${POSTGRES_USER:-postgres} -d ${OMNIBASE_INFRA_DB:-omnibase_infra} -c 'SELECT COUNT(*) FROM node_registrations'"

  check "PostgreSQL: patterns table" \
    "docker exec omninode-postgres psql -U ${POSTGRES_USER:-postgres} -d ${OMNIINTELLIGENCE_DB:-omniintelligence} -c 'SELECT COUNT(*) FROM patterns'"

  # Kafka / Redpanda
  check "Redpanda: container running" \
    "docker ps --format '{{.Names}}' | grep -q omninode-redpanda"

  check "Redpanda: cluster healthy" \
    "docker exec omninode-redpanda rpk cluster health"

  check "Kafka: broker reachable" \
    "docker exec omninode-redpanda rpk topic list"

  check "Kafka: session events topic" \
    "docker exec omninode-redpanda rpk topic list | grep -q 'session-started'"

  check "Kafka: hook events topic" \
    "docker exec omninode-redpanda rpk topic list | grep -q 'claude-hook-event'"

  check "Kafka: intelligence topics" \
    "docker exec omninode-redpanda rpk topic list | grep -q 'intent-classified'"

  # Qdrant
  check "Qdrant: container running" \
    "docker ps --format '{{.Names}}' | grep -q omninode-qdrant"

  check "Qdrant: health endpoint" \
    "curl -sf http://localhost:${QDRANT_HTTP_PORT:-6333}/healthz"

  check_warn "Qdrant: patterns collection" \
    "curl -sf http://localhost:${QDRANT_HTTP_PORT:-6333}/collections/omninode_patterns | grep -q 'ok'"

  # Valkey
  check "Valkey: container running" \
    "docker ps --format '{{.Names}}' | grep -q omninode-valkey"

  check "Valkey: PING/PONG" \
    "docker exec omninode-valkey valkey-cli -a ${VALKEY_PASSWORD:-valkey-dev-password} ping | grep -q PONG"
fi

# =============================================================================
# Section 2: Python Environment
# =============================================================================
if [[ "$RUN_PYTHON" == "true" ]]; then
  [[ "$JSON_OUTPUT" != "true" ]] && echo -e "\n${BOLD}${CYAN}━━━ Python Environment ━━━${NC}"

  # Activate venv
  if [[ -f "${VENV_DIR}/bin/activate" ]]; then
    source "${VENV_DIR}/bin/activate"
  fi

  check "Python: version >= 3.12" \
    "python3 -c 'import sys; assert sys.version_info >= (3, 12)'"

  check "Python: venv exists" \
    "test -f '${VENV_DIR}/bin/activate'"

  # Package imports
  check "Import: omnibase_spi" \
    "python -c 'import omnibase_spi'"

  check "Import: omnibase_core" \
    "python -c 'import omnibase_core'"

  check_warn "Import: omnibase_infra" \
    "python -c 'import omnibase_infra'"

  check_warn "Import: omniintelligence" \
    "python -c 'import omniintelligence'"

  check_warn "Import: omnimemory" \
    "python -c 'import omnimemory'"

  check_warn "Import: omniclaude" \
    "python -c 'import omniclaude'"

  # Key sub-module imports
  check_warn "Import: omnibase_core.nodes (4-node arch)" \
    "python -c 'from omnibase_core.nodes import NodeCompute'"

  check_warn "Import: omnibase_spi.protocols" \
    "python -c 'from omnibase_spi.protocols.nodes import ProtocolNode'"

  # Repository existence
  for repo in omnibase_spi omnibase_core omnibase_infra omniintelligence omnimemory omniclaude omnidash onex_change_control; do
    check "Repo exists: ${repo}" \
      "test -d '${WORKSPACE}/${repo}'"
  done
fi

# =============================================================================
# Section 3: Service Endpoints
# =============================================================================
if [[ "$RUN_SERVICES" == "true" ]]; then
  [[ "$JSON_OUTPUT" != "true" ]] && echo -e "\n${BOLD}${CYAN}━━━ Service Endpoints ━━━${NC}"

  check_warn "Intelligence API: reachable" \
    "curl -sf http://localhost:8053/health || curl -sf http://localhost:8053/docs"

  check_warn "OmniDash: reachable" \
    "curl -sf http://localhost:${OMNIDASH_PORT:-3000}/"

  check_warn "Redpanda Console: reachable" \
    "curl -sf http://localhost:${REDPANDA_CONSOLE_PORT:-8080}/"

  # Unix socket for emit daemon
  check_warn "Emit daemon: socket exists" \
    "test -S /tmp/omniclaude-emit.sock"
fi

# =============================================================================
# Section 4: Functional Smoke Tests
# =============================================================================
if [[ "$RUN_SMOKE" == "true" ]]; then
  [[ "$JSON_OUTPUT" != "true" ]] && echo -e "\n${BOLD}${CYAN}━━━ Functional Smoke Tests ━━━${NC}"

  # Kafka produce/consume test
  check_warn "Kafka: produce test event" \
    "echo '{\"test\":true}' | docker exec -i omninode-redpanda rpk topic produce onex.evt.observability.metrics.v1"

  check_warn "Kafka: consume test event" \
    "timeout 5 docker exec omninode-redpanda rpk topic consume onex.evt.observability.metrics.v1 --num 1 --offset end 2>/dev/null"

  # PostgreSQL write test
  check_warn "PostgreSQL: write test record" \
    "docker exec omninode-postgres psql -U ${POSTGRES_USER:-postgres} -d ${OMNIBASE_INFRA_DB:-omnibase_infra} -c \"INSERT INTO db_metadata (key, value) VALUES ('test_validation', '$(date +%s)') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value\""

  # Qdrant vector test
  check_warn "Qdrant: upsert test vector" \
    "curl -sf -X PUT 'http://localhost:${QDRANT_HTTP_PORT:-6333}/collections/omninode_patterns/points?wait=true' \
      -H 'Content-Type: application/json' \
      -d '{\"points\":[{\"id\":99999,\"vector\":$(python3 -c "print([0.1]*1536)"),\"payload\":{\"test\":true}}]}'"

  # Python test suites
  if [[ -f "${VENV_DIR}/bin/activate" ]]; then
    source "${VENV_DIR}/bin/activate"

    check_warn "omnibase_core: pytest" \
      "cd ${WORKSPACE}/omnibase_core && python -m pytest tests/ -x -q --tb=no 2>/dev/null"

    check_warn "omnibase_spi: pytest" \
      "cd ${WORKSPACE}/omnibase_spi && python -m pytest tests/ -x -q --tb=no 2>/dev/null"
  fi
fi

# =============================================================================
# Section 5: Claude Code Integration
# =============================================================================
if [[ "$RUN_CLAUDE" == "true" ]]; then
  [[ "$JSON_OUTPUT" != "true" ]] && echo -e "\n${BOLD}${CYAN}━━━ Claude Code Integration ━━━${NC}"

  PLUGIN_DIR="$HOME/.claude/plugins/onex"

  check_warn "Plugin: directory exists" \
    "test -d '${PLUGIN_DIR}'"

  check_warn "Plugin: hooks.json" \
    "test -f '${PLUGIN_DIR}/hooks/hooks.json'"

  check_warn "Plugin: agent configs" \
    "test -d '${PLUGIN_DIR}/agents/configs'"

  check_warn "Plugin: skills directory" \
    "test -d '${PLUGIN_DIR}/skills'"

  if [[ -d "${PLUGIN_DIR}/agents/configs" ]]; then
    AGENT_COUNT=$(find "${PLUGIN_DIR}/agents/configs" -name "*.yaml" -o -name "*.yml" 2>/dev/null | wc -l)
    check_warn "Plugin: agent count >= 50" \
      "test $AGENT_COUNT -ge 50"
  fi

  check_warn "CLAUDE.md: exists in workspace" \
    "test -f '${WORKSPACE}/CLAUDE.md'"

  check_warn "OmniClaude: .env configured" \
    "test -f '${WORKSPACE}/omniclaude/.env'"
fi

# =============================================================================
# Results Summary
# =============================================================================
if [[ "$JSON_OUTPUT" == "true" ]]; then
  echo "{"
  echo "  \"total\": $TOTAL,"
  echo "  \"pass\": $PASS,"
  echo "  \"fail\": $FAIL,"
  echo "  \"warn\": $WARN,"
  echo "  \"results\": ["
  for i in "${!RESULTS[@]}"; do
    IFS='|' read -r status name <<< "${RESULTS[$i]}"
    COMMA=""
    [[ $i -lt $((${#RESULTS[@]} - 1)) ]] && COMMA=","
    echo "    {\"status\": \"$status\", \"name\": \"$name\"}${COMMA}"
  done
  echo "  ]"
  echo "}"
else
  echo ""
  echo -e "${BOLD}"
  echo "╔══════════════════════════════════════════════════════════════════╗"
  echo "║                    Validation Results                          ║"
  echo "╠══════════════════════════════════════════════════════════════════╣"
  printf "║  Total: %-4d │ " "$TOTAL"
  printf "Pass: ${GREEN}%-4d${NC}${BOLD} │ " "$PASS"
  printf "Fail: ${RED}%-4d${NC}${BOLD} │ " "$FAIL"
  printf "Warn: ${YELLOW}%-4d${NC}${BOLD}      ║\n" "$WARN"
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo -e "${NC}"

  if [[ $FAIL -gt 0 ]]; then
    echo -e "${RED}❌ Some checks failed. Review output above.${NC}"
    exit 1
  elif [[ $WARN -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  All critical checks passed. Some optional features have warnings.${NC}"
    exit 0
  else
    echo -e "${GREEN}✅ All checks passed! OmniNode platform is fully operational.${NC}"
    exit 0
  fi
fi

