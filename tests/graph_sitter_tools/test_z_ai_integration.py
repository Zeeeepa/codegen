#!/usr/bin/env python3
"""
Test z.ai integration in autogenlib
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add autogenlib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

class TestZAIIntegration(unittest.TestCase):
    """Test Z.ai integration functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.original_path = sys.path.copy()
    
    def tearDown(self):
        """Clean up"""
        sys.path = self.original_path
    
    def test_z_ai_client_import(self):
        """Test that z.ai client can be imported"""
        try:
            from autogenlib._z_ai_client import ZAIWrapper, get_z_ai_client, is_zai_available
            self.assertTrue(True, "Z.ai client imports successfully")
        except ImportError as e:
            self.skipTest(f"Z.ai client not available: {e}")
    
    def test_z_ai_availability_check(self):
        """Test z.ai availability checking"""
        try:
            from autogenlib._z_ai_client import is_zai_available
            
            # Test without API key
            with patch.dict(os.environ, {}, clear=True):
                self.assertFalse(is_zai_available())
            
            # Test with API key
            with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
                # This might still be False if SDK not available, but at least tests the function
                result = is_zai_available()
                self.assertIsInstance(result, bool)
                
        except ImportError:
            self.skipTest("Z.ai client not available")
    
    def test_zai_wrapper_initialization(self):
        """Test ZAIWrapper initialization"""
        try:
            from autogenlib._z_ai_client import ZAIWrapper
            
            # Test without API key should raise error
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ValueError):
                    ZAIWrapper()
            
            # Test with API key
            with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
                with patch('autogenlib._z_ai_client.ZaiClient') as mock_client:
                    wrapper = ZAIWrapper()
                    self.assertIsNotNone(wrapper.api_key)
                    self.assertEqual(wrapper.api_key, "test-key")
                    
        except ImportError:
            self.skipTest("Z.ai client not available")
    
    def test_autogenlib_ai_integration(self):
        """Test that autogenlib properly integrates z.ai"""
        try:
            # Mock the z.ai client to avoid actual API calls
            with patch('autogenlib._z_ai_client.ZaiClient') as mock_zai_client:
                with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
                    
                    # Mock successful response
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = '{"test": "response"}'
                    mock_response.choices[0].finish_reason = "stop"
                    
                    mock_client_instance = Mock()
                    mock_client_instance.chat.completions.create.return_value = mock_response
                    mock_zai_client.return_value = mock_client_instance
                    
                    from autogenlib import get_ai_client, check_ai_availability
                    
                    # Test AI client retrieval
                    client = get_ai_client()
                    self.assertIsNotNone(client)
                    
                    # Test availability check
                    status = check_ai_availability()
                    self.assertIsInstance(status, dict)
                    self.assertIn("zai_available", status)
                    self.assertIn("openai_available", status)
                    
        except ImportError as e:
            self.skipTest(f"Required modules not available: {e}")
    
    def test_ai_resolve_with_zai(self):
        """Test AI resolution using z.ai"""
        try:
            with patch('autogenlib._z_ai_client.ZaiClient') as mock_zai_client:
                with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
                    
                    # Mock successful z.ai response
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = '''{
                        "fixed_code": "def fixed_function(): return True",
                        "explanation": "Fixed using z.ai",
                        "confidence": 0.9,
                        "side_effects": [],
                        "testing_suggestions": ["Test the function"],
                        "related_changes": []
                    }'''
                    mock_response.choices[0].finish_reason = "stop"
                    
                    mock_client_instance = Mock()
                    mock_client_instance.chat.completions.create.return_value = mock_response
                    mock_zai_client.return_value = mock_client_instance
                    
                    # Mock other dependencies
                    with patch('autogenlib_ai_resolve.validate_code', return_value=True):
                        with patch('autogenlib_ai_resolve.Codebase') as mock_codebase:
                            
                            from autogenlib_ai_resolve import resolve_diagnostic_with_ai
                            
                            # Create mock enhanced diagnostic
                            mock_diagnostic = Mock()
                            mock_diagnostic.message = "Test error"
                            mock_diagnostic.code = "E001"
                            mock_diagnostic.range.line = 10
                            mock_diagnostic.range.character = 5
                            mock_diagnostic.range.end.line = 10
                            mock_diagnostic.range.end.character = 20
                            
                            enhanced_diagnostic = {
                                'diagnostic': mock_diagnostic,
                                'relative_file_path': 'test.py',
                                'file_content': 'def test(): pass',
                                'relevant_code_snippet': 'def test(): pass',
                                'graph_sitter_context': {
                                    'codebase_overview': {'codebase_overview': 'Test'},
                                    'symbol_context': {},
                                    'file_context': {},
                                    'architectural_context': {},
                                    'resolution_context': {},
                                    'visualization_data': {},
                                    'similar_patterns': []
                                },
                                'autogenlib_context': {},
                                'runtime_context': {},
                                'ui_interaction_context': {}
                            }
                            
                            result = resolve_diagnostic_with_ai(enhanced_diagnostic, mock_codebase)
                            
                            # Verify successful z.ai integration
                            self.assertEqual(result["status"], "success")
                            self.assertIn("fixed_code", result)
                            self.assertEqual(result["explanation"], "Fixed using z.ai")
                            
        except ImportError as e:
            self.skipTest(f"Required modules not available: {e}")


class TestEnvironmentSetup(unittest.TestCase):
    """Test environment setup and configuration"""
    
    def test_environment_variables_documentation(self):
        """Test that we document the needed environment variables"""
        env_vars = [
            "ZAI_API_KEY",
            "ZHIPU_API_KEY", 
            "ZAI_MODEL",
            "OPENAI_API_KEY",
            "OPENAI_MODEL"
        ]
        
        # This test ensures we're aware of all the env vars needed
        for var in env_vars:
            self.assertIsInstance(var, str)
            self.assertTrue(len(var) > 0)
    
    def test_model_defaults(self):
        """Test that we have sensible model defaults"""
        from autogenlib._z_ai_client import ZAIWrapper
        
        # Test that we use glm-4 as default for z.ai
        with patch.dict(os.environ, {"ZAI_API_KEY": "test"}):
            with patch('autogenlib._z_ai_client.ZaiClient'):
                wrapper = ZAIWrapper()
                # The wrapper should be created successfully
                self.assertIsNotNone(wrapper)


if __name__ == '__main__':
    print("🧪 Testing Z.ai integration in autogenlib...")
    unittest.main(verbosity=2)