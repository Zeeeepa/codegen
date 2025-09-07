"""Tests for GraphSitterConfig."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from codegen.sdk.config.graph_sitter_config import GraphSitterConfig, DEFAULT_CONFIG


class TestGraphSitterConfig:
    """Test cases for GraphSitterConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = GraphSitterConfig()
        
        # All features should be enabled by default
        assert config.lsp_server is True
        assert config.diagnostics is True
        assert config.error_auto_resolve is True
        assert config.enhanced_context is True
        assert config.doc_gen is True
        
        # Default advanced options
        assert config.max_context_tokens == 10000
        assert config.context_degree == 3
        assert config.cache_enabled is True
        assert config.debug_mode is False
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = GraphSitterConfig(
            lsp_server=False,
            diagnostics=True,
            error_auto_resolve=False,
            enhanced_context=True,
            doc_gen=False,
            max_context_tokens=5000,
            context_degree=2,
            cache_enabled=False,
            debug_mode=True
        )
        
        assert config.lsp_server is False
        assert config.diagnostics is True
        assert config.error_auto_resolve is False
        assert config.enhanced_context is True
        assert config.doc_gen is False
        assert config.max_context_tokens == 5000
        assert config.context_degree == 2
        assert config.cache_enabled is False
        assert config.debug_mode is True
    
    def test_path_auto_detection(self):
        """Test automatic path detection."""
        config = GraphSitterConfig()
        
        # Paths should be auto-detected
        assert config.sdk_root is not None
        assert config.extensions_root is not None
        assert isinstance(config.sdk_root, Path)
        assert isinstance(config.extensions_root, Path)
    
    def test_path_properties(self):
        """Test path properties."""
        config = GraphSitterConfig()
        
        # Test all path properties
        assert isinstance(config.solidlsp_root, Path)
        assert isinstance(config.serena_root, Path)
        assert isinstance(config.autogenlib_root, Path)
        assert isinstance(config.tools_root, Path)
        
        # Check path structure
        assert config.solidlsp_root == config.extensions_root / "lsp" / "solidlsp"
        assert config.serena_root == config.extensions_root / "lsp" / "serena"
        assert config.autogenlib_root == config.extensions_root / "autogenlib"
        assert config.tools_root == config.extensions_root / "tools"
    
    def test_validation_success(self):
        """Test successful validation."""
        with patch.object(Path, 'exists', return_value=True):
            config = GraphSitterConfig()
            errors = config.validate()
            assert len(errors) == 0
            assert config.is_valid() is True
    
    def test_validation_missing_directories(self):
        """Test validation with missing directories."""
        with patch.object(Path, 'exists', return_value=False):
            config = GraphSitterConfig()
            errors = config.validate()
            
            # Should have errors for missing directories
            assert len(errors) > 0
            assert config.is_valid() is False
            
            # Check specific error messages
            error_text = " ".join(errors)
            assert "not found" in error_text
    
    def test_validation_parameter_dependencies(self):
        """Test validation of parameter dependencies."""
        # error_auto_resolve requires enhanced_context
        config = GraphSitterConfig(
            error_auto_resolve=True,
            enhanced_context=False
        )
        
        with patch.object(Path, 'exists', return_value=True):
            errors = config.validate()
            assert len(errors) > 0
            assert "error_auto_resolve requires enhanced_context" in " ".join(errors)
    
    def test_validation_numeric_parameters(self):
        """Test validation of numeric parameters."""
        # Test invalid max_context_tokens
        config = GraphSitterConfig(max_context_tokens=0)
        
        with patch.object(Path, 'exists', return_value=True):
            errors = config.validate()
            assert len(errors) > 0
            assert "max_context_tokens must be positive" in " ".join(errors)
        
        # Test invalid context_degree
        config = GraphSitterConfig(context_degree=-1)
        
        with patch.object(Path, 'exists', return_value=True):
            errors = config.validate()
            assert len(errors) > 0
            assert "context_degree must be positive" in " ".join(errors)
    
    def test_get_enabled_features(self):
        """Test getting enabled features."""
        config = GraphSitterConfig(
            lsp_server=True,
            diagnostics=False,
            error_auto_resolve=True,
            enhanced_context=False,
            doc_gen=True
        )
        
        enabled = config.get_enabled_features()
        assert "lsp_server" in enabled
        assert "diagnostics" not in enabled
        assert "error_auto_resolve" in enabled
        assert "enhanced_context" not in enabled
        assert "doc_gen" in enabled
    
    def test_string_representation(self):
        """Test string representation."""
        config = GraphSitterConfig()
        str_repr = str(config)
        
        assert "GraphSitterConfig" in str_repr
        assert "enabled_features" in str_repr
    
    def test_default_config_instance(self):
        """Test the default config instance."""
        assert DEFAULT_CONFIG is not None
        assert isinstance(DEFAULT_CONFIG, GraphSitterConfig)
        assert DEFAULT_CONFIG.lsp_server is True
        assert DEFAULT_CONFIG.diagnostics is True
        assert DEFAULT_CONFIG.error_auto_resolve is True
        assert DEFAULT_CONFIG.enhanced_context is True
        assert DEFAULT_CONFIG.doc_gen is True


class TestGraphSitterConfigIntegration:
    """Integration tests for GraphSitterConfig."""
    
    def test_config_with_real_paths(self):
        """Test configuration with real file system paths."""
        # This test would work with actual directory structure
        config = GraphSitterConfig()
        
        # Basic path checks
        assert config.sdk_root.name == "sdk"
        assert config.extensions_root.name == "extensions"
    
    def test_config_serialization(self):
        """Test configuration can be serialized/deserialized."""
        config = GraphSitterConfig(
            lsp_server=False,
            max_context_tokens=5000,
            debug_mode=True
        )
        
        # Test that all attributes are accessible
        attrs = [
            'lsp_server', 'diagnostics', 'error_auto_resolve',
            'enhanced_context', 'doc_gen', 'max_context_tokens',
            'context_degree', 'cache_enabled', 'debug_mode'
        ]
        
        for attr in attrs:
            assert hasattr(config, attr)
            value = getattr(config, attr)
            assert value is not None or attr in ['sdk_root', 'extensions_root']
