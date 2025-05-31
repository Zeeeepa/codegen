"""Enhanced AutoGenLib with improved dynamic import system and context awareness."""

import hashlib
import inspect
import os
import sys
import time
from typing import Any, Dict, List, Optional, Protocol
from functools import lru_cache
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class GenerationContext:
    """Context information for code generation."""
    module_path: str
    caller_context: Dict[str, Any]
    codebase_patterns: Dict[str, Any]
    performance_history: Dict[str, float]
    similarity_score: float = 0.0


class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    
    def generate(self, prompt: str, context: GenerationContext = None) -> str:
        """Generate code based on prompt and context."""
        ...
    
    def get_performance_score(self) -> float:
        """Get current performance score for this provider."""
        ...


class OpenAIProvider:
    """OpenAI LLM provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.performance_scores = []
    
    def generate(self, prompt: str, context: GenerationContext = None) -> str:
        """Generate code using OpenAI API."""
        # Simplified implementation - would use actual OpenAI API
        start_time = time.time()
        
        # Enhanced prompt with context
        if context:
            enhanced_prompt = self._enhance_prompt_with_context(prompt, context)
        else:
            enhanced_prompt = prompt
        
        # Simulate API call
        result = f"# Generated code for: {enhanced_prompt[:50]}...\n\ndef generated_function():\n    pass"
        
        # Track performance
        generation_time = time.time() - start_time
        self.performance_scores.append(1.0 / generation_time)  # Inverse of time
        
        return result
    
    def _enhance_prompt_with_context(self, prompt: str, context: GenerationContext) -> str:
        """Enhance prompt with context information."""
        context_parts = []
        
        if context.codebase_patterns:
            patterns = context.codebase_patterns
            context_parts.append(f"Follow these patterns: {patterns}")
        
        if context.caller_context:
            caller_info = context.caller_context
            context_parts.append(f"Caller context: {caller_info}")
        
        if context_parts:
            return f"{prompt}\n\nContext:\n" + "\n".join(context_parts)
        
        return prompt
    
    def get_performance_score(self) -> float:
        """Get average performance score."""
        if not self.performance_scores:
            return 0.0
        return sum(self.performance_scores[-10:]) / min(len(self.performance_scores), 10)


class ProviderPerformanceTracker:
    """Tracks performance of different LLM providers."""
    
    def __init__(self):
        self.provider_scores = {}
        self.provider_usage_count = {}
    
    def record_performance(self, provider_name: str, score: float):
        """Record performance score for a provider."""
        if provider_name not in self.provider_scores:
            self.provider_scores[provider_name] = []
        
        self.provider_scores[provider_name].append(score)
        self.provider_usage_count[provider_name] = self.provider_usage_count.get(provider_name, 0) + 1
    
    def get_best_provider(self, providers: List[LLMProvider]) -> LLMProvider:
        """Select the best performing provider."""
        if not providers:
            raise ValueError("No providers available")
        
        best_provider = providers[0]
        best_score = 0.0
        
        for provider in providers:
            score = provider.get_performance_score()
            if score > best_score:
                best_score = score
                best_provider = provider
        
        return best_provider


class CodebasePatternAnalyzer:
    """Analyzes codebase patterns for context-aware generation."""
    
    def __init__(self, codebase_path: str = None):
        self.codebase_path = codebase_path
        self.pattern_cache = {}
    
    @lru_cache(maxsize=100)
    def extract_patterns(self, module_path: str = None) -> Dict[str, Any]:
        """Extract coding patterns from the codebase."""
        if not self.codebase_path:
            return self._get_default_patterns()
        
        # Simplified pattern extraction
        patterns = {
            "naming_conventions": self._analyze_naming_conventions(),
            "import_patterns": self._analyze_import_patterns(),
            "function_patterns": self._analyze_function_patterns(),
            "error_handling": self._analyze_error_handling(),
            "documentation_style": self._analyze_documentation_style()
        }
        
        return patterns
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """Get default patterns when no codebase is available."""
        return {
            "naming_conventions": "snake_case",
            "import_patterns": ["standard_library_first", "third_party_second", "local_imports_last"],
            "function_patterns": ["type_hints", "docstrings"],
            "error_handling": "exceptions",
            "documentation_style": "google"
        }
    
    def _analyze_naming_conventions(self) -> str:
        """Analyze naming conventions in the codebase."""
        # Simplified implementation
        return "snake_case"
    
    def _analyze_import_patterns(self) -> List[str]:
        """Analyze import patterns."""
        return ["standard_library_first", "third_party_second", "local_imports_last"]
    
    def _analyze_function_patterns(self) -> List[str]:
        """Analyze function definition patterns."""
        return ["type_hints", "docstrings", "error_handling"]
    
    def _analyze_error_handling(self) -> str:
        """Analyze error handling patterns."""
        return "exceptions"
    
    def _analyze_documentation_style(self) -> str:
        """Analyze documentation style."""
        return "google"


class ContextSimilarityCalculator:
    """Calculates similarity between generation contexts for intelligent caching."""
    
    @staticmethod
    def calculate_similarity(context1: GenerationContext, context2: GenerationContext) -> float:
        """Calculate similarity score between two contexts."""
        if not context1 or not context2:
            return 0.0
        
        # Simple similarity based on module path and patterns
        path_similarity = 1.0 if context1.module_path == context2.module_path else 0.0
        
        # Pattern similarity
        patterns1 = context1.codebase_patterns or {}
        patterns2 = context2.codebase_patterns or {}
        
        common_patterns = set(patterns1.keys()) & set(patterns2.keys())
        total_patterns = set(patterns1.keys()) | set(patterns2.keys())
        
        pattern_similarity = len(common_patterns) / len(total_patterns) if total_patterns else 0.0
        
        # Weighted average
        return (path_similarity * 0.4) + (pattern_similarity * 0.6)


class EnhancedAutoGenLib:
    """Enhanced AutoGenLib with improved context awareness and performance."""
    
    def __init__(
        self, 
        providers: List[LLMProvider] = None,
        codebase_path: str = None,
        enable_caching: bool = True,
        cache_similarity_threshold: float = 0.8
    ):
        self.providers = providers or []
        self.pattern_analyzer = CodebasePatternAnalyzer(codebase_path)
        self.performance_tracker = ProviderPerformanceTracker()
        self.enable_caching = enable_caching
        self.cache_similarity_threshold = cache_similarity_threshold
        
        # Enhanced caching system
        self.generation_cache = {}
        self.context_cache = {}
        
        # Performance metrics
        self.generation_stats = {
            "total_generations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_generation_time": 0.0
        }
    
    def add_provider(self, provider: LLMProvider):
        """Add an LLM provider."""
        self.providers.append(provider)
    
    def _compute_context_hash(self, context: GenerationContext) -> str:
        """Compute hash for context-based caching."""
        context_str = f"{context.module_path}_{context.codebase_patterns}_{context.caller_context}"
        return hashlib.md5(context_str.encode()).hexdigest()
    
    def _find_similar_cached_context(self, context: GenerationContext) -> Optional[str]:
        """Find similar cached context based on similarity threshold."""
        if not self.enable_caching:
            return None
        
        for cached_hash, cached_context in self.context_cache.items():
            similarity = ContextSimilarityCalculator.calculate_similarity(context, cached_context)
            if similarity >= self.cache_similarity_threshold:
                return cached_hash
        
        return None
    
    def _build_full_context(self, module_path: str, caller_context: Dict[str, Any]) -> GenerationContext:
        """Build comprehensive context for generation."""
        # Extract codebase patterns
        patterns = self.pattern_analyzer.extract_patterns(module_path)
        
        # Get performance history
        performance_history = {}
        for provider in self.providers:
            provider_name = type(provider).__name__
            performance_history[provider_name] = provider.get_performance_score()
        
        return GenerationContext(
            module_path=module_path,
            caller_context=caller_context,
            codebase_patterns=patterns,
            performance_history=performance_history
        )
    
    def _get_caller_context(self) -> Dict[str, Any]:
        """Extract context from the calling code."""
        frame = inspect.currentframe()
        try:
            # Go up the stack to find the actual caller
            caller_frame = frame.f_back.f_back.f_back  # Skip internal frames
            
            if caller_frame:
                caller_locals = caller_frame.f_locals
                caller_globals = caller_frame.f_globals
                
                # Extract relevant context
                context = {
                    "local_variables": list(caller_locals.keys()),
                    "imported_modules": [name for name in caller_globals.keys() if not name.startswith('__')],
                    "function_name": caller_frame.f_code.co_name,
                    "filename": caller_frame.f_code.co_filename
                }
                
                return context
        finally:
            del frame
        
        return {}
    
    def generate_with_context(self, module_path: str, description: str) -> str:
        """Generate code with enhanced context awareness."""
        start_time = time.time()
        self.generation_stats["total_generations"] += 1
        
        # Build context
        caller_context = self._get_caller_context()
        full_context = self._build_full_context(module_path, caller_context)
        
        # Check for similar cached context
        if self.enable_caching:
            similar_hash = self._find_similar_cached_context(full_context)
            if similar_hash and similar_hash in self.generation_cache:
                self.generation_stats["cache_hits"] += 1
                return self.generation_cache[similar_hash]
        
        # Cache miss - generate new code
        self.generation_stats["cache_misses"] += 1
        
        # Select best provider
        if not self.providers:
            raise ValueError("No LLM providers configured")
        
        provider = self.performance_tracker.get_best_provider(self.providers)
        
        # Generate code
        try:
            result = provider.generate(description, full_context)
            
            # Cache the result
            if self.enable_caching:
                context_hash = self._compute_context_hash(full_context)
                self.generation_cache[context_hash] = result
                self.context_cache[context_hash] = full_context
            
            # Update performance tracking
            generation_time = time.time() - start_time
            self._update_performance_stats(generation_time)
            
            return result
            
        except Exception as e:
            # Try fallback providers
            for fallback_provider in self.providers:
                if fallback_provider != provider:
                    try:
                        result = fallback_provider.generate(description, full_context)
                        
                        # Cache successful fallback
                        if self.enable_caching:
                            context_hash = self._compute_context_hash(full_context)
                            self.generation_cache[context_hash] = result
                            self.context_cache[context_hash] = full_context
                        
                        return result
                    except Exception:
                        continue
            
            # All providers failed
            raise Exception(f"All providers failed to generate code: {e}")
    
    def _update_performance_stats(self, generation_time: float):
        """Update performance statistics."""
        current_avg = self.generation_stats["average_generation_time"]
        total_gens = self.generation_stats["total_generations"]
        
        # Calculate new average
        new_avg = ((current_avg * (total_gens - 1)) + generation_time) / total_gens
        self.generation_stats["average_generation_time"] = new_avg
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        cache_hit_rate = 0.0
        if self.generation_stats["total_generations"] > 0:
            cache_hit_rate = self.generation_stats["cache_hits"] / self.generation_stats["total_generations"]
        
        return {
            **self.generation_stats,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self.generation_cache),
            "providers_count": len(self.providers),
            "caching_enabled": self.enable_caching
        }
    
    def clear_cache(self):
        """Clear the generation cache."""
        self.generation_cache.clear()
        self.context_cache.clear()
    
    def optimize_cache(self, max_size: int = 1000):
        """Optimize cache by removing least recently used entries."""
        if len(self.generation_cache) <= max_size:
            return
        
        # Simple LRU implementation - remove oldest entries
        # In a real implementation, you'd track access times
        items_to_remove = len(self.generation_cache) - max_size
        keys_to_remove = list(self.generation_cache.keys())[:items_to_remove]
        
        for key in keys_to_remove:
            self.generation_cache.pop(key, None)
            self.context_cache.pop(key, None)


class MultiProviderAutoGen(EnhancedAutoGenLib):
    """Multi-provider AutoGen with intelligent provider selection."""
    
    def __init__(self, providers: List[LLMProvider], **kwargs):
        super().__init__(providers=providers, **kwargs)
        self.provider_failure_counts = {}
    
    def generate_optimized(self, module_path: str, description: str) -> str:
        """Generate code with optimized provider selection."""
        # Sort providers by performance score
        sorted_providers = sorted(
            self.providers, 
            key=lambda p: p.get_performance_score(), 
            reverse=True
        )
        
        for provider in sorted_providers:
            provider_name = type(provider).__name__
            
            # Skip providers with high failure rates
            failure_rate = self.provider_failure_counts.get(provider_name, 0)
            if failure_rate > 3:  # Skip if more than 3 recent failures
                continue
            
            try:
                # Build context
                caller_context = self._get_caller_context()
                full_context = self._build_full_context(module_path, caller_context)
                
                result = provider.generate(description, full_context)
                
                # Reset failure count on success
                self.provider_failure_counts[provider_name] = 0
                
                return result
                
            except Exception as e:
                # Increment failure count
                self.provider_failure_counts[provider_name] = failure_rate + 1
                continue
        
        raise Exception("All providers failed or are temporarily disabled")


# Example usage and factory functions
def create_enhanced_autogenlib(
    openai_api_key: str = None,
    codebase_path: str = None,
    enable_caching: bool = True
) -> EnhancedAutoGenLib:
    """Factory function to create enhanced AutoGenLib instance."""
    
    providers = []
    
    # Add OpenAI provider if API key is provided
    if openai_api_key:
        providers.append(OpenAIProvider(openai_api_key))
    
    # Add other providers as needed
    # providers.append(AnthropicProvider(...))
    # providers.append(LocalLLMProvider(...))
    
    return EnhancedAutoGenLib(
        providers=providers,
        codebase_path=codebase_path,
        enable_caching=enable_caching
    )


# Integration with existing AutoGenLib patterns
class ContextAwareGenerator:
    """Context-aware code generator that integrates with Graph-Sitter."""
    
    def __init__(self, autogenlib: EnhancedAutoGenLib, graph_sitter_analyzer=None):
        self.autogenlib = autogenlib
        self.analyzer = graph_sitter_analyzer
    
    def generate_with_analysis(self, module_path: str, description: str) -> str:
        """Generate code with Graph-Sitter analysis integration."""
        enhanced_description = description
        
        if self.analyzer:
            # Analyze existing codebase for patterns
            patterns = self.analyzer.extract_patterns()
            
            # Enhance description with patterns
            enhanced_description = f"""
            {description}
            
            Follow these existing codebase patterns:
            - Naming: {patterns.get('naming_conventions', 'snake_case')}
            - Imports: {patterns.get('import_patterns', [])}
            - Functions: {patterns.get('function_patterns', [])}
            - Error handling: {patterns.get('error_handling', 'exceptions')}
            - Documentation: {patterns.get('documentation_style', 'google')}
            """
        
        return self.autogenlib.generate_with_context(module_path, enhanced_description)


if __name__ == "__main__":
    # Example usage
    autogenlib = create_enhanced_autogenlib(
        openai_api_key="your_api_key_here",
        codebase_path="./src",
        enable_caching=True
    )
    
    # Generate code with context
    result = autogenlib.generate_with_context(
        "utils.authentication", 
        "Create a JWT token validation function"
    )
    
    print("Generated code:", result)
    
    # Check performance stats
    stats = autogenlib.get_performance_stats()
    print("Performance stats:", stats)
