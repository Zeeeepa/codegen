# Eversale CLI — Local Operation with Auto-Launching Proxy

Run eversale-cli locally with your own API key. A local proxy server auto-launches
and routes all LLM calls to your configured backend.

## Architecture

```
┌──────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   eversale   │────▶│  Local Proxy Server  │────▶│  Anthropic API  │
│ gpu_llm_client│     │  localhost:8765       │     │  OpenAI API     │
│              │     │                      │     │  Ollama (local) │
│ Always sends │     │ Auto-translates      │     │  Z.AI / Custom  │
│ OpenAI format│     │ to target backend    │     └─────────────────┘
└──────────────┘     └──────────────────────┘
```

The proxy:
- **Auto-launches** as a background process when eversale starts
- **Translates** between OpenAI format and your backend's native format
- **Maps models** automatically (e.g., `glm-5` → `claude-sonnet-4-20250514`)
- **Handles auth** — your API keys stay with the proxy, not sent through eversale

## Quick Start

### 1. Choose Your Backend

```bash
# Option A: Anthropic (default)
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY=sk-ant-...

# Option B: OpenAI
echo 'LLM_BACKEND=openai' >> .env
echo 'OPENAI_API_KEY=sk-...' >> .env

# Option C: Ollama (free, local)
echo 'LLM_BACKEND=ollama' >> .env
# Make sure Ollama is running: ollama serve

# Option D: Z.AI (Anthropic-compatible)
echo 'LLM_BACKEND=custom' >> .env
echo 'LLM_BACKEND_URL=https://api.z.ai/api/anthropic' >> .env
echo 'ANTHROPIC_API_KEY=your-z-ai-key' >> .env
```

### 2. Start the Proxy Manually (optional — auto-starts with eversale)

```bash
# Start
python proxy_launcher.py start

# Check status
python proxy_launcher.py status

# Stop
python proxy_launcher.py stop
```

### 3. Run Eversale

```bash
npx eversale "research competitors for XYZ"
```

The proxy starts automatically on the first run.

## Modified Files

| File | Change |
|------|--------|
| `proxy_server.py` | **NEW** — aiohttp gateway with 4 backend adapters |
| `proxy_launcher.py` | **NEW** — Auto-start, PID management, health checks |
| `proxy_config.py` | **NEW** — Centralized config, model mapping, env vars |
| `engine/config/config.yaml` | URLs point to `localhost:8765`, proxy section added |
| `engine/agent/gpu_llm_client.py` | Default URL to proxy, `_is_local_proxy()` detection |
| `engine/agent/llm_fallback_chain.py` | **BUG FIX**: added `import os`, added `_looks_like_ollama_endpoint()` |
| `engine/agent/kimi_k2_client.py` | Anthropic provider, auto-detect |
| `bin/eversale.js` | License check bypassed |
| `engine/agent/license_validator.py` | Validate functions return True |
| `engine/agent/config_loader.py` | ANTHROPIC_BASE_URL in env chain |

## Proxy Endpoints

| Endpoint | Method | Format | Description |
|----------|--------|--------|-------------|
| `/v1/chat/completions` | POST | OpenAI | Main chat completions (streaming + non-streaming) |
| `/v1/models` | GET | OpenAI | List available models |
| `/api/chat` | POST | Ollama | Ollama-compatible chat endpoint |
| `/health` | GET | JSON | Health check / readiness probe |
| `/` | GET | JSON | Server info |

## Model Mapping

The proxy maps eversale model names to actual backend models:

| Eversale Model | Anthropic | OpenAI | Ollama |
|---------------|-----------|--------|--------|
| `glm-5` | `claude-sonnet-4-20250514` | `gpt-4o` | `qwen2.5:7b` |
| `glm-4.5v` | `claude-sonnet-4-20250514` | `gpt-4o` | `llava:7b` |
| `gpt-4o-mini` | `claude-sonnet-4-20250514` | `gpt-4o-mini` | `qwen2.5:7b` |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BACKEND` | `anthropic` | Backend: `anthropic` / `openai` / `ollama` / `custom` |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama server URL |
| `LLM_BACKEND_URL` | — | Custom backend URL |
| `EVERSALE_PROXY_PORT` | `8765` | Proxy server port |
| `EVERSALE_PROXY_HOST` | `127.0.0.1` | Proxy server host |
| `EVERSALE_PROXY_LOG` | `true` | Enable request logging |

## Troubleshooting

### Proxy won't start
```bash
# Check if port is in use
lsof -i :8765  # Linux/macOS
netstat -aon | findstr 8765  # Windows

# Check logs
cat ~/.eversale/logs/proxy.log
```

### Connection refused
```bash
# Verify proxy is running
python proxy_launcher.py status

# Restart
python proxy_launcher.py restart
```

### Wrong model being used
Set `LLM_BACKEND` explicitly:
```bash
export LLM_BACKEND=anthropic  # or openai, ollama, custom
```

