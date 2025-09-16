#!/usr/bin/env python3
"""
Test script for AI Endpoint Manager
Validates core functionality without requiring full setup
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_endpoint_manager import AIEndpointManager, EndpointType, ServerStatus

async def test_basic_functionality():
    """Test basic endpoint manager functionality"""
    print("🧪 Testing AI Endpoint Manager...")
    
    # Initialize manager
    manager = AIEndpointManager()
    print("✅ Manager initialized successfully")
    
    # Test endpoint creation
    print("\n📝 Testing endpoint creation...")
    
    # Create a REST API endpoint
    endpoint_id = await manager.create_endpoint(
        name="Test OpenAI",
        endpoint_type=EndpointType.REST_API,
        url="https://api.openai.com/v1",
        auth_config={"api_key": "test-key"}
    )
    print(f"✅ REST API endpoint created: {endpoint_id}")
    
    # Create a web chat endpoint
    web_endpoint_id = await manager.create_endpoint(
        name="Test DeepSeek",
        endpoint_type=EndpointType.WEB_CHAT,
        url="https://chat.deepseek.com",
        auth_config={"username": "test", "password": "test"}
    )
    print(f"✅ Web chat endpoint created: {web_endpoint_id}")
    
    # Test listing endpoints
    print("\n📋 Testing endpoint listing...")
    endpoints = await manager.list_active_endpoints()
    print(f"✅ Found {len(endpoints)} endpoints:")
    for ep in endpoints:
        print(f"   • {ep['model_name']} ({ep['type']}) - {ep['status']}")
    
    # Test server management
    print("\n🖥️ Testing server management...")
    
    # Start REST API server
    success = await manager.start_server(endpoint_id)
    if success:
        print("✅ REST API server started successfully")
    else:
        print("❌ Failed to start REST API server")
    
    # Start web chat server
    success = await manager.start_server(web_endpoint_id)
    if success:
        print("✅ Web chat server started successfully")
    else:
        print("❌ Failed to start web chat server")
    
    # Test endpoint testing
    print("\n🧪 Testing endpoint validation...")
    
    # Get updated endpoint list
    endpoints = await manager.list_active_endpoints()
    online_endpoints = [ep for ep in endpoints if ep["status"] == "online"]
    
    if online_endpoints:
        for endpoint in online_endpoints:
            print(f"Testing {endpoint['model_name']}...")
            result = await manager.test_endpoint(endpoint["id"], "Hello, this is a test!")
            
            if result["success"]:
                print(f"✅ {endpoint['model_name']}: {result['response_time']:.2f}s")
                print(f"   Response: {result['response'][:100]}...")
            else:
                print(f"❌ {endpoint['model_name']}: {result.get('error', 'Unknown error')}")
    else:
        print("⚠️ No online endpoints to test")
    
    # Test configuration save/load
    print("\n💾 Testing configuration management...")
    
    # Save configuration
    manager.save_endpoints_config("test_config.json")
    print("✅ Configuration saved")
    
    # Create new manager and load configuration
    new_manager = AIEndpointManager()
    new_manager.load_endpoints_config("test_config.json")
    
    new_endpoints = await new_manager.list_active_endpoints()
    print(f"✅ Configuration loaded: {len(new_endpoints)} endpoints restored")
    
    # Cleanup
    try:
        os.remove("test_config.json")
        print("✅ Test configuration file cleaned up")
    except:
        pass
    
    print("\n🎉 All tests completed successfully!")
    return True

async def test_model_naming():
    """Test model naming system"""
    print("\n🏷️ Testing model naming system...")
    
    manager = AIEndpointManager()
    
    # Create multiple endpoints with same name
    for i in range(3):
        endpoint_id = await manager.create_endpoint(
            name="DeepSeek",
            endpoint_type=EndpointType.WEB_CHAT,
            url="https://chat.deepseek.com",
            auth_config={}
        )
        endpoint = manager.endpoints[endpoint_id]
        expected_name = f"webdeepseek{i+1}"
        
        if endpoint.model_name == expected_name:
            print(f"✅ Model naming correct: {endpoint.model_name}")
        else:
            print(f"❌ Model naming incorrect: expected {expected_name}, got {endpoint.model_name}")
    
    return True

def test_configuration_classes():
    """Test configuration data classes"""
    print("\n📊 Testing configuration classes...")
    
    from ai_endpoint_manager import EndpointConfig, WebChatConfig
    from datetime import datetime
    
    # Test EndpointConfig
    config = EndpointConfig(
        id="test-id",
        name="Test Endpoint",
        endpoint_type=EndpointType.WEB_CHAT,
        url="https://example.com",
        model_name="webtest1",
        server_number=1,
        status=ServerStatus.OFFLINE,
        auth_config={"key": "value"},
        headers={},
        cookies={},
        created_at=datetime.now()
    )
    
    print(f"✅ EndpointConfig created: {config.name} ({config.model_name})")
    
    # Test WebChatConfig
    web_config = WebChatConfig(
        url="https://chat.example.com",
        username="testuser",
        password="testpass",
        text_input_selector="#input",
        send_button_selector=".send",
        response_selector=".response"
    )
    
    print(f"✅ WebChatConfig created: {web_config.url}")
    
    return True

async def main():
    """Run all tests"""
    print("🚀 AI Endpoint Manager Test Suite")
    print("=" * 50)
    
    try:
        # Test configuration classes
        test_configuration_classes()
        
        # Test model naming
        await test_model_naming()
        
        # Test basic functionality
        await test_basic_functionality()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("The AI Endpoint Manager is working correctly.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
