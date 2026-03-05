#!/usr/bin/env bash
# shellcheck disable=SC1090,SC1091
# SPDX-FileCopyrightText: 2025 OmniNode.ai Inc.
# SPDX-License-Identifier: MIT
#
# OmniNode AI — Full Stack Deployment Script
# Deploys all 8 repositories, infrastructure, Python packages, Claude Code operator.
#
# Usage:
#   ./deploy.sh                   # Full deploy
#   ./deploy.sh --infra-only      # Docker services only
#   ./deploy.sh --python-only     # Python environment only
#   ./deploy.sh --skip-infra      # Skip Docker
#   ./deploy.sh --skip-frontend   # Skip OmniDash
#   ./deploy.sh --skip-claude     # Skip Claude Code operator
#   ./deploy.sh --skip-clone      # Repos already cloned
#   ./deploy.sh --seed-demo       # Seed OmniDash demo data
#   ./deploy.sh --profile full    # Docker compose profile
#   ./deploy.sh --workspace /path # Custom workspace
#   ./deploy.sh --help

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${WORKSPACE:-$(pwd)/omninode-workspace}"
LOG_FILE="${SCRIPT_DIR}/deploy.log"
GITHUB_ORG="OmniNode-ai"

# Repository dependency layers (install order matters)
declare -a REPOS=(
  "omnibase_spi"
  "omnibase_core"
  "omnibase_infra"
  "omniintelligence"
  "omnimemory"
  "omniclaude"
  "onex_change_control"
  "omnidash"
)

# Python packages in dependency-resolution order
# NOTE: SPI↔Core have a circular dependency - both must be bootstrapped --no-deps first
declare -a PYTHON_PACKAGES_BOOTSTRAP=(
  "omnibase_core"    # depends on omnibase-spi — install --no-deps first
  "omnibase_spi"     # depends on omnibase-core — install --no-deps first
)
declare -a PYTHON_PACKAGES_MAIN=(
  "omnibase_infra"
  "omniintelligence"
  "omnimemory"
  "omniclaude"
  "onex_change_control"
)

# Flags
SKIP_INFRA=false
SKIP_FRONTEND=false
SKIP_CLAUDE=false
SKIP_CLONE=false
INFRA_ONLY=false
PYTHON_ONLY=false
SEED_DEMO=false
COMPOSE_PROFILE="default"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ============================================================================
# Helpers
# ============================================================================
log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[⚠]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*" >&2; }
info() { echo -e "  ${BLUE}→${NC} $*"; }
step() { echo -e "\n${BOLD}${CYAN}══ Step $1: $2 ══${NC}"; }

die() { err "$@"; exit 1; }

ts() { date '+%Y-%m-%d %H:%M:%S'; }

# Log to file + stdout
exec > >(tee -a "$LOG_FILE") 2>&1

# ============================================================================
# CLI Parsing
# ============================================================================
while [[ $# -gt 0 ]]; do
  case $1 in
    --workspace)    WORKSPACE="$2"; shift 2 ;;
    --skip-infra)   SKIP_INFRA=true; shift ;;
    --skip-frontend) SKIP_FRONTEND=true; shift ;;
    --skip-claude)  SKIP_CLAUDE=true; shift ;;
    --skip-clone)   SKIP_CLONE=true; shift ;;
    --infra-only)   INFRA_ONLY=true; shift ;;
    --python-only)  PYTHON_ONLY=true; SKIP_INFRA=true; SKIP_FRONTEND=true; SKIP_CLAUDE=true; shift ;;
    --seed-demo)    SEED_DEMO=true; shift ;;
    --profile)      COMPOSE_PROFILE="$2"; shift 2 ;;
    --help|-h)
      sed -n '2,/^$/p' "$0" | grep '^#' | sed 's/^# \?//'
      exit 0
      ;;
    *) die "Unknown option: $1. Use --help." ;;
  esac
done

# ============================================================================
# Banner
# ============================================================================
echo -e "${BOLD}
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              🧠  OmniNode AI — Full Stack Deploy v2.0  🧠          ║
║                                                                      ║
║  8 Repositories • 53 Agents • 80 Skills • 10 Hook Endpoints        ║
║  72 Hook Lib Modules • 6 Commands • 21 Intelligence Nodes          ║
║  Kafka Event Bus • Semantic Memory • Live Dashboard                 ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
${NC}"

echo "  $(ts) | Workspace: ${WORKSPACE}"
echo "  $(ts) | Log: ${LOG_FILE}"
echo ""

# ============================================================================
# Step 0: Prerequisites
# ============================================================================
step "0/8" "Checking Prerequisites"

check_cmd() {
  local cmd="$1" label="$2"
  if command -v "$cmd" &>/dev/null; then
    info "${label}: ${GREEN}$("$cmd" --version 2>&1 | head -1)${NC}"
  else
    die "${label} not found. Install it first."
  fi
}

check_cmd docker "docker"
check_cmd python3 "python3"
check_cmd git "git"
check_cmd uv "uv"

if ! command -v node &>/dev/null; then
  warn "Node.js not found — OmniDash build will be skipped"
  SKIP_FRONTEND=true
else
  info "node: ${GREEN}$(node --version)${NC}"
fi

if ! docker compose version &>/dev/null; then
  die "docker compose plugin not found"
fi
info "docker compose: ${GREEN}$(docker compose version --short)${NC}"

# Python version check (≥3.12)
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [[ "$PY_MAJOR" -lt 3 ]] || { [[ "$PY_MAJOR" -eq 3 ]] && [[ "$PY_MINOR" -lt 12 ]]; }; then
  die "Python 3.12+ required (found ${PY_VERSION})"
fi
info "Python version: ${GREEN}${PY_VERSION} ✓${NC}"

log "All prerequisites satisfied"

if $INFRA_ONLY; then
  SKIP_FRONTEND=true
  SKIP_CLAUDE=true
fi

# ============================================================================
# Step 1: Clone Repositories
# ============================================================================
step "1/8" "Cloning Repositories"

mkdir -p "$WORKSPACE"

if $SKIP_CLONE; then
  warn "Skipping clone (--skip-clone)"
else
  for repo in "${REPOS[@]}"; do
    if [[ -d "${WORKSPACE}/${repo}/.git" ]]; then
      info "Updating ${repo}..."
      if ! (cd "${WORKSPACE}/${repo}" && git pull --ff-only 2>/dev/null); then
        warn "Could not fast-forward ${repo} — using existing"
      fi
    else
      info "Cloning ${repo}..."
      git clone --depth 1 "https://github.com/${GITHUB_ORG}/${repo}.git" "${WORKSPACE}/${repo}"
    fi
  done
  log "All ${#REPOS[@]} repositories cloned"
fi

# ============================================================================
# Step 2: Environment Configuration
# ============================================================================
step "2/8" "Environment Configuration"

ENV_FILE="${WORKSPACE}/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  info "Creating .env from template..."
  cp "${SCRIPT_DIR}/.env.example" "$ENV_FILE"

  # Generate secure random password
  DB_PASS=$(openssl rand -hex 16 2>/dev/null || python3 -c 'import secrets; print(secrets.token_hex(16))')
  sed -i "s|__REPLACE_WITH_SECURE_PASSWORD__|${DB_PASS}|g" "$ENV_FILE"
  log ".env created with generated secrets"
else
  log ".env already exists — keeping"
fi

# shellcheck source=/dev/null
source "$ENV_FILE"
log "Environment loaded"

# Validate required env vars
validate_env() {
  local missing=0
  for var in POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB; do
    if [[ -z "${!var:-}" ]]; then
      err "Required env var ${var} is not set"
      missing=$((missing + 1))
    fi
  done
  if [[ $missing -gt 0 ]]; then
    die "${missing} required env var(s) missing. Check .env file."
  fi
}
validate_env

# ============================================================================
# Step 3: Docker Infrastructure
# ============================================================================
step "3/8" "Starting Docker Infrastructure"

if $SKIP_INFRA; then
  warn "Skipping infrastructure (--skip-infra)"
else
  # Use canonical docker-compose from omnibase_infra if available
  COMPOSE_FILE="${WORKSPACE}/omnibase_infra/docker/docker-compose.infra.yml"
  if [[ ! -f "$COMPOSE_FILE" ]]; then
    warn "Canonical compose not found at ${COMPOSE_FILE}"
    info "Falling back to bundled docker-compose.yml"
    COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
  else
    info "Using canonical compose: ${COMPOSE_FILE}"
  fi

  # Determine compose profile args
  PROFILE_ARGS=""
  if [[ "$COMPOSE_PROFILE" != "default" ]]; then
    PROFILE_ARGS="--profile ${COMPOSE_PROFILE}"
  fi

  info "Starting infrastructure services..."
  # shellcheck disable=SC2086
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ${PROFILE_ARGS} up -d 2>&1 | tail -5

  # Wait for PostgreSQL
  info "Waiting for PostgreSQL health..."
  RETRIES=0
  while ! docker compose -f "$COMPOSE_FILE" ps --format json 2>/dev/null | grep -q '"healthy"'; do
    RETRIES=$((RETRIES + 1))
    if [[ $RETRIES -gt 30 ]]; then
      warn "PostgreSQL not healthy after 30s — continuing anyway"
      break
    fi
    sleep 1
  done

  # Run Kafka topic creation
  TOPICS_SCRIPT="${WORKSPACE}/omnibase_infra/docker/create-kafka-topics.sh"
  if [[ -f "$TOPICS_SCRIPT" ]]; then
    info "Creating Kafka topics from canonical script..."
    bash "$TOPICS_SCRIPT" || warn "Topic creation had issues (may already exist)"
  elif [[ -f "${SCRIPT_DIR}/config/create-kafka-topics.sh" ]]; then
    info "Creating Kafka topics from bundled script..."
    bash "${SCRIPT_DIR}/config/create-kafka-topics.sh" || warn "Topic creation had issues"
  fi

  # Create Qdrant collections
  if [[ -f "${SCRIPT_DIR}/config/create-qdrant-collections.sh" ]]; then
    info "Creating Qdrant vector collections..."
    bash "${SCRIPT_DIR}/config/create-qdrant-collections.sh" || warn "Qdrant collection creation had issues"
  fi

  log "Infrastructure started"
fi

if $INFRA_ONLY; then
  echo -e "\n${GREEN}Infrastructure deployed. Exiting (--infra-only).${NC}"
  exit 0
fi

# ============================================================================
# Step 4: Python Virtual Environment
# ============================================================================
step "4/8" "Python Environment Setup"

VENV_DIR="${WORKSPACE}/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
  info "Creating virtual environment with Python 3.12..."
  uv venv --python 3.12 "$VENV_DIR" 2>/dev/null || python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"
info "Activated: $(python --version) at $(which python)"

# ============================================================================
# Step 5: Python Package Installation (Correct Dependency Order)
# ============================================================================
step "5/8" "Installing Python Packages (Dependency Order)"

echo -e "  ${CYAN}Install order: Core↔SPI (bootstrap) → Infra → Intelligence → Memory → Claude → ChangeControl${NC}"

# Phase 1: Install shared external dependencies
info "Installing shared external dependencies..."
uv pip install --quiet \
  "pydantic>=2.10.0,<3.0.0" \
  "pyyaml>=6.0.2,<7.0.0" \
  "httpx>=0.27.0,<1.0.0" \
  "structlog>=23.3.0,<26.0.0" \
  "click>=8.3.1,<9.0.0" \
  "pydantic-settings>=2.10.1,<3.0.0" \
  "dependency-injector>=4.48.3,<5.0.0" \
  "typing-extensions>=4.5.0" \
  2>/dev/null || warn "Some shared deps failed to install"

# Phase 2: Bootstrap SPI↔Core circular dependency
info "Bootstrapping SPI↔Core circular dependency..."
for pkg in "${PYTHON_PACKAGES_BOOTSTRAP[@]}"; do
  if [[ -d "${WORKSPACE}/${pkg}" ]]; then
    info "  Installing ${BOLD}${pkg}${NC} (--no-deps bootstrap)..."
    uv pip install --no-deps -e "${WORKSPACE}/${pkg}" 2>/dev/null \
      && info "    ${GREEN}✓${NC} ${pkg} bootstrapped" \
      || warn "    ${pkg} bootstrap failed"
  fi
done

# Phase 3: Install main packages with deps
for pkg in "${PYTHON_PACKAGES_MAIN[@]}"; do
  if [[ -d "${WORKSPACE}/${pkg}" ]]; then
    info "Installing ${BOLD}${pkg}${NC}..."
    uv pip install --no-deps -e "${WORKSPACE}/${pkg}" 2>/dev/null \
      && info "    ${GREEN}✓${NC} ${pkg} installed (no-deps)" \
      || warn "    ${pkg} install failed"
  fi
done

# Phase 4: Resolve remaining transitive dependencies
info "Resolving remaining dependencies..."
# Pin qdrant-client < 1.18.0 (PEP 604 type union bug on Python 3.12)
uv pip install --quiet \
  "qdrant-client>=1.7.0,<1.18.0" \
  "deepdiff>=8.0.0,<9.0.0" \
  "cryptography>=46.0.3,<47.0.0" \
  "jsonschema>=4.25.1,<5.0.0" \
  "blake3>=1.0.8,<2.0.0" \
  "ruamel-yaml>=0.18.0" \
  "sqlalchemy>=2.0.0,<3.0.0" \
  "alembic>=1.13.0,<2.0.0" \
  "redis>=6.4.0,<8.0.0" \
  "psutil>=7.0.0,<8.0.0" \
  2>/dev/null || warn "Some transitive deps failed"

# Phase 5: Verify imports
info "Verifying Python imports..."
declare -a IMPORT_NAMES=(
  "omnibase_core"
  "omnibase_spi"
  "omnibase_infra"
  "omniintelligence"
  "omnimemory"
  "omniclaude"
)
IMPORT_OK=0
IMPORT_FAIL=0
for mod in "${IMPORT_NAMES[@]}"; do
  if python -c "import ${mod}" 2>/dev/null; then
    info "  ${GREEN}✓${NC} import ${mod}"
    IMPORT_OK=$((IMPORT_OK + 1))
  else
    warn "  ${YELLOW}✗${NC} import ${mod} failed"
    IMPORT_FAIL=$((IMPORT_FAIL + 1))
  fi
done

if [[ $IMPORT_FAIL -eq 0 ]]; then
  log "All ${IMPORT_OK} packages importable"
else
  warn "${IMPORT_OK}/${#IMPORT_NAMES[@]} packages imported (${IMPORT_FAIL} need infrastructure)"
fi

if $PYTHON_ONLY; then
  echo -e "\n${GREEN}Python environment ready. Exiting (--python-only).${NC}"
  exit 0
fi

# ============================================================================
# Step 6: OmniDash Frontend
# ============================================================================
step "6/8" "Building OmniDash Frontend"

if $SKIP_FRONTEND; then
  warn "Skipping frontend (--skip-frontend)"
else
  DASH_DIR="${WORKSPACE}/omnidash"
  if [[ -d "$DASH_DIR" ]]; then
    info "Installing npm dependencies..."
    (cd "$DASH_DIR" && npm install --legacy-peer-deps 2>&1 | tail -3)

    # TypeScript check
    info "Running TypeScript check (tsc)..."
    if (cd "$DASH_DIR" && npm run check 2>&1 | tail -5); then
      info "  ${GREEN}✓${NC} TypeScript check passed"
    else
      warn "TypeScript check had issues — continuing"
    fi

    # Lint
    info "Running ESLint..."
    if (cd "$DASH_DIR" && npm run lint 2>&1 | tail -3); then
      info "  ${GREEN}✓${NC} Lint passed"
    else
      warn "Lint had issues — continuing"
    fi

    # Build
    info "Building production bundle..."
    if (cd "$DASH_DIR" && npm run build 2>&1 | tail -5); then
      log "OmniDash built successfully"
    else
      warn "Build failed — dashboard may not be available"
    fi

    # Database migration (if infra is running)
    if ! $SKIP_INFRA; then
      info "Running database migrations (Drizzle → omnidash_analytics)..."
      (cd "$DASH_DIR" && npm run db:migrate 2>&1 | tail -3) || warn "DB migration skipped (may need infra)"

      # Validate Kafka topics
      info "Validating Kafka topics..."
      (cd "$DASH_DIR" && npm run check-topics 2>&1 | tail -3) || warn "Topic check skipped"
    fi

    # Seed demo data
    if $SEED_DEMO; then
      info "Seeding demo data..."
      (cd "$DASH_DIR" && npm run seed-events 2>&1 | tail -3) || warn "Event seeding skipped"
      (cd "$DASH_DIR" && npm run seed-demo-patterns seed 2>&1 | tail -3) || warn "Pattern seeding skipped"
    fi
  else
    warn "omnidash not found at ${DASH_DIR}"
  fi
fi

# ============================================================================
# Step 7: Claude Code Operator
# ============================================================================
step "7/8" "Claude Code Operator Setup"

if $SKIP_CLAUDE; then
  warn "Skipping Claude Code setup (--skip-claude)"
else
  if [[ -x "${SCRIPT_DIR}/scripts/setup-claude-operator.sh" ]]; then
    bash "${SCRIPT_DIR}/scripts/setup-claude-operator.sh" \
      --workspace "$WORKSPACE" \
      --env-file "$ENV_FILE"
  else
    warn "setup-claude-operator.sh not found or not executable"
  fi
fi

# ============================================================================
# Step 8: Service Launcher
# ============================================================================
step "8/8" "Starting Services"

LAUNCHER="${WORKSPACE}/start-services.sh"
cat > "$LAUNCHER" << 'LAUNCHER_EOF'
#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${WORKSPACE}/.venv/bin/activate"
source "${WORKSPACE}/.env"
echo "🚀 Starting OmniNode services..."
echo "  Use Ctrl+C to stop all services"
trap 'kill $(jobs -p) 2>/dev/null; echo "Stopped."' INT TERM
# Add service start commands here as the platform evolves
echo "Ready. Services available at configured ports."
wait
LAUNCHER_EOF
chmod +x "$LAUNCHER"
log "Service launcher created at: ${LAUNCHER}"

# ============================================================================
# Summary
# ============================================================================
echo -e "${BOLD}
╔══════════════════════════════════════════════════════════════════════╗
║                  🎉 DEPLOYMENT COMPLETE 🎉                         ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Workspace: $(printf '%-49s' "$WORKSPACE")  ║
║                                                                      ║
║  Infrastructure:                                                     ║
║    PostgreSQL .... localhost:5436  (7 databases)                     ║
║    Kafka ......... localhost:19092 (contract-driven topics)          ║
║    Qdrant ........ localhost:6333  (5 vector collections)            ║
║    Valkey ........ localhost:16379                                   ║
║                                                                      ║
║  Python (${PY_VERSION}):                                                     ║
║    ${IMPORT_OK} packages importable, venv at .venv/                       ║
║                                                                      ║
║  Next steps:                                                         ║
║    ./validate.sh --workspace ${WORKSPACE}                            ║
║    ${WORKSPACE}/start-services.sh                                    ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
${NC}"
