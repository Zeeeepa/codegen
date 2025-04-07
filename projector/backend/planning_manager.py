import os
import json
import logging
import time
import threading
from typing import Dict, List, Optional, Any

from codegen.agents.planning_agent import PlanningAgent
from codegen.agents.planning.planning import PlanStepStatus

class PlanningManager:
    """Manager for project planning and task tracking."""
    
    def __init__(self, github_manager):
        """Initialize the planning manager."""
        self.github_manager = github_manager
        self.logger = logging.getLogger(__name__)
        self.plans = {}
        self.active_plans = {}
        self.planning_agent = None
        self.plan_locks = {}  # Locks for thread-safe plan updates
    
    def _initialize_planning_agent(self):
        """Initialize the planning agent on demand."""
        if self.planning_agent is None:
            try:
                self.planning_agent = PlanningAgent(
                    model_provider="anthropic",
                    model_name="claude-3-5-sonnet-latest"
                )
                self.logger.info("Planning agent initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing planning agent: {e}")
                raise
    
    def create_plan(self, project_name: str, requirements: str, plan_text: str = None) -> Dict[str, Any]:
        """Create a new project plan.
        
        Args:
            project_name: Name of the project
            requirements: Project requirements
            plan_text: Optional pre-generated plan text
            
        Returns:
            Dictionary with plan details
        """
        try:
            # Create a unique plan ID
            plan_id = f"plan_{int(time.time())}"
            
            # Generate plan text if not provided
            if not plan_text:
                self._initialize_planning_agent()
                
                plan_prompt = f"""
                Create a detailed implementation plan for the following project:
                
                Project: {project_name}
                
                Requirements:
                {requirements}
                
                Please create a plan with the following:
                1. High-level overview of the implementation approach
                2. List of features to implement
                3. For each feature, provide:
                   - Description
                   - Implementation steps
                   - Dependencies
                   - Estimated complexity
                4. Suggested order of implementation
                5. Potential challenges and mitigations
                
                Format the plan as a structured markdown document.
                """
                
                plan_text = self.planning_agent.run(plan_prompt)
            
            # Parse the plan text to extract features and tasks
            features = self._extract_features_from_plan(plan_text)
            
            # Create the plan structure
            plan = {
                "id": plan_id,
                "project_name": project_name,
                "requirements": requirements,
                "plan_text": plan_text,
                "features": features,
                "status": "planning",
                "created_at": time.time(),
                "updated_at": time.time(),
                "active_features": [],
                "completed_features": [],
                "pending_features": list(features.keys())
            }
            
            # Store the plan
            self.plans[plan_id] = plan
            
            # Create a lock for this plan
            self.plan_locks[plan_id] = threading.RLock()
            
            return plan
        except Exception as e:
            self.logger.error(f"Error creating plan: {e}")
            return {"error": str(e)}
    
    def _extract_features_from_plan(self, plan_text: str) -> Dict[str, Any]:
        """Extract features from the plan text.
        
        Args:
            plan_text: The plan text to parse
            
        Returns:
            Dictionary of features
        """
        features = {}
        
        # Simple parsing logic - in a real implementation, this would be more robust
        # and potentially use the AI to extract structured data
        lines = plan_text.split("\n")
        current_feature = None
        feature_name = None
        
        for line in lines:
            line = line.strip()
            
            # Look for feature headings
            if line.startswith("## Feature:") or line.startswith("### Feature:"):
                if current_feature and feature_name:
                    features[feature_name] = current_feature
                
                feature_name = line.split(":", 1)[1].strip() if ":" in line else line.lstrip("#").strip()
                current_feature = {
                    "name": feature_name,
                    "description": "",
                    "steps": [],
                    "dependencies": [],
                    "complexity": "medium",
                    "status": "not_started"
                }
            
            # Look for description
            elif current_feature and line.startswith("Description:"):
                current_feature["description"] = line.replace("Description:", "").strip()
            
            # Look for steps
            elif current_feature and (line.startswith("- [ ]") or line.startswith("* [ ]")):
                step_text = line.replace("- [ ]", "").replace("* [ ]", "").strip()
                current_feature["steps"].append({
                    "description": step_text,
                    "status": "not_started"
                })
            
            # Look for dependencies
            elif current_feature and line.startswith("Dependencies:"):
                deps_text = line.replace("Dependencies:", "").strip()
                if deps_text:
                    current_feature["dependencies"] = [d.strip() for d in deps_text.split(",")]
            
            # Look for complexity
            elif current_feature and line.startswith("Complexity:"):
                current_feature["complexity"] = line.replace("Complexity:", "").strip().lower()
        
        # Add the last feature if it exists
        if current_feature and feature_name:
            features[feature_name] = current_feature
        
        return features
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get a plan by ID.
        
        Args:
            plan_id: ID of the plan to get
            
        Returns:
            The plan or None if not found
        """
        return self.plans.get(plan_id)
    
    def list_plans(self) -> List[Dict[str, Any]]:
        """List all plans.
        
        Returns:
            List of plans
        """
        return list(self.plans.values())
    
    def update_plan(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Update a plan with new values.
        
        Args:
            plan_id: ID of the plan to update
            **kwargs: New values for the plan
            
        Returns:
            The updated plan or error
        """
        if plan_id not in self.plans:
            return {"error": f"Plan with ID {plan_id} not found"}
        
        with self.plan_locks[plan_id]:
            plan = self.plans[plan_id]
            
            # Update plan attributes
            for key, value in kwargs.items():
                if key in plan:
                    plan[key] = value
            
            # Update timestamp
            plan["updated_at"] = time.time()
            
            return plan
    
    def start_feature(self, plan_id: str, feature_name: str) -> Dict[str, Any]:
        """Start implementing a feature.
        
        Args:
            plan_id: ID of the plan
            feature_name: Name of the feature to start
            
        Returns:
            Result of the operation
        """
        if plan_id not in self.plans:
            return {"error": f"Plan with ID {plan_id} not found"}
        
        with self.plan_locks[plan_id]:
            plan = self.plans[plan_id]
            
            if feature_name not in plan["features"]:
                return {"error": f"Feature {feature_name} not found in plan"}
            
            if feature_name in plan["active_features"]:
                return {"error": f"Feature {feature_name} is already active"}
            
            if feature_name in plan["completed_features"]:
                return {"error": f"Feature {feature_name} is already completed"}
            
            # Check dependencies
            feature = plan["features"][feature_name]
            dependencies = feature.get("dependencies", [])
            
            for dep in dependencies:
                if dep not in plan["completed_features"]:
                    return {"error": f"Dependency {dep} is not completed yet"}
            
            # Move feature from pending to active
            if feature_name in plan["pending_features"]:
                plan["pending_features"].remove(feature_name)
            
            plan["active_features"].append(feature_name)
            feature["status"] = "in_progress"
            feature["started_at"] = time.time()
            
            # Update timestamp
            plan["updated_at"] = time.time()
            
            return {
                "success": True,
                "feature": feature_name,
                "plan_id": plan_id
            }
    
    def complete_feature(self, plan_id: str, feature_name: str) -> Dict[str, Any]:
        """Mark a feature as completed.
        
        Args:
            plan_id: ID of the plan
            feature_name: Name of the feature to complete
            
        Returns:
            Result of the operation
        """
        if plan_id not in self.plans:
            return {"error": f"Plan with ID {plan_id} not found"}
        
        with self.plan_locks[plan_id]:
            plan = self.plans[plan_id]
            
            if feature_name not in plan["features"]:
                return {"error": f"Feature {feature_name} not found in plan"}
            
            if feature_name in plan["completed_features"]:
                return {"error": f"Feature {feature_name} is already completed"}
            
            # Move feature from active to completed
            if feature_name in plan["active_features"]:
                plan["active_features"].remove(feature_name)
            
            plan["completed_features"].append(feature_name)
            plan["features"][feature_name]["status"] = "completed"
            plan["features"][feature_name]["completed_at"] = time.time()
            
            # Update timestamp
            plan["updated_at"] = time.time()
            
            # Check if all features are completed
            if len(plan["completed_features"]) == len(plan["features"]):
                plan["status"] = "completed"
            
            return {
                "success": True,
                "feature": feature_name,
                "plan_id": plan_id,
                "all_completed": plan["status"] == "completed"
            }
    
    def update_feature_status(self, plan_id: str, feature_name: str, status: str) -> Dict[str, Any]:
        """Update the status of a feature.
        
        Args:
            plan_id: ID of the plan
            feature_name: Name of the feature to update
            status: New status for the feature
            
        Returns:
            Result of the operation
        """
        if plan_id not in self.plans:
            return {"error": f"Plan with ID {plan_id} not found"}
        
        with self.plan_locks[plan_id]:
            plan = self.plans[plan_id]
            
            if feature_name not in plan["features"]:
                return {"error": f"Feature {feature_name} not found in plan"}
            
            feature = plan["features"][feature_name]
            old_status = feature["status"]
            
            # Update feature status
            feature["status"] = status
            
            # Update feature lists based on status
            if status == "completed" and feature_name not in plan["completed_features"]:
                if feature_name in plan["active_features"]:
                    plan["active_features"].remove(feature_name)
                if feature_name in plan["pending_features"]:
                    plan["pending_features"].remove(feature_name)
                plan["completed_features"].append(feature_name)
                feature["completed_at"] = time.time()
            
            elif status == "in_progress" and feature_name not in plan["active_features"]:
                if feature_name in plan["pending_features"]:
                    plan["pending_features"].remove(feature_name)
                if feature_name in plan["completed_features"]:
                    plan["completed_features"].remove(feature_name)
                plan["active_features"].append(feature_name)
                feature["started_at"] = time.time()
            
            elif status == "not_started" and feature_name not in plan["pending_features"]:
                if feature_name in plan["active_features"]:
                    plan["active_features"].remove(feature_name)
                if feature_name in plan["completed_features"]:
                    plan["completed_features"].remove(feature_name)
                plan["pending_features"].append(feature_name)
            
            # Update timestamp
            plan["updated_at"] = time.time()
            
            # Check if all features are completed
            if status == "completed" and len(plan["completed_features"]) == len(plan["features"]):
                plan["status"] = "completed"
            elif plan["status"] == "completed" and len(plan["completed_features"]) < len(plan["features"]):
                plan["status"] = "in_progress"
            
            return {
                "success": True,
                "feature": feature_name,
                "old_status": old_status,
                "new_status": status,
                "plan_id": plan_id
            }
    
    def update_step_status(self, plan_id: str, feature_name: str, step_index: int, status: str) -> Dict[str, Any]:
        """Update the status of a step in a feature.
        
        Args:
            plan_id: ID of the plan
            feature_name: Name of the feature
            step_index: Index of the step to update
            status: New status for the step
            
        Returns:
            Result of the operation
        """
        if plan_id not in self.plans:
            return {"error": f"Plan with ID {plan_id} not found"}
        
        with self.plan_locks[plan_id]:
            plan = self.plans[plan_id]
            
            if feature_name not in plan["features"]:
                return {"error": f"Feature {feature_name} not found in plan"}
            
            feature = plan["features"][feature_name]
            
            if step_index < 0 or step_index >= len(feature["steps"]):
                return {"error": f"Step index {step_index} is out of range"}
            
            step = feature["steps"][step_index]
            old_status = step["status"]
            
            # Update step status
            step["status"] = status
            
            # Update timestamp
            step["updated_at"] = time.time()
            
            # Check if all steps are completed
            all_completed = all(s["status"] == "completed" for s in feature["steps"])
            
            # Update feature status if all steps are completed
            if all_completed and feature["status"] != "completed":
                self.update_feature_status(plan_id, feature_name, "completed")
            
            return {
                "success": True,
                "feature": feature_name,
                "step_index": step_index,
                "old_status": old_status,
                "new_status": status,
                "plan_id": plan_id,
                "all_steps_completed": all_completed
            }
    
    def get_plan_progress(self, plan_id: str) -> Dict[str, Any]:
        """Get the progress of a plan.
        
        Args:
            plan_id: ID of the plan
            
        Returns:
            Progress information
        """
        if plan_id not in self.plans:
            return {"error": f"Plan with ID {plan_id} not found"}
        
        with self.plan_locks[plan_id]:
            plan = self.plans[plan_id]
            
            total_features = len(plan["features"])
            completed_features = len(plan["completed_features"])
            active_features = len(plan["active_features"])
            pending_features = len(plan["pending_features"])
            
            # Calculate step progress
            total_steps = 0
            completed_steps = 0
            
            for feature_name, feature in plan["features"].items():
                steps = feature.get("steps", [])
                total_steps += len(steps)
                completed_steps += sum(1 for step in steps if step.get("status") == "completed")
            
            # Calculate percentages
            feature_progress = (completed_features / total_features * 100) if total_features > 0 else 0
            step_progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0
            
            return {
                "plan_id": plan_id,
                "status": plan["status"],
                "total_features": total_features,
                "completed_features": completed_features,
                "active_features": active_features,
                "pending_features": pending_features,
                "feature_progress": feature_progress,
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "step_progress": step_progress,
                "updated_at": plan["updated_at"]
            }
    
    def handle_concurrent_planning(self, project_ids: List[str]) -> Dict[str, Any]:
        """Handle concurrent planning for multiple projects.
        
        Args:
            project_ids: List of project IDs to plan concurrently
            
        Returns:
            Status of concurrent planning
        """
        # Initialize planning agent if needed
        self._initialize_planning_agent()
        
        # Track concurrent planning status
        concurrent_status = {
            "total_projects": len(project_ids),
            "completed_projects": 0,
            "active_projects": [],
            "pending_projects": project_ids.copy(),
            "results": {}
        }
        
        # Start planning threads
        threads = []
        
        for project_id in project_ids:
            thread = threading.Thread(
                target=self._plan_project_thread,
                args=(project_id, concurrent_status)
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Return initial status
        return {
            "status": "planning_started",
            "projects": project_ids,
            "concurrent_status": concurrent_status
        }
    
    def _plan_project_thread(self, project_id: str, concurrent_status: Dict[str, Any]):
        """Thread function for planning a project.
        
        Args:
            project_id: ID of the project to plan
            concurrent_status: Shared status dictionary
        """
        try:
            # Update status
            with threading.RLock():
                if project_id in concurrent_status["pending_projects"]:
                    concurrent_status["pending_projects"].remove(project_id)
                concurrent_status["active_projects"].append(project_id)
            
            # TODO: Implement actual planning logic here
            # This would involve getting project details, requirements, etc.
            # and then creating a plan
            
            # For now, just simulate planning
            time.sleep(2)  # Simulate planning work
            
            # Update status
            with threading.RLock():
                if project_id in concurrent_status["active_projects"]:
                    concurrent_status["active_projects"].remove(project_id)
                concurrent_status["completed_projects"] += 1
                concurrent_status["results"][project_id] = {
                    "status": "completed",
                    "plan_id": f"plan_{project_id}_{int(time.time())}"
                }
        except Exception as e:
            self.logger.error(f"Error planning project {project_id}: {e}")
            
            # Update status
            with threading.RLock():
                if project_id in concurrent_status["active_projects"]:
                    concurrent_status["active_projects"].remove(project_id)
                concurrent_status["results"][project_id] = {
                    "status": "error",
                    "error": str(e)
                }
