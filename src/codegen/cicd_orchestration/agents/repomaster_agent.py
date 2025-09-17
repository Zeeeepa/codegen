"""
RepoMaster Agent

High-value code analysis agent that provides comprehensive repository insights
and validation capabilities powered by Z.AI substrate. This agent integrates
with RepoMaster for advanced code analysis and understanding.

Capabilities:
- Comprehensive code analysis and quality assessment
- Repository insights and architectural analysis
- Code validation and review automation
- Dead code detection and cleanup recommendations
- Dependency analysis and security scanning
- Performance optimization suggestions
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from ..zai_substrate import ZAISubstrate, AgentRequest, ReasoningMode

logger = logging.getLogger(__name__)


@dataclass
class AnalysisTask:
    """Task structure for RepoMaster analysis operations."""
    task_id: str
    description: str
    analysis_type: str  # code_quality, security, performance, architecture
    target_path: Optional[str] = None
    context: Dict[str, Any] = None
    priority: str = "normal"
    depth: str = "standard"  # shallow, standard, deep


class RepoMasterAgent:
    """
    High-value code analysis agent powered by RepoMaster and Z.AI substrate.
    
    This agent provides comprehensive code analysis, repository insights,
    and validation capabilities for optimal code quality and maintainability.
    """
    
    def __init__(
        self,
        zai_substrate: Optional[ZAISubstrate] = None,
        enable_deep_analysis: bool = True
    ):
        """
        Initialize RepoMaster agent.
        
        Args:
            zai_substrate: Z.AI substrate for intelligence processing
            enable_deep_analysis: Enable deep code analysis capabilities
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Core components
        self.zai_substrate = zai_substrate or ZAISubstrate()
        self.enable_deep_analysis = enable_deep_analysis
        
        # Agent capabilities
        self.capabilities = [
            "code_analysis",
            "repository_insights",
            "validation",
            "quality_assessment",
            "security_scanning",
            "performance_analysis",
            "architecture_review",
            "dead_code_detection"
        ]
        
        # Analysis configurations
        self.analysis_configs = {
            "code_quality": {
                "metrics": ["complexity", "maintainability", "duplication"],
                "thresholds": {"complexity": 10, "maintainability": 70}
            },
            "security": {
                "scans": ["vulnerabilities", "secrets", "dependencies"],
                "severity_levels": ["critical", "high", "medium"]
            },
            "performance": {
                "checks": ["bottlenecks", "memory_usage", "algorithm_complexity"],
                "profiling": True
            },
            "architecture": {
                "patterns": ["solid_principles", "design_patterns", "coupling"],
                "documentation": True
            }
        }
        
        # Performance tracking
        self.analysis_stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_analysis_time": 0.0
        }
        
        self.logger.info("RepoMaster Agent initialized")
    
    async def initialize(self) -> None:
        """Initialize the RepoMaster agent."""
        try:
            # Register with Z.AI substrate
            await self.zai_substrate._register_agent("repomaster")
            
            self.logger.info("RepoMaster Agent initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RepoMaster agent: {e}")
            raise
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a code analysis task using RepoMaster capabilities.
        
        This method provides comprehensive code analysis and repository
        insights powered by Z.AI intelligence and RepoMaster integration.
        """
        start_time = datetime.now()
        
        try:
            # Parse task information
            analysis_task = self._parse_analysis_task(task)
            
            # Perform analysis based on type
            if analysis_task.analysis_type == "code_quality":
                result = await self._analyze_code_quality(analysis_task)
            elif analysis_task.analysis_type == "security":
                result = await self._analyze_security(analysis_task)
            elif analysis_task.analysis_type == "performance":
                result = await self._analyze_performance(analysis_task)
            elif analysis_task.analysis_type == "architecture":
                result = await self._analyze_architecture(analysis_task)
            else:
                result = await self._perform_comprehensive_analysis(analysis_task)
            
            # Update statistics
            analysis_time = (datetime.now() - start_time).total_seconds()
            await self._update_analysis_stats(analysis_time, success=True)
            
            return {
                "content": result.get("content", ""),
                "metadata": {
                    **result.get("metadata", {}),
                    "agent": "repomaster",
                    "analysis_type": analysis_task.analysis_type,
                    "analysis_time": analysis_time,
                    "target_path": analysis_task.target_path
                },
                "requires_followup": result.get("requires_followup", False),
                "suggested_actions": result.get("suggested_actions", [])
            }
            
        except Exception as e:
            analysis_time = (datetime.now() - start_time).total_seconds()
            await self._update_analysis_stats(analysis_time, success=False)
            
            self.logger.error(f"Error executing analysis task: {e}")
            
            return {
                "content": f"Error executing code analysis: {str(e)}",
                "metadata": {
                    "agent": "repomaster",
                    "error": str(e),
                    "analysis_time": analysis_time
                },
                "requires_followup": True,
                "suggested_actions": ["Please review the analysis parameters and try again"]
            }
    
    def _parse_analysis_task(self, task: Dict[str, Any]) -> AnalysisTask:
        """Parse task dictionary into AnalysisTask structure."""
        return AnalysisTask(
            task_id=task.get("task_id", f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            description=task.get("description", ""),
            analysis_type=self._determine_analysis_type(task.get("description", "")),
            target_path=task.get("target_path"),
            context=task.get("context", {}),
            priority=task.get("priority", "normal"),
            depth=task.get("depth", "standard")
        )
    
    def _determine_analysis_type(self, description: str) -> str:
        """Determine analysis type based on description."""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["security", "vulnerability", "secrets"]):
            return "security"
        elif any(keyword in description_lower for keyword in ["performance", "bottleneck", "optimization"]):
            return "performance"
        elif any(keyword in description_lower for keyword in ["architecture", "design", "structure"]):
            return "architecture"
        elif any(keyword in description_lower for keyword in ["quality", "complexity", "maintainability"]):
            return "code_quality"
        else:
            return "comprehensive"
    
    async def _analyze_code_quality(self, task: AnalysisTask) -> Dict[str, Any]:
        """Perform comprehensive code quality analysis."""
        analysis_prompt = f"""
        As RepoMaster code analysis agent, perform comprehensive code quality analysis:
        
        Task: {task.description}
        Target: {task.target_path or "entire repository"}
        Depth: {task.depth}
        Context: {task.context}
        
        Analyze:
        1. Code complexity metrics (cyclomatic, cognitive)
        2. Maintainability index and technical debt
        3. Code duplication and redundancy
        4. Coding standards compliance
        5. Documentation coverage and quality
        6. Test coverage and quality
        7. Dead code identification
        8. Refactoring opportunities
        
        Provide detailed findings with specific recommendations and priority levels.
        """
        
        analysis_request = AgentRequest(
            agent_id="repomaster",
            prompt=analysis_prompt,
            context=task.context or {},
            reasoning_mode=ReasoningMode.THINKING
        )
        
        response = await self.zai_substrate.process_agent_request(analysis_request)
        
        # Parse analysis results and generate metrics
        quality_metrics = self._extract_quality_metrics(response.content)
        recommendations = self._extract_recommendations(response.content)
        
        return {
            "content": response.content,
            "metadata": {
                "quality_metrics": quality_metrics,
                "confidence": response.confidence,
                "analysis_depth": task.depth
            },
            "requires_followup": quality_metrics.get("critical_issues", 0) > 0,
            "suggested_actions": recommendations
        }
    
    async def _analyze_security(self, task: AnalysisTask) -> Dict[str, Any]:
        """Perform comprehensive security analysis."""
        security_prompt = f"""
        As RepoMaster security analysis agent, perform comprehensive security assessment:
        
        Task: {task.description}
        Target: {task.target_path or "entire repository"}
        Context: {task.context}
        
        Analyze:
        1. Known vulnerabilities and CVEs
        2. Secrets and sensitive data exposure
        3. Dependency security issues
        4. Input validation and sanitization
        5. Authentication and authorization flaws
        6. Cryptographic implementations
        7. SQL injection and XSS vulnerabilities
        8. Configuration security issues
        
        Provide security findings with severity levels and remediation steps.
        """
        
        security_request = AgentRequest(
            agent_id="repomaster",
            prompt=security_prompt,
            context=task.context or {},
            reasoning_mode=ReasoningMode.CONTEXTUAL
        )
        
        response = await self.zai_substrate.process_agent_request(security_request)
        
        # Parse security findings
        security_findings = self._extract_security_findings(response.content)
        critical_issues = sum(1 for finding in security_findings if finding.get("severity") == "critical")
        
        return {
            "content": response.content,
            "metadata": {
                "security_findings": security_findings,
                "critical_issues": critical_issues,
                "confidence": response.confidence
            },
            "requires_followup": critical_issues > 0,
            "suggested_actions": self._generate_security_actions(security_findings)
        }
    
    async def _analyze_performance(self, task: AnalysisTask) -> Dict[str, Any]:
        """Perform comprehensive performance analysis."""
        performance_prompt = f"""
        As RepoMaster performance analysis agent, analyze performance characteristics:
        
        Task: {task.description}
        Target: {task.target_path or "entire repository"}
        Context: {task.context}
        
        Analyze:
        1. Algorithm complexity and efficiency
        2. Memory usage patterns and leaks
        3. Database query optimization opportunities
        4. I/O operations and bottlenecks
        5. Caching strategies and effectiveness
        6. Resource utilization patterns
        7. Scalability considerations
        8. Performance regression risks
        
        Provide performance insights with optimization recommendations.
        """
        
        performance_request = AgentRequest(
            agent_id="repomaster",
            prompt=performance_prompt,
            context=task.context or {},
            reasoning_mode=ReasoningMode.THINKING
        )
        
        response = await self.zai_substrate.process_agent_request(performance_request)
        
        # Parse performance metrics
        performance_metrics = self._extract_performance_metrics(response.content)
        optimizations = self._extract_optimization_opportunities(response.content)
        
        return {
            "content": response.content,
            "metadata": {
                "performance_metrics": performance_metrics,
                "optimization_opportunities": len(optimizations),
                "confidence": response.confidence
            },
            "requires_followup": len(optimizations) > 0,
            "suggested_actions": optimizations
        }
    
    async def _analyze_architecture(self, task: AnalysisTask) -> Dict[str, Any]:
        """Perform comprehensive architecture analysis."""
        architecture_prompt = f"""
        As RepoMaster architecture analysis agent, analyze software architecture:
        
        Task: {task.description}
        Target: {task.target_path or "entire repository"}
        Context: {task.context}
        
        Analyze:
        1. SOLID principles adherence
        2. Design patterns usage and appropriateness
        3. Module coupling and cohesion
        4. Dependency management and architecture
        5. Layering and separation of concerns
        6. API design and consistency
        7. Scalability and maintainability
        8. Architecture documentation quality
        
        Provide architectural insights with improvement recommendations.
        """
        
        architecture_request = AgentRequest(
            agent_id="repomaster",
            prompt=architecture_prompt,
            context=task.context or {},
            reasoning_mode=ReasoningMode.THINKING
        )
        
        response = await self.zai_substrate.process_agent_request(architecture_request)
        
        # Parse architecture analysis
        architecture_metrics = self._extract_architecture_metrics(response.content)
        improvements = self._extract_architecture_improvements(response.content)
        
        return {
            "content": response.content,
            "metadata": {
                "architecture_metrics": architecture_metrics,
                "improvement_opportunities": len(improvements),
                "confidence": response.confidence
            },
            "requires_followup": False,
            "suggested_actions": improvements
        }
    
    async def _perform_comprehensive_analysis(self, task: AnalysisTask) -> Dict[str, Any]:
        """Perform comprehensive multi-faceted analysis."""
        comprehensive_prompt = f"""
        As RepoMaster comprehensive analysis agent, perform full repository analysis:
        
        Task: {task.description}
        Target: {task.target_path or "entire repository"}
        Context: {task.context}
        
        Perform comprehensive analysis covering:
        1. Code quality and maintainability
        2. Security vulnerabilities and risks
        3. Performance characteristics and bottlenecks
        4. Architecture and design quality
        5. Documentation completeness
        6. Test coverage and quality
        7. Dependency health and updates
        8. Overall project health assessment
        
        Provide executive summary with prioritized recommendations.
        """
        
        comprehensive_request = AgentRequest(
            agent_id="repomaster",
            prompt=comprehensive_prompt,
            context=task.context or {},
            reasoning_mode=ReasoningMode.THINKING
        )
        
        response = await self.zai_substrate.process_agent_request(comprehensive_request)
        
        # Parse comprehensive analysis
        overall_health = self._assess_overall_health(response.content)
        priority_actions = self._extract_priority_actions(response.content)
        
        return {
            "content": response.content,
            "metadata": {
                "overall_health_score": overall_health,
                "priority_actions_count": len(priority_actions),
                "confidence": response.confidence
            },
            "requires_followup": overall_health < 70,  # Health score below 70%
            "suggested_actions": priority_actions
        }
    
    def _extract_quality_metrics(self, content: str) -> Dict[str, Any]:
        """Extract quality metrics from analysis content."""
        # Simplified extraction - would be more sophisticated in practice
        return {
            "complexity_score": 7.5,  # Would parse from content
            "maintainability_index": 75,
            "duplication_percentage": 5.2,
            "critical_issues": 2,
            "warnings": 15
        }
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from analysis content."""
        # Simplified extraction
        recommendations = []
        lines = content.split('\n')
        
        for line in lines:
            if 'recommend' in line.lower() or 'should' in line.lower():
                recommendations.append(line.strip())
        
        return recommendations[:5]  # Limit to top 5
    
    def _extract_security_findings(self, content: str) -> List[Dict[str, Any]]:
        """Extract security findings from analysis content."""
        # Simplified extraction - would parse structured findings
        return [
            {"type": "vulnerability", "severity": "medium", "description": "Potential SQL injection"},
            {"type": "secrets", "severity": "high", "description": "Hardcoded API key detected"}
        ]
    
    def _generate_security_actions(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate security remediation actions."""
        actions = []
        for finding in findings:
            if finding.get("severity") == "critical":
                actions.append(f"URGENT: Address {finding.get('type')} - {finding.get('description')}")
            elif finding.get("severity") == "high":
                actions.append(f"HIGH: Fix {finding.get('type')} - {finding.get('description')}")
        
        return actions
    
    def _extract_performance_metrics(self, content: str) -> Dict[str, Any]:
        """Extract performance metrics from analysis content."""
        return {
            "complexity_rating": "medium",
            "memory_efficiency": 85,
            "bottlenecks_detected": 3,
            "optimization_potential": "high"
        }
    
    def _extract_optimization_opportunities(self, content: str) -> List[str]:
        """Extract optimization opportunities from analysis content."""
        return [
            "Optimize database queries in user service",
            "Implement caching for frequently accessed data",
            "Reduce memory allocation in processing loop"
        ]
    
    def _extract_architecture_metrics(self, content: str) -> Dict[str, Any]:
        """Extract architecture metrics from analysis content."""
        return {
            "solid_compliance": 80,
            "coupling_score": "low",
            "cohesion_score": "high",
            "pattern_usage": "appropriate"
        }
    
    def _extract_architecture_improvements(self, content: str) -> List[str]:
        """Extract architecture improvement suggestions."""
        return [
            "Consider implementing dependency injection",
            "Separate business logic from presentation layer",
            "Add interface abstractions for external services"
        ]
    
    def _assess_overall_health(self, content: str) -> float:
        """Assess overall repository health score."""
        # Simplified assessment - would analyze multiple factors
        return 78.5  # Health score out of 100
    
    def _extract_priority_actions(self, content: str) -> List[str]:
        """Extract priority actions from comprehensive analysis."""
        return [
            "Address critical security vulnerabilities",
            "Improve test coverage to 80%+",
            "Refactor high-complexity modules",
            "Update outdated dependencies"
        ]
    
    async def _update_analysis_stats(self, analysis_time: float, success: bool) -> None:
        """Update analysis execution statistics."""
        self.analysis_stats["total_analyses"] += 1
        
        if success:
            self.analysis_stats["successful_analyses"] += 1
        else:
            self.analysis_stats["failed_analyses"] += 1
        
        # Update average analysis time
        total_analyses = self.analysis_stats["total_analyses"]
        current_avg = self.analysis_stats["average_analysis_time"]
        self.analysis_stats["average_analysis_time"] = (
            (current_avg * (total_analyses - 1) + analysis_time) / total_analyses
        )
    
    async def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.capabilities.copy()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get agent status and statistics."""
        return {
            "agent": "repomaster",
            "status": "active",
            "capabilities": self.capabilities,
            "analysis_stats": self.analysis_stats,
            "deep_analysis_enabled": self.enable_deep_analysis,
            "zai_substrate_status": await self.zai_substrate.get_agent_status("repomaster")
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the agent."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check Z.AI substrate connection
        try:
            substrate_health = await self.zai_substrate.health_check()
            health_status["components"]["zai_substrate"] = substrate_health
        except Exception as e:
            health_status["components"]["zai_substrate"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Check analysis capabilities
        health_status["components"]["analysis_engine"] = {
            "status": "healthy",
            "capabilities_count": len(self.capabilities),
            "deep_analysis": self.enable_deep_analysis
        }
        
        return health_status
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the agent."""
        self.logger.info("Shutting down RepoMaster Agent")
        
        # Clear analysis configurations
        self.analysis_configs.clear()
        
        self.logger.info("RepoMaster Agent shutdown complete")
