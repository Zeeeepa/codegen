---
skill_id: mcp-manager
mcp_server: foxruv-agent
category: meta
tags: [management, automation, maintenance]
agent_db_tracking: false
---

# MCP Manager - Meta Skill

## Purpose

This is a **meta skill** for managing the MCP skill system itself. It doesn't invoke an external MCP server, but provides commands for maintaining skills.

## Commands

### Import Global MCPs

Import MCPs from `~/.claude/settings.json` into this project as skills.

```bash
npx foxruv-agent mcp import [options]
```

**Options:**
- `--backup` - Backup Claude settings before modification (default: true)
- `--disable-global` - Remove global MCPs after import
- `--dry-run` - Show what would be imported without changes

**Example:**
```bash
# Import with backup, keep global MCPs enabled
npx foxruv-agent mcp import --backup --no-disable-global

# Import and disable global MCPs (project-only)
npx foxruv-agent mcp import --disable-global

# See what would be imported
npx foxruv-agent mcp import --dry-run
```

### Synchronize Index

Scan `mcp-skills/` and update `INDEX.md` with all skill files.

```bash
npx foxruv-agent mcp sync-index
```

Use this after:
- Manually creating new skill files
- Deleting obsolete skills
- Reorganizing skill categories

### Initialize Infrastructure

Set up FoxRuv agent infrastructure in a new project.

```bash
npx foxruv-agent init [options]
```

**Options:**
- `--force` - Overwrite existing files
- `--no-claude-md` - Skip CLAUDE.md generation
- `--no-skills` - Skip mcp-skills directory creation

**Example:**
```bash
# Standard initialization
npx foxruv-agent init

# Force overwrite everything
npx foxruv-agent init --force

# Only create skills directory, skip CLAUDE.md
npx foxruv-agent init --no-claude-md
```

## Maintenance Workflows

### Adding a New Skill Manually

1. **Copy template:**
   ```bash
   cp mcp-skills/_template.md mcp-skills/my-new-skill.md
   ```

2. **Edit skill file:**
   - Update frontmatter (`skill_id`, `category`, `tags`)
   - Fill in tool descriptions
   - Add complete examples
   - Document common issues

3. **Sync index:**
   ```bash
   npx foxruv-agent mcp sync-index
   ```

4. **Test the skill:**
   ```bash
   npx claude-flow mcp my-new-skill --tool <tool-name> --args '{}'
   ```

### Updating an Existing Skill

1. **Edit the skill file** in `mcp-skills/<skill-id>.md`
2. **Update "Last Updated" date** in frontmatter
3. **Test changes** with example commands
4. **Commit** the updated skill file

No index sync needed unless you changed the `skill_id` or `category`.

### Removing an Obsolete Skill

1. **Delete the skill file:**
   ```bash
   rm mcp-skills/obsolete-skill.md
   ```

2. **Sync index:**
   ```bash
   npx foxruv-agent mcp sync-index
   ```

3. **Check for references:**
   ```bash
   grep -r "obsolete-skill" .
   ```

4. **Remove from CLAUDE.md** if manually listed

### Migrating to New Project

1. **Copy skill files:**
   ```bash
   cp -r old-project/mcp-skills new-project/
   ```

2. **Initialize new project:**
   ```bash
   cd new-project
   npx foxruv-agent init
   ```

3. **Sync index:**
   ```bash
   npx foxruv-agent mcp sync-index
   ```

## Integration with AgentDB

While this meta skill doesn't track its own usage, it manages skills that do.

**Tracked data per skill:**
- Total invocations
- Success/failure rates
- Common argument patterns
- Error frequencies
- Latency distributions

**Access tracking data:**
```bash
npm run iris:evaluate -- --project <name> --filter mcp_usage
```

## Automation

### Auto-import on Project Setup

Add to your project setup script:

```bash
#!/bin/bash
# setup.sh

npm install @foxruv/iris
npx foxruv-agent init
npx foxruv-agent mcp import --backup

echo "✅ FoxRuv agent infrastructure ready!"
```

### CI/CD Validation

Validate skills in CI:

```yaml
# .github/workflows/validate-skills.yml
name: Validate MCP Skills

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check skill index is synced
        run: |
          npx foxruv-agent mcp sync-index
          git diff --exit-code mcp-skills/INDEX.md

      - name: Validate skill frontmatter
        run: |
          for file in mcp-skills/*.md; do
            if [[ "$file" == *"INDEX"* ]] || [[ "$file" == *"_template"* ]]; then
              continue
            fi
            echo "Validating $file..."
            grep -q "^skill_id:" "$file" || exit 1
            grep -q "^category:" "$file" || exit 1
          done
```

### Pre-commit Hook

Ensure index stays in sync:

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Check if any skill files changed
if git diff --cached --name-only | grep -q "^mcp-skills/.*\.md$"; then
  echo "MCP skills changed, syncing index..."
  npx foxruv-agent mcp sync-index
  git add mcp-skills/INDEX.md
fi
```

## Troubleshooting

### "npx foxruv-agent not found"

**Cause:** Package not installed
**Fix:**
```bash
npm install @foxruv/iris
```

### "Permission denied"

**Cause:** CLI script not executable
**Fix:**
```bash
chmod +x node_modules/@foxruv/iris/dist/cli/foxruv-agent.js
```

### "INDEX.md out of sync"

**Cause:** Skills added/removed without syncing
**Fix:**
```bash
npx foxruv-agent mcp sync-index
```

## References

- [MCP Management Guide](../docs/guides/MCP_MANAGEMENT.md)
- [CLAUDE.md](../CLAUDE.md)
- [FoxRuv Agent Learning Core](https://github.com/ruvnet/agent-learning-core)

## See Also

- [`_template.md`](./_template.md) - Template for new skills
- [`INDEX.md`](./INDEX.md) - Complete skill directory
