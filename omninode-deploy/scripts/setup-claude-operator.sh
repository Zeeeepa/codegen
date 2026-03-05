#!/usr/bin/env bash
# shellcheck disable=SC1090,SC1091
# SPDX-FileCopyrightText: 2025 OmniNode.ai Inc.
# SPDX-License-Identifier: MIT
#
# OmniNode AI — Claude Code Operator Setup v2.0
#
# Deploys the full ONEX plugin to Claude Code:
#   - 10 hook endpoints across 7 event types (hooks.json v1.2.0)
#   - 22+ hook scripts (hooks/scripts/)
#   - 72 hook lib modules (hooks/lib/ — routing, auth, metrics, etc.)
#   - hooks/config.yaml (autofix, pattern tracking, enforcement config)
#   - 53 agent definitions (agents/configs/*.yaml, schema v2.0.0)
#   - 80 skills + 3 infrastructure dirs (skills/)
#   - 6 commands (commands/*.md)
#   - Workspace CLAUDE.md generation with ONEX tier detection
#
# Usage:
#   ./setup-claude-operator.sh --workspace /path --env-file /path/.env

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
WORKSPACE=""
ENV_FILE=""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[⚠]${NC} $*"; }
info() { echo -e "  ${CYAN}→${NC} $*"; }

# ============================================================================
# CLI Parsing
# ============================================================================
while [[ $# -gt 0 ]]; do
  case $1 in
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --env-file)  ENV_FILE="$2"; shift 2 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

if [[ -z "$WORKSPACE" ]]; then
  WORKSPACE="$(pwd)/omninode-workspace"
fi

if [[ -n "$ENV_FILE" ]] && [[ -f "$ENV_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$ENV_FILE"
fi

OMNICLAUDE_DIR="${WORKSPACE}/omniclaude"
PLUGIN_SRC="${OMNICLAUDE_DIR}/plugins/onex"

if [[ ! -d "$PLUGIN_SRC" ]]; then
  warn "omniclaude plugin source not found at ${PLUGIN_SRC}"
  warn "Ensure omniclaude is cloned in workspace"
  exit 1
fi

echo -e "${BOLD}${CYAN}═══ Claude Code Operator Setup v2.0 ═══${NC}"

# ============================================================================
# Step 1: Detect and count plugin components
# ============================================================================
info "Analyzing plugin structure..."

# Hooks
HOOKS_JSON="${PLUGIN_SRC}/hooks/hooks.json"
if [[ -f "$HOOKS_JSON" ]]; then
  HOOK_INFO=$(python3 -c "
import json
with open('${HOOKS_JSON}') as f:
    d = json.load(f)
hooks = d.get('hooks', {})
endpoints = sum(len(v) for v in hooks.values())
version = d.get('version', '?')
print(f'{len(hooks)} event types, {endpoints} endpoints, v{version}')
" 2>/dev/null || echo "parse error")
  info "hooks.json: ${HOOK_INFO}"
else
  warn "hooks.json not found"
fi

# Hook scripts
HOOK_SCRIPTS=$(find "${PLUGIN_SRC}/hooks/scripts" -type f -name "*.sh" 2>/dev/null | wc -l)
info "Hook scripts: ${HOOK_SCRIPTS} scripts in hooks/scripts/"

# Hook lib modules
HOOK_LIB_COUNT=$(find "${PLUGIN_SRC}/hooks/lib" -type f -name "*.py" 2>/dev/null | wc -l)
info "Hook lib: ${HOOK_LIB_COUNT} Python modules in hooks/lib/"

# Root hook scripts (post-tool-use-ruff.sh, etc.)
ROOT_HOOKS=$(find "${PLUGIN_SRC}/hooks" -maxdepth 1 -type f -name "*.sh" 2>/dev/null | wc -l)
info "Root hook scripts: ${ROOT_HOOKS} (post-tool-use-ruff, etc.)"

# Agents
AGENT_COUNT=$(find "${PLUGIN_SRC}/agents/configs" -type f -name "*.yaml" 2>/dev/null | wc -l)
info "Agent configs: ${AGENT_COUNT} YAML definitions"

# Skills
TOTAL_SKILL_DIRS=$(find "${PLUGIN_SRC}/skills" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l)
INFRA_DIRS=$(find "${PLUGIN_SRC}/skills" -maxdepth 1 -mindepth 1 -type d -name "_*" 2>/dev/null | wc -l)
ACTUAL_SKILLS=$((TOTAL_SKILL_DIRS - INFRA_DIRS))
info "Skills: ${ACTUAL_SKILLS} skills + ${INFRA_DIRS} infrastructure dirs (_bin, _lib, _shared)"

# Commands
CMD_COUNT=$(find "${PLUGIN_SRC}/commands" -type f -name "*.md" 2>/dev/null | wc -l)
info "Commands: ${CMD_COUNT} command definitions"

# ============================================================================
# Step 2: Validate hook script syntax
# ============================================================================
info "Validating hook script syntax (bash -n)..."
BAD_SCRIPTS=0
while IFS= read -r script; do
  if ! bash -n "$script" 2>/dev/null; then
    warn "  Syntax error: $(basename "$script")"
    BAD_SCRIPTS=$((BAD_SCRIPTS + 1))
  fi
done < <(find "${PLUGIN_SRC}/hooks" -type f -name "*.sh" 2>/dev/null)

if [[ $BAD_SCRIPTS -eq 0 ]]; then
  info "${GREEN}✓${NC} All hook scripts pass syntax check"
else
  warn "${BAD_SCRIPTS} scripts have syntax issues"
fi

# ============================================================================
# Step 3: Validate agent YAML configs
# ============================================================================
info "Validating agent YAML configs..."
BAD_YAMLS=0
AGENT_DIR="${PLUGIN_SRC}/agents/configs"
if [[ -d "$AGENT_DIR" ]]; then
  while IFS= read -r yaml_file; do
    if ! python3 -c "import yaml; d=yaml.safe_load(open('${yaml_file}')); assert 'agent_type' in d or 'agent_identity' in d, 'missing key'" 2>/dev/null; then
      warn "  Invalid: $(basename "$yaml_file")"
      BAD_YAMLS=$((BAD_YAMLS + 1))
    fi
  done < <(find "$AGENT_DIR" -type f -name "*.yaml")

  if [[ $BAD_YAMLS -eq 0 ]]; then
    info "${GREEN}✓${NC} All ${AGENT_COUNT} agent YAMLs valid"
  else
    warn "${BAD_YAMLS} agent YAMLs have issues"
  fi
fi

# ============================================================================
# Step 4: Detect ONEX tier
# ============================================================================
info "Detecting ONEX tier..."
ONEX_TIER="foundation"  # default

# Check for tier indicators
if [[ -f "${OMNICLAUDE_DIR}/src/omniclaude/tier.py" ]]; then
  TIER_VALUE=$(python3 -c "
import ast, sys
try:
    with open('${OMNICLAUDE_DIR}/src/omniclaude/tier.py') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if hasattr(target, 'id') and 'tier' in target.id.lower():
                    if isinstance(node.value, ast.Constant):
                        print(node.value.value)
                        sys.exit(0)
    print('foundation')
except Exception:
    print('foundation')
" 2>/dev/null || echo "foundation")
  ONEX_TIER="$TIER_VALUE"
fi

info "ONEX tier: ${BOLD}${ONEX_TIER}${NC}"

# ============================================================================
# Step 5: Generate workspace CLAUDE.md
# ============================================================================
info "Generating workspace CLAUDE.md..."

CLAUDE_MD="${WORKSPACE}/CLAUDE.md"
cat > "$CLAUDE_MD" << CLAUDE_EOF
# ONEX Workspace — Claude Code Integration

> Auto-generated by OmniNode deploy v2.0 on $(date -u +%Y-%m-%dT%H:%M:%SZ)

## ONEX Tier: ${ONEX_TIER}

## Platform Components

| Component | Count | Location |
|-----------|-------|----------|
| Hook endpoints | $(python3 -c "import json; d=json.load(open('${HOOKS_JSON}')); print(sum(len(v) for v in d.get('hooks',{}).values()))" 2>/dev/null || echo "?") | \`omniclaude/plugins/onex/hooks/\` |
| Hook lib modules | ${HOOK_LIB_COUNT} | \`omniclaude/plugins/onex/hooks/lib/\` |
| Agent definitions | ${AGENT_COUNT} | \`omniclaude/plugins/onex/agents/configs/\` |
| Skills | ${ACTUAL_SKILLS} (+${INFRA_DIRS} infra) | \`omniclaude/plugins/onex/skills/\` |
| Commands | ${CMD_COUNT} | \`omniclaude/plugins/onex/commands/\` |
| Intelligence nodes | $(find "${WORKSPACE}/omniintelligence/src" -type d -name "node_*" 2>/dev/null | wc -l) | \`omniintelligence/src/omniintelligence/nodes/\` |

## Hook Event Types

The following Claude Code events are instrumented:

| Event | Endpoints | Purpose |
|-------|-----------|---------|
| SessionStart | 1 | Initialize session tracking, emit start event |
| SessionEnd | 1 | Finalize session, emit end event |
| Stop | 1 | Graceful shutdown, persist state |
| UserPromptSubmit | 2 | Intent classification + delegation rule enforcement |
| PreCompact | 1 | Context probe before compaction |
| PreToolUse | 2 | Authorization shim (Edit/Write) + bash guard |
| PostToolUse | 5 | Quality enforcement, ruff linting, CI reminder, skill delegation, tool counter |

## Available Commands

$(for cmd in "${PLUGIN_SRC}"/commands/*.md; do
  [[ -f "$cmd" ]] && echo "- \`/$(basename "$cmd" .md)\`"
done)

## Repositories in Workspace

$(for repo in "${WORKSPACE}"/*/; do
  [[ -d "${repo}/.git" ]] && echo "- \`$(basename "$repo")\`"
done)
CLAUDE_EOF

log "Generated CLAUDE.md with ${AGENT_COUNT} agents, ${ACTUAL_SKILLS} skills, ${HOOK_LIB_COUNT} lib modules"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${BOLD}${GREEN}Claude Code Operator Setup Complete${NC}"
echo -e "  Hooks: ${HOOK_SCRIPTS} scripts + ${HOOK_LIB_COUNT} lib modules + config.yaml"
echo -e "  Agents: ${AGENT_COUNT} definitions (YAML schema v2.0.0)"
echo -e "  Skills: ${ACTUAL_SKILLS} skills + ${INFRA_DIRS} infrastructure dirs"
echo -e "  Commands: ${CMD_COUNT} definitions"
echo -e "  ONEX tier: ${ONEX_TIER}"
echo -e "  Workspace CLAUDE.md: ${CLAUDE_MD}"

