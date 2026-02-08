# CodegenRestDashboard (No-deps REST UI + Commands)

This package adds a dependency-free dashboard and Node.js command scripts to interact with the Codegen REST API.

Important:
- Do NOT commit real secrets. Create CodegenRestDashboard/.env locally (see .env.example)
- The browser UI never receives your API token; a tiny local proxy server injects auth headers
- Cloudflare Worker webhook is provided separately for production webhooks

## Quick start

1) Copy .env.example to .env and fill in your values
```
cp CodegenRestDashboard/.env.example CodegenRestDashboard/.env
```

2) Start the local server (serves UI and proxies API)
```
node CodegenRestDashboard/server.js
```
Then open http://localhost:8787

3) Use commands (examples)
```
node CodegenRestDashboard/commands/create_agent_run.js --prompt "Hello" --model "Sonnet 4.5"
node CodegenRestDashboard/commands/list_agent_runs.js --state active --limit 20
node CodegenRestDashboard/commands/get_agent_run.js --id 123
node CodegenRestDashboard/commands/resume_agent_run.js --id 123 --prompt "Continue"
node CodegenRestDashboard/commands/generate_setup_commands.js --repo_id 999
```

4) Mock mode (no network)
```
CODEGEN_OFFLINE=1 node CodegenRestDashboard/server.js
```

## Files
- commands/: Node CLI scripts, no external deps
- dashboard/: Vanilla HTML/CSS/JS UI
- utils/env.js: safe .env loader (Node-only)
- utils/apiClient.js: shared REST client for Node context
- server.js: local static server + API proxy (injects Authorization)
- webhook_server.js: Cloudflare Worker handler for /webhook
- mock/: local fixtures for offline development

## Security
- .env is in .gitignore. Do not commit it.
- The token is used only in Node (server/commands). The browser never sees it.

## Webhook (Cloudflare)
- Deploy CodegenRestDashboard/webhook_server.js as a Worker (route /webhook)
- Configure your DNS so https://www.pixelium.uk/webhook points to the Worker
- Optionally set CODEGEN_WEBHOOK_SECRET and verify HMAC in the worker

## New features
- Auto-refresh only UI (no manual refresh button)
- Header shows only Active count (hover reveals top active runs)
- Compact run cards with status dots; click a completed run to open logs/resume dialog; click an active run’s “Chain” to configure multi-template chaining
- Per-run template selection and chaining (Templates tab manages templates)
- Follow-up automation sends templates in sequence on each completion cycle
- Desktop notifications (optional, via browser permission) + in-app toasts

## Extra commands
```
node CodegenRestDashboard/commands/get_agent_run_logs.js --id 123 --skip 0 --limit 100
node CodegenRestDashboard/commands/ban_agent_run.js --id 123 [--before <order>] [--after <order>]
node CodegenRestDashboard/commands/unban_agent_run.js --id 123 [--before <order>] [--after <order>]
```

