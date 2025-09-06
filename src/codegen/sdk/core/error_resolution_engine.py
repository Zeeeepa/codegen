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
Error Resolution Engine

This module provides automated error resolution capabilities with intelligent
fix suggestions, code transformations, and validation.
"""

import asyncio
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union, Tuple
import threading
import time
from dataclasses import dataclass, field
from enum import Enum

from .integration_interfaces import (
    IErrorResolver, UnifiedDiagnostic, UnifiedSymbol, UnifiedLocation,
    UnifiedRange, UnifiedPosition, DiagnosticSeverity, SymbolKind
)
from .unified_config import UnifiedConfiguration
from .autogenlib_context_enhancer import EnhancedContext

logger = logging.getLogger(__name__)


class FixType(Enum):
    """Types of fixes that can be applied"""
    IMPORT_MISSING = "import_missing"
    TYPE_ANNOTATION = "type_annotation"
    SYNTAX_ERROR = "syntax_error"
    UNDEFINED_VARIABLE = "undefined_variable"
    UNUSED_IMPORT = "unused_import"
    DEAD_CODE = "dead_code"
    REFACTOR = "refactor"
    PERFORMANCE = "performance"


@dataclass
class CodeFix:
    """Represents a code fix"""
    fix_type: FixType
    title: str
    description: str
    file_path: str
    range: UnifiedRange
    new_text: str
    confidence: float
    impact_score: float = 0.0
    validation_required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolutionResult:
    """Result of error resolution"""
    diagnostic: UnifiedDiagnostic
    fixes: List[CodeFix]
    applied_fixes: List[CodeFix] = field(default_factory=list)
    resolution_confidence: float = 0.0
    auto_applied: bool = False
    validation_passed: bool = False
    error_message: Optional[str] = None


class ErrorResolutionEngine(IErrorResolver):
    """
    Automated error resolution engine that provides intelligent fixes
    for common programming errors and code quality issues.
    """
    
    def __init__(self, config: UnifiedConfiguration):
        self.config = config
        self.project_root: Optional[str] = None
        
        # Component dependencies
        self._context_enhancer = None
        self._diagnostic_collector = None
        self._language_server = None
        
        # Resolution patterns
        self._resolution_patterns: Dict[str, List[Dict[str, Any]]] = {}
        self._custom_resolvers: Dict[str, callable] = {}
        
        # State management
        self._lock = threading.RLock()
        self._initialized = False
        
        # Performance tracking
        self._resolution_metrics: Dict[str, Any] = {}
        
        # Initialize built-in patterns
        self._initialize_resolution_patterns()
        
        logger.info("Error resolution engine initialized")
    
    def set_context_enhancer(self, context_enhancer):
        """Inject context enhancer dependency"""
        self._context_enhancer = context_enhancer
    
    def set_diagnostic_collector(self, diagnostic_collector):
        """Inject diagnostic collector dependency"""
        self._diagnostic_collector = diagnostic_collector
    
    def set_language_server(self, language_server):
        """Inject language server dependency"""
        self._language_server = language_server
    
    def initialize(self, project_root: str) -> bool:
        """Initialize the error resolution engine"""
        try:
            with self._lock:
                if self._initialized:
                    return True
                
                self.project_root = project_root
                self._initialized = True
                
                logger.info(f"Error resolution engine initialized for {project_root}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize error resolution engine: {e}")
            return False
    
    async def resolve_error(self, diagnostic: UnifiedDiagnostic, file_path: str, 
                          enhanced_context: Optional[EnhancedContext] = None) -> ResolutionResult:
        """Resolve a single error with automatic fixes"""
        try:
            start_time = time.time()
            
            # Get enhanced context if not provided
            if enhanced_context is None and self._context_enhancer:
                enhanced_context = await self._context_enhancer.enhance_context(diagnostic, file_path)
            
            # Generate fixes
            fixes = await self._generate_fixes(diagnostic, file_path, enhanced_context)
            
            # Calculate resolution confidence
            resolution_confidence = self._calculate_resolution_confidence(fixes)
            
            # Auto-apply high-confidence fixes if enabled
            applied_fixes = []
            auto_applied = False
            validation_passed = False
            error_message = None
            
            if self.config.errorautoresolve and resolution_confidence > 0.8:
                try:
                    applied_fixes = await self._apply_fixes(fixes, file_path)
                    auto_applied = True
                    validation_passed = await self._validate_fixes(applied_fixes, file_path)
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"Failed to auto-apply fixes: {e}")
            
            # Update metrics
            resolution_time = time.time() - start_time
            self._update_resolution_metrics(diagnostic, fixes, resolution_time)
            
            return ResolutionResult(
                diagnostic=diagnostic,
                fixes=fixes,
                applied_fixes=applied_fixes,
                resolution_confidence=resolution_confidence,
                auto_applied=auto_applied,
                validation_passed=validation_passed,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"Failed to resolve error: {e}")
            return ResolutionResult(
                diagnostic=diagnostic,
                fixes=[],
                error_message=str(e)
            )
    
    async def resolve_errors(self, diagnostics: List[UnifiedDiagnostic], 
                           file_paths: Optional[List[str]] = None) -> List[ResolutionResult]:
        """Resolve multiple errors"""
        try:
            results = []
            
            for i, diagnostic in enumerate(diagnostics):
                file_path = file_paths[i] if file_paths and i < len(file_paths) else "unknown"
                result = await self.resolve_error(diagnostic, file_path)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to resolve errors: {e}")
            return []
    
    def add_custom_resolver(self, pattern: str, resolver: callable) -> None:
        """Add a custom error resolver"""
        try:
            self._custom_resolvers[pattern] = resolver
            logger.info(f"Added custom resolver for pattern: {pattern}")
            
        except Exception as e:
            logger.error(f"Failed to add custom resolver: {e}")
    
    # Private methods
    
    def _initialize_resolution_patterns(self) -> None:
        """Initialize built-in resolution patterns"""
        try:
            # Python patterns
            self._resolution_patterns["python"] = [
                {
                    "pattern": r"name '(\w+)' is not defined",
                    "fix_type": FixType.UNDEFINED_VARIABLE,
                    "resolver": self._resolve_undefined_variable
                },
                {
                    "pattern": r"No module named '([\w\.]+)'",
                    "fix_type": FixType.IMPORT_MISSING,
                    "resolver": self._resolve_missing_import
                },
                {
                    "pattern": r"unused import '([\w\.]+)'",
                    "fix_type": FixType.UNUSED_IMPORT,
                    "resolver": self._resolve_unused_import
                },
                {
                    "pattern": r"invalid syntax",
                    "fix_type": FixType.SYNTAX_ERROR,
                    "resolver": self._resolve_syntax_error
                }
            ]
            
            # JavaScript/TypeScript patterns
            self._resolution_patterns["javascript"] = [
                {
                    "pattern": r"'(\w+)' is not defined",
                    "fix_type": FixType.UNDEFINED_VARIABLE,
                    "resolver": self._resolve_undefined_variable
                },
                {
                    "pattern": r"Cannot find module '([\w\./]+)'",
                    "fix_type": FixType.IMPORT_MISSING,
                    "resolver": self._resolve_missing_import
                }
            ]
            
            logger.debug("Resolution patterns initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize resolution patterns: {e}")
    
    async def _generate_fixes(self, diagnostic: UnifiedDiagnostic, file_path: str,
                            enhanced_context: Optional[EnhancedContext]) -> List[CodeFix]:
        """Generate fixes for a diagnostic"""
        try:
            fixes = []
            
            # Try pattern-based resolution
            pattern_fixes = await self._generate_pattern_fixes(diagnostic, file_path, enhanced_context)
            fixes.extend(pattern_fixes)
            
            # Try custom resolvers
            custom_fixes = await self._generate_custom_fixes(diagnostic, file_path, enhanced_context)
            fixes.extend(custom_fixes)
            
            # Try context-based resolution
            if enhanced_context:
                context_fixes = await self._generate_context_fixes(diagnostic, file_path, enhanced_context)
                fixes.extend(context_fixes)
            
            # Sort by confidence
            fixes.sort(key=lambda x: x.confidence, reverse=True)
            
            return fixes[:5]  # Return top 5 fixes
            
        except Exception as e:
            logger.error(f"Failed to generate fixes: {e}")
            return []
    
    async def _generate_pattern_fixes(self, diagnostic: UnifiedDiagnostic, file_path: str,
                                    enhanced_context: Optional[EnhancedContext]) -> List[CodeFix]:
        """Generate fixes using pattern matching"""
        try:
            fixes = []
            language = self._detect_language(file_path)
            
            if language not in self._resolution_patterns:
                return fixes
            
            patterns = self._resolution_patterns[language]
            
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                match = re.search(pattern, diagnostic.message)
                
                if match:
                    resolver = pattern_info["resolver"]
                    fix = await resolver(diagnostic, file_path, match, enhanced_context)
                    if fix:
                        fixes.append(fix)
            
            return fixes
            
        except Exception as e:
            logger.error(f"Failed to generate pattern fixes: {e}")
            return []
    
    async def _generate_custom_fixes(self, diagnostic: UnifiedDiagnostic, file_path: str,
                                   enhanced_context: Optional[EnhancedContext]) -> List[CodeFix]:
        """Generate fixes using custom resolvers"""
        try:
            fixes = []
            
            for pattern, resolver in self._custom_resolvers.items():
                if re.search(pattern, diagnostic.message):
                    try:
                        fix = await resolver(diagnostic, file_path, enhanced_context)
                        if fix:
                            fixes.append(fix)
                    except Exception as e:
                        logger.debug(f"Custom resolver failed: {e}")
            
            return fixes
            
        except Exception as e:
            logger.error(f"Failed to generate custom fixes: {e}")
            return []
    
    async def _generate_context_fixes(self, diagnostic: UnifiedDiagnostic, file_path: str,
                                    enhanced_context: EnhancedContext) -> List[CodeFix]:
        """Generate fixes using enhanced context"""
        try:
            fixes = []
            
            # Use suggested fixes from context enhancer
            for suggested_fix in enhanced_context.suggested_fixes:
                fix = CodeFix(
                    fix_type=FixType(suggested_fix.get('fix_type', 'refactor')),
                    title=suggested_fix.get('title', 'Context-based fix'),
                    description=suggested_fix.get('description', ''),
                    file_path=file_path,
                    range=diagnostic.range,
                    new_text=suggested_fix.get('suggested_code', ''),
                    confidence=suggested_fix.get('confidence', 0.5)
                )
                fixes.append(fix)
            
            return fixes
            
        except Exception as e:
            logger.error(f"Failed to generate context fixes: {e}")
            return []
    
    # Specific resolvers
    
    async def _resolve_undefined_variable(self, diagnostic: UnifiedDiagnostic, file_path: str,
                                        match: re.Match, enhanced_context: Optional[EnhancedContext]) -> Optional[CodeFix]:
        """Resolve undefined variable errors"""
        try:
            variable_name = match.group(1)
            
            # Check if it's a common import
            common_imports = {
                'os': 'import os',
                'sys': 'import sys',
                'json': 'import json',
                'time': 'import time',
                'datetime': 'from datetime import datetime',
                'Path': 'from pathlib import Path'
            }
            
            if variable_name in common_imports:
                return CodeFix(
                    fix_type=FixType.IMPORT_MISSING,
                    title=f"Add import for {variable_name}",
                    description=f"Import {variable_name} module",
                    file_path=file_path,
                    range=UnifiedRange(
                        start=UnifiedPosition(line=0, character=0),
                        end=UnifiedPosition(line=0, character=0)
                    ),
                    new_text=common_imports[variable_name] + '\n',
                    confidence=0.8
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to resolve undefined variable: {e}")
            return None
    
    async def _resolve_missing_import(self, diagnostic: UnifiedDiagnostic, file_path: str,
                                    match: re.Match, enhanced_context: Optional[EnhancedContext]) -> Optional[CodeFix]:
        """Resolve missing import errors"""
        try:
            module_name = match.group(1)
            
            return CodeFix(
                fix_type=FixType.IMPORT_MISSING,
                title=f"Add import for {module_name}",
                description=f"Import missing module {module_name}",
                file_path=file_path,
                range=UnifiedRange(
                    start=UnifiedPosition(line=0, character=0),
                    end=UnifiedPosition(line=0, character=0)
                ),
                new_text=f"import {module_name}\n",
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"Failed to resolve missing import: {e}")
            return None
    
    async def _resolve_unused_import(self, diagnostic: UnifiedDiagnostic, file_path: str,
                                   match: re.Match, enhanced_context: Optional[EnhancedContext]) -> Optional[CodeFix]:
        """Resolve unused import errors"""
        try:
            if not diagnostic.range:
                return None
            
            return CodeFix(
                fix_type=FixType.UNUSED_IMPORT,
                title="Remove unused import",
                description="Remove the unused import statement",
                file_path=file_path,
                range=diagnostic.range,
                new_text="",
                confidence=0.95
            )
            
        except Exception as e:
            logger.error(f"Failed to resolve unused import: {e}")
            return None
    
    async def _resolve_syntax_error(self, diagnostic: UnifiedDiagnostic, file_path: str,
                                  match: re.Match, enhanced_context: Optional[EnhancedContext]) -> Optional[CodeFix]:
        """Resolve syntax errors"""
        try:
            # This is a complex resolver that would need more context
            # For now, return a low-confidence suggestion
            return CodeFix(
                fix_type=FixType.SYNTAX_ERROR,
                title="Fix syntax error",
                description="Manual review required for syntax error",
                file_path=file_path,
                range=diagnostic.range or UnifiedRange(
                    start=UnifiedPosition(line=0, character=0),
                    end=UnifiedPosition(line=0, character=0)
                ),
                new_text="# TODO: Fix syntax error",
                confidence=0.3,
                validation_required=True
            )
            
        except Exception as e:
            logger.error(f"Failed to resolve syntax error: {e}")
            return None
    
    async def _apply_fixes(self, fixes: List[CodeFix], file_path: str) -> List[CodeFix]:
        """Apply fixes to the file"""
        try:
            applied_fixes = []
            
            # Read current file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                return applied_fixes
            
            # Apply fixes in reverse order (by line number) to maintain positions
            fixes_to_apply = [f for f in fixes if f.confidence > 0.8]
            fixes_to_apply.sort(key=lambda x: x.range.start.line, reverse=True)
            
            for fix in fixes_to_apply:
                try:
                    if fix.fix_type == FixType.IMPORT_MISSING and fix.range.start.line == 0:
                        # Add import at the beginning
                        lines.insert(0, fix.new_text.rstrip())
                        applied_fixes.append(fix)
                    elif fix.fix_type == FixType.UNUSED_IMPORT:
                        # Remove the line
                        if 0 <= fix.range.start.line < len(lines):
                            lines.pop(fix.range.start.line)
                            applied_fixes.append(fix)
                    else:
                        # Replace text in range
                        start_line = fix.range.start.line
                        end_line = fix.range.end.line
                        
                        if 0 <= start_line < len(lines):
                            if start_line == end_line:
                                # Single line replacement
                                line = lines[start_line]
                                new_line = (line[:fix.range.start.character] + 
                                          fix.new_text + 
                                          line[fix.range.end.character:])
                                lines[start_line] = new_line
                            else:
                                # Multi-line replacement
                                lines[start_line:end_line+1] = [fix.new_text]
                            
                            applied_fixes.append(fix)
                            
                except Exception as e:
                    logger.error(f"Failed to apply fix: {e}")
            
            # Write back to file
            if applied_fixes:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    logger.info(f"Applied {len(applied_fixes)} fixes to {file_path}")
                except Exception as e:
                    logger.error(f"Failed to write file {file_path}: {e}")
                    return []
            
            return applied_fixes
            
        except Exception as e:
            logger.error(f"Failed to apply fixes: {e}")
            return []
    
    async def _validate_fixes(self, applied_fixes: List[CodeFix], file_path: str) -> bool:
        """Validate that applied fixes don't break the code"""
        try:
            if not applied_fixes:
                return True
            
            # Basic validation - check if file is still parseable
            language = self._detect_language(file_path)
            
            if language == "python":
                return await self._validate_python_syntax(file_path)
            elif language in ["javascript", "typescript"]:
                return await self._validate_js_syntax(file_path)
            
            return True  # Default to true for unknown languages
            
        except Exception as e:
            logger.error(f"Failed to validate fixes: {e}")
            return False
    
    async def _validate_python_syntax(self, file_path: str) -> bool:
        """Validate Python syntax"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            compile(content, file_path, 'exec')
            return True
            
        except SyntaxError as e:
            logger.warning(f"Syntax error after applying fixes: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to validate Python syntax: {e}")
            return False
    
    async def _validate_js_syntax(self, file_path: str) -> bool:
        """Validate JavaScript/TypeScript syntax"""
        try:
            # This would require a JavaScript parser
            # For now, return True as a placeholder
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate JS syntax: {e}")
            return False
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        extension = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php'
        }
        
        return language_map.get(extension, 'unknown')
    
    def _calculate_resolution_confidence(self, fixes: List[CodeFix]) -> float:
        """Calculate overall resolution confidence"""
        if not fixes:
            return 0.0
        
        # Weight by confidence and impact
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for fix in fixes:
            weight = fix.confidence * (1.0 + fix.impact_score)
            weighted_confidence += fix.confidence * weight
            total_weight += weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def _update_resolution_metrics(self, diagnostic: UnifiedDiagnostic, 
                                 fixes: List[CodeFix], resolution_time: float) -> None:
        """Update resolution metrics"""
        try:
            key = f"{diagnostic.source}:{diagnostic.severity.value}"
            
            if key not in self._resolution_metrics:
                self._resolution_metrics[key] = {
                    'count': 0,
                    'total_time': 0.0,
                    'total_fixes': 0,
                    'successful_resolutions': 0
                }
            
            metrics = self._resolution_metrics[key]
            metrics['count'] += 1
            metrics['total_time'] += resolution_time
            metrics['total_fixes'] += len(fixes)
            
            if fixes and max(fix.confidence for fix in fixes) > 0.8:
                metrics['successful_resolutions'] += 1
                
        except Exception as e:
            logger.error(f"Failed to update resolution metrics: {e}")
    
    def get_resolution_metrics(self) -> Dict[str, Any]:
        """Get resolution metrics"""
        try:
            return {
                'initialized': self._initialized,
                'project_root': self.project_root,
                'resolution_patterns': {
                    lang: len(patterns) for lang, patterns in self._resolution_patterns.items()
                },
                'custom_resolvers': len(self._custom_resolvers),
                'metrics': dict(self._resolution_metrics)
            }
            
        except Exception as e:
            logger.error(f"Failed to get resolution metrics: {e}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status"""
        return {
            'initialized': self._initialized,
            'project_root': self.project_root,
            'config': {
                'errorautoresolve': self.config.errorautoresolve
            },
            'patterns_loaded': sum(len(patterns) for patterns in self._resolution_patterns.values()),
            'custom_resolvers': len(self._custom_resolvers)
        }
