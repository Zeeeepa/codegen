#!/usr/bin/env python3
"""
Eversale CLI - Local Agent Verification Script
Tests all 7 code changes for local operation with Z.AI Anthropic-compatible API.
"""

import os
import sys
import json
import asyncio
import importlib
import traceback

# Set environment variables BEFORE any imports
os.environ.setdefault('ANTHROPIC_API_KEY', os.environ.get('ANTHROPIC_API_KEY', 'your-api-key-here'))
os.environ['ANTHROPIC_BASE_URL'] = 'https://api.z.ai/api/anthropic'
os.environ['ANTHROPIC_MODEL'] = 'glm-5'
os.environ['ANTHROPIC_DEFAULT_OPUS_MODEL'] = 'glm-5'
os.environ['ANTHROPIC_DEFAULT_SONNET_MODEL'] = 'glm-5'
os.environ['ANTHROPIC_DEFAULT_HAIKU_MODEL'] = 'glm-5'

# Add engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine', 'agent'))

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
WARN = "\033[93m⚠️  WARN\033[0m"

results = []

def test(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((name, condition))
    print(f"  {status} {name}")
    if detail:
        print(f"         {detail}")
    return condition


print("=" * 65)
print("  🔧 EVERSALE CLI — Local Agent Verification")
print("  API: Z.AI Anthropic-compatible | Model: GLM-5")
print("=" * 65)

# =========================================================
# TEST 1: Config YAML
# =========================================================
print("\n📋 TEST 1: config.yaml")
import yaml
with open('engine/config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

test("LLM mode is 'local'", config['llm']['mode'] == 'local', f"mode={config['llm']['mode']}")
test("base_url points to Z.AI", 'z.ai' in config['llm'].get('base_url', ''), f"base_url={config['llm'].get('base_url')}")
test("main_model is glm-5", config['llm']['main_model'] == 'glm-5', f"main_model={config['llm']['main_model']}")
test("vision_model is glm-5", config['llm']['vision_model'] == 'glm-5')
test("No eversale.io references in LLM URLs",
     'eversale.io' not in str(config['llm'].get('base_url', '')) and 
     'eversale.io' not in str(config['llm'].get('remote_url', '')))
test("strategic_planner uses glm-5", config['strategic_planner']['primary_llm'] == 'glm-5')
test("dual_llm uses glm-5", config['dual_llm']['orchestrator_model'] == 'glm-5')

# =========================================================
# TEST 2: gpu_llm_client.py
# =========================================================
print("\n📋 TEST 2: gpu_llm_client.py")
try:
    from gpu_llm_client import GPULLMClient, GPU_LLM_URL, GPU_MODELS
    
    test("GPU_LLM_URL reads ANTHROPIC_BASE_URL", 'z.ai' in GPU_LLM_URL or 'ANTHROPIC' in str(GPU_LLM_URL), 
         f"GPU_LLM_URL={GPU_LLM_URL}")
    
    client = GPULLMClient()
    test("Client base_url uses Z.AI", 'z.ai' in client.base_url, f"base_url={client.base_url}")
    test("Client is NOT eversale proxy", not client._is_eversale_proxy())
    test("API token loaded from ANTHROPIC_API_KEY", bool(client.api_token), f"token_len={len(client.api_token) if client.api_token else 0}")
    
    test("GPU_MODELS use glm-5", all('glm-5' in v for v in GPU_MODELS.values()),
         f"models={GPU_MODELS}")
except Exception as e:
    test("gpu_llm_client import", False, f"Error: {e}")
    traceback.print_exc()

# =========================================================
# TEST 3: llm_fallback_chain.py
# =========================================================
print("\n📋 TEST 3: llm_fallback_chain.py")
try:
    # Read the file content to check defaults
    with open('engine/agent/llm_fallback_chain.py', 'r') as f:
        fc_content = f.read()
    
    test("Fallback chain defaults to ANTHROPIC_BASE_URL",
         "os.environ.get('ANTHROPIC_BASE_URL'" in fc_content)
    test("Main model defaults to ANTHROPIC_MODEL",
         "os.environ.get('ANTHROPIC_MODEL'" in fc_content)
    test("No eversale.io in defaults",
         'eversale.io/api/llm' not in fc_content.split('os.environ.get')[0] if 'os.environ.get' in fc_content else True)
except Exception as e:
    test("llm_fallback_chain.py read", False, f"Error: {e}")

# =========================================================
# TEST 4: kimi_k2_client.py
# =========================================================
print("\n📋 TEST 4: kimi_k2_client.py")
try:
    with open('engine/agent/kimi_k2_client.py', 'r') as f:
        kimi_content = f.read()
    
    test("Anthropic provider added to PROVIDERS", '"anthropic"' in kimi_content)
    test("Auto-detect tries anthropic first", '["anthropic", "moonshot"' in kimi_content)
    test("ANTHROPIC_API_KEY in env_key", '"ANTHROPIC_API_KEY"' in kimi_content)
except Exception as e:
    test("kimi_k2_client.py read", False, f"Error: {e}")

# =========================================================
# TEST 5: eversale.js license bypass
# =========================================================
print("\n📋 TEST 5: bin/eversale.js license bypass")
try:
    with open('bin/eversale.js', 'r') as f:
        js_content = f.read()
    
    test("hasLicense = true (bypassed)", 'const hasLicense = true;' in js_content)
    test("No fs.existsSync(LICENSE_FILE) check", 'fs.existsSync(LICENSE_FILE)' not in js_content)
except Exception as e:
    test("eversale.js read", False, f"Error: {e}")

# =========================================================
# TEST 6: license_validator.py
# =========================================================
print("\n📋 TEST 6: license_validator.py")
try:
    from license_validator import validate_license_sync, validate_license
    
    is_valid, message = validate_license_sync()
    test("validate_license_sync() returns True", is_valid, f"msg={message}")
    test("Message mentions local mode", 'local' in message.lower() or 'bypassed' in message.lower(),
         f"msg={message}")
    
    # Test async version
    loop = asyncio.new_event_loop()
    is_valid_async, msg_async = loop.run_until_complete(validate_license())
    loop.close()
    test("validate_license() async returns True", is_valid_async, f"msg={msg_async}")
except Exception as e:
    test("license_validator import", False, f"Error: {e}")
    traceback.print_exc()

# =========================================================
# TEST 7: config_loader.py
# =========================================================
print("\n📋 TEST 7: config_loader.py")
try:
    with open('engine/agent/config_loader.py', 'r') as f:
        cl_content = f.read()
    
    test("ANTHROPIC_BASE_URL in env chain", "ANTHROPIC_BASE_URL" in cl_content)
    test("Z.AI as fallback URL", "z.ai" in cl_content)
    test("glm-5 in LOCAL_MODEL_MAPPING", '"glm-5": "glm-5"' in cl_content)
    test("UI-TARS mapped to glm-5", '"0000/ui-tars-1.5-7b:latest": "glm-5"' in cl_content)
except Exception as e:
    test("config_loader.py read", False, f"Error: {e}")

# =========================================================
# TEST 8: Live API call to Z.AI
# =========================================================
print("\n📋 TEST 8: Live API call to Z.AI Anthropic endpoint")
try:
    import urllib.request
    import urllib.error
    
    url = "https://api.z.ai/api/anthropic/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": os.environ['ANTHROPIC_API_KEY'],
        "anthropic-version": "2023-06-01",
    }
    data = json.dumps({
        "model": "glm-5",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "Say hello in exactly 5 words."}]
    }).encode()
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_data = json.loads(resp.read().decode())
            content = response_data.get('content', [{}])[0].get('text', '')
            model_used = response_data.get('model', 'unknown')
            test("API responds successfully", resp.status == 200, f"status={resp.status}")
            test("Got response content", bool(content), f"response='{content[:80]}'")
            test("Model reported", bool(model_used), f"model={model_used}")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else 'No body'
        test("API responds successfully", False, f"HTTP {e.code}: {body[:200]}")
    except urllib.error.URLError as e:
        test("API responds successfully", False, f"URL Error: {e.reason}")
except Exception as e:
    test("Live API call", False, f"Error: {e}")
    traceback.print_exc()

# =========================================================
# SUMMARY
# =========================================================
print("\n" + "=" * 65)
passed = sum(1 for _, ok in results if ok)
total = len(results)
pct = (passed / total * 100) if total > 0 else 0

if passed == total:
    print(f"  🎉 ALL {total} TESTS PASSED ({pct:.0f}%)")
else:
    failed = total - passed
    print(f"  📊 {passed}/{total} passed, {failed} failed ({pct:.0f}%)")
    print("\n  Failed tests:")
    for name, ok in results:
        if not ok:
            print(f"    ❌ {name}")

print("=" * 65)
sys.exit(0 if passed == total else 1)
