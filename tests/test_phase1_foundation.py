"""
Comprehensive Test Suite for Phase 1 Foundation

This test suite validates all Phase 1 components including the main interface,
configuration management, exception handling, and integration readiness.
"""

import pytest
import asyncio
import tempfile
import json
import yaml
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Import the components to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

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


class TestVisualInterfaceConfig:
    """Test suite for VisualInterfaceConfig."""
    
    def test_default_configuration(self):
        """Test default configuration creation."""
        config = VisualInterfaceConfig()
        
        # Verify default values
        assert config.environment == "development"
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.api.base_url == "https://api.codegen.com"
        assert config.roma.endpoint == "http://localhost:8080"
        assert config.zai.base_url == "https://api.z.ai"
        assert config.storage.sqlite_path == "data/visual_interface.db"
        
        # Verify feature flags
        assert config.is_feature_enabled("visual_workflows") is True
        assert config.is_feature_enabled("ai_chat") is True
        assert config.is_feature_enabled("trace_intelligence") is True
    
    def test_environment_variable_loading(self):
        """Test configuration loading from environment variables."""
        with patch.dict(os.environ, {
            'CODEGEN_API_TOKEN': 'test_token',
            'CODEGEN_ORG_ID': 'test_org',
            'ENVIRONMENT': 'production',
            'DEBUG': 'true',
            'LOG_LEVEL': 'DEBUG'
        }):
            config = VisualInterfaceConfig.load_default()
            
            assert config.api.api_token == 'test_token'
            assert config.api.organization_id == 'test_org'
            assert config.environment == 'production'
            assert config.debug is True
            assert config.log_level == 'DEBUG'
    
    def test_yaml_configuration_loading(self):
        """Test configuration loading from YAML file."""
        config_data = {
            'environment': 'staging',
            'debug': True,
            'api': {
                'base_url': 'https://staging-api.codegen.com',
                'timeout': 60
            },
            'roma': {
                'endpoint': 'http://roma-staging:8080',
                'max_task_depth': 10
            },
            'features': {
                'roma_integration': False,
                'zai_integration': True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = VisualInterfaceConfig.load_from_file(config_path)
            
            assert config.environment == 'staging'
            assert config.debug is True
            assert config.api.base_url == 'https://staging-api.codegen.com'
            assert config.api.timeout == 60
            assert config.roma.endpoint == 'http://roma-staging:8080'
            assert config.roma.max_task_depth == 10
            assert config.is_feature_enabled('roma_integration') is False
            assert config.is_feature_enabled('zai_integration') is True
        finally:
            os.unlink(config_path)
    
    def test_json_configuration_loading(self):
        """Test configuration loading from JSON file."""
        config_data = {
            'environment': 'test',
            'api': {
                'base_url': 'https://test-api.codegen.com'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            config = VisualInterfaceConfig.load_from_file(config_path)
            
            assert config.environment == 'test'
            assert config.api.base_url == 'https://test-api.codegen.com'
        finally:
            os.unlink(config_path)
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Valid configuration
        config = VisualInterfaceConfig()
        config.api.api_token = "test_token"
        config.api.organization_id = "test_org"
        
        assert config.validate() is True
        
        # Invalid configuration - missing API token
        config.api.api_token = None
        assert config.validate() is False
    
    def test_feature_flag_management(self):
        """Test feature flag management."""
        config = VisualInterfaceConfig()
        
        # Test enabling/disabling features
        config.disable_feature('ai_chat')
        assert config.is_feature_enabled('ai_chat') is False
        
        config.enable_feature('ai_chat')
        assert config.is_feature_enabled('ai_chat') is True
        
        # Test non-existent feature
        assert config.is_feature_enabled('non_existent_feature') is False
    
    def test_configuration_serialization(self):
        """Test configuration to/from dictionary conversion."""
        config = VisualInterfaceConfig()
        config.environment = 'test'
        config.debug = True
        
        # Convert to dictionary
        config_dict = config.to_dict()
        assert config_dict['environment'] == 'test'
        assert config_dict['debug'] is True
        assert 'api' in config_dict
        assert 'roma' in config_dict
        
        # Test saving to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            config.save_to_file(config_path)
            
            # Verify file was created and contains expected data
            with open(config_path, 'r') as f:
                saved_data = yaml.safe_load(f)
            
            assert saved_data['environment'] == 'test'
            assert saved_data['debug'] is True
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)


class TestCodegenVisualInterface:
    """Test suite for CodegenVisualInterface."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = VisualInterfaceConfig()
        config.api.api_token = "test_token"
        config.api.organization_id = "test_org"
        config.health_check_interval = 1  # Fast health checks for testing
        config.session_maintenance_interval = 1  # Fast maintenance for testing
        return config
    
    @pytest.fixture
    def interface(self, config):
        """Create a test interface instance."""
        return CodegenVisualInterface(config)
    
    def test_interface_initialization(self, interface):
        """Test interface initialization."""
        assert interface.config is not None
        assert interface.state.session_id is not None
        assert interface.health.overall_status == "unknown"
        assert interface._initialized is False
        assert len(interface._background_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_interface_full_initialization(self, interface):
        """Test complete interface initialization."""
        await interface.initialize()
        
        assert interface._initialized is True
        assert len(interface._background_tasks) > 0
        assert interface.state.user_id == interface.config.user_id
        assert interface.state.organization_id == interface.config.organization_id
        
        # Cleanup
        await interface.shutdown()
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, interface):
        """Test health monitoring system."""
        await interface.initialize()
        
        # Wait for at least one health check
        await asyncio.sleep(1.5)
        
        # Verify health check was performed
        assert interface.health.last_check is not None
        assert interface.health.overall_status in ["healthy", "degraded", "unhealthy"]
        
        # All components should be "not_initialized" or "pending_implementation"
        assert interface.health.codegen_api in ["not_initialized", "pending_implementation"]
        assert interface.health.roma_orchestrator in ["not_initialized", "pending_implementation"]
        
        await interface.shutdown()
    
    @pytest.mark.asyncio
    async def test_session_maintenance(self, interface):
        """Test session maintenance system."""
        await interface.initialize()
        
        original_activity = interface.state.last_activity
        
        # Wait for maintenance cycle
        await asyncio.sleep(1.5)
        
        # Verify activity was updated
        assert interface.state.last_activity > original_activity
        
        await interface.shutdown()
    
    @pytest.mark.asyncio
    async def test_system_status_reporting(self, interface):
        """Test system status reporting."""
        await interface.initialize()
        
        status = await interface.get_system_status()
        
        assert 'session_id' in status
        assert 'initialized' in status
        assert 'health' in status
        assert 'state' in status
        
        assert status['initialized'] is True
        assert status['session_id'] == interface.state.session_id
        assert 'overall_status' in status['health']
        assert 'components' in status['health']
        
        await interface.shutdown()
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, interface):
        """Test graceful shutdown."""
        await interface.initialize()
        
        # Verify background tasks are running
        assert len(interface._background_tasks) > 0
        running_tasks = [task for task in interface._background_tasks if not task.done()]
        assert len(running_tasks) > 0
        
        # Shutdown
        await interface.shutdown()
        
        # Verify shutdown event is set
        assert interface._shutdown_event.is_set()
        
        # Verify all tasks are cancelled or completed
        for task in interface._background_tasks:
            assert task.done()
    
    @pytest.mark.asyncio
    async def test_double_initialization_protection(self, interface):
        """Test protection against double initialization."""
        await interface.initialize()
        assert interface._initialized is True
        
        # Second initialization should be ignored
        await interface.initialize()
        assert interface._initialized is True
        
        await interface.shutdown()
    
    @pytest.mark.asyncio
    async def test_initialization_failure_handling(self):
        """Test handling of initialization failures."""
        # Create config with invalid settings to trigger failure
        config = VisualInterfaceConfig()
        # Don't set required API token to trigger validation failure
        
        interface = CodegenVisualInterface(config)
        
        with pytest.raises(CodegenVisualInterfaceError):
            await interface.initialize()
    
    def test_interface_string_representation(self, interface):
        """Test string representation."""
        repr_str = repr(interface)
        assert "CodegenVisualInterface" in repr_str
        assert interface.state.session_id in repr_str
        assert interface.health.overall_status in repr_str


class TestExceptionHandling:
    """Test suite for exception handling."""
    
    def test_base_exception(self):
        """Test base exception functionality."""
        error = CodegenVisualInterfaceError("Test error", "TEST_ERROR", {"key": "value"})
        
        assert str(error) == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
        
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "CodegenVisualInterfaceError"
        assert error_dict["message"] == "Test error"
        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["details"] == {"key": "value"}
    
    def test_api_integration_error(self):
        """Test API integration error."""
        error = APIIntegrationError(
            "API call failed", 
            "codegen_api", 
            status_code=500,
            response_data={"error": "Internal server error"}
        )
        
        assert error.api_name == "codegen_api"
        assert error.status_code == 500
        assert error.response_data == {"error": "Internal server error"}
        assert error.error_code == "API_INTEGRATION_ERROR"
    
    def test_orchestration_error(self):
        """Test orchestration error."""
        error = OrchestrationError(
            "Task failed",
            "roma",
            task_id="task_123",
            workflow_id="workflow_456"
        )
        
        assert error.orchestrator == "roma"
        assert error.task_id == "task_123"
        assert error.workflow_id == "workflow_456"
        assert error.error_code == "ORCHESTRATION_ERROR"
    
    def test_trace_retrieval_error(self):
        """Test trace retrieval error."""
        error = TraceRetrievalError(
            "Trace not found",
            trace_id="trace_123",
            agent_run_id="run_456"
        )
        
        assert error.trace_id == "trace_123"
        assert error.agent_run_id == "run_456"
        assert error.error_code == "TRACE_RETRIEVAL_ERROR"
    
    def test_exception_from_dict(self):
        """Test creating exceptions from dictionary data."""
        error_data = {
            "error_type": "APIIntegrationError",
            "message": "API failed",
            "error_code": "API_INTEGRATION_ERROR",
            "details": {
                "api_name": "test_api",
                "status_code": 404
            }
        }
        
        error = create_exception_from_dict(error_data)
        
        assert isinstance(error, APIIntegrationError)
        assert error.message == "API failed"
        assert error.api_name == "test_api"
        assert error.status_code == 404
    
    def test_exception_from_dict_fallback(self):
        """Test fallback behavior for unknown exception types."""
        error_data = {
            "error_type": "UnknownError",
            "message": "Unknown error",
            "error_code": "UNKNOWN_ERROR"
        }
        
        error = create_exception_from_dict(error_data)
        
        assert isinstance(error, CodegenVisualInterfaceError)
        assert error.message == "Unknown error"
        assert error.error_code == "UNKNOWN_ERROR"


class TestInterfaceState:
    """Test suite for InterfaceState."""
    
    def test_state_initialization(self):
        """Test state initialization."""
        state = InterfaceState()
        
        assert state.session_id is not None
        assert len(state.session_id) > 0
        assert state.user_id is None
        assert state.organization_id is None
        assert state.active_projects == []
        assert state.active_workflows == []
        assert state.chat_context == {}
        assert isinstance(state.last_activity, datetime)
        
        # Integration states should be False by default
        assert state.roma_connected is False
        assert state.zai_connected is False
        assert state.grainchain_connected is False
        assert state.codegen_api_connected is False


class TestSystemHealth:
    """Test suite for SystemHealth."""
    
    def test_health_initialization(self):
        """Test health initialization."""
        health = SystemHealth()
        
        assert health.overall_status == "unknown"
        assert health.codegen_api == "unknown"
        assert health.roma_orchestrator == "unknown"
        assert health.zai_intelligence == "unknown"
        assert health.grainchain_sandbox == "unknown"
        assert health.trace_system == "unknown"
        assert health.chat_engine == "unknown"
        assert health.visual_renderer == "unknown"
        assert isinstance(health.last_check, datetime)
    
    def test_health_status_checking(self):
        """Test health status checking."""
        health = SystemHealth()
        
        # All unknown - not healthy
        assert health.is_healthy() is False
        
        # Set all to healthy
        health.codegen_api = "healthy"
        health.roma_orchestrator = "healthy"
        health.zai_intelligence = "healthy"
        health.grainchain_sandbox = "healthy"
        health.trace_system = "healthy"
        health.chat_engine = "healthy"
        health.visual_renderer = "healthy"
        
        assert health.is_healthy() is True
        
        # One unhealthy component
        health.codegen_api = "unhealthy"
        assert health.is_healthy() is False


class TestFactoryFunction:
    """Test suite for factory function."""
    
    def test_create_visual_interface_default(self):
        """Test creating interface with default config."""
        with patch.dict(os.environ, {
            'CODEGEN_API_TOKEN': 'test_token',
            'CODEGEN_ORG_ID': 'test_org'
        }):
            interface = create_visual_interface()
            
            assert isinstance(interface, CodegenVisualInterface)
            assert interface.config.api.api_token == 'test_token'
            assert interface.config.api.organization_id == 'test_org'
    
    def test_create_visual_interface_custom_config(self):
        """Test creating interface with custom config."""
        config = VisualInterfaceConfig()
        config.api.api_token = "custom_token"
        config.api.organization_id = "custom_org"
        config.environment = "test"
        
        interface = create_visual_interface(config)
        
        assert isinstance(interface, CodegenVisualInterface)
        assert interface.config.api.api_token == "custom_token"
        assert interface.config.api.organization_id == "custom_org"
        assert interface.config.environment == "test"


# Integration test for the complete Phase 1 system
class TestPhase1Integration:
    """Integration tests for Phase 1 components."""
    
    @pytest.mark.asyncio
    async def test_complete_lifecycle(self):
        """Test complete interface lifecycle."""
        # Create configuration
        config = VisualInterfaceConfig()
        config.api.api_token = "test_token"
        config.api.organization_id = "test_org"
        config.health_check_interval = 0.5
        config.session_maintenance_interval = 0.5
        
        # Create interface
        interface = create_visual_interface(config)
        
        try:
            # Initialize
            await interface.initialize()
            assert interface._initialized is True
            
            # Wait for background services to run
            await asyncio.sleep(1.0)
            
            # Check system status
            status = await interface.get_system_status()
            assert status['initialized'] is True
            assert 'session_id' in status
            
            # Verify health monitoring is working
            assert interface.health.last_check is not None
            
            # Verify session maintenance is working
            assert interface.state.last_activity is not None
            
        finally:
            # Shutdown
            await interface.shutdown()
            assert interface._shutdown_event.is_set()
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling across components."""
        # Test configuration error
        config = VisualInterfaceConfig()
        # Missing required API token
        
        interface = CodegenVisualInterface(config)
        
        with pytest.raises(CodegenVisualInterfaceError) as exc_info:
            await interface.initialize()
        
        assert "Invalid configuration" in str(exc_info.value)
    
    def test_configuration_integration(self):
        """Test configuration system integration."""
        # Test environment variable override
        with patch.dict(os.environ, {
            'CODEGEN_API_TOKEN': 'env_token',
            'ENVIRONMENT': 'production',
            'DEBUG': 'true'
        }):
            config = VisualInterfaceConfig.load_default()
            
            assert config.api.api_token == 'env_token'
            assert config.environment == 'production'
            assert config.debug is True
            
            # Test validation
            config.api.organization_id = 'test_org'
            assert config.validate() is True


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
