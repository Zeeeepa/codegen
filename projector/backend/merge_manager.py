"""
Merge manager for handling branch and PR merges in the projector application.
"""
import logging
from datetime import datetime

class MergeManager:
    """Manager for handling branch and PR merges."""
    
    def __init__(self, github_manager, project_manager):
        """Initialize the merge manager."""
        self.github_manager = github_manager
        self.project_manager = project_manager
        self.logger = logging.getLogger(__name__)
    
    def handle_branch_merge(self, project_id, source_branch, target_branch):
        """Handle a branch merge event."""
        project = self.project_manager.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        # Record the merge event
        merge_info = {
            "type": "branch_merge",
            "head_branch": source_branch,
            "base_branch": target_branch,
            "merged_at": datetime.now().isoformat()
        }
        
        # Add to project's merge history
        project.merges.append(merge_info)
        
        # Save project changes
        self.project_manager.db.save_project(project)
        
        return {
            "success": True,
            "merge_info": merge_info
        }
    
    def handle_pr_merge(self, project_id, pr_number):
        """Handle a PR merge event."""
        return self.project_manager.handle_pr_merged(project_id, pr_number)
    
    def get_merge_history(self, project_id):
        """Get the merge history for a project."""
        project = self.project_manager.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        return {
            "success": True,
            "merges": project.merges,
            "total_merges": len(project.merges)
        }
