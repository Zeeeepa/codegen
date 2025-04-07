"""
Project Manager for MultiThread Slack GitHub Tool.
"""
import uuid
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from agentgen.application.projector.backend.project import Project
from agentgen.application.projector.backend.project_database import ProjectDatabase
from agentgen.application.projector.backend.github_manager import GitHubManager
from agentgen.application.projector.backend.slack_manager import SlackManager
from agentgen.application.projector.backend.thread_pool import ThreadPool
from agentgen.agents.pr_review_agent import PRReviewAgent

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
                    model_name="claude-3-7-sonnet-latest"
                )
                self.logger.info("PR review agent initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing PR review agent: {e}")
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
        
        # Create a Slack thread for this project if a channel is specified
        if slack_channel:
            thread_ts = self.slack_manager.create_thread(
                f"Project: {name}",
                f"New project created: {name}\nGit URL: {git_url}\nProject ID: {project_id}",
                channel=slack_channel
            )
            if thread_ts:
                project.slack_thread_ts = thread_ts
                self.db.save_project(project)
        
        self.logger.info(f"Added project: {name} (ID: {project_id})")
        
        return project_id
    
    def get_project(self, project_id):
        """Get a project by ID."""
        return self.projects.get(project_id)
    
    def get_project_by_name(self, name):
        """Get a project by name."""
        for project_id, project in self.projects.items():
            if project.name.lower() == name.lower():
                return project
        return None
    
    def list_projects(self):
        """List all projects."""
        return list(self.projects.values())
    
    def update_project(self, project_id, **kwargs):
        """Update project properties."""
        project = self.get_project(project_id)
        
        if not project:
            return False
        
        # Update properties
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        # Save changes
        self.db.save_project(project)
        
        return True
    
    def delete_project(self, project_id):
        """Delete a project."""
        if project_id in self.projects:
            del self.projects[project_id]
            if project_id in self.project_progress:
                del self.project_progress[project_id]
            if project_id in self.project_prs:
                del self.project_prs[project_id]
            return self.db.delete_project(project_id)
        
        return False
    
    def track_pr(self, project_id, pr_number, pr_url, feature_name, status="open"):
        """Track a pull request for a project."""
        if project_id not in self.projects:
            return False
        
        # Add PR to tracking
        pr_info = {
            "pr_number": pr_number,
            "pr_url": pr_url,
            "feature_name": feature_name,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        # Check if PR already exists
        for i, pr in enumerate(self.project_prs[project_id]):
            if pr["pr_number"] == pr_number:
                # Update existing PR
                self.project_prs[project_id][i] = pr_info
                return True
        
        # Add new PR
        self.project_prs[project_id].append(pr_info)
        
        # Update project progress
        self._update_project_progress(project_id)
        
        # Notify in Slack if thread exists
        project = self.get_project(project_id)
        if project and project.slack_channel and project.slack_thread_ts:
            self.slack_manager.reply_to_thread(
                project.slack_thread_ts,
                f"New PR #{pr_number} created for feature: {feature_name}\nURL: {pr_url}"
            )
        
        return True
    
    def update_pr_status(self, project_id, pr_number, status):
        """Update the status of a pull request."""
        if project_id not in self.projects:
            return False
        
        # Find and update PR
        for i, pr in enumerate(self.project_prs[project_id]):
            if pr["pr_number"] == pr_number:
                self.project_prs[project_id][i]["status"] = status
                self.project_prs[project_id][i]["last_updated"] = datetime.now().isoformat()
                
                # Update project progress
                self._update_project_progress(project_id)
                
                # Notify in Slack if thread exists
                project = self.get_project(project_id)
                if project and project.slack_channel and project.slack_thread_ts:
                    emoji = "✅" if status == "merged" else "🔄" if status == "open" else "❌"
                    self.slack_manager.reply_to_thread(
                        project.slack_thread_ts,
                        f"{emoji} PR #{pr_number} status updated to: {status}"
                    )
                
                return True
        
        return False
    
    def _update_project_progress(self, project_id):
        """Update project progress based on PR status."""
        if project_id not in self.projects or project_id not in self.project_prs:
            return
        
        # Count features by status
        total_features = len(set(pr["feature_name"] for pr in self.project_prs[project_id]))
        completed_features = len(set(pr["feature_name"] for pr in self.project_prs[project_id] if pr["status"] == "merged"))
        in_progress_features = len(set(pr["feature_name"] for pr in self.project_prs[project_id] if pr["status"] == "open"))
        pending_features = total_features - completed_features - in_progress_features
        
        # Update progress
        self.project_progress[project_id] = {
            "total_features": total_features,
            "completed_features": completed_features,
            "in_progress_features": in_progress_features,
            "pending_features": pending_features,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_project_progress(self, project_id):
        """Get the progress of a project."""
        if project_id in self.project_progress:
            return self.project_progress[project_id]
        return None
    
    def get_project_prs(self, project_id):
        """Get all pull requests for a project."""
        if project_id in self.project_prs:
            return self.project_prs[project_id]
        return []
    
    def validate_pr_against_requirements(self, project_id, pr_number):
        """Validate a PR against project requirements using PR review agent."""
        project = self.get_project(project_id)
        
        if not project:
            return {"error": "Project not found"}
        
        # Submit validation task to thread pool
        task_id = f"validate_pr_{project_id}_{pr_number}"
        
        self.thread_pool.submit(
            self._validate_pr_task,
            project_id=project_id,
            pr_number=pr_number
        )
        
        return {"status": "validation_started", "task_id": task_id}
    
    def _validate_pr_task(self, project_id, pr_number):
        """Task to validate a PR against requirements."""
        project = self.get_project(project_id)
        
        if not project:
            return {"error": "Project not found"}
        
        try:
            # Initialize PR review agent if needed
            self._initialize_pr_review_agent()
            
            # Get PR details
            pr_info = None
            for pr in self.project_prs[project_id]:
                if pr["pr_number"] == pr_number:
                    pr_info = pr
                    break
            
            if not pr_info:
                return {"error": "PR not found"}
            
            # Get repository name from git_url
            repo_parts = project.git_url.split("/")
            repo_name = repo_parts[-1].replace(".git", "") if repo_parts[-1].endswith(".git") else repo_parts[-1]
            full_repo_name = f"{self.github_manager.username}/{repo_name}"
            
            # Use PR review agent to validate PR
            validation_result = self.pr_review_agent.review_pr(
                full_repo_name, 
                pr_number,
                project_requirements=project.requirements
            )
            
            # Update PR status based on validation
            pr_info["validation_result"] = validation_result
            pr_info["last_updated"] = datetime.now().isoformat()
            
            # Notify in Slack if thread exists
            if project.slack_channel and project.slack_thread_ts:
                status_emoji = "✅" if validation_result.get("compliant", False) else "❌"
                message = f"{status_emoji} PR #{pr_number} validation result: {'Compliant' if validation_result.get('compliant', False) else 'Non-compliant'}"
                
                issues = validation_result.get("issues", [])
                if issues:
                    message += "\n\nIssues:"
                    for issue in issues:
                        message += f"\n- {issue}"
                
                suggestions = validation_result.get("suggestions", [])
                if suggestions:
                    message += "\n\nSuggestions:"
                    for suggestion in suggestions:
                        if isinstance(suggestion, dict):
                            desc = suggestion.get("description", "")
                            file_path = suggestion.get("file_path")
                            line_number = suggestion.get("line_number")
                            
                            if file_path and line_number:
                                message += f"\n- {desc} (in `{file_path}` at line {line_number})"
                            elif file_path:
                                message += f"\n- {desc} (in `{file_path}`)"
                            else:
                                message += f"\n- {desc}"
                        else:
                            message += f"\n- {suggestion}"
                
                self.slack_manager.reply_to_thread(
                    project.slack_thread_ts,
                    message
                )
            
            return {"status": "validation_completed", "result": validation_result}
        
        except Exception as e:
            self.logger.error(f"Error validating PR: {e}")
            return {"error": str(e)}
    
    def send_next_requirement(self, project_id):
        """Send the next requirement for a project via Slack."""
        project = self.get_project(project_id)
        
        if not project or not project.slack_channel or not project.slack_thread_ts:
            return {"error": "Project not found or Slack channel not configured"}
        
        # Get project progress
        progress = self.get_project_progress(project_id)
        
        if not progress:
            return {"error": "Project progress not found"}
        
        # Parse project plan to extract next requirement
        next_requirement = self._extract_next_requirement(project)
        
        if not next_requirement:
            return {"error": "No more requirements to implement"}
        
        # Send requirement to Slack
        message = f"📋 *Next Requirement*\n\n{next_requirement}"
        
        result = self.slack_manager.reply_to_thread(
            project.slack_thread_ts,
            message
        )
        
        return {"status": "requirement_sent", "requirement": next_requirement}
    
    def _extract_next_requirement(self, project):
        """Extract the next requirement from the project plan."""
        try:
            # Parse the project plan to find requirements
            plan_lines = project.plan.split("\n")
            
            # Look for features or requirements sections
            features_section = False
            requirements = []
            
            for line in plan_lines:
                line = line.strip()
                
                # Check for section headers
                if "feature" in line.lower() and (":" in line or "-" in line):
                    features_section = True
                    continue
                
                # If we're in the features section, collect requirements
                if features_section and line and (line.startswith("-") or line.startswith("*") or line.startswith("#")):
                    # Clean up the line
                    requirement = line.lstrip("-*# ").strip()
                    if requirement:
                        requirements.append(requirement)
            
            # Get completed features
            completed_features = set()
            for pr in self.project_prs.get(project.id, []):
                if pr["status"] == "merged":
                    completed_features.add(pr["feature_name"].lower())
            
            # Find the first requirement that hasn't been completed
            for req in requirements:
                if req.lower() not in completed_features:
                    return req
            
            # If no specific requirement found, return a generic one
            return "Implement the next feature according to the project plan."
            
        except Exception as e:
            self.logger.error(f"Error extracting next requirement: {e}")
            return "Implement the next feature according to the project plan."
    
    def generate_progress_report(self, project_id):
        """Generate a progress report for a project."""
        project = self.get_project(project_id)
        
        if not project:
            return {"error": "Project not found"}
        
        progress = self.get_project_progress(project_id)
        prs = self.get_project_prs(project_id)
        
        if not progress:
            return {"error": "Project progress not found"}
        
        # Calculate percentages
        total = progress["total_features"]
        completed_percent = (progress["completed_features"] / total * 100) if total > 0 else 0
        in_progress_percent = (progress["in_progress_features"] / total * 100) if total > 0 else 0
        pending_percent = (progress["pending_features"] / total * 100) if total > 0 else 0
        
        # Generate report
        report = f"""# Progress Report: {project.name}

## Overview
- **Total Features**: {total}
- **Completed**: {progress["completed_features"]} ({completed_percent:.1f}%)
- **In Progress**: {progress["in_progress_features"]} ({in_progress_percent:.1f}%)
- **Pending**: {progress["pending_features"]} ({pending_percent:.1f}%)
- **Last Updated**: {progress["last_updated"]}

## Pull Requests
"""
        
        # Add PR details
        for pr in prs:
            status_emoji = "✅" if pr["status"] == "merged" else "🔄" if pr["status"] == "open" else "❌"
            report += f"- {status_emoji} **PR #{pr['pr_number']}**: {pr['feature_name']} - {pr['status'].upper()}\n"
            report += f"  URL: {pr['pr_url']}\n"
            
            # Add validation results if available
            if "validation_result" in pr:
                validation = pr["validation_result"]
                if validation.get("compliant", False):
                    report += f"  Validation: ✅ Compliant\n"
                else:
                    report += f"  Validation: ❌ Non-compliant\n"
                    
                    # Add issues if any
                    issues = validation.get("issues", [])
                    if issues:
                        report += "  Issues:\n"
                        for issue in issues[:3]:  # Limit to 3 issues to keep report concise
                            report += f"    - {issue}\n"
                        if len(issues) > 3:
                            report += f"    - ... and {len(issues) - 3} more issues\n"
        
        # Add next steps
        next_requirement = self._extract_next_requirement(project)
        if next_requirement:
            report += f"\n## Next Steps\n- {next_requirement}\n"
        
        return {"status": "report_generated", "report": report}
    
    def find_project_for_pr(self, pr_number):
        """Find which project a PR belongs to."""
        for project_id, prs in self.project_prs.items():
            for pr in prs:
                if pr["pr_number"] == pr_number:
                    return self.get_project(project_id)
        return None