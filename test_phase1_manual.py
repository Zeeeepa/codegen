#!/usr/bin/env python3
"""
Manual Test Runner for Phase 1 Foundation

This script manually tests the Phase 1 foundation components without pytest
to validate the implementation works correctly.
"""

import asyncio
import sys
import tempfile
import json
import yaml
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all imports work correctly."""
    print("🔍 Testing imports...")
    
    try:
        from codegen_visual_interface import (
            CodegenVisualInterface,
            VisualInterfaceConfig,
            create_visual_interface,
            CodegenVisualInterfaceError,
            APIIntegrationError,
            OrchestrationError,
            TraceRetrievalError
        )
        from codegen_visual_interface.core.foundation import InterfaceState, SystemHealth
        from codegen_visual_interface.core.config import APIConfig, ROMAConfig, ZAIConfig
        from codegen_visual_interface.core.exceptions import create_exception_from_dict
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration system."""
    print("\n⚙️ Testing configuration system...")
    
    try:
        from codegen_visual_interface.core.config import VisualInterfaceConfig
        
        # Test default configuration
        config = VisualInterfaceConfig()
        assert config.environment == "development"
        assert config.debug is False
        assert config.api.base_url == "https://api.codegen.com"
        print("✅ Default configuration works")
        
        # Test feature flags
        assert config.is_feature_enabled("visual_workflows") is True
        config.disable_feature("visual_workflows")
        assert config.is_feature_enabled("visual_workflows") is False
        config.enable_feature("visual_workflows")
        assert config.is_feature_enabled("visual_workflows") is True
        print("✅ Feature flags work")
        
        # Test validation
        config.api.api_token = "test_token"
        config.api.organization_id = "test_org"
        assert config.validate() is True
        print("✅ Configuration validation works")
        
        # Test serialization
        config_dict = config.to_dict()
        assert "api" in config_dict
        assert "roma" in config_dict
        print("✅ Configuration serialization works")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_exceptions():
    """Test exception system."""
    print("\n🚨 Testing exception system...")
    
    try:
        from codegen_visual_interface.core.exceptions import (
            CodegenVisualInterfaceError,
            APIIntegrationError,
            OrchestrationError,
            create_exception_from_dict
        )
        
        # Test base exception
        error = CodegenVisualInterfaceError("Test error", "TEST_ERROR", {"key": "value"})
        assert str(error) == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
        print("✅ Base exception works")
        
        # Test specific exceptions
        api_error = APIIntegrationError("API failed", "test_api", 500)
        assert api_error.api_name == "test_api"
        assert api_error.status_code == 500
        print("✅ API integration error works")
        
        orch_error = OrchestrationError("Task failed", "roma", "task_123")
        assert orch_error.orchestrator == "roma"
        assert orch_error.task_id == "task_123"
        print("✅ Orchestration error works")
        
        # Test exception from dict
        error_data = {
            "error_type": "APIIntegrationError",
            "message": "API failed",
            "error_code": "API_INTEGRATION_ERROR",
            "details": {"api_name": "test_api", "status_code": 404}
        }
        recreated_error = create_exception_from_dict(error_data)
        assert isinstance(recreated_error, APIIntegrationError)
        assert recreated_error.api_name == "test_api"
        print("✅ Exception from dict works")
        
        return True
    except Exception as e:
        print(f"❌ Exception test failed: {e}")
        return False

async def test_interface():
    """Test the main interface."""
    print("\n🖥️ Testing main interface...")
    
    try:
        from codegen_visual_interface import CodegenVisualInterface, VisualInterfaceConfig
        
        # Create test configuration
        config = VisualInterfaceConfig()
        config.api.api_token = "test_token"
        config.api.organization_id = "test_org"
        config.health_check_interval = 0.5  # Fast for testing
        config.session_maintenance_interval = 0.5
        
        # Create interface
        interface = CodegenVisualInterface(config)
        assert interface.config is not None
        assert interface.state.session_id is not None
        assert interface._initialized is False
        print("✅ Interface creation works")
        
        # Test initialization
        await interface.initialize()
        assert interface._initialized is True
        assert len(interface._background_tasks) > 0
        print("✅ Interface initialization works")
        
        # Wait for background services
        await asyncio.sleep(1.0)
        
        # Test system status
        status = await interface.get_system_status()
        assert "session_id" in status
        assert "initialized" in status
        assert status["initialized"] is True
        print("✅ System status reporting works")
        
        # Test health monitoring
        assert interface.health.last_check is not None
        print("✅ Health monitoring works")
        
        # Test graceful shutdown
        await interface.shutdown()
        assert interface._shutdown_event.is_set()
        print("✅ Graceful shutdown works")
        
        return True
    except Exception as e:
        print(f"❌ Interface test failed: {e}")
        return False

def test_state_and_health():
    """Test state and health classes."""
    print("\n📊 Testing state and health classes...")
    
    try:
        from codegen_visual_interface.core.foundation import InterfaceState, SystemHealth
        
        # Test interface state
        state = InterfaceState()
        assert state.session_id is not None
        assert len(state.session_id) > 0
        assert state.active_projects == []
        assert state.roma_connected is False
        print("✅ Interface state works")
        
        # Test system health
        health = SystemHealth()
        assert health.overall_status == "unknown"
        assert health.is_healthy() is False
        
        # Set all components to healthy
        health.codegen_api = "healthy"
        health.roma_orchestrator = "healthy"
        health.zai_intelligence = "healthy"
        health.grainchain_sandbox = "healthy"
        health.trace_system = "healthy"
        health.chat_engine = "healthy"
        health.visual_renderer = "healthy"
        
        assert health.is_healthy() is True
        print("✅ System health works")
        
        return True
    except Exception as e:
        print(f"❌ State and health test failed: {e}")
        return False

def test_factory_function():
    """Test factory function."""
    print("\n🏭 Testing factory function...")
    
    try:
        from codegen_visual_interface import create_visual_interface, VisualInterfaceConfig
        
        # Test with custom config
        config = VisualInterfaceConfig()
        config.api.api_token = "test_token"
        config.api.organization_id = "test_org"
        
        interface = create_visual_interface(config)
        assert interface.config.api.api_token == "test_token"
        print("✅ Factory function works")
        
        return True
    except Exception as e:
        print(f"❌ Factory function test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests."""
    print("🚀 Starting Phase 1 Foundation Tests\n")
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Exceptions", test_exceptions),
        ("State and Health", test_state_and_health),
        ("Factory Function", test_factory_function),
        ("Main Interface", test_interface)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} test FAILED with exception: {e}")
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Phase 1 foundation is ready.")
        return True
    else:
        print(f"\n⚠️ {failed} tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
