"""
Project Manager for MultiThread Slack GitHub Tool.
"""
import uuid
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from codegen.agents.planning_agent import PlanningAgent
from codegen.agents.pr_review_agent import PRReviewAgent
from codegen.agents.planning.planning import PlanStepStatus
from projector.backend.project import Project
from projector.backend.project_database import ProjectDatabase
from projector.backend.github_manager import GitHubManager
from projector.backend.slack_manager import SlackManager
from projector.backend.thread_pool import ThreadPool

class ProjectManager:
    """Manages multiple projects and their configurations with a focus on tracking progress."""
    
    def __init__(
        self,
        github_manager: GitHubManager,
        slack_manager: SlackManager,
        thread_pool: ThreadPool
    ):
        """Initialize the ProjectManager with required dependencies."""
        self.logger = logging.getLogger(__name__)
        self.db = ProjectDatabase()
        self.projects = {}
        self.github_manager = github_manager
        self.slack_manager = slack_manager
        self.thread_pool = thread_pool
        
        # Track project progress
        self.project_progress = {}
        
        # Track PR status for each project
        self.project_prs = {}
        
        # PR review agent for validating PRs
        self.pr_review_agent = None
        
        # Planning agent for creating implementation plans
        self.planning_agent = None
        
        # Active project implementations
        self.active_implementations = {}
        
        # Load projects from database
        self._load_projects()
    
    def _load_projects(self):
        """Load projects from database."""
        for project in self.db.list_projects():
            self.projects[project.id] = project
            # Initialize progress tracking
            self.project_progress[project.id] = {
                "total_features": 0,
                "completed_features": 0,
                "in_progress_features": 0,
                "pending_features": 0,
                "last_updated": datetime.now().isoformat()
            }
            # Initialize PR tracking
            self.project_prs[project.id] = []
    
    def _initialize_pr_review_agent(self):
        """Initialize the PR review agent on demand."""
        if self.pr_review_agent is None:
            try:
                # For now, we'll use a mock codebase since we're not directly using code analysis
                mock_codebase = type('MockCodebase', (), {})()
                self.pr_review_agent = PRReviewAgent(
                    codebase=mock_codebase,
                    github_token=self.github_manager.github_token,
                    model_provider="anthropic",
                    model_name="claude-3-5-sonnet-latest"
                )
                self.logger.info("PR review agent initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing PR review agent: {e}")
                raise
    
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
    
    def _generate_project_id(self, name):
        """Generate a unique project ID based on name."""
        # Create a slug from the name
        slug = name.lower().replace(" ", "-")
        
        # Add a short UUID to ensure uniqueness
        unique_id = str(uuid.uuid4())[:8]
        
        return f"{slug}-{unique_id}"
    
    def add_project(self, name, git_url, slack_channel=None, requirements=None, plan=None):
        """Add a new project with optional requirements and plan."""
        project_id = self._generate_project_id(name)
        project = Project(
            id=project_id,
            name=name,
            git_url=git_url,
            slack_channel=slack_channel,
            requirements=requirements or "",
            plan=plan or ""
        )
        
        # Save to memory
        self.projects[project_id] = project
        
        # Initialize progress tracking
        self.project_progress[project_id] = {
            "total_features": 0,
            "completed_features": 0,
            "in_progress_features": 0,
            "pending_features": 0,
            "last_updated": datetime.now().isoformat()
        }
        
        # Initialize PR tracking
        self.project_prs[project_id] = []
        
        # Save to database
        self.db.save_project(project)
        
        return project_id
    
    def get_project(self, project_id):
        """Get a project by ID."""
        return self.projects.get(project_id)
    
    def update_project(self, project_id, **kwargs):
        """Update a project with new values."""
        project = self.get_project(project_id)
        if not project:
            return None
        
        # Update project attributes
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        # Update timestamp
        project.updated_at = datetime.now().isoformat()
        
        # Save to database
        self.db.save_project(project)
        
        return project
    
    def delete_project(self, project_id):
        """Delete a project."""
        if project_id in self.projects:
            # Remove from memory
            del self.projects[project_id]
            
            # Remove progress tracking
            if project_id in self.project_progress:
                del self.project_progress[project_id]
            
            # Remove PR tracking
            if project_id in self.project_prs:
                del self.project_prs[project_id]
            
            # Remove from database
            self.db.delete_project(project_id)
            
            return True
        
        return False
    
    def list_projects(self):
        """List all projects."""
        return list(self.projects.values())
    
    def create_implementation_plan(self, project_id, requirements=None):
        """Create an implementation plan for a project."""
        project = self.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        # Use requirements from project if not provided
        requirements_text = requirements or project.requirements
        if not requirements_text:
            return {"error": "No requirements provided"}
        
        # Initialize planning agent if needed
        self._initialize_planning_agent()
        
        try:
            # Generate a plan using the planning agent
            plan_prompt = f"""
            Create a detailed implementation plan for the following project:
            
            Project: {project.name}
            
            Requirements:
            {requirements_text}
            
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
            
            # Generate the plan
            plan_text = self.planning_agent.run(plan_prompt)
            
            # Update the project with the plan
            project.plan = plan_text
            project.updated_at = datetime.now().isoformat()
            
            # Extract features from the plan
            features = self._extract_features_from_plan(plan_text)
            project.features = features
            
            # Update progress tracking
            self.project_progress[project_id] = {
                "total_features": len(features),
                "completed_features": 0,
                "in_progress_features": 0,
                "pending_features": len(features),
                "last_updated": datetime.now().isoformat()
            }
            
            # Save to database
            self.db.save_project(project)
            
            return {
                "success": True,
                "plan": plan_text,
                "features": features
            }
        except Exception as e:
            self.logger.error(f"Error creating implementation plan: {e}")
            return {"error": str(e)}
    
    def _extract_features_from_plan(self, plan_text):
        """Extract features from the plan text."""
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
    
    def start_implementation(self, project_id, max_concurrent_features=None):
        """Start implementing a project."""
        project = self.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        if not project.features:
            return {"error": "No features defined for this project"}
        
        # Set maximum concurrent features
        max_concurrent = max_concurrent_features or project.max_parallel_tasks
        
        # Initialize active implementation tracking
        if project_id not in self.active_implementations:
            self.active_implementations[project_id] = {
                "active_features": [],
                "completed_features": [],
                "pending_features": list(project.features.keys()),
                "max_concurrent": max_concurrent
            }
        
        # Start implementation
        implementation = self.active_implementations[project_id]
        
        # Calculate how many new features we can start
        available_slots = max_concurrent - len(implementation["active_features"])
        features_to_start = min(available_slots, len(implementation["pending_features"]))
        
        started_features = []
        
        for _ in range(features_to_start):
            if not implementation["pending_features"]:
                break
            
            # Get the next feature
            feature_name = implementation["pending_features"].pop(0)
            feature = project.features[feature_name]
            
            # Create a branch for the feature
            branch_name = f"{project.name.lower().replace(' ', '-')}-{feature_name.lower().replace(' ', '-')}"
            try:
                branch_result = self.github_manager.create_branch(
                    repo_url=project.git_url,
                    branch_name=branch_name,
                    base_branch="main"  # Assuming main is the default branch
                )
                
                # Store branch information
                project.branches[feature_name] = {
                    "name": branch_name,
                    "created_at": datetime.now().isoformat(),
                    "status": "active"
                }
                
                # Update feature status
                feature["status"] = "in_progress"
                feature["branch"] = branch_name
                feature["started_at"] = datetime.now().isoformat()
                
                # Create a Slack thread for the feature
                thread_result = self.slack_manager.create_thread(
                    channel=project.slack_channel,
                    text=f"Starting implementation of feature: *{feature_name}*\n\n{feature['description']}\n\nBranch: `{branch_name}`"
                )
                
                if thread_result.get("ok"):
                    thread_ts = thread_result.get("ts")
                    feature["thread_ts"] = thread_ts
                    project.active_threads[feature_name] = thread_ts
                
                # Add to active features
                implementation["active_features"].append(feature_name)
                
                # Update progress tracking
                self.project_progress[project_id]["in_progress_features"] += 1
                self.project_progress[project_id]["pending_features"] -= 1
                
                started_features.append(feature_name)
                
            except Exception as e:
                self.logger.error(f"Error starting feature {feature_name}: {e}")
                # Put the feature back in pending
                implementation["pending_features"].insert(0, feature_name)
        
        # Save project changes
        self.db.save_project(project)
        
        return {
            "success": True,
            "started_features": started_features,
            "active_features": implementation["active_features"],
            "pending_features": implementation["pending_features"]
        }
    
    def send_feature_tasks(self, project_id, feature_name):
        """Send tasks for a feature to Slack."""
        project = self.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        if feature_name not in project.features:
            return {"error": f"Feature {feature_name} not found in project"}
        
        feature = project.features[feature_name]
        
        if feature["status"] != "in_progress":
            return {"error": f"Feature {feature_name} is not in progress"}
        
        if "thread_ts" not in feature:
            return {"error": f"No Slack thread found for feature {feature_name}"}
        
        thread_ts = feature["thread_ts"]
        
        # Send tasks to the thread
        sent_tasks = []
        
        for i, step in enumerate(feature["steps"]):
            if step["status"] == "not_started":
                # Send the task to Slack
                task_message = f"Task {i+1}: {step['description']}"
                
                result = self.slack_manager.send_message(
                    channel=project.slack_channel,
                    text=task_message,
                    thread_ts=thread_ts
                )
                
                if result.get("ok"):
                    step["status"] = "in_progress"
                    step["task_ts"] = result.get("ts")
                    sent_tasks.append(step["description"])
        
        # Save project changes
        self.db.save_project(project)
        
        return {
            "success": True,
            "feature": feature_name,
            "sent_tasks": sent_tasks
        }
    
    def handle_pr_received(self, project_id, feature_name, pr_url):
        """Handle a received PR for a feature."""
        project = self.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        if feature_name not in project.features:
            return {"error": f"Feature {feature_name} not found in project"}
        
        feature = project.features[feature_name]
        
        # Initialize PR review agent if needed
        self._initialize_pr_review_agent()
        
        # Update PR status
        project.pr_status[feature_name] = {
            "url": pr_url,
            "status": "reviewing",
            "received_at": datetime.now().isoformat()
        }
        
        # Notify in the feature thread
        if "thread_ts" in feature:
            self.slack_manager.send_message(
                channel=project.slack_channel,
                text=f"PR received for feature *{feature_name}*: {pr_url}\n\nReviewing...",
                thread_ts=feature["thread_ts"]
            )
        
        # Review the PR
        try:
            review_result = self.pr_review_agent.review_pr(pr_url)
            
            # Update PR status with review result
            project.pr_status[feature_name]["status"] = "reviewed"
            project.pr_status[feature_name]["review_result"] = review_result
            
            # Notify planning agent
            self._notify_planning_agent_about_pr(project_id, feature_name, pr_url, review_result)
            
            # Notify in the feature thread
            if "thread_ts" in feature:
                self.slack_manager.send_message(
                    channel=project.slack_channel,
                    text=f"PR review completed for feature *{feature_name}*\n\nSummary: {review_result.get('summary', 'No summary available')}",
                    thread_ts=feature["thread_ts"]
                )
            
            # Save project changes
            self.db.save_project(project)
            
            return {
                "success": True,
                "feature": feature_name,
                "pr_url": pr_url,
                "review_result": review_result
            }
        except Exception as e:
            self.logger.error(f"Error reviewing PR for feature {feature_name}: {e}")
            
            # Update PR status with error
            project.pr_status[feature_name]["status"] = "review_failed"
            project.pr_status[feature_name]["error"] = str(e)
            
            # Save project changes
            self.db.save_project(project)
            
            return {"error": str(e)}
    
    def handle_pr_merged(self, project_id, pr_number):
        """Handle a merged PR for a project."""
        project = self.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        # Get PR information from GitHub
        merge_info = self.github_manager.merge_pull_request(pr_number)
        
        if not merge_info.get("success"):
            return {"error": f"Failed to merge PR: {merge_info.get('error')}"}
        
        # Add merge to project's merge history
        project.merges.append(merge_info)
        
        # Find the feature associated with this PR
        feature_name = None
        for fname, pr_info in project.pr_status.items():
            if pr_info.get("pr_number") == pr_number:
                feature_name = fname
                break
        
        # Update feature status if found
        if feature_name and feature_name in project.features:
            feature = project.features[feature_name]
            feature["status"] = "completed"
            feature["completed_at"] = datetime.now().isoformat()
            
            # Notify in the feature thread
            if "thread_ts" in feature:
                self.slack_manager.send_message(
                    channel=project.slack_channel,
                    text=f"PR for feature *{feature_name}* has been merged! 🎉\n\nFeature is now complete.",
                    thread_ts=feature["thread_ts"]
                )
            
            # Update progress tracking
            self.project_progress[project_id]["completed_features"] += 1
            self.project_progress[project_id]["in_progress_features"] -= 1
        
        # Save project changes
        self.db.save_project(project)
        
        return {
            "success": True,
            "merge_info": merge_info,
            "feature_name": feature_name
        }
    
    def _notify_planning_agent_about_pr(self, project_id, feature_name, pr_url, review_result):
        """Notify the planning agent about a PR review."""
        # Initialize planning agent if needed
        self._initialize_planning_agent()
        
        project = self.get_project(project_id)
        if not project:
            return
        
        # Create notification for planning agent
        notification = f"""
        PR Review Notification
        
        Project: {project.name}
        Feature: {feature_name}
        PR URL: {pr_url}
        
        Review Summary: {review_result.get('summary', 'No summary available')}
        
        Status: {review_result.get('status', 'Unknown')}
        
        Please update the project plan accordingly.
        """
        
        # Send notification to planning agent
        try:
            response = self.planning_agent.run(notification)
            self.logger.info(f"Planning agent response: {response}")
        except Exception as e:
            self.logger.error(f"Error notifying planning agent: {e}")
    
    def get_project_status(self, project_id):
        """Get the status of a project."""
        project = self.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        # Get progress
        progress = self.project_progress.get(project_id, {})
        
        # Get active implementation
        implementation = self.active_implementations.get(project_id, {
            "active_features": [],
            "completed_features": [],
            "pending_features": list(project.features.keys()) if project.features else []
        })
        
        # Calculate overall progress percentage
        total_features = progress.get("total_features", 0)
        completed_features = progress.get("completed_features", 0)
        progress_percentage = (completed_features / total_features * 100) if total_features > 0 else 0
        
        return {
            "project": project.to_dict(),
            "progress": progress,
            "progress_percentage": progress_percentage,
            "implementation": implementation,
            "pr_status": project.pr_status
        }