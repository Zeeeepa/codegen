"""Prototype demonstrating SDK + Graph-Sitter + AutoGenLib integration."""

import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

# Import enhanced components
from enhanced_sdk_components.enhanced_agent import EnhancedAgent, ContextProvider
from enhanced_sdk_components.enhanced_autogenlib import EnhancedAutoGenLib, create_enhanced_autogenlib

# Simulated imports for Graph-Sitter and Codegen SDK
from codegen.sdk.core.codebase import Codebase
from codegen.agents.agent import Agent


class AnalysisType(Enum):
    """Types of code analysis."""
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    PATTERNS = "patterns"


@dataclass
class AnalysisResult:
    """Result of code analysis."""
    analysis_type: AnalysisType
    score: float
    issues: List[str]
    suggestions: List[str]
    patterns_found: List[str]
    execution_time: float


class GraphSitterAnalyzer:
    """Enhanced Graph-Sitter analyzer with multiple analysis types."""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.analysis_cache = {}
    
    def get_relevant_context(self, prompt: str) -> Dict[str, Any]:
        """Get context relevant to the prompt."""
        # Analyze prompt to determine relevant code elements
        keywords = prompt.lower().split()
        
        context = {
            "relevant_functions": self._find_relevant_functions(keywords),
            "relevant_classes": self._find_relevant_classes(keywords),
            "dependencies": self._analyze_dependencies(keywords),
            "patterns": self._extract_patterns(),
            "complexity_metrics": self._calculate_complexity_metrics()
        }
        
        return context
    
    def _find_relevant_functions(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Find functions relevant to the keywords."""
        relevant_functions = []
        
        for function in self.codebase.functions:
            relevance_score = 0
            
            # Check function name
            for keyword in keywords:
                if keyword in function.name.lower():
                    relevance_score += 2
            
            # Check function docstring
            if hasattr(function, 'docstring') and function.docstring:
                for keyword in keywords:
                    if keyword in function.docstring.lower():
                        relevance_score += 1
            
            if relevance_score > 0:
                relevant_functions.append({
                    "name": function.name,
                    "file": function.file.path if hasattr(function, 'file') else "unknown",
                    "relevance_score": relevance_score,
                    "signature": str(function),
                    "complexity": self._calculate_function_complexity(function)
                })
        
        # Sort by relevance and return top 10
        relevant_functions.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_functions[:10]
    
    def _find_relevant_classes(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Find classes relevant to the keywords."""
        relevant_classes = []
        
        for cls in self.codebase.classes:
            relevance_score = 0
            
            # Check class name
            for keyword in keywords:
                if keyword in cls.name.lower():
                    relevance_score += 2
            
            if relevance_score > 0:
                relevant_classes.append({
                    "name": cls.name,
                    "file": cls.file.path if hasattr(cls, 'file') else "unknown",
                    "relevance_score": relevance_score,
                    "methods": [method.name for method in cls.methods] if hasattr(cls, 'methods') else [],
                    "inheritance": self._analyze_inheritance(cls)
                })
        
        relevant_classes.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_classes[:5]
    
    def _analyze_dependencies(self, keywords: List[str]) -> Dict[str, Any]:
        """Analyze dependencies relevant to the keywords."""
        return {
            "imports": [imp.module for imp in self.codebase.imports][:15],
            "external_modules": [mod.name for mod in self.codebase.external_modules][:10],
            "internal_dependencies": self._find_internal_dependencies(keywords)
        }
    
    def _extract_patterns(self) -> Dict[str, Any]:
        """Extract coding patterns from the codebase."""
        return {
            "design_patterns": ["singleton", "factory", "observer"],
            "architectural_patterns": ["mvc", "layered"],
            "naming_conventions": "snake_case",
            "error_handling_patterns": ["try_except", "custom_exceptions"],
            "testing_patterns": ["unit_tests", "integration_tests"]
        }
    
    def _calculate_complexity_metrics(self) -> Dict[str, float]:
        """Calculate complexity metrics for the codebase."""
        return {
            "cyclomatic_complexity": 3.2,
            "maintainability_index": 78.5,
            "lines_of_code": len(self.codebase.files) * 100,  # Simplified
            "technical_debt_ratio": 0.15
        }
    
    def _calculate_function_complexity(self, function) -> int:
        """Calculate complexity for a specific function."""
        # Simplified complexity calculation
        return len(str(function)) // 50  # Rough estimate
    
    def _analyze_inheritance(self, cls) -> List[str]:
        """Analyze inheritance hierarchy for a class."""
        # Simplified inheritance analysis
        return ["BaseClass"] if hasattr(cls, 'base_classes') else []
    
    def _find_internal_dependencies(self, keywords: List[str]) -> List[str]:
        """Find internal module dependencies."""
        return ["utils", "models", "services"]  # Simplified
    
    def analyze_impact(self, change_description: str) -> AnalysisResult:
        """Analyze the impact of a potential change."""
        start_time = time.time()
        
        # Simulate impact analysis
        impact_score = 0.7  # High impact
        issues = ["Potential breaking change in API", "May affect dependent modules"]
        suggestions = ["Add deprecation warnings", "Update documentation", "Add migration guide"]
        patterns = ["api_versioning", "backward_compatibility"]
        
        execution_time = time.time() - start_time
        
        return AnalysisResult(
            analysis_type=AnalysisType.SEMANTIC,
            score=impact_score,
            issues=issues,
            suggestions=suggestions,
            patterns_found=patterns,
            execution_time=execution_time
        )
    
    def apply_changes(self, changes: str) -> bool:
        """Apply changes to the codebase."""
        # Simplified change application
        print(f"Applying changes: {changes[:100]}...")
        return True


class IntegratedSDK:
    """Integrated SDK combining Agent, Graph-Sitter, and AutoGenLib."""
    
    def __init__(
        self, 
        agent_config: Dict[str, Any], 
        codebase_path: str,
        autogenlib_config: Dict[str, Any] = None
    ):
        # Initialize components
        self.agent = EnhancedAgent(**agent_config)
        self.codebase = Codebase(codebase_path)
        self.analyzer = GraphSitterAnalyzer(self.codebase)
        
        # Initialize AutoGenLib
        autogenlib_config = autogenlib_config or {}
        self.autogenlib = create_enhanced_autogenlib(
            codebase_path=codebase_path,
            **autogenlib_config
        )
        
        # Add Graph-Sitter context provider to agent
        from enhanced_sdk_components.enhanced_agent import GraphSitterContextProvider
        graph_sitter_provider = GraphSitterContextProvider(self.codebase)
        self.agent.add_context_provider(graph_sitter_provider)
        
        # Performance tracking
        self.execution_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "average_execution_time": 0.0,
            "cache_hit_rate": 0.0
        }
    
    def analyze_and_execute(self, prompt: str, analysis_types: List[AnalysisType] = None) -> Dict[str, Any]:
        """Comprehensive analysis and execution workflow."""
        start_time = time.time()
        self.execution_stats["total_operations"] += 1
        
        try:
            # Step 1: Multi-type analysis
            analysis_results = self._perform_comprehensive_analysis(prompt, analysis_types)
            
            # Step 2: Context enhancement
            context = self.analyzer.get_relevant_context(prompt)
            
            # Step 3: Generate initial solution using AutoGenLib if applicable
            initial_solution = None
            if self._should_use_autogenlib(prompt):
                initial_solution = self._generate_with_autogenlib(prompt, context)
            
            # Step 4: Enhanced prompt creation
            enhanced_prompt = self._create_enhanced_prompt(prompt, context, analysis_results, initial_solution)
            
            # Step 5: Execute with enhanced agent
            task = self.agent.run_with_context(enhanced_prompt)
            
            # Step 6: Post-processing and validation
            if task.status == "completed" and task.result:
                validation_result = self._validate_result(task.result, analysis_results)
                if validation_result["is_valid"]:
                    self._apply_results_to_codebase(task.result)
                else:
                    # Retry with validation feedback
                    task = self._retry_with_feedback(enhanced_prompt, validation_result)
            
            # Update performance stats
            execution_time = time.time() - start_time
            self._update_performance_stats(execution_time, True)
            
            self.execution_stats["successful_operations"] += 1
            
            return {
                "task": task,
                "analysis_results": analysis_results,
                "context": context,
                "initial_solution": initial_solution,
                "execution_time": execution_time,
                "validation": validation_result if 'validation_result' in locals() else None
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_performance_stats(execution_time, False)
            
            return {
                "error": str(e),
                "execution_time": execution_time,
                "analysis_results": analysis_results if 'analysis_results' in locals() else None
            }
    
    def _perform_comprehensive_analysis(self, prompt: str, analysis_types: List[AnalysisType] = None) -> Dict[AnalysisType, AnalysisResult]:
        """Perform comprehensive code analysis."""
        if analysis_types is None:
            analysis_types = [AnalysisType.SEMANTIC, AnalysisType.PATTERNS, AnalysisType.PERFORMANCE]
        
        results = {}
        
        for analysis_type in analysis_types:
            if analysis_type == AnalysisType.SEMANTIC:
                results[analysis_type] = self._semantic_analysis(prompt)
            elif analysis_type == AnalysisType.PATTERNS:
                results[analysis_type] = self._pattern_analysis(prompt)
            elif analysis_type == AnalysisType.PERFORMANCE:
                results[analysis_type] = self._performance_analysis(prompt)
            elif analysis_type == AnalysisType.SECURITY:
                results[analysis_type] = self._security_analysis(prompt)
            elif analysis_type == AnalysisType.SYNTAX:
                results[analysis_type] = self._syntax_analysis(prompt)
        
        return results
    
    def _semantic_analysis(self, prompt: str) -> AnalysisResult:
        """Perform semantic analysis."""
        start_time = time.time()
        
        # Simulate semantic analysis
        score = 0.85
        issues = ["Potential naming inconsistency", "Missing type hints"]
        suggestions = ["Use consistent naming", "Add type annotations"]
        patterns = ["factory_pattern", "dependency_injection"]
        
        return AnalysisResult(
            analysis_type=AnalysisType.SEMANTIC,
            score=score,
            issues=issues,
            suggestions=suggestions,
            patterns_found=patterns,
            execution_time=time.time() - start_time
        )
    
    def _pattern_analysis(self, prompt: str) -> AnalysisResult:
        """Perform pattern analysis."""
        start_time = time.time()
        
        score = 0.78
        issues = ["Inconsistent error handling pattern"]
        suggestions = ["Standardize exception handling", "Use context managers"]
        patterns = ["singleton", "observer", "strategy"]
        
        return AnalysisResult(
            analysis_type=AnalysisType.PATTERNS,
            score=score,
            issues=issues,
            suggestions=suggestions,
            patterns_found=patterns,
            execution_time=time.time() - start_time
        )
    
    def _performance_analysis(self, prompt: str) -> AnalysisResult:
        """Perform performance analysis."""
        start_time = time.time()
        
        score = 0.72
        issues = ["Potential N+1 query problem", "Inefficient loop structure"]
        suggestions = ["Use batch queries", "Optimize loop logic", "Add caching"]
        patterns = ["lazy_loading", "caching", "connection_pooling"]
        
        return AnalysisResult(
            analysis_type=AnalysisType.PERFORMANCE,
            score=score,
            issues=issues,
            suggestions=suggestions,
            patterns_found=patterns,
            execution_time=time.time() - start_time
        )
    
    def _security_analysis(self, prompt: str) -> AnalysisResult:
        """Perform security analysis."""
        start_time = time.time()
        
        score = 0.88
        issues = ["Potential SQL injection vulnerability"]
        suggestions = ["Use parameterized queries", "Add input validation"]
        patterns = ["input_sanitization", "authentication", "authorization"]
        
        return AnalysisResult(
            analysis_type=AnalysisType.SECURITY,
            score=score,
            issues=issues,
            suggestions=suggestions,
            patterns_found=patterns,
            execution_time=time.time() - start_time
        )
    
    def _syntax_analysis(self, prompt: str) -> AnalysisResult:
        """Perform syntax analysis."""
        start_time = time.time()
        
        score = 0.95
        issues = []
        suggestions = ["Consider using f-strings", "Add trailing commas"]
        patterns = ["pep8_compliance", "consistent_formatting"]
        
        return AnalysisResult(
            analysis_type=AnalysisType.SYNTAX,
            score=score,
            issues=issues,
            suggestions=suggestions,
            patterns_found=patterns,
            execution_time=time.time() - start_time
        )
    
    def _should_use_autogenlib(self, prompt: str) -> bool:
        """Determine if AutoGenLib should be used for initial code generation."""
        autogenlib_keywords = ["generate", "create", "implement", "build", "scaffold"]
        return any(keyword in prompt.lower() for keyword in autogenlib_keywords)
    
    def _generate_with_autogenlib(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate initial solution using AutoGenLib."""
        # Extract module path from context or prompt
        module_path = "generated.module"
        
        # Create description for AutoGenLib
        description = f"Generate code for: {prompt}"
        
        return self.autogenlib.generate_with_context(module_path, description)
    
    def _create_enhanced_prompt(
        self, 
        original_prompt: str, 
        context: Dict[str, Any], 
        analysis_results: Dict[AnalysisType, AnalysisResult],
        initial_solution: str = None
    ) -> str:
        """Create an enhanced prompt with all available context."""
        
        enhanced_prompt = f"{original_prompt}\n\n"
        
        # Add context information
        if context.get("relevant_functions"):
            enhanced_prompt += "## Relevant Functions:\n"
            for func in context["relevant_functions"][:3]:  # Top 3
                enhanced_prompt += f"- {func['name']} (complexity: {func['complexity']})\n"
            enhanced_prompt += "\n"
        
        if context.get("relevant_classes"):
            enhanced_prompt += "## Relevant Classes:\n"
            for cls in context["relevant_classes"][:3]:  # Top 3
                enhanced_prompt += f"- {cls['name']} (methods: {len(cls['methods'])})\n"
            enhanced_prompt += "\n"
        
        # Add analysis insights
        enhanced_prompt += "## Analysis Insights:\n"
        for analysis_type, result in analysis_results.items():
            enhanced_prompt += f"### {analysis_type.value.title()} Analysis (Score: {result.score:.2f}):\n"
            if result.issues:
                enhanced_prompt += f"Issues: {', '.join(result.issues[:2])}\n"
            if result.suggestions:
                enhanced_prompt += f"Suggestions: {', '.join(result.suggestions[:2])}\n"
            enhanced_prompt += "\n"
        
        # Add patterns information
        if context.get("patterns"):
            patterns = context["patterns"]
            enhanced_prompt += f"## Codebase Patterns:\n"
            enhanced_prompt += f"- Design patterns: {', '.join(patterns.get('design_patterns', []))}\n"
            enhanced_prompt += f"- Naming: {patterns.get('naming_conventions', 'unknown')}\n"
            enhanced_prompt += f"- Error handling: {', '.join(patterns.get('error_handling_patterns', []))}\n\n"
        
        # Add initial solution if available
        if initial_solution:
            enhanced_prompt += f"## Initial Generated Solution:\n```\n{initial_solution}\n```\n\n"
            enhanced_prompt += "Please review and improve this initial solution based on the analysis above.\n"
        
        enhanced_prompt += "Please consider all the above context and analysis when generating your response."
        
        return enhanced_prompt
    
    def _validate_result(self, result: str, analysis_results: Dict[AnalysisType, AnalysisResult]) -> Dict[str, Any]:
        """Validate the result against analysis findings."""
        validation = {
            "is_valid": True,
            "issues": [],
            "suggestions": [],
            "confidence_score": 0.9
        }
        
        # Simple validation based on analysis results
        for analysis_type, analysis_result in analysis_results.items():
            if analysis_result.score < 0.7:
                validation["issues"].append(f"Low {analysis_type.value} score: {analysis_result.score}")
                validation["confidence_score"] -= 0.1
        
        if validation["confidence_score"] < 0.6:
            validation["is_valid"] = False
        
        return validation
    
    def _retry_with_feedback(self, original_prompt: str, validation_result: Dict[str, Any]):
        """Retry execution with validation feedback."""
        feedback_prompt = f"{original_prompt}\n\n## Validation Feedback:\n"
        feedback_prompt += f"Issues found: {', '.join(validation_result['issues'])}\n"
        feedback_prompt += f"Please address these issues in your response."
        
        return self.agent.run_with_context(feedback_prompt)
    
    def _apply_results_to_codebase(self, result: str) -> bool:
        """Apply results to the codebase if applicable."""
        return self.analyzer.apply_changes(result)
    
    def _update_performance_stats(self, execution_time: float, success: bool):
        """Update performance statistics."""
        current_avg = self.execution_stats["average_execution_time"]
        total_ops = self.execution_stats["total_operations"]
        
        # Update average execution time
        new_avg = ((current_avg * (total_ops - 1)) + execution_time) / total_ops
        self.execution_stats["average_execution_time"] = new_avg
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        success_rate = 0.0
        if self.execution_stats["total_operations"] > 0:
            success_rate = self.execution_stats["successful_operations"] / self.execution_stats["total_operations"]
        
        return {
            **self.execution_stats,
            "success_rate": success_rate,
            "agent_stats": self.agent.get_performance_stats(),
            "autogenlib_stats": self.autogenlib.get_performance_stats()
        }
    
    async def analyze_and_execute_async(self, prompt: str, analysis_types: List[AnalysisType] = None) -> Dict[str, Any]:
        """Asynchronous version of analyze_and_execute."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze_and_execute, prompt, analysis_types)


# Example usage and demonstration
def demo_integrated_sdk():
    """Demonstrate the integrated SDK capabilities."""
    
    print("🚀 Initializing Integrated SDK...")
    
    # Configuration
    agent_config = {
        "token": "demo_token",
        "org_id": 1,
        "worker_pool_size": 2
    }
    
    autogenlib_config = {
        "enable_caching": True,
        "openai_api_key": "demo_key"
    }
    
    # Initialize integrated SDK
    try:
        sdk = IntegratedSDK(
            agent_config=agent_config,
            codebase_path="./src",  # Would be actual codebase path
            autogenlib_config=autogenlib_config
        )
        
        print("✅ SDK initialized successfully")
        
        # Demo 1: Comprehensive analysis and execution
        print("\n📊 Demo 1: Comprehensive Analysis")
        prompt = "Refactor the authentication module to improve security and performance"
        
        result = sdk.analyze_and_execute(
            prompt, 
            analysis_types=[AnalysisType.SECURITY, AnalysisType.PERFORMANCE, AnalysisType.PATTERNS]
        )
        
        print(f"Execution time: {result['execution_time']:.2f}s")
        print(f"Analysis results: {len(result.get('analysis_results', {}))} types completed")
        
        # Demo 2: Code generation with AutoGenLib
        print("\n🔧 Demo 2: Code Generation")
        generation_prompt = "Create a new JWT token validation service with error handling"
        
        generation_result = sdk.analyze_and_execute(generation_prompt)
        print(f"Generation completed in {generation_result['execution_time']:.2f}s")
        
        # Demo 3: Performance statistics
        print("\n📈 Demo 3: Performance Statistics")
        stats = sdk.get_performance_stats()
        print(f"Success rate: {stats['success_rate']:.2%}")
        print(f"Average execution time: {stats['average_execution_time']:.2f}s")
        print(f"Cache hit rate: {stats['agent_stats']['cache_size']} items cached")
        
        return sdk
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return None


async def demo_async_operations():
    """Demonstrate asynchronous operations."""
    print("\n🔄 Demo: Async Operations")
    
    agent_config = {"token": "demo_token", "org_id": 1}
    sdk = IntegratedSDK(agent_config, "./src")
    
    # Run multiple operations concurrently
    prompts = [
        "Optimize database queries in user service",
        "Add error handling to payment module",
        "Implement caching for API responses"
    ]
    
    start_time = time.time()
    
    tasks = [
        sdk.analyze_and_execute_async(prompt, [AnalysisType.PERFORMANCE])
        for prompt in prompts
    ]
    
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    print(f"Completed {len(results)} operations in {total_time:.2f}s")
    
    for i, result in enumerate(results):
        print(f"Operation {i+1}: {result['execution_time']:.2f}s")


if __name__ == "__main__":
    # Run synchronous demo
    sdk = demo_integrated_sdk()
    
    # Run async demo
    if sdk:
        print("\n" + "="*50)
        asyncio.run(demo_async_operations())
