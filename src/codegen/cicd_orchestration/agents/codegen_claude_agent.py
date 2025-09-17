"""
Codegen Claude Agent

High-value development agent that integrates Codegen core operations with
Claude AI capabilities through Z.AI substrate. This agent provides maximum
development value by combining:

- Codegen core library operations (project retrieval, PR creation, analysis)
- Claude AI integration for intelligent development assistance
- Z.AI substrate for enhanced reasoning and context awareness
- Direct integration with existing Codegen workflows

Capabilities:
- Development task execution with Claude intelligence
- PR creation and management through Codegen core
- Project analysis and insights
- Code generation and modification
- Integration with existing Codegen Claude workflows
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from ...agent_operations import AgentOperationsManager
from ..zai_substrate import ZAISubstrate, AgentRequest, ReasoningMode

logger = logging.getLogger(__name__)


@dataclass
class CodegenTask:
    """Task structure for Codegen Claude agent processing."""
    task_id: str
    description: str
    task_type: str  # development, pr_creation, analysis, code_generation
    context: Dict[str, Any]
    priority: str = "normal"
    codegen_operations: List[str] = None  # Specific Codegen operations to perform


class CodegenClaudeAgent:
    """
    High-value development agent combining Codegen operations with Claude AI.
    
    This agent serves as the primary development assistant, leveraging both
    the operational capabilities of Codegen and the intelligence of Claude
    through the Z.AI substrate for optimal development workflows.
    """
    
    def __init__(
        self,
        codegen_manager: Optional[AgentOperationsManager] = None,
        zai_substrate: Optional[ZAISubstrate] = None
    ):
        """
        Initialize Codegen Claude agent.
        
        Args:
            codegen_manager: Codegen operations manager for core functionality
            zai_substrate: Z.AI substrate for intelligence processing
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Core components
        self.codegen_manager = codegen_manager or AgentOperationsManager()
        self.zai_substrate = zai_substrate or ZAISubstrate()
        
        # Agent capabilities
        self.capabilities = [
            "development",
            "code_generation", 
            "pr_creation",
            "project_analysis",
            "code_review",
            "debugging",
            "refactoring",
            "testing"
        ]
        
        # Performance tracking
        self.task_stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0
        }
        
        self.logger.info("Codegen Claude Agent initialized")
    
    async def initialize(self) -> None:
        """Initialize the Codegen Claude agent."""
        try:
            # Initialize Codegen operations manager
            await self.codegen_manager.initialize()
            
            # Register with Z.AI substrate
            await self.zai_substrate._register_agent("codegen_claude")
            
            self.logger.info("Codegen Claude Agent initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Codegen Claude agent: {e}")
            raise
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a development task using Codegen operations and Claude intelligence.
        
        This method coordinates between Codegen core operations and Claude AI
        to provide intelligent development assistance with operational capabilities.
        """
        start_time = datetime.now()
        
        try:
            # Parse task information
            codegen_task = self._parse_task(task)
            
            # Analyze task with Claude intelligence through Z.AI
            task_analysis = await self._analyze_task_with_claude(codegen_task)
            
            # Execute based on task type
            if codegen_task.task_type == "development":
                result = await self._execute_development_task(codegen_task, task_analysis)
            elif codegen_task.task_type == "pr_creation":
                result = await self._execute_pr_creation_task(codegen_task, task_analysis)
            elif codegen_task.task_type == "analysis":
                result = await self._execute_analysis_task(codegen_task, task_analysis)
            elif codegen_task.task_type == "code_generation":
                result = await self._execute_code_generation_task(codegen_task, task_analysis)
            else:
                result = await self._execute_general_task(codegen_task, task_analysis)
            
            # Update statistics
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._update_task_stats(execution_time, success=True)
            
            return {
                "content": result.get("content", ""),
                "metadata": {
                    **result.get("metadata", {}),
                    "agent": "codegen_claude",
                    "task_type": codegen_task.task_type,
                    "execution_time": execution_time,
                    "codegen_operations": result.get("codegen_operations", [])
                },
                "requires_followup": result.get("requires_followup", False),
                "suggested_actions": result.get("suggested_actions", [])
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._update_task_stats(execution_time, success=False)
            
            self.logger.error(f"Error executing task: {e}")
            
            return {
                "content": f"Error executing development task: {str(e)}",
                "metadata": {
                    "agent": "codegen_claude",
                    "error": str(e),
                    "execution_time": execution_time
                },
                "requires_followup": True,
                "suggested_actions": ["Please review the task requirements and try again"]
            }
    
    def _parse_task(self, task: Dict[str, Any]) -> CodegenTask:
        """Parse task dictionary into CodegenTask structure."""
        return CodegenTask(
            task_id=task.get("task_id", f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            description=task.get("description", ""),
            task_type=self._determine_task_type(task.get("description", "")),
            context=task.get("context", {}),
            priority=task.get("priority", "normal"),
            codegen_operations=task.get("codegen_operations", [])
        )
    
    def _determine_task_type(self, description: str) -> str:
        """Determine task type based on description."""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["pr", "pull request", "merge"]):
            return "pr_creation"
        elif any(keyword in description_lower for keyword in ["analyze", "review", "inspect"]):
            return "analysis"
        elif any(keyword in description_lower for keyword in ["generate", "create", "write"]):
            return "code_generation"
        else:
            return "development"
    
    async def _analyze_task_with_claude(
        self, 
        task: CodegenTask
    ) -> Dict[str, Any]:
        """Analyze task using Claude intelligence through Z.AI substrate."""
        analysis_prompt = f"""
        As a Codegen Claude development agent, analyze this development task:
        
        Task: {task.description}
        Type: {task.task_type}
        Context: {task.context}
        Priority: {task.priority}
        
        Provide analysis including:
        1. Required Codegen operations
        2. Development approach and strategy
        3. Potential challenges and solutions
        4. Estimated complexity and effort
        5. Success criteria and validation steps
        6. Integration points with existing codebase
        
        Focus on practical development execution using Codegen capabilities.
        """
        
        analysis_request = AgentRequest(
            agent_id="codegen_claude",
            prompt=analysis_prompt,
            context=task.context,
            reasoning_mode=ReasoningMode.THINKING
        )
        
        response = await self.zai_substrate.process_agent_request(analysis_request)
        
        return {
            "analysis": response.content,
            "reasoning_trace": response.reasoning_trace,
            "confidence": response.confidence,
            "recommended_operations": self._extract_codegen_operations(response.content),
            "complexity": self._assess_complexity(response.content),
            "estimated_time": self._estimate_execution_time(response.content)
        }
    
    def _extract_codegen_operations(self, analysis_content: str) -> List[str]:
        """Extract recommended Codegen operations from analysis."""
        operations = []
        content_lower = analysis_content.lower()
        
        if "create pr" in content_lower or "pull request" in content_lower:
            operations.append("create_pr")
        
        if "analyze project" in content_lower or "project analysis" in content_lower:
            operations.append("analyze_project")
        
        if "claude" in content_lower and "chat" in content_lower:
            operations.append("claude_chat")
        
        if "retrieve" in content_lower and "project" in content_lower:
            operations.append("retrieve_project")
        
        return operations
    
    def _assess_complexity(self, analysis_content: str) -> str:
        """Assess task complexity from analysis."""
        content_lower = analysis_content.lower()
        
        if any(keyword in content_lower for keyword in ["complex", "challenging", "difficult"]):
            return "high"
        elif any(keyword in content_lower for keyword in ["moderate", "medium", "some"]):
            return "medium"
        else:
            return "low"
    
    def _estimate_execution_time(self, analysis_content: str) -> float:
        """Estimate execution time from analysis."""
        content_lower = analysis_content.lower()
        
        if "quick" in content_lower or "simple" in content_lower:
            return 2.0
        elif "complex" in content_lower or "challenging" in content_lower:
            return 10.0
        else:
            return 5.0
    
    async def _execute_development_task(
        self, 
        task: CodegenTask, 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute general development task."""
        # Use Codegen operations manager for development tasks
        response = await self.codegen_manager.chat(
            message=f"""
            Execute this development task:
            
            Task: {task.description}
            Analysis: {analysis.get('analysis', '')}
            Recommended Operations: {analysis.get('recommended_operations', [])}
            
            Use appropriate Codegen operations to complete this task.
            """,
            session_id=f"codegen_claude_{task.task_id}",
            context=task.context
        )
        
        return {
            "content": response.content,
            "metadata": {
                "codegen_operations": ["chat"],
                "engine_used": response.engine_used.value,
                "confidence": response.confidence
            },
            "requires_followup": response.requires_followup,
            "suggested_actions": response.suggested_actions
        }
    
    async def _execute_pr_creation_task(
        self, 
        task: CodegenTask, 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute PR creation task using Codegen operations."""
        # Use Codegen operations for PR creation
        response = await self.codegen_manager.create_agent(
            prompt=f"""
            Create a PR for this development task:
            
            Task: {task.description}
            Context: {task.context}
            Analysis: {analysis.get('analysis', '')}
            
            Follow best practices for PR creation and include appropriate
            documentation and testing.
            """,
            context=task.context
        )
        
        return {
            "content": f"PR creation initiated: {response.get('response', '')}",
            "metadata": {
                "codegen_operations": ["create_agent"],
                "agent_id": response.get('metadata', {}).get('agent_id'),
                "web_url": response.get('metadata', {}).get('web_url')
            },
            "requires_followup": True,
            "suggested_actions": [
                "Monitor PR creation progress",
                "Review generated PR when complete"
            ]
        }
    
    async def _execute_analysis_task(
        self, 
        task: CodegenTask, 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute code analysis task."""
        # Use Codegen operations for code analysis
        response = await self.codegen_manager.analyze_code(
            code_query=task.description,
            context=task.context
        )
        
        return {
            "content": response.get('analysis', ''),
            "metadata": {
                "codegen_operations": ["analyze_code"],
                "analysis_type": "code_analysis"
            },
            "requires_followup": False,
            "suggested_actions": response.get('suggested_actions', [])
        }
    
    async def _execute_code_generation_task(
        self, 
        task: CodegenTask, 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute code generation task."""
        # Use Claude intelligence through Z.AI for code generation
        generation_request = AgentRequest(
            agent_id="codegen_claude",
            prompt=f"""
            Generate code for this task:
            
            Task: {task.description}
            Context: {task.context}
            Analysis: {analysis.get('analysis', '')}
            
            Provide complete, working code with appropriate comments,
            error handling, and following best practices.
            """,
            context=task.context,
            reasoning_mode=ReasoningMode.CONTEXTUAL
        )
        
        response = await self.zai_substrate.process_agent_request(generation_request)
        
        return {
            "content": response.content,
            "metadata": {
                "codegen_operations": ["code_generation"],
                "confidence": response.confidence,
                "model_used": response.model_used
            },
            "requires_followup": False,
            "suggested_actions": [
                "Review generated code",
                "Test implementation",
                "Integrate with existing codebase"
            ]
        }
    
    async def _execute_general_task(
        self, 
        task: CodegenTask, 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute general task using appropriate Codegen operations."""
        # Determine best approach based on analysis
        recommended_ops = analysis.get('recommended_operations', [])
        
        if 'create_pr' in recommended_ops:
            return await self._execute_pr_creation_task(task, analysis)
        elif 'analyze_project' in recommended_ops:
            return await self._execute_analysis_task(task, analysis)
        else:
            return await self._execute_development_task(task, analysis)
    
    async def _update_task_stats(self, execution_time: float, success: bool) -> None:
        """Update task execution statistics."""
        self.task_stats["total_tasks"] += 1
        
        if success:
            self.task_stats["successful_tasks"] += 1
        else:
            self.task_stats["failed_tasks"] += 1
        
        # Update average execution time
        total_tasks = self.task_stats["total_tasks"]
        current_avg = self.task_stats["average_execution_time"]
        self.task_stats["average_execution_time"] = (
            (current_avg * (total_tasks - 1) + execution_time) / total_tasks
        )
    
    async def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.capabilities.copy()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get agent status and statistics."""
        return {
            "agent": "codegen_claude",
            "status": "active",
            "capabilities": self.capabilities,
            "task_stats": self.task_stats,
            "codegen_manager_status": "active",  # Would check actual status
            "zai_substrate_status": await self.zai_substrate.get_agent_status("codegen_claude")
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the agent."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check Codegen operations manager
        try:
            # Would perform actual health check
            health_status["components"]["codegen_manager"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["codegen_manager"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Check Z.AI substrate connection
        try:
            substrate_health = await self.zai_substrate.health_check()
            health_status["components"]["zai_substrate"] = substrate_health
        except Exception as e:
            health_status["components"]["zai_substrate"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        return health_status
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the agent."""
        self.logger.info("Shutting down Codegen Claude Agent")
        
        try:
            # Shutdown Codegen operations manager
            await self.codegen_manager.shutdown()
            
            self.logger.info("Codegen Claude Agent shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during agent shutdown: {e}")
            raise
