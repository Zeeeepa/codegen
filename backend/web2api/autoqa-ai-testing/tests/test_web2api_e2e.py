#!/usr/bin/env python3
"""
End-to-end test for Web2API with k2think.ai

This script tests the complete flow:
1. Register service
2. Trigger discovery
3. Execute chat completion via OpenAI API
4. Validate response
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import httpx


# Configuration
API_BASE_URL = os.environ.get("WEB2API_URL", "http://localhost:8000")
K2THINK_URL = "https://k2think.ai"
K2THINK_EMAIL = os.environ.get("K2THINK_EMAIL", "developer@pixelium.uk")
K2THINK_PASSWORD = os.environ.get("K2THINK_PASSWORD", "developer123")


async def test_register_service():
    """Test 1: Register k2think service"""
    print("\n" + "="*60)
    print("TEST 1: Register Service")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/services",
            json={
                "name": "k2think",
                "url": K2THINK_URL,
                "description": "K2Think AI Service",
                "credentials": {
                    "email": K2THINK_EMAIL,
                    "password": K2THINK_PASSWORD
                }
            },
            timeout=30.0
        )

        if response.status_code == 201:
            data = response.json()
            print(f"✅ Service registered successfully")
            print(f"   ID: {data['id']}")
            print(f"   Name: {data['name']}")
            print(f"   Status: {data['status']}")
            return data['id']
        else:
            print(f"❌ Failed to register service: {response.status_code}")
            print(f"   Response: {response.text}")
            return None


async def test_list_services():
    """Test 2: List all services"""
    print("\n" + "="*60)
    print("TEST 2: List Services")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/services",
            timeout=10.0
        )

        if response.status_code == 200:
            services = response.json()
            print(f"✅ Found {len(services)} service(s)")
            for service in services:
                print(f"   - {service['name']} ({service['status']})")
            return services
        else:
            print(f"❌ Failed to list services: {response.status_code}")
            return []


async def test_trigger_discovery(service_id: str):
    """Test 3: Trigger service discovery"""
    print("\n" + "="*60)
    print("TEST 3: Trigger Discovery")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/services/{service_id}/discover",
            timeout=10.0
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Discovery triggered")
            print(f"   Status: {data['status']}")
            return True
        else:
            print(f"❌ Failed to trigger discovery: {response.status_code}")
            return False


async def test_chat_completion():
    """Test 4: Send chat completion via OpenAI API"""
    print("\n" + "="*60)
    print("TEST 4: Chat Completion (OpenAI-compatible)")
    print("="*60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        request_data = {
            "model": "k2think",
            "messages": [
                {
                    "role": "user",
                    "content": "Write a haiku about programming"
                }
            ]
        }

        print(f"   Sending request to {API_BASE_URL}/v1/chat/completions")
        print(f"   Model: {request_data['model']}")
        print(f"   Message: {request_data['messages'][0]['content']}")

        response = await client.post(
            f"{API_BASE_URL}/v1/chat/completions",
            json=request_data
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Chat completion successful!")
            print(f"   ID: {data['id']}")
            print(f"   Model: {data['model']}")
            print(f"   Tokens: {data['usage']['total_tokens']}")
            print(f"\n   Response:")
            choice = data['choices'][0]
            message = choice['message']['content']
            print(f"   {message}")
            return True
        else:
            print(f"\n❌ Chat completion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False


async def test_list_models():
    """Test 5: List available models"""
    print("\n" + "="*60)
    print("TEST 5: List Models")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/v1/models",
            timeout=10.0
        )

        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            print(f"✅ Found {len(models)} model(s)")
            for model in models:
                print(f"   - {model['id']} (owned_by: {model['owned_by']})")
            return True
        else:
            print(f"❌ Failed to list models: {response.status_code}")
            return False


async def test_health_check():
    """Test 0: Health check"""
    print("\n" + "="*60)
    print("TEST 0: Health Check")
    print("="*60)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/health",
                timeout=5.0
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Server is healthy")
                print(f"   Status: {data['status']}")
                print(f"   Browser connected: {data['browser_connected']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print(f"   Make sure server is running at {API_BASE_URL}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Web2API End-to-End Test Suite")
    print("="*60)
    print(f"API URL: {API_BASE_URL}")
    print(f"Target Service: {K2THINK_URL}")
    print(f"Test started at: {datetime.now().isoformat()}")

    results = []

    # Test 0: Health check
    results.append(("Health Check", await test_health_check()))

    if not results[-1][1]:
        print("\n❌ Server is not available. Exiting tests.")
        return

    # Test 1: Register service
    service_id = await test_register_service()
    results.append(("Register Service", service_id is not None))

    if not service_id:
        print("\n❌ Could not register service. Exiting tests.")
        return

    # Test 2: List services
    services = await test_list_services()
    results.append(("List Services", len(services) > 0))

    # Test 3: Trigger discovery
    discovery_ok = await test_trigger_discovery(service_id)
    results.append(("Trigger Discovery", discovery_ok))

    # Wait for discovery to complete
    print("\n⏳ Waiting 10 seconds for discovery to complete...")
    await asyncio.sleep(10)

    # Test 4: Chat completion
    chat_ok = await test_chat_completion()
    results.append(("Chat Completion", chat_ok))

    # Test 5: List models
    models_ok = await test_list_models()
    results.append(("List Models", models_ok))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "-"*60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
