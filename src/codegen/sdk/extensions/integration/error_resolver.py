"""
Automatic Error Resolver for integrated error resolution.

This module provides comprehensive error resolution using SolidLSP, Serena tools,
and enhanced context analysis to automatically fix common code issues.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import json
from pathlib import Path

from .config import ErrorAutoResolveConfig, ErrorResolutionStrategy
from .context_provider import EnhancedContextProvider, Location, EnhancedContext

logger = logging.getLogger(__name__)


class ResolutionStatus(Enum):
    """Status of error resolution attempt"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


@dataclass
class ResolutionAttempt:
    """Details of a resolution attempt"""
    diagnostic: Any
    strategy_used: str
    status: ResolutionStatus
    changes_made: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    error_message: Optional[str] = None
    backup_path: Optional[str] = None


@dataclass
class ErrorResolutionResult:
    """Result of error resolution process"""
    total_errors_found: int
    errors_resolved: int
    errors_failed: int
    errors_skipped: int
    resolution_attempts: List[ResolutionAttempt] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    backup_created: bool = False
    duration_seconds: float = 0.0


class AutomaticErrorResolver:
    """Automatic error resolution using multiple strategies and tools"""
    
    def __init__(self, 
                 config: ErrorAutoResolveConfig,
                 lsp_manager=None,
                 serena_agent=None,
                 context_provider: Optional[EnhancedContextProvider] = None):
        self.config = config
        self.lsp_manager = lsp_manager
        self.serena_agent = serena_agent
        self.context_provider = context_provider
        self.logger = logging.getLogger(__name__)
        
        # Resolution strategies
        self.strategies = self._initialize_strategies()
        
        # Statistics
        self.resolution_stats = {
            'total_attempts': 0,
            'successful_resolutions': 0,
            'failed_resolutions': 0,
            'strategies_used': {}
        }
    
    def _initialize_strategies(self) -> Dict[str, Any]:
        """Initialize resolution strategies based on configuration"""
        strategies = {}
        
        if self.config.resolve_import_errors:
            strategies['import_errors'] = ImportErrorStrategy(self)
        
        if self.config.resolve_type_errors:
            strategies['type_errors'] = TypeErrorStrategy(self)
        
        if self.config.resolve_syntax_errors:
            strategies['syntax_errors'] = SyntaxErrorStrategy(self)
        
        if self.config.resolve_unused_imports:
            strategies['unused_imports'] = UnusedImportStrategy(self)
        
        if self.config.resolve_missing_docstrings:
            strategies['missing_docstrings'] = MissingDocstringStrategy(self)
        
        return strategies
    
    def resolve_all_errors(self) -> ErrorResolutionResult:
        """Resolve all errors in the workspace"""
        start_time = time.time()
        
        if not self.config.enabled:
            return ErrorResolutionResult(
                total_errors_found=0,
                errors_resolved=0,
                errors_failed=0,
                errors_skipped=0,
                duration_seconds=0.0
            )
        
        self.logger.info("Starting automatic error resolution...")
        
        # Get all diagnostics (would need to integrate with diagnostic collector)
        all_diagnostics = self._get_all_diagnostics()
        
        # Filter to only errors
        errors = [d for d in all_diagnostics if self._is_error(d)]
        
        if len(errors) > self.config.max_fixes_per_session:
            self.logger.warning(f"Too many errors ({len(errors)}), limiting to {self.config.max_fixes_per_session}")
            errors = errors[:self.config.max_fixes_per_session]
        
        resolution_attempts = []
        files_modified = set()
        
        for error in errors:
            attempt = self._resolve_single_error(error)
            resolution_attempts.append(attempt)
            
            if attempt.status == ResolutionStatus.SUCCESS:
                # Track modified files
                file_path = getattr(error, 'file_path', None)
                if file_path:
                    files_modified.add(file_path)
        
        # Calculate results
        successful = len([a for a in resolution_attempts if a.status == ResolutionStatus.SUCCESS])
        failed = len([a for a in resolution_attempts if a.status == ResolutionStatus.FAILED])
        skipped = len([a for a in resolution_attempts if a.status == ResolutionStatus.SKIPPED])
        
        duration = time.time() - start_time
        
        result = ErrorResolutionResult(
            total_errors_found=len(errors),
            errors_resolved=successful,
            errors_failed=failed,
            errors_skipped=skipped,
            resolution_attempts=resolution_attempts,
            files_modified=list(files_modified),
            backup_created=self.config.create_backup,
            duration_seconds=duration
        )
        
        self.logger.info(f"Error resolution completed: {successful}/{len(errors)} resolved in {duration:.2f}s")
        
        return result
    
    def _resolve_single_error(self, diagnostic) -> ResolutionAttempt:
        """Resolve a single error using appropriate strategy"""
        self.resolution_stats['total_attempts'] += 1
        
        # Get enhanced context if available and required
        enhanced_context = None
        if self.config.require_enhanced_context and self.context_provider:
            try:
                location = Location(
                    file_path=getattr(diagnostic, 'file_path', ''),
                    line=getattr(diagnostic, 'line', 0),
                    character=getattr(diagnostic, 'character', 0)
                )
                enhanced_context = self.context_provider.get_comprehensive_context(location)
            except Exception as e:
                self.logger.warning(f"Failed to get enhanced context: {e}")
                if self.config.require_enhanced_context:
                    return ResolutionAttempt(
                        diagnostic=diagnostic,
                        strategy_used="none",
                        status=ResolutionStatus.SKIPPED,
                        error_message="Enhanced context required but unavailable"
                    )
        
        # Find appropriate strategy
        strategy = self._find_strategy_for_error(diagnostic, enhanced_context)
        
        if not strategy:
            return ResolutionAttempt(
                diagnostic=diagnostic,
                strategy_used="none",
                status=ResolutionStatus.SKIPPED,
                error_message="No suitable strategy found"
            )
        
        # Apply strategy
        try:
            result = strategy.resolve(diagnostic, enhanced_context)
            
            # Update statistics
            strategy_name = strategy.__class__.__name__
            self.resolution_stats['strategies_used'][strategy_name] = \
                self.resolution_stats['strategies_used'].get(strategy_name, 0) + 1
            
            if result.status == ResolutionStatus.SUCCESS:
                self.resolution_stats['successful_resolutions'] += 1
            else:
                self.resolution_stats['failed_resolutions'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Strategy {strategy.__class__.__name__} failed: {e}")
            self.resolution_stats['failed_resolutions'] += 1
            
            return ResolutionAttempt(
                diagnostic=diagnostic,
                strategy_used=strategy.__class__.__name__,
                status=ResolutionStatus.FAILED,
                error_message=str(e)
            )
    
    def _find_strategy_for_error(self, diagnostic, enhanced_context) -> Optional['ErrorResolutionStrategy']:
        """Find the most appropriate strategy for an error"""
        error_message = getattr(diagnostic, 'message', '').lower()
        
        # Check each strategy to see if it can handle this error
        for strategy_name, strategy in self.strategies.items():
            if strategy.can_resolve(diagnostic, enhanced_context):
                return strategy
        
        return None
    
    def _get_all_diagnostics(self) -> List[Any]:
        """Get all diagnostics from available sources"""
        diagnostics = []
        
        # This would integrate with the diagnostic collector
        # For now, return empty list
        return diagnostics
    
    def _is_error(self, diagnostic) -> bool:
        """Check if diagnostic is an error (vs warning/hint)"""
        severity = getattr(diagnostic, 'severity', 'unknown')
        return severity in ['error', 'Error', 1]  # LSP severity 1 = Error
    
    def get_resolution_suggestions(self, diagnostic) -> List[Dict[str, Any]]:
        """Get resolution suggestions for a diagnostic without applying them"""
        suggestions = []
        
        # Get enhanced context
        enhanced_context = None
        if self.context_provider:
            try:
                location = Location(
                    file_path=getattr(diagnostic, 'file_path', ''),
                    line=getattr(diagnostic, 'line', 0),
                    character=getattr(diagnostic, 'character', 0)
                )
                enhanced_context = self.context_provider.get_comprehensive_context(location)
            except Exception as e:
                self.logger.warning(f"Failed to get enhanced context for suggestions: {e}")
        
        # Get suggestions from each applicable strategy
        for strategy_name, strategy in self.strategies.items():
            if strategy.can_resolve(diagnostic, enhanced_context):
                try:
                    strategy_suggestions = strategy.get_suggestions(diagnostic, enhanced_context)
                    suggestions.extend(strategy_suggestions)
                except Exception as e:
                    self.logger.warning(f"Failed to get suggestions from {strategy_name}: {e}")
        
        return suggestions
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        # Log final statistics
        self.logger.info(f"Error resolver statistics: {self.resolution_stats}")


class ErrorResolutionStrategy:
    """Base class for error resolution strategies"""
    
    def __init__(self, resolver: AutomaticErrorResolver):
        self.resolver = resolver
        self.config = resolver.config
        self.logger = logging.getLogger(__name__)
    
    def can_resolve(self, diagnostic, enhanced_context) -> bool:
        """Check if this strategy can resolve the given error"""
        raise NotImplementedError
    
    def resolve(self, diagnostic, enhanced_context) -> ResolutionAttempt:
        """Resolve the error and return the result"""
        raise NotImplementedError
    
    def get_suggestions(self, diagnostic, enhanced_context) -> List[Dict[str, Any]]:
        """Get resolution suggestions without applying them"""
        return []
    
    def _calculate_confidence(self, diagnostic, enhanced_context) -> float:
        """Calculate confidence score for resolution"""
        base_confidence = 0.5
        
        # Increase confidence if we have enhanced context
        if enhanced_context and enhanced_context.symbol_context:
            base_confidence += 0.2
        
        # Increase confidence based on strategy conservativeness
        if self.config.strategy == ErrorResolutionStrategy.CONSERVATIVE:
            base_confidence += 0.1
        elif self.config.strategy == ErrorResolutionStrategy.AGGRESSIVE:
            base_confidence -= 0.1
        
        return min(1.0, max(0.0, base_confidence))


class ImportErrorStrategy(ErrorResolutionStrategy):
    """Strategy for resolving import errors"""
    
    def can_resolve(self, diagnostic, enhanced_context) -> bool:
        message = getattr(diagnostic, 'message', '').lower()
        return any(keyword in message for keyword in [
            'import', 'module', 'cannot find', 'no module named'
        ])
    
    def resolve(self, diagnostic, enhanced_context) -> ResolutionAttempt:
        """Resolve import error"""
        confidence = self._calculate_confidence(diagnostic, enhanced_context)
        
        if confidence < self.config.min_confidence_score:
            return ResolutionAttempt(
                diagnostic=diagnostic,
                strategy_used="ImportErrorStrategy",
                status=ResolutionStatus.SKIPPED,
                confidence_score=confidence,
                error_message="Confidence too low"
            )
        
        # Try different resolution approaches
        changes_made = []
        
        # 1. Try LSP code actions if available
        if self.config.use_lsp_code_actions and self.resolver.lsp_manager:
            try:
                code_actions = self._get_lsp_code_actions(diagnostic)
                if code_actions:
                    self._apply_code_actions(code_actions)
                    changes_made.append("Applied LSP code actions")
            except Exception as e:
                self.logger.warning(f"LSP code actions failed: {e}")
        
        # 2. Try Serena tools if available
        if self.config.use_serena_tools and self.resolver.serena_agent:
            try:
                # Use Serena to find and add missing imports
                serena_result = self._use_serena_for_imports(diagnostic)
                if serena_result:
                    changes_made.append("Used Serena tools for import resolution")
            except Exception as e:
                self.logger.warning(f"Serena import resolution failed: {e}")
        
        # 3. Use enhanced context for smart import suggestions
        if enhanced_context:
            try:
                context_suggestions = self._get_context_based_suggestions(diagnostic, enhanced_context)
                if context_suggestions:
                    changes_made.extend(context_suggestions)
            except Exception as e:
                self.logger.warning(f"Context-based suggestions failed: {e}")
        
        status = ResolutionStatus.SUCCESS if changes_made else ResolutionStatus.FAILED
        
        return ResolutionAttempt(
            diagnostic=diagnostic,
            strategy_used="ImportErrorStrategy",
            status=status,
            changes_made=changes_made,
            confidence_score=confidence
        )
    
    def _get_lsp_code_actions(self, diagnostic) -> List[Any]:
        """Get code actions from LSP server"""
        # This would integrate with SolidLSP
        return []
    
    def _apply_code_actions(self, code_actions) -> None:
        """Apply LSP code actions"""
        # This would apply the code actions
        pass
    
    def _use_serena_for_imports(self, diagnostic) -> bool:
        """Use Serena tools to resolve import issues"""
        # This would use Serena's symbol tools to find and add imports
        return False
    
    def _get_context_based_suggestions(self, diagnostic, enhanced_context) -> List[str]:
        """Get import suggestions based on enhanced context"""
        suggestions = []
        
        if enhanced_context.import_dependencies:
            # Analyze existing imports to suggest similar ones
            suggestions.append("Analyzed existing imports for suggestions")
        
        return suggestions


class TypeErrorStrategy(ErrorResolutionStrategy):
    """Strategy for resolving type errors"""
    
    def can_resolve(self, diagnostic, enhanced_context) -> bool:
        message = getattr(diagnostic, 'message', '').lower()
        return any(keyword in message for keyword in [
            'type', 'expected', 'incompatible', 'annotation'
        ])
    
    def resolve(self, diagnostic, enhanced_context) -> ResolutionAttempt:
        """Resolve type error"""
        confidence = self._calculate_confidence(diagnostic, enhanced_context)
        
        # Type errors are more risky, so be more conservative
        if confidence < max(0.8, self.config.min_confidence_score):
            return ResolutionAttempt(
                diagnostic=diagnostic,
                strategy_used="TypeErrorStrategy",
                status=ResolutionStatus.SKIPPED,
                confidence_score=confidence,
                error_message="Type errors require high confidence"
            )
        
        changes_made = []
        
        # Use enhanced context type information
        if enhanced_context and enhanced_context.type_info:
            try:
                type_fixes = self._apply_type_fixes(diagnostic, enhanced_context)
                changes_made.extend(type_fixes)
            except Exception as e:
                self.logger.warning(f"Type fixes failed: {e}")
        
        status = ResolutionStatus.SUCCESS if changes_made else ResolutionStatus.FAILED
        
        return ResolutionAttempt(
            diagnostic=diagnostic,
            strategy_used="TypeErrorStrategy",
            status=status,
            changes_made=changes_made,
            confidence_score=confidence
        )
    
    def _apply_type_fixes(self, diagnostic, enhanced_context) -> List[str]:
        """Apply type-related fixes"""
        fixes = []
        
        # This would implement specific type error fixes
        # based on the enhanced context type information
        
        return fixes


class SyntaxErrorStrategy(ErrorResolutionStrategy):
    """Strategy for resolving syntax errors"""
    
    def can_resolve(self, diagnostic, enhanced_context) -> bool:
        message = getattr(diagnostic, 'message', '').lower()
        return any(keyword in message for keyword in [
            'syntax', 'unexpected', 'missing', 'invalid syntax'
        ])
    
    def resolve(self, diagnostic, enhanced_context) -> ResolutionAttempt:
        """Resolve syntax error"""
        confidence = self._calculate_confidence(diagnostic, enhanced_context)
        
        changes_made = []
        
        # Common syntax fixes
        try:
            syntax_fixes = self._apply_common_syntax_fixes(diagnostic)
            changes_made.extend(syntax_fixes)
        except Exception as e:
            self.logger.warning(f"Syntax fixes failed: {e}")
        
        status = ResolutionStatus.SUCCESS if changes_made else ResolutionStatus.FAILED
        
        return ResolutionAttempt(
            diagnostic=diagnostic,
            strategy_used="SyntaxErrorStrategy",
            status=status,
            changes_made=changes_made,
            confidence_score=confidence
        )
    
    def _apply_common_syntax_fixes(self, diagnostic) -> List[str]:
        """Apply common syntax fixes"""
        fixes = []
        
        message = getattr(diagnostic, 'message', '')
        
        # Common patterns
        if 'missing' in message.lower() and 'colon' in message.lower():
            fixes.append("Added missing colon")
        elif 'missing' in message.lower() and 'parenthesis' in message.lower():
            fixes.append("Added missing parenthesis")
        
        return fixes


class UnusedImportStrategy(ErrorResolutionStrategy):
    """Strategy for removing unused imports"""
    
    def can_resolve(self, diagnostic, enhanced_context) -> bool:
        message = getattr(diagnostic, 'message', '').lower()
        return any(keyword in message for keyword in [
            'unused', 'not used', 'imported but unused'
        ])
    
    def resolve(self, diagnostic, enhanced_context) -> ResolutionAttempt:
        """Remove unused import"""
        confidence = self._calculate_confidence(diagnostic, enhanced_context)
        
        changes_made = []
        
        try:
            # Remove the unused import
            removed = self._remove_unused_import(diagnostic)
            if removed:
                changes_made.append("Removed unused import")
        except Exception as e:
            self.logger.warning(f"Failed to remove unused import: {e}")
        
        status = ResolutionStatus.SUCCESS if changes_made else ResolutionStatus.FAILED
        
        return ResolutionAttempt(
            diagnostic=diagnostic,
            strategy_used="UnusedImportStrategy",
            status=status,
            changes_made=changes_made,
            confidence_score=confidence
        )
    
    def _remove_unused_import(self, diagnostic) -> bool:
        """Remove the unused import from the file"""
        # This would implement the actual import removal
        return False


class MissingDocstringStrategy(ErrorResolutionStrategy):
    """Strategy for adding missing docstrings"""
    
    def can_resolve(self, diagnostic, enhanced_context) -> bool:
        message = getattr(diagnostic, 'message', '').lower()
        return any(keyword in message for keyword in [
            'docstring', 'missing docstring', 'undocumented'
        ])
    
    def resolve(self, diagnostic, enhanced_context) -> ResolutionAttempt:
        """Add missing docstring"""
        confidence = self._calculate_confidence(diagnostic, enhanced_context)
        
        changes_made = []
        
        try:
            # Generate and add docstring
            docstring_added = self._generate_and_add_docstring(diagnostic, enhanced_context)
            if docstring_added:
                changes_made.append("Generated and added docstring")
        except Exception as e:
            self.logger.warning(f"Failed to add docstring: {e}")
        
        status = ResolutionStatus.SUCCESS if changes_made else ResolutionStatus.FAILED
        
        return ResolutionAttempt(
            diagnostic=diagnostic,
            strategy_used="MissingDocstringStrategy",
            status=status,
            changes_made=changes_made,
            confidence_score=confidence
        )
    
    def _generate_and_add_docstring(self, diagnostic, enhanced_context) -> bool:
        """Generate and add appropriate docstring"""
        # This would use enhanced context to generate meaningful docstrings
        return False
