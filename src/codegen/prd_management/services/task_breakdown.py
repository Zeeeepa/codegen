"""
Task Breakdown Service - Converts PRDs into executable tasks using AI
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ...sdk.client import CodegenClient
from ..core.prd_template import PRDTemplate, Task, TaskType, TaskStatus
from ..core.pro_mode_engine import ProModeEngine, ProModeRequest


@dataclass
class TaskBreakdownConfig:
    max_tasks_per_prd: int = 50
    task_complexity_threshold: int = 10
    dependency_analysis_enabled: bool = True


class TaskBreakdownService:
    """
    Service for breaking down PRDs into executable tasks using AI analysis
    """
    
    def __init__(self, codegen_client: CodegenClient, pro_mode_engine: ProModeEngine):
        self.codegen_client = codegen_client
        self.pro_mode_engine = pro_mode_engine
        self.config = TaskBreakdownConfig()
    
    async def breakdown_prd_into_tasks(
        self,
        prd: PRDTemplate,
        org_id: int,
        repo_id: int
    ) -> List[Task]:
        """
        Break down a PRD into executable tasks
        
        Args:
            prd: The PRD to break down
            org_id: Organization ID
            repo_id: Repository ID
            
        Returns:
            List of executable tasks
        """
        
        # Generate task breakdown using Pro Mode for better results
        task_breakdown_prompt = self._build_task_breakdown_prompt(prd)
        
        pro_mode_request = ProModeRequest(
            prompt=task_breakdown_prompt,
            num_gens=5,  # Use fewer generations for task breakdown
            temperature=0.7,  # Lower temperature for more structured output
            org_id=org_id,
            repo_id=repo_id
        )
        
        pro_mode_result = await self.pro_mode_engine.execute_pro_mode(pro_mode_request)
        
        # Parse tasks from the result
        tasks = self._parse_tasks_from_response(pro_mode_result.final, prd.id)
        
        # Analyze dependencies
        if self.config.dependency_analysis_enabled:
            tasks = await self._analyze_task_dependencies(tasks, org_id, repo_id)
        
        # Validate task structure
        self._validate_tasks(tasks)
        
        return tasks
    
    def _build_task_breakdown_prompt(self, prd: PRDTemplate) -> str:
        """Build comprehensive task breakdown prompt"""
        
        return f"""
# Task Breakdown for PRD Implementation

## PRD Details
**Title**: {prd.title}
**Goal**: {prd.goal}
**What**: {prd.what}

**Success Criteria**:
{chr(10).join(f"- {criteria}" for criteria in prd.success_criteria)}

**Context**:
- Codebase Tree: {prd.context.codebase_tree}
- Desired Tree: {prd.context.desired_tree}
- Gotchas: {', '.join(prd.context.gotchas)}

**Data Models**: {prd.implementation.data_models}
**Pseudocode**: {prd.implementation.pseudocode}

## Task Breakdown Requirements

Break down this PRD into specific, executable tasks that can be implemented by AI agents.

### Task Structure
Each task should have:
1. **ID**: Unique identifier (task-1, task-2, etc.)
2. **Title**: Clear, actionable title
3. **Description**: Detailed description of what needs to be done
4. **Type**: CREATE, MODIFY, DELETE, or TEST
5. **Files**: List of files that will be created/modified
6. **Dependencies**: List of task IDs that must complete first
7. **Validation Criteria**: How to verify the task is complete
8. **Estimated Duration**: Rough time estimate

### Task Types
- **CREATE**: Create new files, components, or features
- **MODIFY**: Modify existing files or functionality
- **DELETE**: Remove files or functionality
- **TEST**: Create or update tests

### Guidelines
1. Keep tasks focused and atomic (one clear responsibility)
2. Ensure tasks can be executed independently when dependencies are met
3. Include both implementation and testing tasks
4. Consider file structure and organization
5. Include validation steps for each task
6. Order tasks logically with proper dependencies

## Output Format
Provide the task breakdown in JSON format:

```json
{{
  "tasks": [
    {{
      "id": "task-1",
      "title": "Create user authentication data models",
      "description": "Create TypeScript interfaces and types for user authentication including User, AuthToken, and LoginRequest types",
      "type": "CREATE",
      "files": ["src/types/auth.ts", "src/types/user.ts"],
      "dependencies": [],
      "validation_criteria": [
        "Types compile without errors",
        "All required fields are defined",
        "Types are exported properly"
      ],
      "estimated_duration": "30 minutes"
    }},
    {{
      "id": "task-2", 
      "title": "Implement authentication service",
      "description": "Create authentication service with login, logout, and token validation methods",
      "type": "CREATE",
      "files": ["src/services/authService.ts"],
      "dependencies": ["task-1"],
      "validation_criteria": [
        "Service methods are implemented",
        "Error handling is included",
        "Service is properly exported"
      ],
      "estimated_duration": "1 hour"
    }}
  ]
}}
```

Generate a comprehensive task breakdown that covers all aspects of the PRD implementation.
"""
    
    def _parse_tasks_from_response(self, response: str, prd_id: str) -> List[Task]:
        """Parse tasks from AI response"""
        
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in task breakdown response")
            
            json_str = response[json_start:json_end]
            parsed_data = json.loads(json_str)
            
            tasks = []
            for task_data in parsed_data.get('tasks', []):
                task = Task(
                    id=task_data['id'],
                    title=task_data['title'],
                    description=task_data['description'],
                    type=TaskType(task_data['type'].upper()),
                    files=task_data.get('files', []),
                    dependencies=task_data.get('dependencies', []),
                    status=TaskStatus.PENDING,
                    validation_criteria=task_data.get('validation_criteria', []),
                    estimated_duration=task_data.get('estimated_duration')
                )
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            raise Exception(f"Failed to parse tasks from response: {str(e)}")
    
    async def _analyze_task_dependencies(
        self,
        tasks: List[Task],
        org_id: int,
        repo_id: int
    ) -> List[Task]:
        """Analyze and optimize task dependencies"""
        
        dependency_analysis_prompt = f"""
# Task Dependency Analysis

## Current Tasks
{self._format_tasks_for_analysis(tasks)}

## Analysis Requirements
1. Verify all dependencies are valid (referenced tasks exist)
2. Check for circular dependencies
3. Optimize dependency order for parallel execution
4. Identify tasks that can run in parallel
5. Suggest dependency improvements

## Output Format
Provide the optimized task list with corrected dependencies in JSON format:

```json
{{
  "tasks": [
    {{
      "id": "task-1",
      "dependencies": [],
      "parallel_group": 1,
      "critical_path": true
    }},
    {{
      "id": "task-2", 
      "dependencies": ["task-1"],
      "parallel_group": 2,
      "critical_path": false
    }}
  ],
  "analysis": {{
    "parallel_groups": 3,
    "critical_path_length": 5,
    "optimization_notes": ["Tasks 2 and 3 can run in parallel", "Task 4 dependency on task 1 removed"]
  }}
}}
```
"""
        
        agent_run = await self.codegen_client.create_agent_run(
            org_id=org_id,
            prompt=dependency_analysis_prompt,
            repo_id=repo_id
        )
        
        result = await self._poll_completion(org_id, agent_run.id)
        
        # Parse dependency analysis and update tasks
        try:
            analysis_data = json.loads(result.get('output', '{}'))
            optimized_tasks = analysis_data.get('tasks', [])
            
            # Update task dependencies based on analysis
            task_map = {task.id: task for task in tasks}
            
            for optimized_task in optimized_tasks:
                task_id = optimized_task['id']
                if task_id in task_map:
                    task_map[task_id].dependencies = optimized_task.get('dependencies', [])
            
            return list(task_map.values())
            
        except Exception as e:
            print(f"Dependency analysis failed, using original tasks: {e}")
            return tasks
    
    def _format_tasks_for_analysis(self, tasks: List[Task]) -> str:
        """Format tasks for dependency analysis"""
        
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append(f"""
Task ID: {task.id}
Title: {task.title}
Type: {task.type.value}
Files: {', '.join(task.files)}
Dependencies: {', '.join(task.dependencies)}
""")
        
        return '\n'.join(formatted_tasks)
    
    def _validate_tasks(self, tasks: List[Task]) -> None:
        """Validate task structure and dependencies"""
        
        if not tasks:
            raise ValueError("No tasks generated from PRD")
        
        if len(tasks) > self.config.max_tasks_per_prd:
            raise ValueError(f"Too many tasks generated: {len(tasks)} > {self.config.max_tasks_per_prd}")
        
        # Check for duplicate task IDs
        task_ids = [task.id for task in tasks]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("Duplicate task IDs found")
        
        # Validate dependencies reference existing tasks
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    raise ValueError(f"Task {task.id} references non-existent dependency: {dep_id}")
        
        # Check for circular dependencies
        self._check_circular_dependencies(tasks)
    
    def _check_circular_dependencies(self, tasks: List[Task]) -> None:
        """Check for circular dependencies in task list"""
        
        task_map = {task.id: task for task in tasks}
        visited = set()
        rec_stack = set()
        
        def has_cycle(task_id: str) -> bool:
            if task_id in rec_stack:
                return True
            if task_id in visited:
                return False
            
            visited.add(task_id)
            rec_stack.add(task_id)
            
            task = task_map.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    if has_cycle(dep_id):
                        return True
            
            rec_stack.remove(task_id)
            return False
        
        for task in tasks:
            if task.id not in visited:
                if has_cycle(task.id):
                    raise ValueError(f"Circular dependency detected involving task: {task.id}")
    
    async def _poll_completion(self, org_id: int, agent_run_id: str) -> Dict[str, Any]:
        """Poll for agent run completion"""
        timeout = 300  # 5 minutes
        poll_interval = 10  # 10 seconds
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                agent_run = await self.codegen_client.get_agent_run(org_id, agent_run_id)
                
                if agent_run.status == "COMPLETE":
                    return agent_run.result or {}
                elif agent_run.status == "FAILED":
                    raise Exception(f"Task breakdown failed: {agent_run.error}")
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(poll_interval)
        
        raise Exception("Task breakdown timed out")
    
    # Utility methods for task management
    def get_ready_tasks(self, tasks: List[Task]) -> List[Task]:
        """Get tasks that are ready to execute (dependencies completed)"""
        
        completed_task_ids = {
            task.id for task in tasks 
            if task.status == TaskStatus.COMPLETED
        }
        
        ready_tasks = []
        for task in tasks:
            if task.status == TaskStatus.PENDING:
                dependencies_met = all(
                    dep_id in completed_task_ids 
                    for dep_id in task.dependencies
                )
                if dependencies_met:
                    ready_tasks.append(task)
        
        return ready_tasks
    
    def get_task_execution_order(self, tasks: List[Task]) -> List[List[Task]]:
        """Get tasks organized by execution order (parallel groups)"""
        
        task_map = {task.id: task for task in tasks}
        execution_order = []
        remaining_tasks = set(task.id for task in tasks)
        completed_tasks = set()
        
        while remaining_tasks:
            # Find tasks with no pending dependencies
            ready_task_ids = []
            for task_id in remaining_tasks:
                task = task_map[task_id]
                dependencies_met = all(
                    dep_id in completed_tasks 
                    for dep_id in task.dependencies
                )
                if dependencies_met:
                    ready_task_ids.append(task_id)
            
            if not ready_task_ids:
                # This shouldn't happen if dependencies are valid
                raise Exception("No ready tasks found - possible circular dependency")
            
            # Add ready tasks to execution order
            ready_tasks = [task_map[task_id] for task_id in ready_task_ids]
            execution_order.append(ready_tasks)
            
            # Mark tasks as completed for next iteration
            completed_tasks.update(ready_task_ids)
            remaining_tasks -= set(ready_task_ids)
        
        return execution_order

