#!/usr/bin/env python3
"""
Eversale Local Proxy Server — Auto-launching API Gateway

A lightweight aiohttp server that sits between eversale's LLM client
and the actual LLM backend. Translates requests between formats and
routes to the configured backend (Anthropic, OpenAI, Ollama, or custom).

Endpoints exposed:
  POST /v1/chat/completions  — OpenAI-compatible chat completions
  GET  /v1/models            — Model listing
  POST /api/chat             — Ollama-compatible chat
  GET  /health               — Health check

Usage:
  python proxy_server.py                    # Start with env var config
  python proxy_server.py --port 8765        # Override port
  python proxy_server.py --backend openai   # Override backend
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
from typing import Dict, Any, Optional

import aiohttp
from aiohttp import web

from proxy_config import ProxyConfig

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("eversale.proxy")


def setup_logging(config: ProxyConfig) -> None:
    """Configure logging to console and optionally to file."""
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(fmt)
    logger.addHandler(console)
    logger.setLevel(logging.INFO)

    if config.log_file:
        os.makedirs(os.path.dirname(config.log_file), exist_ok=True)
        fh = logging.FileHandler(config.log_file)
        fh.setFormatter(fmt)
        logger.addHandler(fh)


# ---------------------------------------------------------------------------
# Backend Adapters
# ---------------------------------------------------------------------------
class BackendAdapter:
    """Base class for LLM backend adapters."""

    def __init__(self, config: ProxyConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(
                total=self.config.request_timeout,
                connect=self.config.connect_timeout,
            )
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def chat_completions(
        self, request: web.Request, payload: Dict[str, Any], stream: bool = False
    ) -> web.Response:
        raise NotImplementedError

    async def list_models(self) -> web.Response:
        raise NotImplementedError


class AnthropicAdapter(BackendAdapter):
    """Translates OpenAI-format requests to Anthropic Messages API."""

    async def chat_completions(
        self, request: web.Request, payload: Dict[str, Any], stream: bool = False
    ) -> web.Response:
        session = await self.get_session()
        base_url = self.config.get_backend_url()
        url = f"{base_url}/v1/messages"

        # Map model name
        model = self.config.map_model(payload.get("model", "glm-5"))

        # Extract system message
        messages = payload.get("messages", [])
        system_text = ""
        user_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_text += msg.get("content", "") + "\n"
            else:
                user_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })

        # Build Anthropic request
        anthropic_payload: Dict[str, Any] = {
            "model": model,
            "messages": user_messages if user_messages else [{"role": "user", "content": "Hello"}],
            "max_tokens": payload.get("max_tokens", 4096),
            "temperature": payload.get("temperature", 0.1),
        }
        if system_text.strip():
            anthropic_payload["system"] = system_text.strip()
        if stream:
            anthropic_payload["stream"] = True

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.get_api_key(),
            "anthropic-version": self.config.anthropic_api_version,
        }

        if stream:
            return await self._stream_anthropic(request, session, url, anthropic_payload, headers, model)
        else:
            return await self._non_stream_anthropic(session, url, anthropic_payload, headers, model)

    async def _non_stream_anthropic(
        self, session, url, payload, headers, model
    ) -> web.Response:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                logger.error(f"Anthropic error {resp.status}: {error_text}")
                return web.json_response(
                    {"error": {"message": error_text, "type": "backend_error"}},
                    status=resp.status,
                )
            data = await resp.json()

        # Translate Anthropic response → OpenAI format
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        openai_response = {
            "id": data.get("id", f"chatcmpl-{int(time.time())}"),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": _map_stop_reason(data.get("stop_reason")),
                }
            ],
            "usage": {
                "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
                "total_tokens": (
                    data.get("usage", {}).get("input_tokens", 0)
                    + data.get("usage", {}).get("output_tokens", 0)
                ),
            },
        }
        return web.json_response(openai_response)

    async def _stream_anthropic(
        self, request, session, url, payload, headers, model
    ) -> web.StreamResponse:
        response = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(request)

        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                error_event = _sse_event(
                    {"error": {"message": error_text, "type": "backend_error"}}
                )
                await response.write(error_event.encode())
                await response.write(b"data: [DONE]\n\n")
                return response

            chunk_id = f"chatcmpl-{int(time.time())}"
            async for line in resp.content:
                decoded = line.decode("utf-8", errors="replace").strip()
                if not decoded.startswith("data: "):
                    continue
                json_str = decoded[6:]
                if json_str == "[DONE]":
                    await response.write(b"data: [DONE]\n\n")
                    break

                try:
                    event = json.loads(json_str)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type", "")

                if event_type == "content_block_delta":
                    delta_text = event.get("delta", {}).get("text", "")
                    if delta_text:
                        openai_chunk = {
                            "id": chunk_id,
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": delta_text},
                                    "finish_reason": None,
                                }
                            ],
                        }
                        await response.write(
                            f"data: {json.dumps(openai_chunk)}\n\n".encode()
                        )

                elif event_type == "message_stop":
                    final_chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "finish_reason": "stop",
                            }
                        ],
                    }
                    await response.write(
                        f"data: {json.dumps(final_chunk)}\n\n".encode()
                    )
                    await response.write(b"data: [DONE]\n\n")

        return response

    async def list_models(self) -> web.Response:
        models = list(self.config.model_map_anthropic.values())
        unique_models = list(dict.fromkeys(models))
        return web.json_response({
            "object": "list",
            "data": [
                {
                    "id": m,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "anthropic",
                }
                for m in unique_models
            ],
        })


class OpenAIAdapter(BackendAdapter):
    """Passes through OpenAI-format requests with model mapping and key injection."""

    async def chat_completions(
        self, request: web.Request, payload: Dict[str, Any], stream: bool = False
    ) -> web.Response:
        session = await self.get_session()
        base_url = self.config.get_backend_url()
        url = f"{base_url}/chat/completions"

        # Map model name
        payload["model"] = self.config.map_model(payload.get("model", "glm-5"))
        payload["stream"] = stream

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.get_api_key()}",
        }

        if stream:
            return await self._stream_passthrough(request, session, url, payload, headers)
        else:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    return web.json_response(
                        {"error": {"message": error_text}}, status=resp.status
                    )
                data = await resp.json()
                return web.json_response(data)

    async def _stream_passthrough(
        self, request, session, url, payload, headers
    ) -> web.StreamResponse:
        response = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(request)

        async with session.post(url, json=payload, headers=headers) as resp:
            async for chunk in resp.content.iter_any():
                await response.write(chunk)

        return response

    async def list_models(self) -> web.Response:
        session = await self.get_session()
        base_url = self.config.get_backend_url()
        headers = {"Authorization": f"Bearer {self.config.get_api_key()}"}
        try:
            async with session.get(f"{base_url}/models", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return web.json_response(data)
        except Exception as e:
            logger.warning(f"Failed to list OpenAI models: {e}")
        return web.json_response({"object": "list", "data": []})


class OllamaAdapter(BackendAdapter):
    """Translates OpenAI-format requests to Ollama API format."""

    async def chat_completions(
        self, request: web.Request, payload: Dict[str, Any], stream: bool = False
    ) -> web.Response:
        session = await self.get_session()
        base_url = self.config.get_backend_url()
        url = f"{base_url}/api/chat"

        model = self.config.map_model(payload.get("model", "glm-5"))
        messages = payload.get("messages", [])

        ollama_payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": payload.get("temperature", 0.1),
                "num_predict": payload.get("max_tokens", 2000),
            },
            "stream": stream,
        }

        if stream:
            return await self._stream_ollama(request, session, url, ollama_payload, model)
        else:
            return await self._non_stream_ollama(session, url, ollama_payload, model)

    async def _non_stream_ollama(
        self, session, url, payload, model
    ) -> web.Response:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                return web.json_response(
                    {"error": {"message": error_text}}, status=resp.status
                )
            data = await resp.json()

        content = data.get("message", {}).get("content", "")
        tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)

        openai_response = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": tokens,
            },
        }
        return web.json_response(openai_response)

    async def _stream_ollama(
        self, request, session, url, payload, model
    ) -> web.StreamResponse:
        response = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(request)

        chunk_id = f"chatcmpl-{int(time.time())}"
        async with session.post(url, json=payload) as resp:
            async for line in resp.content:
                decoded = line.decode("utf-8", errors="replace").strip()
                if not decoded:
                    continue
                try:
                    data = json.loads(decoded)
                except json.JSONDecodeError:
                    continue

                content = data.get("message", {}).get("content", "")
                done = data.get("done", False)

                if content:
                    chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": content},
                                "finish_reason": None,
                            }
                        ],
                    }
                    await response.write(f"data: {json.dumps(chunk)}\n\n".encode())

                if done:
                    final_chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "finish_reason": "stop",
                            }
                        ],
                    }
                    await response.write(
                        f"data: {json.dumps(final_chunk)}\n\n".encode()
                    )
                    await response.write(b"data: [DONE]\n\n")

        return response

    async def list_models(self) -> web.Response:
        session = await self.get_session()
        base_url = self.config.get_backend_url()
        try:
            async with session.get(f"{base_url}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = data.get("models", [])
                    return web.json_response({
                        "object": "list",
                        "data": [
                            {
                                "id": m.get("name", "unknown"),
                                "object": "model",
                                "created": int(time.time()),
                                "owned_by": "ollama",
                            }
                            for m in models
                        ],
                    })
        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")

        return web.json_response({"object": "list", "data": []})


class CustomAdapter(BackendAdapter):
    """
    Passthrough adapter for custom OpenAI-compatible endpoints
    (e.g., Z.AI, LM Studio, vLLM).
    """

    async def chat_completions(
        self, request: web.Request, payload: Dict[str, Any], stream: bool = False
    ) -> web.Response:
        session = await self.get_session()
        base_url = self.config.get_backend_url()

        model = self.config.map_model(payload.get("model", "glm-5"))
        payload["model"] = model
        payload["stream"] = stream

        headers = {
            "Content-Type": "application/json",
        }
        api_key = self.config.get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            headers["x-api-key"] = api_key

        # Determine URL pattern
        if "/v1" in base_url:
            url = f"{base_url}/chat/completions"
        else:
            url = f"{base_url}/v1/chat/completions"

        if stream:
            return await self._stream_passthrough(request, session, url, payload, headers)
        else:
            async with session.post(url, json=payload, headers=headers) as resp:
                data = await resp.text()
                return web.Response(
                    text=data,
                    status=resp.status,
                    content_type=resp.content_type or "application/json",
                )

    async def _stream_passthrough(
        self, request, session, url, payload, headers
    ) -> web.StreamResponse:
        response = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(request)

        async with session.post(url, json=payload, headers=headers) as resp:
            async for chunk in resp.content.iter_any():
                await response.write(chunk)

        return response

    async def list_models(self) -> web.Response:
        return web.json_response({
            "object": "list",
            "data": [
                {
                    "id": "glm-5",
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "custom",
                }
            ],
        })


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _map_stop_reason(anthropic_reason: Optional[str]) -> str:
    """Map Anthropic stop_reason to OpenAI finish_reason."""
    mapping = {
        "end_turn": "stop",
        "stop_sequence": "stop",
        "max_tokens": "length",
    }
    return mapping.get(anthropic_reason or "", "stop")


def _sse_event(data: Any) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _get_adapter(config: ProxyConfig) -> BackendAdapter:
    """Create the appropriate backend adapter."""
    if config.backend == "anthropic":
        return AnthropicAdapter(config)
    elif config.backend == "openai":
        return OpenAIAdapter(config)
    elif config.backend == "ollama":
        return OllamaAdapter(config)
    elif config.backend == "custom":
        return CustomAdapter(config)
    else:
        logger.warning(f"Unknown backend '{config.backend}', using custom adapter")
        return CustomAdapter(config)


# ---------------------------------------------------------------------------
# Route Handlers
# ---------------------------------------------------------------------------
async def handle_chat_completions(request: web.Request) -> web.Response:
    """POST /v1/chat/completions — OpenAI-compatible endpoint."""
    adapter: BackendAdapter = request.app["adapter"]
    config: ProxyConfig = request.app["config"]

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return web.json_response(
            {"error": {"message": "Invalid JSON body"}}, status=400
        )

    stream = payload.get("stream", False)
    model = payload.get("model", "glm-5")

    if config.log_requests:
        logger.info(
            f"→ /v1/chat/completions model={model} stream={stream} "
            f"backend={config.backend} → {config.map_model(model)}"
        )

    start = time.time()
    try:
        resp = await adapter.chat_completions(request, payload, stream=stream)
        elapsed = int((time.time() - start) * 1000)
        if config.log_requests:
            logger.info(f"← Response in {elapsed}ms")
        return resp
    except aiohttp.ClientError as e:
        logger.error(f"Backend error: {e}")
        return web.json_response(
            {"error": {"message": f"Backend connection error: {e}", "type": "backend_error"}},
            status=502,
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return web.json_response(
            {"error": {"message": str(e), "type": "internal_error"}},
            status=500,
        )


async def handle_ollama_chat(request: web.Request) -> web.Response:
    """POST /api/chat — Ollama-compatible endpoint.

    Accepts Ollama-format requests and translates them to the active backend.
    """
    adapter: BackendAdapter = request.app["adapter"]
    config: ProxyConfig = request.app["config"]

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    # Translate Ollama format → OpenAI format
    model = payload.get("model", "glm-5")
    messages = payload.get("messages", [])
    stream = payload.get("stream", False)
    options = payload.get("options", {})

    openai_payload = {
        "model": model,
        "messages": messages,
        "temperature": options.get("temperature", 0.1),
        "max_tokens": options.get("num_predict", 2000),
        "stream": stream,
    }

    if config.log_requests:
        logger.info(
            f"→ /api/chat (ollama) model={model} stream={stream} "
            f"→ translated to OpenAI format"
        )

    try:
        resp = await adapter.chat_completions(request, openai_payload, stream=stream)

        # If the response is non-streaming JSON, translate back to Ollama format
        if not stream and isinstance(resp, web.Response) and resp.content_type == "application/json":
            try:
                body = json.loads(resp.body)
                if "choices" in body:
                    content = body["choices"][0]["message"]["content"]
                    ollama_resp = {
                        "message": {"role": "assistant", "content": content},
                        "model": model,
                        "done": True,
                        "eval_count": body.get("usage", {}).get("completion_tokens", 0),
                        "prompt_eval_count": body.get("usage", {}).get("prompt_tokens", 0),
                    }
                    return web.json_response(ollama_resp)
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

        return resp
    except Exception as e:
        logger.error(f"Ollama endpoint error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_models(request: web.Request) -> web.Response:
    """GET /v1/models — List available models."""
    adapter: BackendAdapter = request.app["adapter"]
    return await adapter.list_models()


async def handle_health(request: web.Request) -> web.Response:
    """GET /health — Health check."""
    config: ProxyConfig = request.app["config"]
    return web.json_response({
        "status": "ok",
        "backend": config.backend,
        "backend_url": config.get_backend_url(),
        "port": config.port,
        "timestamp": int(time.time()),
    })


async def handle_root(request: web.Request) -> web.Response:
    """GET / — Root info."""
    config: ProxyConfig = request.app["config"]
    return web.json_response({
        "name": "eversale-local-proxy",
        "version": "1.0.0",
        "backend": config.backend,
        "endpoints": [
            "POST /v1/chat/completions",
            "GET  /v1/models",
            "POST /api/chat",
            "GET  /health",
        ],
    })


# ---------------------------------------------------------------------------
# App Lifecycle
# ---------------------------------------------------------------------------
async def on_startup(app: web.Application) -> None:
    config: ProxyConfig = app["config"]
    adapter = _get_adapter(config)
    app["adapter"] = adapter
    logger.info(
        f"🚀 Eversale proxy started on {config.host}:{config.port} "
        f"→ backend={config.backend} ({config.get_backend_url()})"
    )


async def on_shutdown(app: web.Application) -> None:
    adapter: BackendAdapter = app.get("adapter")
    if adapter:
        await adapter.close()
    logger.info("Proxy server shut down")


def create_app(config: ProxyConfig) -> web.Application:
    """Create the aiohttp application."""
    app = web.Application()
    app["config"] = config

    # Routes
    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health)
    app.router.add_post("/v1/chat/completions", handle_chat_completions)
    app.router.add_get("/v1/models", handle_models)
    app.router.add_post("/api/chat", handle_ollama_chat)

    # Lifecycle
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Eversale Local Proxy Server")
    parser.add_argument("--port", type=int, help="Server port (default: from env or 8765)")
    parser.add_argument("--host", type=str, help="Server host (default: 127.0.0.1)")
    parser.add_argument("--backend", type=str, help="LLM backend (anthropic/openai/ollama/custom)")
    args = parser.parse_args()

    config = ProxyConfig.from_env()

    if args.port:
        config.port = args.port
    if args.host:
        config.host = args.host
    if args.backend:
        config.backend = args.backend

    setup_logging(config)

    app = create_app(config)
    web.run_app(app, host=config.host, port=config.port, print=None)


if __name__ == "__main__":
    main()

