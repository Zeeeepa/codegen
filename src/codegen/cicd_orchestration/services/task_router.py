"""
Task Router

Intelligent task routing and execution planning for the CI/CD orchestration system.
Routes tasks to appropriate agents based on capabilities, load, and task requirements.

Following KISS principles with straightforward routing logic and clear decision making.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TaskRequirement:
    """Requirements for task execution."""
    capabilities: List[str]
    priority: str = "normal"
    estimated_duration: float = 5.0
    resource_requirements: Dict[str, Any] = None


@dataclass
class ExecutionPlan:
    """Execution plan for a task or set of tasks."""
    plan_id: str
    tasks: List[Dict[str, Any]]
    agent_assignments: Dict[str, str]
    execution_order: List[str]
    estimated_total_duration: float
    resource_requirements: Dict[str, Any]


class TaskRouter:
    """
    Simple task router for intelligent agent assignment and execution planning.
    
    Routes tasks to the most appropriate agents based on capabilities,
    current load, and task requirements using straightforward logic.
    """
    
    def __init__(self):
        """Initialize the task router."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Routing statistics
        self.routing_stats = {
            "total_tasks_routed": 0,
            "successful_routings": 0,
            "failed_routings": 0,
            "average_routing_time": 0.0
        }
        
        # Agent capability mappings
        self.capability_mappings = {
            "development": ["codegen_claude"],
            "code_generation": ["codegen_claude"],
            "pr_creation": ["codegen_claude"],
            "project_analysis": ["codegen_claude"],
            "code_analysis": ["repomaster"],
            "repository_insights": ["repomaster"],
            "validation": ["repomaster"],
            "quality_assessment": ["repomaster"],
            "security_scanning": ["repomaster"],
            "performance_analysis": ["repomaster"]
        }
        
        self.logger.info("Task Router initialized")
    
    async def create_execution_plan(
        self,
        request: Any,  # OrchestrationRequest
        task_analysis: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Create an execution plan for a request based on task analysis.
        
        Args:
            request: Orchestration request
            task_analysis: Analysis of the request and task requirements
            
        Returns:
            Execution plan with task assignments and ordering
        """
        start_time = datetime.now()
        
        try:
            # Extract task requirements from analysis
            requirements = self._extract_task_requirements(request, task_analysis)
            
            # Break down into individual tasks if needed
            tasks = self._decompose_request_into_tasks(request, requirements)
            
            # Route each task to appropriate agent
            agent_assignments = {}
            for task in tasks:
                agent = await self._route_task_to_agent(task, requirements)
                agent_assignments[task["task_id"]] = agent
            
            # Determine execution order
            execution_order = self._determine_execution_order(tasks, agent_assignments)
            
            # Calculate resource requirements and duration
            total_duration = sum(task.get("estimated_duration", 5.0) for task in tasks)
            resource_requirements = self._calculate_resource_requirements(tasks)
            
            # Update routing statistics
            routing_time = (datetime.now() - start_time).total_seconds()
            await self._update_routing_stats(routing_time, success=True)
            
            plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return ExecutionPlan(
                plan_id=plan_id,
                tasks=tasks,
                agent_assignments=agent_assignments,
                execution_order=execution_order,
                estimated_total_duration=total_duration,
                resource_requirements=resource_requirements
            )
            
        except Exception as e:
            routing_time = (datetime.now() - start_time).total_seconds()
            await self._update_routing_stats(routing_time, success=False)
            
            self.logger.error(f"Error creating execution plan: {e}")
            raise
    
    def _extract_task_requirements(
        self,
        request: Any,
        task_analysis: Dict[str, Any]
    ) -> TaskRequirement:
        """Extract task requirements from request and analysis."""
        # Determine required capabilities based on request content
        required_capabilities = []
        message_lower = request.message.lower()
        
        # Map message content to capabilities
        if any(keyword in message_lower for keyword in ["code", "develop", "create", "build"]):
            required_capabilities.append("development")
        
        if any(keyword in message_lower for keyword in ["analyze", "review", "quality"]):
            required_capabilities.append("code_analysis")
        
        if any(keyword in message_lower for keyword in ["pr", "pull request"]):
            required_capabilities.append("pr_creation")
        
        if any(keyword in message_lower for keyword in ["security", "vulnerability"]):
            required_capabilities.append("security_scanning")
        
        if any(keyword in message_lower for keyword in ["performance", "optimize"]):
            required_capabilities.append("performance_analysis")
        
        # Default to development if no specific capabilities identified
        if not required_capabilities:
            required_capabilities.append("development")
        
        return TaskRequirement(
            capabilities=required_capabilities,
            priority=request.task_priority,
            estimated_duration=task_analysis.get("estimated_time", 5.0),
            resource_requirements=task_analysis.get("resource_requirements", {})
        )
    
    def _decompose_request_into_tasks(
        self,
        request: Any,
        requirements: TaskRequirement
    ) -> List[Dict[str, Any]]:
        """Decompose request into individual executable tasks."""
        # For now, create a single task from the request
        # In a more complex implementation, this would intelligently break down
        # complex requests into multiple coordinated tasks
        
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = {
            "task_id": task_id,
            "description": request.message,
            "capabilities": requirements.capabilities,
            "priority": requirements.priority,
            "estimated_duration": requirements.estimated_duration,
            "context": request.user_context or {},
            "agent": None  # Will be assigned by routing
        }
        
        return [task]
    
    async def _route_task_to_agent(
        self,
        task: Dict[str, Any],
        requirements: TaskRequirement
    ) -> str:
        """
        Route a task to the most appropriate agent.
        
        Args:
            task: Task to route
            requirements: Task requirements
            
        Returns:
            Name of the selected agent
        """
        # Find agents that can handle the required capabilities
        candidate_agents = set()
        
        for capability in requirements.capabilities:
            agents_for_capability = self.capability_mappings.get(capability, [])
            if candidate_agents:
                # Intersection - agents that can handle all capabilities
                candidate_agents &= set(agents_for_capability)
            else:
                # First capability - start with these agents
                candidate_agents = set(agents_for_capability)
        
        # If no agents can handle all capabilities, find best partial match
        if not candidate_agents:
            candidate_agents = self._find_best_partial_match(requirements.capabilities)
        
        # Select best agent from candidates based on load and suitability
        if candidate_agents:
            return self._select_best_agent(list(candidate_agents), task, requirements)
        else:
            # Fallback to default agent
            return "codegen_claude"
    
    def _find_best_partial_match(self, capabilities: List[str]) -> set:
        """Find agents that can handle the most capabilities."""
        agent_scores = {}
        
        for capability in capabilities:
            agents_for_capability = self.capability_mappings.get(capability, [])
            for agent in agents_for_capability:
                agent_scores[agent] = agent_scores.get(agent, 0) + 1
        
        if not agent_scores:
            return set()
        
        # Return agents with highest capability match count
        max_score = max(agent_scores.values())
        return {agent for agent, score in agent_scores.items() if score == max_score}
    
    def _select_best_agent(
        self,
        candidate_agents: List[str],
        task: Dict[str, Any],
        requirements: TaskRequirement
    ) -> str:
        """Select the best agent from candidates based on various factors."""
        if len(candidate_agents) == 1:
            return candidate_agents[0]
        
        # Simple selection logic - prefer based on task type
        task_description = task.get("description", "").lower()
        
        # Prefer RepoMaster for analysis tasks
        if any(keyword in task_description for keyword in ["analyze", "review", "quality", "security"]):
            if "repomaster" in candidate_agents:
                return "repomaster"
        
        # Prefer Codegen Claude for development tasks
        if any(keyword in task_description for keyword in ["code", "develop", "create", "pr"]):
            if "codegen_claude" in candidate_agents:
                return "codegen_claude"
        
        # Default to first candidate
        return candidate_agents[0]
    
    def _determine_execution_order(
        self,
        tasks: List[Dict[str, Any]],
        agent_assignments: Dict[str, str]
    ) -> List[str]:
        """Determine optimal execution order for tasks."""
        # For now, simple sequential order based on priority
        # In a more complex implementation, this would consider dependencies
        # and optimize for parallel execution where possible
        
        # Sort by priority (urgent > high > normal > low)
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        
        sorted_tasks = sorted(
            tasks,
            key=lambda t: priority_order.get(t.get("priority", "normal"), 2)
        )
        
        return [task["task_id"] for task in sorted_tasks]
    
    def _calculate_resource_requirements(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate total resource requirements for all tasks."""
        total_agents = len(set(task.get("agent") for task in tasks if task.get("agent")))
        total_duration = sum(task.get("estimated_duration", 5.0) for task in tasks)
        
        # Determine complexity based on task count and duration
        if len(tasks) > 3 or total_duration > 15.0:
            complexity = "high"
        elif len(tasks) > 1 or total_duration > 5.0:
            complexity = "medium"
        else:
            complexity = "low"
        
        return {
            "agents_required": total_agents,
            "estimated_duration": total_duration,
            "complexity": complexity,
            "parallel_execution": len(tasks) > 1
        }
    
    async def _update_routing_stats(self, routing_time: float, success: bool) -> None:
        """Update routing statistics."""
        self.routing_stats["total_tasks_routed"] += 1
        
        if success:
            self.routing_stats["successful_routings"] += 1
        else:
            self.routing_stats["failed_routings"] += 1
        
        # Update average routing time
        total_routings = self.routing_stats["total_tasks_routed"]
        current_avg = self.routing_stats["average_routing_time"]
        self.routing_stats["average_routing_time"] = (
            (current_avg * (total_routings - 1) + routing_time) / total_routings
        )
    
    async def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return self.routing_stats.copy()
    
    async def get_capability_mappings(self) -> Dict[str, List[str]]:
        """Get current capability to agent mappings."""
        return self.capability_mappings.copy()
    
    async def update_capability_mapping(
        self,
        capability: str,
        agents: List[str]
    ) -> None:
        """
        Update the mapping of a capability to agents.
        
        Args:
            capability: Capability name
            agents: List of agent names that provide this capability
        """
        self.capability_mappings[capability] = agents
        self.logger.info(f"Updated capability mapping: {capability} -> {agents}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the task router."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "routing_stats": self.routing_stats,
            "capability_mappings_count": len(self.capability_mappings),
            "total_agents": len(set(
                agent for agents in self.capability_mappings.values() 
                for agent in agents
            ))
        }
