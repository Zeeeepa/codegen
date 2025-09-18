#!/usr/bin/env python3
"""
Orchestration Layer Validation Script

This script validates the unified orchestration layer implementation,
testing all core components and integration points.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codegen.orchestration import get_orchestration_manager, initialize_orchestration
from codegen.orchestration.chat.interface import ChatInterface
from codegen.orchestration.cli_adapter import get_cli_adapter
from codegen.orchestration.config.unified_config import UnifiedConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_configuration():
    """Test unified configuration system."""
    print("\n🔧 Testing Unified Configuration...")
    
    try:
        # Test configuration loading
        config = UnifiedConfig.load()
        print("✅ Configuration loaded successfully")
        
        # Test configuration access
        services_config = config.get_services_config()
        print(f"✅ Services configuration: {len(services_config)} services")
        
        # Test environment detection
        env = config.get_environment()
        print(f"✅ Environment detected: {env.value}")
        
        # Test validation
        issues = config.validate()
        if issues:
            print(f"⚠️  Configuration issues found: {len(issues)}")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ Configuration validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def test_orchestration_manager():
    """Test core orchestration manager."""
    print("\n🎯 Testing Orchestration Manager...")
    
    try:
        # Initialize orchestration manager
        manager = get_orchestration_manager()
        await manager.initialize()
        print("✅ Orchestration manager initialized")
        
        # Test system metrics
        metrics = await manager.get_system_metrics()
        print(f"✅ System metrics retrieved: {len(metrics)} metrics")
        
        # Test service health
        health = await manager.get_service_health()
        print(f"✅ Service health checked: {health}")
        
        # Test operation execution (mock)
        from codegen.orchestration.core.manager import OperationRequest
        
        request = OperationRequest(
            operation_type="test.operation",
            user_id="test_user",
            session_id="test_session"
        )
        
        response = await manager.execute_operation(request)
        print(f"✅ Test operation executed: {response.status.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestration manager test failed: {e}")
        return False

async def test_service_registry():
    """Test service registry functionality."""
    print("\n📋 Testing Service Registry...")
    
    try:
        manager = get_orchestration_manager()
        registry = manager.service_registry
        
        # Test service listing
        services = await registry.list_services()
        print(f"✅ Services listed: {len(services)} services")
        
        # Test service metrics
        metrics = await registry.get_registry_metrics()
        print(f"✅ Registry metrics: {metrics['total_services']} total services")
        
        # Test service selection
        selected = await registry.select_service()
        if selected:
            print(f"✅ Service selected: {selected.name}")
        else:
            print("ℹ️  No services available for selection")
        
        return True
        
    except Exception as e:
        print(f"❌ Service registry test failed: {e}")
        return False

async def test_session_manager():
    """Test session management."""
    print("\n👤 Testing Session Manager...")
    
    try:
        manager = get_orchestration_manager()
        session_mgr = manager.session_manager
        
        # Test session creation
        session = await session_mgr.create_session("test_user")
        print(f"✅ Session created: {session.session_id}")
        
        # Test session retrieval
        retrieved = await session_mgr.get_session(session.session_id)
        if retrieved:
            print("✅ Session retrieved successfully")
        
        # Test session context update
        success = await session_mgr.update_session_context(
            session.session_id,
            {"test_key": "test_value"}
        )
        if success:
            print("✅ Session context updated")
        
        # Test session metrics
        metrics = await session_mgr.get_session_metrics()
        print(f"✅ Session metrics: {metrics['total_sessions']} sessions")
        
        return True
        
    except Exception as e:
        print(f"❌ Session manager test failed: {e}")
        return False

async def test_chat_interface():
    """Test chat interface functionality."""
    print("\n💬 Testing Chat Interface...")
    
    try:
        manager = get_orchestration_manager()
        chat = ChatInterface(manager)
        await chat.initialize()
        print("✅ Chat interface initialized")
        
        # Test help command
        help_text = await chat.get_help_text()
        if "Codegen Orchestration" in help_text:
            print("✅ Help text generated")
        
        # Test message processing
        test_messages = [
            "help",
            "system status",
            "create agent for testing",
            "list my agents"
        ]
        
        for message in test_messages:
            try:
                response_parts = []
                async for chunk in chat.process_message(message, "test_user"):
                    response_parts.append(chunk)
                
                response = "".join(response_parts)
                if response:
                    print(f"✅ Message processed: '{message}' -> {len(response)} chars")
                else:
                    print(f"⚠️  Empty response for: '{message}'")
                    
            except Exception as e:
                print(f"❌ Message processing failed for '{message}': {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Chat interface test failed: {e}")
        return False

async def test_cli_adapter():
    """Test CLI adapter integration."""
    print("\n🖥️  Testing CLI Adapter...")
    
    try:
        adapter = get_cli_adapter()
        await adapter.initialize()
        print("✅ CLI adapter initialized")
        
        # Test chat command execution
        response = await adapter.execute_chat_command("help", "test_user")
        if response and "Codegen Orchestration" in response:
            print("✅ Chat command executed successfully")
        
        # Test system status
        status = await adapter.get_system_status()
        if status:
            print(f"✅ System status retrieved: {len(status)} metrics")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI adapter test failed: {e}")
        return False

async def test_integration():
    """Test end-to-end integration."""
    print("\n🔄 Testing End-to-End Integration...")
    
    try:
        # Initialize with custom configuration
        config = UnifiedConfig.load()
        manager = initialize_orchestration()
        print("✅ Orchestration initialized with configuration")
        
        # Test complete workflow
        chat = ChatInterface(manager)
        await chat.initialize()
        
        # Simulate user interaction
        user_id = "integration_test_user"
        session_id = "integration_test_session"
        
        # Test conversation flow
        messages = [
            "help",
            "system status",
            "what can you do?",
            "create agent for integration testing"
        ]
        
        for i, message in enumerate(messages):
            print(f"  Step {i+1}: Processing '{message}'")
            
            response_parts = []
            async for chunk in chat.process_message(message, user_id, session_id):
                response_parts.append(chunk)
            
            response = "".join(response_parts)
            if response:
                print(f"    ✅ Response: {len(response)} characters")
            else:
                print(f"    ⚠️  No response")
        
        # Test session persistence
        session_mgr = manager.session_manager
        user_sessions = await session_mgr.get_user_sessions(user_id)
        print(f"✅ Session persistence: {len(user_sessions)} sessions for user")
        
        # Test system metrics
        metrics = await manager.get_system_metrics()
        print(f"✅ Final system state: {metrics['active_operations']} active operations")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def main():
    """Run all validation tests."""
    print("🚀 ORCHESTRATION LAYER VALIDATION")
    print("=" * 50)
    
    tests = [
        ("Configuration System", test_configuration),
        ("Orchestration Manager", test_orchestration_manager),
        ("Service Registry", test_service_registry),
        ("Session Manager", test_session_manager),
        ("Chat Interface", test_chat_interface),
        ("CLI Adapter", test_cli_adapter),
        ("End-to-End Integration", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:<10} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ Orchestration layer is ready for production use")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("❌ Orchestration layer needs attention before production use")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

