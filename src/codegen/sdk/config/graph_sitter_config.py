"""Configuration schema for graph-sitter SDK extensions integration."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class GraphSitterConfig:
    """Configuration for graph-sitter SDK extensions.

    This configuration controls the integration of SolidLSP, Serena, AutogenLib,
    and the tools directory into a unified system with 5 main parameters.
    """

    # Core configuration parameters (all default to True)
    lsp_server: bool = True
    """Enable SolidLSP language server functionality for real-time code analysis."""

    diagnostics: bool = True
    """Enable unified diagnostics from SolidLSP + Serena + graph-sitter tools."""

    error_auto_resolve: bool = True
    """Enable intelligent error auto-resolution using combined contexts."""

    enhanced_context: bool = True
    """Enable enhanced context retrieval from autogenlib + solidlsp + graph-sitter + serena."""

    doc_gen: bool = True
    """Enable comprehensive documentation generation using all 15 tools."""

    # Advanced configuration options
    max_context_tokens: int = 10000
    """Maximum tokens for context retrieval operations."""

    context_degree: int = 3
    """Maximum degree for recursive context collection."""

    cache_enabled: bool = True
    """Enable caching for performance optimization."""

    debug_mode: bool = False
    """Enable debug logging and verbose output."""

    # Directory paths (auto-detected if not specified)
    sdk_root: Path | None = None
    """Root directory of the SDK (auto-detected)."""

    extensions_root: Path | None = None
    """Root directory of extensions (auto-detected)."""

    def __post_init__(self):
        """Initialize auto-detected paths."""
        if self.sdk_root is None:
            # Auto-detect SDK root
            current_file = Path(__file__)
            self.sdk_root = current_file.parent.parent

        if self.extensions_root is None:
            self.extensions_root = self.sdk_root / "extensions"

    @property
    def solidlsp_root(self) -> Path:
        """Path to SolidLSP root directory."""
        if self.extensions_root is None:
            msg = "extensions_root is not set"
            raise ValueError(msg)
        return self.extensions_root / "lsp" / "solidlsp"

    @property
    def serena_root(self) -> Path:
        """Path to Serena root directory."""
        if self.extensions_root is None:
            msg = "extensions_root is not set"
            raise ValueError(msg)
        return self.extensions_root / "lsp" / "serena"

    @property
    def autogenlib_root(self) -> Path:
        """Path to AutogenLib root directory."""
        if self.extensions_root is None:
            msg = "extensions_root is not set"
            raise ValueError(msg)
        return self.extensions_root / "autogenlib"

    @property
    def tools_root(self) -> Path:
        """Path to tools directory."""
        if self.extensions_root is None:
            msg = "extensions_root is not set"
            raise ValueError(msg)
        return self.extensions_root / "tools"

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        # Check that required directories exist
        required_dirs = [
            ("SDK root", self.sdk_root),
            ("Extensions root", self.extensions_root),
            ("Tools directory", self.tools_root),
            ("AutogenLib directory", self.autogenlib_root),
        ]

        if self.lsp_server:
            required_dirs.extend([
                ("SolidLSP directory", self.solidlsp_root),
                ("Serena directory", self.serena_root),
            ])

        for name, path in required_dirs:
            if path is not None and not path.exists():
                errors.append(f"{name} not found: {path}")

        # Validate parameter combinations
        if self.error_auto_resolve and not self.enhanced_context:
            errors.append("error_auto_resolve requires enhanced_context to be enabled")

        if self.diagnostics and not (self.lsp_server or self.enhanced_context):
            errors.append("diagnostics requires either lsp_server or enhanced_context to be enabled")

        # Validate numeric parameters
        if self.max_context_tokens <= 0:
            errors.append("max_context_tokens must be positive")

        if self.context_degree <= 0:
            errors.append("context_degree must be positive")

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0

    def get_enabled_features(self) -> list[str]:
        """Get list of enabled features."""
        features = []
        if self.lsp_server:
            features.append("lsp_server")
        if self.diagnostics:
            features.append("diagnostics")
        if self.error_auto_resolve:
            features.append("error_auto_resolve")
        if self.enhanced_context:
            features.append("enhanced_context")
        if self.doc_gen:
            features.append("doc_gen")
        return features

    def __str__(self) -> str:
        """String representation of configuration."""
        enabled = self.get_enabled_features()
        return f"GraphSitterConfig(enabled_features={enabled})"


# Default configuration instance
DEFAULT_CONFIG = GraphSitterConfig()
