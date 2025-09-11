"""Tests for UnifiedDiagnostics system."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from codegen.sdk.config.graph_sitter_config import GraphSitterConfig
from codegen.sdk.diagnostics.unified_diagnostics import UnifiedDiagnostics
from codegen.sdk.diagnostics.diagnostic_types import (
    Diagnostic, DiagnosticSeverity, DiagnosticSource,
    DiagnosticRange, DiagnosticPosition
)


class TestUnifiedDiagnostics:
    """Test cases for UnifiedDiagnostics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GraphSitterConfig(
            lsp_server=True,
            diagnostics=True,
            enhanced_context=True,
            error_auto_resolve=True,
            cache_enabled=False,  # Disable cache for testing
            debug_mode=True
        )
        self.diagnostics = UnifiedDiagnostics(self.config)
    
    def test_initialization(self):
        """Test diagnostics system initialization."""
        assert self.diagnostics.config == self.config
        assert not self.diagnostics._cache_enabled
        
        # Check that collectors are initialized based on config
        expected_sources = {
            "solidlsp", "serena", "tools", "graph_sitter", "autogenlib"
        }
        actual_sources = {source.value for source in self.diagnostics._collectors.keys()}
        assert expected_sources.issubset(actual_sources)
    
    def test_initialization_with_disabled_features(self):
        """Test initialization with some features disabled."""
        config = GraphSitterConfig(
            lsp_server=False,
            diagnostics=True,
            enhanced_context=False,
            error_auto_resolve=False
        )
        diagnostics = UnifiedDiagnostics(config)
        
        # Should have no collectors since most features are disabled
        assert len(diagnostics._collectors) == 0
    
    @pytest.mark.asyncio
    async def test_collect_all_diagnostics_empty(self):
        """Test collecting diagnostics when no issues exist."""
        # Mock all collectors to return empty lists
        for collector in self.diagnostics._collectors.values():
            with patch.object(self.diagnostics, collector.__name__, return_value=[]):
                pass
        
        diagnostics = await self.diagnostics.collect_all_diagnostics()
        assert isinstance(diagnostics, list)
        assert len(diagnostics) == 0
    
    @pytest.mark.asyncio
    async def test_collect_all_diagnostics_with_issues(self):
        """Test collecting diagnostics with actual issues."""
        # Create sample diagnostics
        sample_diagnostic = Diagnostic(
            message="Test error message",
            severity=DiagnosticSeverity.ERROR,
            source=DiagnosticSource.SOLIDLSP,
            file_path=Path("test.py"),
            range=DiagnosticRange(
                start=DiagnosticPosition(line=1, character=0),
                end=DiagnosticPosition(line=1, character=10)
            ),
            code="E001",
            tool_name="test_tool"
        )
        
        # Mock one collector to return the sample diagnostic
        with patch.object(
            self.diagnostics, 
            '_collect_solidlsp_diagnostics', 
            return_value=[sample_diagnostic]
        ):
            diagnostics = await self.diagnostics.collect_all_diagnostics()
            
            assert len(diagnostics) == 1
            assert diagnostics[0] == sample_diagnostic
    
    def test_sort_diagnostics(self):
        """Test diagnostic sorting by severity and location."""
        diagnostics = [
            Diagnostic(
                message="Warning",
                severity=DiagnosticSeverity.WARNING,
                source=DiagnosticSource.SERENA,
                file_path=Path("b.py"),
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=2, character=0),
                    end=DiagnosticPosition(line=2, character=5)
                )
            ),
            Diagnostic(
                message="Error",
                severity=DiagnosticSeverity.ERROR,
                source=DiagnosticSource.SOLIDLSP,
                file_path=Path("a.py"),
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=1, character=0),
                    end=DiagnosticPosition(line=1, character=5)
                )
            ),
            Diagnostic(
                message="Info",
                severity=DiagnosticSeverity.INFO,
                source=DiagnosticSource.TOOLS,
                file_path=Path("c.py"),
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=3, character=0),
                    end=DiagnosticPosition(line=3, character=5)
                )
            )
        ]
        
        sorted_diagnostics = self.diagnostics._sort_diagnostics(diagnostics)
        
        # Should be sorted by severity (error first), then by file path
        assert sorted_diagnostics[0].severity == DiagnosticSeverity.ERROR
        assert sorted_diagnostics[1].severity == DiagnosticSeverity.WARNING
        assert sorted_diagnostics[2].severity == DiagnosticSeverity.INFO
    
    def test_get_diagnostics_by_severity(self):
        """Test filtering diagnostics by severity."""
        diagnostics = [
            Diagnostic(
                message="Error 1",
                severity=DiagnosticSeverity.ERROR,
                source=DiagnosticSource.SOLIDLSP,
                file_path=Path("test.py"),
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=1, character=0),
                    end=DiagnosticPosition(line=1, character=5)
                )
            ),
            Diagnostic(
                message="Warning 1",
                severity=DiagnosticSeverity.WARNING,
                source=DiagnosticSource.SERENA,
                file_path=Path("test.py"),
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=2, character=0),
                    end=DiagnosticPosition(line=2, character=5)
                )
            )
        ]
        
        errors = self.diagnostics.get_diagnostics_by_severity(
            diagnostics, DiagnosticSeverity.ERROR
        )
        warnings = self.diagnostics.get_diagnostics_by_severity(
            diagnostics, DiagnosticSeverity.WARNING
        )
        
        assert len(errors) == 1
        assert len(warnings) == 1
        assert errors[0].message == "Error 1"
        assert warnings[0].message == "Warning 1"
    
    def test_get_diagnostics_by_file(self):
        """Test filtering diagnostics by file path."""
        file_a = Path("a.py")
        file_b = Path("b.py")
        
        diagnostics = [
            Diagnostic(
                message="Error in A",
                severity=DiagnosticSeverity.ERROR,
                source=DiagnosticSource.SOLIDLSP,
                file_path=file_a,
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=1, character=0),
                    end=DiagnosticPosition(line=1, character=5)
                )
            ),
            Diagnostic(
                message="Error in B",
                severity=DiagnosticSeverity.ERROR,
                source=DiagnosticSource.SERENA,
                file_path=file_b,
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=1, character=0),
                    end=DiagnosticPosition(line=1, character=5)
                )
            )
        ]
        
        file_a_diagnostics = self.diagnostics.get_diagnostics_by_file(diagnostics, file_a)
        file_b_diagnostics = self.diagnostics.get_diagnostics_by_file(diagnostics, file_b)
        
        assert len(file_a_diagnostics) == 1
        assert len(file_b_diagnostics) == 1
        assert file_a_diagnostics[0].message == "Error in A"
        assert file_b_diagnostics[0].message == "Error in B"
    
    def test_get_diagnostics_by_source(self):
        """Test filtering diagnostics by source."""
        diagnostics = [
            Diagnostic(
                message="SolidLSP Error",
                severity=DiagnosticSeverity.ERROR,
                source=DiagnosticSource.SOLIDLSP,
                file_path=Path("test.py"),
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=1, character=0),
                    end=DiagnosticPosition(line=1, character=5)
                )
            ),
            Diagnostic(
                message="Serena Error",
                severity=DiagnosticSeverity.ERROR,
                source=DiagnosticSource.SERENA,
                file_path=Path("test.py"),
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=2, character=0),
                    end=DiagnosticPosition(line=2, character=5)
                )
            )
        ]
        
        solidlsp_diagnostics = self.diagnostics.get_diagnostics_by_source(
            diagnostics, DiagnosticSource.SOLIDLSP
        )
        serena_diagnostics = self.diagnostics.get_diagnostics_by_source(
            diagnostics, DiagnosticSource.SERENA
        )
        
        assert len(solidlsp_diagnostics) == 1
        assert len(serena_diagnostics) == 1
        assert solidlsp_diagnostics[0].message == "SolidLSP Error"
        assert serena_diagnostics[0].message == "Serena Error"
    
    def test_get_fixable_diagnostics(self):
        """Test filtering fixable diagnostics."""
        diagnostics = [
            Diagnostic(
                message="Fixable error",
                severity=DiagnosticSeverity.ERROR,
                source=DiagnosticSource.SOLIDLSP,
                file_path=Path("test.py"),
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=1, character=0),
                    end=DiagnosticPosition(line=1, character=5)
                ),
                fix_suggestion="Add missing import"
            ),
            Diagnostic(
                message="Non-fixable error",
                severity=DiagnosticSeverity.ERROR,
                source=DiagnosticSource.SERENA,
                file_path=Path("test.py"),
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=2, character=0),
                    end=DiagnosticPosition(line=2, character=5)
                )
            )
        ]
        
        fixable = self.diagnostics.get_fixable_diagnostics(diagnostics)
        
        assert len(fixable) == 1
        assert fixable[0].message == "Fixable error"
        assert fixable[0].fix_suggestion == "Add missing import"
    
    def test_get_summary(self):
        """Test getting diagnostic summary."""
        diagnostics = [
            Diagnostic(
                message="Error 1",
                severity=DiagnosticSeverity.ERROR,
                source=DiagnosticSource.SOLIDLSP,
                file_path=Path("test.py"),
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=1, character=0),
                    end=DiagnosticPosition(line=1, character=5)
                ),
                fix_suggestion="Fix 1"
            ),
            Diagnostic(
                message="Error 2",
                severity=DiagnosticSeverity.ERROR,
                source=DiagnosticSource.SERENA,
                file_path=Path("test.py"),
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=2, character=0),
                    end=DiagnosticPosition(line=2, character=5)
                )
            ),
            Diagnostic(
                message="Warning 1",
                severity=DiagnosticSeverity.WARNING,
                source=DiagnosticSource.TOOLS,
                file_path=Path("test.py"),
                range=DiagnosticRange(
                    start=DiagnosticPosition(line=3, character=0),
                    end=DiagnosticPosition(line=3, character=5)
                )
            )
        ]
        
        summary = self.diagnostics.get_summary(diagnostics)
        
        assert summary["errors"] == 2
        assert summary["warnings"] == 1
        assert summary["info"] == 0
        assert summary["hints"] == 0
        assert summary["total"] == 3
        assert summary["fixable"] == 1
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        # Test with no files
        key1 = self.diagnostics._get_cache_key(None)
        assert key1 == "all_files"
        
        # Test with specific files
        files = [Path("a.py"), Path("b.py")]
        key2 = self.diagnostics._get_cache_key(files)
        assert isinstance(key2, str)
        assert "a.py" in key2
        assert "b.py" in key2
        
        # Test that order doesn't matter
        files_reversed = [Path("b.py"), Path("a.py")]
        key3 = self.diagnostics._get_cache_key(files_reversed)
        assert key2 == key3
    
    def test_clear_cache(self):
        """Test cache clearing."""
        # Add something to cache
        self.diagnostics._cache["test_key"] = []
        assert len(self.diagnostics._cache) == 1
        
        # Clear cache
        self.diagnostics.clear_cache()
        assert len(self.diagnostics._cache) == 0


class TestUnifiedDiagnosticsIntegration:
    """Integration tests for UnifiedDiagnostics."""
    
    def test_collector_initialization_based_on_config(self):
        """Test that collectors are initialized based on configuration."""
        # Test with all features enabled
        config_all = GraphSitterConfig(
            lsp_server=True,
            diagnostics=True,
            enhanced_context=True,
            error_auto_resolve=True,
            doc_gen=True
        )
        diagnostics_all = UnifiedDiagnostics(config_all)
        assert len(diagnostics_all._collectors) == 5
        
        # Test with minimal features
        config_minimal = GraphSitterConfig(
            lsp_server=False,
            diagnostics=True,
            enhanced_context=False,
            error_auto_resolve=False,
            doc_gen=False
        )
        diagnostics_minimal = UnifiedDiagnostics(config_minimal)
        assert len(diagnostics_minimal._collectors) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_collection(self):
        """Test that diagnostic collection works concurrently."""
        config = GraphSitterConfig(
            lsp_server=True,
            diagnostics=True,
            enhanced_context=True,
            error_auto_resolve=True
        )
        diagnostics = UnifiedDiagnostics(config)
        
        # This test verifies that the concurrent collection doesn't crash
        # In a real scenario, the collectors would be implemented
        result = await diagnostics.collect_all_diagnostics()
        assert isinstance(result, list)
