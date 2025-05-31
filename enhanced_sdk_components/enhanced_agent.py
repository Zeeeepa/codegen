"""Enhanced Agent class with Graph-Sitter integration and context awareness."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Union
from functools import lru_cache

from codegen.agents.agent import Agent, AgentTask
from codegen.sdk.core.codebase import Codebase


class ContextProvider:
    """Base class for context providers."""
    
    def get_context(self, prompt: str) -> Dict[str, Any]:
        """Get context relevant to the given prompt."""
        raise NotImplementedError


class GraphSitterContextProvider(ContextProvider):
    """Context provider using Graph-Sitter analysis."""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
    
    def get_context(self, prompt: str) -> Dict[str, Any]:
        """Analyze codebase and extract relevant context for the prompt."""
        context = {
            "relevant_functions": self._find_relevant_functions(prompt),
            "relevant_classes": self._find_relevant_classes(prompt),
            "dependencies": self._analyze_dependencies(prompt),
            "patterns": self._extract_patterns(prompt)
        }
        return context
    
    def _find_relevant_functions(self, prompt: str) -> List[str]:
        """Find functions relevant to the prompt."""
        # Simplified implementation - would use semantic analysis
        relevant_functions = []
        for function in self.codebase.functions:
            if any(keyword in function.name.lower() for keyword in prompt.lower().split()):
                relevant_functions.append(function.name)
        return relevant_functions[:5]  # Limit to top 5
    
    def _find_relevant_classes(self, prompt: str) -> List[str]:
        """Find classes relevant to the prompt."""
        relevant_classes = []
        for cls in self.codebase.classes:
            if any(keyword in cls.name.lower() for keyword in prompt.lower().split()):
                relevant_classes.append(cls.name)
        return relevant_classes[:5]
    
    def _analyze_dependencies(self, prompt: str) -> Dict[str, Any]:
        """Analyze dependencies relevant to the prompt."""
        return {
            "imports": [imp.module for imp in self.codebase.imports][:10],
            "external_modules": [mod.name for mod in self.codebase.external_modules][:5]
        }
    
    def _extract_patterns(self, prompt: str) -> Dict[str, Any]:
        """Extract coding patterns from the codebase."""
        return {
            "common_patterns": ["error_handling", "logging", "validation"],
            "architectural_style": "modular",
            "naming_conventions": "snake_case"
        }


class CacheBackend:
    """Base class for cache backends."""
    
    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        raise NotImplementedError


class InMemoryCache(CacheBackend):
    """Simple in-memory cache implementation."""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            # Check TTL
            if time.time() - self._timestamps[key] < 3600:  # Default 1 hour TTL
                return self._cache[key]
            else:
                # Expired
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        self._cache[key] = value
        self._timestamps[key] = time.time()


class RetryStrategy:
    """Strategy for handling retries with context preservation."""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
    
    def should_retry(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """Determine if we should retry based on the exception and context."""
        # Retry on network errors, rate limits, etc.
        retryable_errors = ["ConnectionError", "TimeoutError", "RateLimitError"]
        return any(error in str(type(exception)) for error in retryable_errors)
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for the given attempt number."""
        return self.base_delay * (self.backoff_factor ** (attempt - 1))
    
    def enhance_prompt(self, original_prompt: str, context: Dict[str, Any]) -> str:
        """Enhance the prompt based on previous failures."""
        errors = context.get("errors", [])
        if errors:
            error_summary = "; ".join(errors[-3:])  # Last 3 errors
            return f"{original_prompt}\n\nNote: Previous attempts failed with: {error_summary}. Please address these issues."
        return original_prompt


class ContextAwareTask(AgentTask):
    """Enhanced AgentTask with context awareness and analysis capabilities."""
    
    def __init__(self, task_data, api_client, org_id, context_manager=None):
        super().__init__(task_data, api_client, org_id)
        self.context_manager = context_manager
        self.code_analysis = None
        self.context_used = {}
    
    def refresh_with_analysis(self):
        """Refresh task status and perform analysis if completed."""
        self.refresh()
        if self.status == "completed" and self.result and self.context_manager:
            self.code_analysis = self.context_manager.analyze_result(self.result)
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of the code analysis."""
        if not self.code_analysis:
            return {"status": "no_analysis", "message": "No analysis available"}
        
        return {
            "status": "analyzed",
            "quality_score": self.code_analysis.get("quality_score", 0),
            "suggestions": self.code_analysis.get("suggestions", []),
            "patterns_used": self.code_analysis.get("patterns", [])
        }


class EnhancedAgent(Agent):
    """Enhanced Agent with Graph-Sitter integration, context awareness, and performance optimizations."""
    
    def __init__(
        self, 
        token: str, 
        org_id: int, 
        base_url: str = None,
        context_providers: List[ContextProvider] = None,
        cache_backend: CacheBackend = None,
        retry_strategy: RetryStrategy = None,
        worker_pool_size: int = 4
    ):
        super().__init__(token, org_id, base_url)
        self.context_providers = context_providers or []
        self.cache = cache_backend or InMemoryCache()
        self.retry_strategy = retry_strategy or RetryStrategy()
        self.worker_pool = ThreadPoolExecutor(max_workers=worker_pool_size)
        
    def add_context_provider(self, provider: ContextProvider):
        """Add a context provider to the agent."""
        self.context_providers.append(provider)
    
    def _build_context(self, prompt: str) -> Dict[str, Any]:
        """Build comprehensive context from all providers."""
        context = {}
        for provider in self.context_providers:
            try:
                provider_context = provider.get_context(prompt)
                context.update(provider_context)
            except Exception as e:
                # Log error but continue with other providers
                print(f"Warning: Context provider {type(provider).__name__} failed: {e}")
        return context
    
    def _enhance_prompt_with_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """Enhance the prompt with relevant context information."""
        if not context:
            return prompt
        
        context_str = self._format_context(context)
        enhanced_prompt = f"""{prompt}

## Relevant Context:
{context_str}

Please consider this context when generating your response."""
        
        return enhanced_prompt
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into a readable string."""
        formatted_parts = []
        
        if "relevant_functions" in context and context["relevant_functions"]:
            formatted_parts.append(f"Relevant functions: {', '.join(context['relevant_functions'])}")
        
        if "relevant_classes" in context and context["relevant_classes"]:
            formatted_parts.append(f"Relevant classes: {', '.join(context['relevant_classes'])}")
        
        if "patterns" in context:
            patterns = context["patterns"]
            if isinstance(patterns, dict):
                formatted_parts.append(f"Code patterns: {', '.join(patterns.get('common_patterns', []))}")
        
        return "\n".join(formatted_parts) if formatted_parts else "No specific context available"
    
    def _generate_cache_key(self, prompt: str) -> str:
        """Generate a cache key for the prompt."""
        import hashlib
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def run_with_context(self, prompt: str, analyze_codebase: bool = True) -> ContextAwareTask:
        """Run agent with enhanced context awareness."""
        context = {}
        if analyze_codebase and self.context_providers:
            context = self._build_context(prompt)
        
        enhanced_prompt = self._enhance_prompt_with_context(prompt, context)
        
        # Use the parent run method but return enhanced task
        task_data = super().run(enhanced_prompt)
        
        # Create enhanced task
        enhanced_task = ContextAwareTask(
            task_data.__dict__, 
            self.api_client, 
            self.org_id
        )
        enhanced_task.context_used = context
        
        return enhanced_task
    
    def run_cached(self, prompt: str, cache_ttl: int = 3600) -> AgentTask:
        """Run agent with caching support."""
        cache_key = self._generate_cache_key(prompt)
        cached_result = self.cache.get(cache_key)
        
        if cached_result:
            # Return cached task
            return AgentTask(cached_result, self.api_client, self.org_id)
        
        # Run normally and cache result
        task = self.run(prompt)
        
        # Cache the task data
        self.cache.set(cache_key, task.__dict__, ttl=cache_ttl)
        
        return task
    
    def run_resilient(self, prompt: str) -> AgentTask:
        """Run agent with intelligent retry logic."""
        context = {"attempt": 0, "errors": []}
        
        while context["attempt"] < self.retry_strategy.max_attempts:
            try:
                return self.run(prompt)
            except Exception as e:
                context["errors"].append(str(e))
                context["attempt"] += 1
                
                if self.retry_strategy.should_retry(e, context):
                    prompt = self.retry_strategy.enhance_prompt(prompt, context)
                    delay = self.retry_strategy.get_delay(context["attempt"])
                    time.sleep(delay)
                else:
                    raise
        
        raise Exception(f"Failed after {self.retry_strategy.max_attempts} attempts")
    
    def run_parallel(self, prompts: List[str]) -> List[AgentTask]:
        """Run multiple prompts in parallel."""
        futures = [
            self.worker_pool.submit(self.run_cached, prompt) 
            for prompt in prompts
        ]
        return [future.result() for future in futures]
    
    async def run_async(self, prompt: str) -> AgentTask:
        """Run agent asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.worker_pool, self.run, prompt)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the agent."""
        return {
            "cache_size": len(getattr(self.cache, '_cache', {})),
            "context_providers": len(self.context_providers),
            "worker_pool_size": self.worker_pool._max_workers,
            "retry_strategy": {
                "max_attempts": self.retry_strategy.max_attempts,
                "base_delay": self.retry_strategy.base_delay
            }
        }


# Example usage and integration patterns
def create_enhanced_agent_with_graph_sitter(
    token: str, 
    org_id: int, 
    codebase_path: str = None
) -> EnhancedAgent:
    """Factory function to create an enhanced agent with Graph-Sitter integration."""
    
    # Create enhanced agent
    agent = EnhancedAgent(
        token=token,
        org_id=org_id,
        cache_backend=InMemoryCache(),
        retry_strategy=RetryStrategy(max_attempts=3),
        worker_pool_size=4
    )
    
    # Add Graph-Sitter context provider if codebase path is provided
    if codebase_path:
        try:
            codebase = Codebase(codebase_path)
            graph_sitter_provider = GraphSitterContextProvider(codebase)
            agent.add_context_provider(graph_sitter_provider)
        except Exception as e:
            print(f"Warning: Could not initialize Graph-Sitter provider: {e}")
    
    return agent


# Example integration with existing codebase
if __name__ == "__main__":
    # Example usage
    agent = create_enhanced_agent_with_graph_sitter(
        token="your_token_here",
        org_id=1,
        codebase_path="./src"
    )
    
    # Run with context awareness
    task = agent.run_with_context("Refactor the authentication module to use JWT tokens")
    
    # Check performance stats
    stats = agent.get_performance_stats()
    print(f"Agent performance stats: {stats}")
    
    # Run multiple tasks in parallel
    prompts = [
        "Add error handling to the API endpoints",
        "Optimize database queries in the user service",
        "Add unit tests for the payment module"
    ]
    
    parallel_tasks = agent.run_parallel(prompts)
    print(f"Completed {len(parallel_tasks)} tasks in parallel")
