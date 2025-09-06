# Copyright 2025 Emcie Co Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for unified configuration system.
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.codegen.sdk.core.unified_config import (
    UnifiedConfiguration, DiagnosticConfig, LSPConfig, 
    ConfigurationManager, LanguageConfig
)


class TestUnifiedConfiguration:
    """Test the unified configuration system"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = UnifiedConfiguration()
        
        assert config.lspserver is True
        assert config.diagnostics is True
        assert config.errorautoresolve is True
        assert config.enhancedcontext is True
        assert isinstance(config.diagnostics, DiagnosticConfig)
        assert isinstance(config.lsp_config, LSPConfig)
    
    def test_configuration_with_custom_values(self):
        """Test configuration with custom values"""
        config = UnifiedConfiguration(
            lspserver=False,
            diagnostics=False,
            errorautoresolve=False,
            enhancedcontext=False
        )
        
        assert config.lspserver is False
        assert config.diagnostics is False
        assert config.errorautoresolve is False
        assert config.enhancedcontext is False
    
    def test_diagnostic_config(self):
        """Test diagnostic configuration"""
        diag_config = DiagnosticConfig(
            enabled=True,
            real_time=False,
            sources=["lsp"],
            severity_filter=["error"]
        )
        
        assert diag_config.enabled is True
        assert diag_config.real_time is False
        assert diag_config.sources == ["lsp"]
        assert diag_config.severity_filter == ["error"]
    
    def test_lsp_config(self):
        """Test LSP configuration"""
        lsp_config = LSPConfig()
        
        # Test default language configs
        assert "python" in lsp_config.languages
        assert "javascript" in lsp_config.languages
        assert "typescript" in lsp_config.languages
        
        # Test Python config
        python_config = lsp_config.languages["python"]
        assert isinstance(python_config, LanguageConfig)
        assert python_config.server_command == ["pylsp"]
    
    def test_language_config(self):
        """Test language configuration"""
        lang_config = LanguageConfig(
            server_command=["test-server"],
            initialization_options={"test": True},
            file_extensions=[".test"]
        )
        
        assert lang_config.server_command == ["test-server"]
        assert lang_config.initialization_options == {"test": True}
        assert lang_config.file_extensions == [".test"]
    
    def test_to_dict(self):
        """Test configuration serialization to dictionary"""
        config = UnifiedConfiguration()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "lspserver" in config_dict
        assert "diagnostics" in config_dict
        assert "errorautoresolve" in config_dict
        assert "enhancedcontext" in config_dict
        assert "lsp_config" in config_dict
    
    def test_from_dict(self):
        """Test configuration deserialization from dictionary"""
        config_dict = {
            "lspserver": False,
            "diagnostics": {
                "enabled": False,
                "real_time": True,
                "sources": ["static_analysis"],
                "severity_filter": ["warning", "error"]
            },
            "errorautoresolve": False,
            "enhancedcontext": False
        }
        
        config = UnifiedConfiguration.from_dict(config_dict)
        
        assert config.lspserver is False
        assert config.diagnostics.enabled is False
        assert config.diagnostics.real_time is True
        assert config.diagnostics.sources == ["static_analysis"]
        assert config.errorautoresolve is False
        assert config.enhancedcontext is False
    
    def test_validate_valid_config(self):
        """Test validation of valid configuration"""
        config = UnifiedConfiguration()
        errors = config.validate()
        assert len(errors) == 0
    
    def test_validate_invalid_config(self):
        """Test validation of invalid configuration"""
        # Create config with invalid diagnostic sources
        config = UnifiedConfiguration()
        config.diagnostics.sources = ["invalid_source"]
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("invalid diagnostic source" in error.lower() for error in errors)


class TestConfigurationManager:
    """Test the configuration manager"""
    
    def test_default_config(self):
        """Test getting default configuration"""
        manager = ConfigurationManager()
        config = manager.get_config()
        
        assert isinstance(config, UnifiedConfiguration)
        assert config.lspserver is True
    
    def test_load_from_file(self):
        """Test loading configuration from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "lspserver": False,
                "diagnostics": {"enabled": False},
                "errorautoresolve": False,
                "enhancedcontext": False
            }
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            manager = ConfigurationManager(config_file)
            config = manager.get_config()
            
            assert config.lspserver is False
            assert config.diagnostics.enabled is False
            assert config.errorautoresolve is False
            assert config.enhancedcontext is False
        finally:
            Path(config_file).unlink()
    
    def test_save_to_file(self):
        """Test saving configuration to file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = f.name
        
        try:
            manager = ConfigurationManager(config_file)
            config = UnifiedConfiguration(lspserver=False)
            
            manager.save_config(config)
            
            # Load and verify
            manager2 = ConfigurationManager(config_file)
            loaded_config = manager2.get_config()
            
            assert loaded_config.lspserver is False
        finally:
            Path(config_file).unlink()
    
    def test_update_config(self):
        """Test updating configuration"""
        manager = ConfigurationManager()
        
        updates = {
            "lspserver": False,
            "errorautoresolve": False
        }
        
        updated_config = manager.update_config(updates)
        
        assert updated_config.lspserver is False
        assert updated_config.errorautoresolve is False
        assert updated_config.diagnostics is True  # Should remain unchanged
    
    def test_get_language_config(self):
        """Test getting language-specific configuration"""
        manager = ConfigurationManager()
        
        python_config = manager.get_language_config("python")
        assert isinstance(python_config, LanguageConfig)
        assert python_config.server_command == ["pylsp"]
        
        # Test non-existent language
        unknown_config = manager.get_language_config("unknown")
        assert unknown_config is None
    
    def test_detect_project_languages(self):
        """Test project language detection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "main.py").write_text("print('hello')")
            (temp_path / "app.js").write_text("console.log('hello')")
            (temp_path / "style.css").write_text("body { color: red; }")
            
            manager = ConfigurationManager()
            languages = manager.detect_project_languages(str(temp_path))
            
            assert "python" in languages
            assert "javascript" in languages
            # CSS should not be detected as it's not in supported languages
    
    def test_create_project_config(self):
        """Test creating project-specific configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "main.py").write_text("print('hello')")
            (temp_path / "app.ts").write_text("console.log('hello')")
            
            manager = ConfigurationManager()
            config = manager.create_project_config(str(temp_path))
            
            assert isinstance(config, UnifiedConfiguration)
            # Should have detected Python and TypeScript
            assert "python" in config.lsp_config.languages
            assert "typescript" in config.lsp_config.languages


class TestLanguageDetection:
    """Test language detection functionality"""
    
    def test_detect_python(self):
        """Test Python file detection"""
        manager = ConfigurationManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "main.py").write_text("print('hello')")
            (temp_path / "setup.py").write_text("from setuptools import setup")
            
            languages = manager.detect_project_languages(str(temp_path))
            assert "python" in languages
    
    def test_detect_javascript(self):
        """Test JavaScript file detection"""
        manager = ConfigurationManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "app.js").write_text("console.log('hello')")
            (temp_path / "component.jsx").write_text("export default function() {}")
            
            languages = manager.detect_project_languages(str(temp_path))
            assert "javascript" in languages
    
    def test_detect_typescript(self):
        """Test TypeScript file detection"""
        manager = ConfigurationManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "app.ts").write_text("const x: number = 42")
            (temp_path / "component.tsx").write_text("export default function(): JSX.Element {}")
            
            languages = manager.detect_project_languages(str(temp_path))
            assert "typescript" in languages
    
    def test_detect_multiple_languages(self):
        """Test detection of multiple languages"""
        manager = ConfigurationManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "main.py").write_text("print('hello')")
            (temp_path / "app.js").write_text("console.log('hello')")
            (temp_path / "server.ts").write_text("const x: number = 42")
            (temp_path / "Main.java").write_text("public class Main {}")
            
            languages = manager.detect_project_languages(str(temp_path))
            
            assert "python" in languages
            assert "javascript" in languages
            assert "typescript" in languages
            assert "java" in languages
    
    def test_ignore_hidden_files(self):
        """Test that hidden files are ignored"""
        manager = ConfigurationManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / ".hidden.py").write_text("print('hidden')")
            (temp_path / "visible.py").write_text("print('visible')")
            
            languages = manager.detect_project_languages(str(temp_path))
            assert "python" in languages  # Should still detect due to visible.py
    
    def test_ignore_common_directories(self):
        """Test that common directories are ignored"""
        manager = ConfigurationManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directories that should be ignored
            node_modules = temp_path / "node_modules"
            node_modules.mkdir()
            (node_modules / "package.js").write_text("module.exports = {}")
            
            venv = temp_path / ".venv"
            venv.mkdir()
            (venv / "lib.py").write_text("import sys")
            
            # Create actual project file
            (temp_path / "main.py").write_text("print('hello')")
            
            languages = manager.detect_project_languages(str(temp_path))
            assert "python" in languages
            # Should not be influenced by files in ignored directories
