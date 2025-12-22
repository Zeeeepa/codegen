# MCP Skill Directory

All MCPs for this project are **on-demand skills**, invoked via `npx claude-flow mcp ...`.

## How to Use

1. **Find a skill**: Browse this index or search `mcp-skills/*.md`
2. **Read the docs**: Open the skill file to see available tools and examples
3. **Propose command**: Let Claude suggest the exact CLI invocation
4. **Execute**: Run the command and track results in AgentDB

## Skills

<!-- SKILLS_LIST_START -->
*No skills yet. Run `npx iris mcp import` to populate.*
<!-- SKILLS_LIST_END -->

## Adding New Skills

### From Global MCPs

```bash
npx iris mcp import
```

### Manually

1. Copy `_template.md` to `<skill-id>.md`
2. Fill in skill details, tools, and examples
3. Run `npx iris mcp sync-index` to update this file

## Skill File Format

Each skill includes:

- **Frontmatter**: `skill_id`, `mcp_server`, `category`, `tags`, `agent_db_tracking`
- **Purpose**: What this skill does
- **Tools**: Available MCP tools with usage examples
- **Examples**: Copy-paste ready command-line examples
- **Integration**: How it connects to AgentDB, Iris, etc.

See `_template.md` for a complete template.

## Categories

Skills are organized by category:

- **Payments**: Stripe, billing, subscriptions
- **Development**: GitHub, GitLab, CI/CD
- **Data**: Databases, APIs, data processing
- **Communication**: Slack, email, WhatsApp
- **Infrastructure**: AWS, Docker, Kubernetes
- **Custom**: Project-specific integrations

## See Also

- [MCP Management Guide](../docs/guides/MCP_MANAGEMENT.md)
- [CLAUDE.md](../CLAUDE.md) - AI operating instructions
- [Iris Docs](../docs/guides/IRIS_PRIME_GUIDE.md)
