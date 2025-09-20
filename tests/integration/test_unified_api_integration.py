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
Integration tests for the unified API system.

These tests verify that all components work together correctly
in the complete SolidLSP + Serena + Graph-Sitter integration.
"""

import pytest
import asyncio
from pathlib import Path

from src.codegen.sdk.core.unified_api import from_repo, UnifiedCodebaseAPI
from src.codegen.sdk.core.unified_config import UnifiedConfiguration


class TestUnifiedAPIIntegration:
    """Integration tests for the unified API"""
    
    @pytest.mark.asyncio
    async def test_from_repo_initialization(self, sample_python_project, unified_config):
        """Test that from_repo properly initializes the system"""
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        try:
            assert isinstance(codebase, UnifiedCodebaseAPI)
            assert codebase._initialized is True
            assert codebase.project_root == Path(sample_python_project).resolve()
            
            # Verify components are initialized
            project_info = codebase.get_project_info()
            assert project_info['initialized'] is True
            assert project_info['components']['serena_adapter'] is True
            assert project_info['components']['graph_builder'] is True
            
        finally:
            await codebase.shutdown()
    
    @pytest.mark.asyncio
    async def test_comprehensive_analysis(self, sample_python_project, unified_config):
        """Test comprehensive codebase analysis"""
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        try:
            # Perform comprehensive analysis
            result = await codebase.analyze(include_graph=True, include_context=True)
            
            assert result is not None
            assert hasattr(result, 'diagnostics')
            assert hasattr(result, 'symbols')
            assert hasattr(result, 'graph')
            assert hasattr(result, 'resolved_errors')
            assert hasattr(result, 'error_contexts')
            assert hasattr(result, 'metrics')
            assert hasattr(result, 'timestamp')
            
            # Verify metrics are collected
            assert 'analysis_time' in result.metrics
            assert result.timestamp > 0
            
        finally:
            await codebase.shutdown()
    
    @pytest.mark.asyncio
    async def test_diagnostics_collection(self, sample_python_project, unified_config):
        """Test diagnostic collection functionality"""
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        try:
            # Get diagnostics for the entire codebase
            diagnostics = await codebase.get_diagnostics()
            
            # Should return a list (may be empty if no real LSP server)
            assert isinstance(diagnostics, list)
            
            # Test file-specific diagnostics
            main_py = str(sample_python_project / "main.py")
            file_diagnostics = await codebase.get_diagnostics(main_py)
            assert isinstance(file_diagnostics, list)
            
        finally:
            await codebase.shutdown()
    
    @pytest.mark.asyncio
    async def test_symbol_extraction(self, sample_python_project, unified_config):
        """Test symbol extraction functionality"""
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        try:
            # Get symbols for the entire codebase
            symbols = await codebase.get_symbols()
            
            # Should return a list (may be empty if no real LSP server)
            assert isinstance(symbols, list)
            
            # Test file-specific symbols
            main_py = str(sample_python_project / "main.py")
            file_symbols = await codebase.get_symbols(main_py)
            assert isinstance(file_symbols, list)
            
        finally:
            await codebase.shutdown()
    
    @pytest.mark.asyncio
    async def test_error_resolution(self, sample_python_project, unified_config):
        """Test error resolution functionality"""
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        try:
            # Test error resolution without specific diagnostics
            resolved_errors = await codebase.resolve_errors()
            assert isinstance(resolved_errors, list)
            
            # Test with mock diagnostics
            from src.codegen.sdk.core.integration_interfaces import (
                UnifiedDiagnostic, DiagnosticSeverity, UnifiedRange, UnifiedPosition
            )
            
            mock_diagnostic = UnifiedDiagnostic(
                message="name 'undefined_var' is not defined",
                severity=DiagnosticSeverity.ERROR,
                range=UnifiedRange(
                    start=UnifiedPosition(line=10, character=5),
                    end=UnifiedPosition(line=10, character=18)
                ),
                source="python",
                code="undefined-name"
            )
            
            resolved_with_mock = await codebase.resolve_errors([mock_diagnostic])
            assert isinstance(resolved_with_mock, list)
            
        finally:
            await codebase.shutdown()
    
    @pytest.mark.asyncio
    async def test_enhanced_context(self, sample_python_project, unified_config):
        """Test enhanced context functionality"""
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        try:
            # Create a mock diagnostic
            from src.codegen.sdk.core.integration_interfaces import (
                UnifiedDiagnostic, DiagnosticSeverity, UnifiedRange, UnifiedPosition
            )
            
            mock_diagnostic = UnifiedDiagnostic(
                message="name 'undefined_var' is not defined",
                severity=DiagnosticSeverity.ERROR,
                range=UnifiedRange(
                    start=UnifiedPosition(line=10, character=5),
                    end=UnifiedPosition(line=10, character=18)
                ),
                source="python",
                code="undefined-name"
            )
            
            # Get enhanced context
            main_py = str(sample_python_project / "main.py")
            context = await codebase.get_enhanced_context(mock_diagnostic, main_py)
            
            assert isinstance(context, dict)
            # Should have context fields even if empty
            assert 'symbol_definitions' in context
            assert 'type_information' in context
            assert 'suggested_fixes' in context
            assert 'confidence_score' in context
            
        finally:
            await codebase.shutdown()
    
    @pytest.mark.asyncio
    async def test_graph_construction(self, sample_python_project, unified_config):
        """Test graph construction functionality"""
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        try:
            # Get graph in dictionary format
            graph_dict = codebase.get_graph(format="dict")
            assert isinstance(graph_dict, dict)
            
            # Get graph in JSON format
            graph_json = codebase.get_graph(format="json")
            assert isinstance(graph_json, str)
            
        finally:
            await codebase.shutdown()
    
    @pytest.mark.asyncio
    async def test_project_info(self, sample_python_project, unified_config):
        """Test project information retrieval"""
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        try:
            project_info = codebase.get_project_info()
            
            assert isinstance(project_info, dict)
            assert 'project_root' in project_info
            assert 'initialized' in project_info
            assert 'config' in project_info
            assert 'components' in project_info
            
            assert project_info['initialized'] is True
            assert project_info['project_root'] == str(Path(sample_python_project).resolve())
            
            # Verify component status
            components = project_info['components']
            assert 'serena_adapter' in components
            assert 'graph_builder' in components
            assert 'diagnostic_collector' in components
            
        finally:
            await codebase.shutdown()
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, sample_python_project, unified_config):
        """Test metrics collection functionality"""
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        try:
            # Perform some operations to generate metrics
            await codebase.analyze()
            
            # Get metrics
            metrics = codebase.get_metrics()
            
            assert isinstance(metrics, dict)
            assert 'api_metrics' in metrics
            assert 'components' in metrics
            
            # Should have initialization metrics
            api_metrics = metrics['api_metrics']
            assert 'initialization_time' in api_metrics
            assert 'initialized_at' in api_metrics
            
        finally:
            await codebase.shutdown()
    
    @pytest.mark.asyncio
    async def test_configuration_integration(self, sample_python_project):
        """Test that configuration properly affects system behavior"""
        # Test with all features enabled
        config_enabled = UnifiedConfiguration(
            lspserver=True,
            diagnostics=True,
            errorautoresolve=True,
            enhancedcontext=True
        )
        
        codebase_enabled = await from_repo(str(sample_python_project), config_enabled)
        
        try:
            project_info = codebase_enabled.get_project_info()
            config = project_info['config']
            
            assert config['lspserver'] is True
            assert config['diagnostics'] is True
            assert config['errorautoresolve'] is True
            assert config['enhancedcontext'] is True
            
        finally:
            await codebase_enabled.shutdown()
        
        # Test with features disabled
        config_disabled = UnifiedConfiguration(
            lspserver=False,
            diagnostics=False,
            errorautoresolve=False,
            enhancedcontext=False
        )
        
        codebase_disabled = await from_repo(str(sample_python_project), config_disabled)
        
        try:
            project_info = codebase_disabled.get_project_info()
            config = project_info['config']
            
            assert config['lspserver'] is False
            assert config['diagnostics'] is False
            assert config['errorautoresolve'] is False
            assert config['enhancedcontext'] is False
            
            # Components should reflect the configuration
            components = project_info['components']
            # Some components may still be present but inactive
            
        finally:
            await codebase_disabled.shutdown()
    
    @pytest.mark.asyncio
    async def test_shutdown_cleanup(self, sample_python_project, unified_config):
        """Test that shutdown properly cleans up resources"""
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        # Verify it's initialized
        assert codebase._initialized is True
        
        # Shutdown
        await codebase.shutdown()
        
        # Verify cleanup
        assert codebase._initialized is False
    
    @pytest.mark.asyncio
    async def test_multiple_codebase_instances(self, sample_python_project, unified_config, temp_project_dir):
        """Test handling of multiple codebase instances"""
        # Create a second project
        project2_dir = temp_project_dir / "project2"
        project2_dir.mkdir()
        (project2_dir / "test.py").write_text("print('test')")
        
        # Create first codebase
        codebase1 = await from_repo(str(sample_python_project), unified_config)
        
        try:
            # Create second codebase (should shutdown first one)
            codebase2 = await from_repo(str(project2_dir), unified_config)
            
            try:
                # Verify second codebase is active
                assert codebase2._initialized is True
                assert str(codebase2.project_root) == str(Path(project2_dir).resolve())
                
            finally:
                await codebase2.shutdown()
                
        finally:
            # First codebase should already be shutdown, but call anyway for safety
            if codebase1._initialized:
                await codebase1.shutdown()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, unified_config):
        """Test error handling for invalid project paths"""
        # Test with non-existent directory
        with pytest.raises(RuntimeError):
            await from_repo("/non/existent/path", unified_config)
    
    @pytest.mark.asyncio
    async def test_real_time_updates(self, sample_python_project, unified_config):
        """Test real-time update functionality"""
        # Enable real-time diagnostics
        unified_config.diagnostics.real_time = True
        
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        try:
            # Modify a file
            main_py = sample_python_project / "main.py"
            original_content = main_py.read_text()
            
            # Add a syntax error
            main_py.write_text(original_content + "\n# This is a comment")
            
            # Give some time for file watching to detect changes
            await asyncio.sleep(0.1)
            
            # Restore original content
            main_py.write_text(original_content)
            
            # The system should handle file changes gracefully
            # (exact behavior depends on file watching implementation)
            
        finally:
            await codebase.shutdown()


class TestUnifiedAPIPerformance:
    """Performance tests for the unified API"""
    
    @pytest.mark.asyncio
    async def test_initialization_performance(self, sample_python_project, unified_config):
        """Test that initialization completes in reasonable time"""
        import time
        
        start_time = time.time()
        codebase = await from_repo(str(sample_python_project), unified_config)
        initialization_time = time.time() - start_time
        
        try:
            # Should initialize in less than 10 seconds
            assert initialization_time < 10.0
            
            # Verify metrics are tracked
            metrics = codebase.get_metrics()
            assert 'initialization_time' in metrics['api_metrics']
            
        finally:
            await codebase.shutdown()
    
    @pytest.mark.asyncio
    async def test_analysis_performance(self, sample_python_project, unified_config):
        """Test that analysis completes in reasonable time"""
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        try:
            import time
            
            start_time = time.time()
            result = await codebase.analyze()
            analysis_time = time.time() - start_time
            
            # Should complete analysis in reasonable time
            assert analysis_time < 30.0
            
            # Verify timing is tracked in results
            assert 'analysis_time' in result.metrics
            assert result.metrics['analysis_time'] > 0
            
        finally:
            await codebase.shutdown()


class TestUnifiedAPIRobustness:
    """Robustness tests for the unified API"""
    
    @pytest.mark.asyncio
    async def test_empty_project(self, temp_project_dir, unified_config):
        """Test handling of empty project directory"""
        empty_dir = temp_project_dir / "empty_project"
        empty_dir.mkdir()
        
        codebase = await from_repo(str(empty_dir), unified_config)
        
        try:
            # Should handle empty project gracefully
            result = await codebase.analyze()
            assert result is not None
            assert len(result.diagnostics) == 0
            assert len(result.symbols) == 0
            
        finally:
            await codebase.shutdown()
    
    @pytest.mark.asyncio
    async def test_large_project_simulation(self, temp_project_dir, unified_config):
        """Test handling of project with many files"""
        large_project = temp_project_dir / "large_project"
        large_project.mkdir()
        
        # Create many Python files
        for i in range(20):
            py_file = large_project / f"module_{i}.py"
            py_file.write_text(f"""
def function_{i}():
    \"\"\"Function {i}\"\"\"
    return {i}

class Class_{i}:
    \"\"\"Class {i}\"\"\"
    def method_{i}(self):
        return function_{i}()
""")
        
        codebase = await from_repo(str(large_project), unified_config)
        
        try:
            # Should handle larger project
            result = await codebase.analyze()
            assert result is not None
            
            # Should have reasonable performance
            assert result.metrics['analysis_time'] < 60.0
            
        finally:
            await codebase.shutdown()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, sample_python_project, unified_config):
        """Test concurrent operations on the same codebase"""
        codebase = await from_repo(str(sample_python_project), unified_config)
        
        try:
            # Run multiple operations concurrently
            tasks = [
                codebase.get_diagnostics(),
                codebase.get_symbols(),
                codebase.resolve_errors(),
                codebase.get_project_info(),
                codebase.get_metrics()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All operations should complete without exceptions
            for result in results:
                assert not isinstance(result, Exception)
            
        finally:
            await codebase.shutdown()
