import os
import sys
import time
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backend components
from backend.slack_manager import SlackManager
from backend.github_manager import GitHubManager
from backend.assistant_agent import AssistantAgent
from backend.planning_manager import PlanningManager
from backend.project_database import ProjectDatabase

class BackendConnector:
    """Connector for interfacing with backend components."""
    
    def __init__(self, slack_token, slack_channel, github_token, github_username, github_repo, 
                openai_api_key=None, ai_enabled=False):
        """Initialize the backend connector."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize backend components
        self.slack_manager = SlackManager(slack_token, slack_channel)
        self.github_manager = GitHubManager(github_token, github_username, github_repo)
        
        # Create docs directory if it doesn't exist
        os.makedirs("./docs", exist_ok=True)
        
        # Initialize project database
        self.project_database = ProjectDatabase()
        
        # Initialize planning manager
        self.planning_manager = PlanningManager(self.project_database)
        
        # Initialize assistant agent
        self.assistant_agent = AssistantAgent(
            self.slack_manager, 
            self.github_manager, 
            "./docs", 
            self.project_database
        )
        
        # Set AI configuration
        self.ai_enabled = ai_enabled
        if ai_enabled and openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
    
    def test_slack_connection(self):
        """Test connection to Slack."""
        try:
            # Try to get channel ID (this will fail if token is invalid)
            channel_id = self.slack_manager.get_channel_id(self.slack_manager.default_channel)
            return channel_id is not None
        except Exception as e:
            self.logger.error(f"Error testing Slack connection: {e}")
            return False
    
    def test_github_connection(self):
        """Test connection to GitHub."""
        try:
            # Try to list branches (this will fail if token is invalid)
            branches = self.github_manager.list_branches()
            return branches is not None and len(branches) > 0
        except Exception as e:
            self.logger.error(f"Error testing GitHub connection: {e}")
            return False
    
    def save_document(self, filename, content):
        """Save a document to the docs directory."""
        try:
            file_path = os.path.join("./docs", filename)
            
            with open(file_path, "w") as f:
                f.write(content)
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving document: {e}")
            return False
    
    def process_document(self, filename):
        """Process a document to extract requirements."""
        try:
            file_path = os.path.join("./docs", filename)
            requirements = self.assistant_agent.process_markdown_document(file_path)
            
            if requirements:
                # Create implementation plan
                plan = self.assistant_agent.create_implementation_plan(requirements)
                
                # Start development for each feature
                for feature_plan in plan:
                    feature_name = feature_plan["feature"]
                    self.assistant_agent.start_feature_development(feature_name, feature_plan)
            
            return requirements
        except Exception as e:
            self.logger.error(f"Error processing document: {e}")
            return None
    
    def list_documents(self):
        """List all documents in the docs directory."""
        try:
            return [f for f in os.listdir("./docs") if f.endswith(".md")]
        except Exception as e:
            self.logger.error(f"Error listing documents: {e}")
            return []
    
    def get_document_content(self, filename):
        """Get the content of a document."""
        try:
            file_path = os.path.join("./docs", filename)
            
            with open(file_path, "r") as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error getting document content: {e}")
            return ""
    
    def delete_document(self, filename):
        """Delete a document."""
        try:
            file_path = os.path.join("./docs", filename)
            os.remove(file_path)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting document: {e}")
            return False
    
    def get_threads(self):
        """Get all active threads."""
        try:
            return self.slack_manager.threads
        except Exception as e:
            self.logger.error(f"Error getting threads: {e}")
            return {}
    
    def get_thread_history(self, topic):
        """Get the history of a thread."""
        try:
            return self.slack_manager.get_thread_history(topic)
        except Exception as e:
            self.logger.error(f"Error getting thread history: {e}")
            return []
    
    def create_thread(self, topic, message):
        """Create a new thread."""
        try:
            thread_ts = self.slack_manager.create_thread(topic, message)
            
            if thread_ts:
                # Also create a branch for this feature
                branch_name = f"feature/{topic.lower().replace(' ', '-')}"
                self.github_manager.create_branch(branch_name)
                
                # Track this feature
                self.assistant_agent.features[topic] = {
                    "branch": branch_name,
                    "status": "in_progress",
                    "plan": {
                        "feature": topic,
                        "steps": [
                            f"Initialize development for {topic}",
                            f"Create GitHub branch for {topic}",
                            f"Implement core functionality for {topic}",
                            f"Test implementation for {topic}",
                            f"Create pull request for {topic}"
                        ]
                    }
                }
            
            return thread_ts is not None
        except Exception as e:
            self.logger.error(f"Error creating thread: {e}")
            return False
    
    def reply_to_thread(self, topic, message):
        """Reply to a thread."""
        try:
            return self.slack_manager.reply_to_thread(topic, message) is not None
        except Exception as e:
            self.logger.error(f"Error replying to thread: {e}")
            return False
    
    def get_features(self):
        """Get all features."""
        try:
            return self.assistant_agent.features
        except Exception as e:
            self.logger.error(f"Error getting features: {e}")
            return {}
    
    def get_feature(self, topic):
        """Get a specific feature."""
        try:
            return self.assistant_agent.features.get(topic)
        except Exception as e:
            self.logger.error(f"Error getting feature: {e}")
            return None
    
    def update_feature_status(self, topic, status, message=None):
        """Update the status of a feature."""
        try:
            return self.assistant_agent.update_feature_status(topic, status, message)
        except Exception as e:
            self.logger.error(f"Error updating feature status: {e}")
            return False
    
    def complete_feature(self, topic):
        """Complete a feature and create a pull request."""
        try:
            return self.assistant_agent.complete_feature(topic)
        except Exception as e:
            self.logger.error(f"Error completing feature: {e}")
            return False
    
    def list_branches(self):
        """List all branches in the repository."""
        try:
            return self.github_manager.list_branches()
        except Exception as e:
            self.logger.error(f"Error listing branches: {e}")
            return []
    
    def create_branch(self, branch_name, base_branch="main"):
        """Create a new branch."""
        try:
            return self.github_manager.create_branch(branch_name, base_branch)
        except Exception as e:
            self.logger.error(f"Error creating branch: {e}")
            return False
    
    def list_pull_requests(self):
        """List all pull requests."""
        try:
            return self.github_manager.list_pull_requests()
        except Exception as e:
            self.logger.error(f"Error listing pull requests: {e}")
            return []
    
    def merge_pull_request(self, pr_number):
        """Merge a pull request."""
        try:
            return self.github_manager.merge_pull_request(pr_number)
        except Exception as e:
            self.logger.error(f"Error merging pull request: {e}")
            return False
    
    def list_repository_files(self, branch="main"):
        """List files in the repository."""
        try:
            return self.github_manager.list_repository_files(branch)
        except Exception as e:
            self.logger.error(f"Error listing repository files: {e}")
            return []
    
    def get_file_content(self, file_path, branch="main"):
        """Get the content of a file from the repository."""
        try:
            return self.github_manager.get_file_content(file_path, branch)
        except Exception as e:
            self.logger.error(f"Error getting file content: {e}")
            return ""
    
    def commit_file(self, file_path, commit_message, branch, content):
        """Commit a file to the repository."""
        try:
            return self.github_manager.commit_file(file_path, commit_message, branch, content)
        except Exception as e:
            self.logger.error(f"Error committing file: {e}")
            return False
    
    def analyze_repository(self):
        """Analyze the repository structure and code."""
        try:
            return self.github_manager.analyze_repository()
        except Exception as e:
            self.logger.error(f"Error analyzing repository: {e}")
            return None
    
    def generate_code(self, feature_name):
        """Generate code for a feature."""
        try:
            feature = self.assistant_agent.features.get(feature_name)
            if not feature:
                return None
            
            return self.github_manager.generate_code_for_feature(
                feature_name, 
                feature.get("plan", {}), 
                self.assistant_agent.ai_assistant
            )
        except Exception as e:
            self.logger.error(f"Error generating code: {e}")
            return None
    
    def create_pull_request(self, feature_name):
        """Create a pull request for a feature."""
        try:
            feature = self.assistant_agent.features.get(feature_name)
            if not feature or "github_branch" not in feature:
                return None
            
            return self.github_manager.create_pull_request_for_feature(
                feature_name, 
                feature["github_branch"]
            )
        except Exception as e:
            self.logger.error(f"Error creating pull request: {e}")
            return None
    
    def create_project(self, name, git_url, slack_channel=None):
        """Create a new project."""
        try:
            return self.project_database.create_project(name, git_url, slack_channel)
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            return None
    
    def list_projects(self):
        """List all projects."""
        try:
            return self.project_database.list_projects()
        except Exception as e:
            self.logger.error(f"Error listing projects: {e}")
            return []
    
    def get_project(self, project_id):
        """Get a project by ID."""
        try:
            return self.project_database.get_project(project_id)
        except Exception as e:
            self.logger.error(f"Error getting project: {e}")
            return None
    
    def delete_project(self, project_id):
        """Delete a project."""
        try:
            return self.project_database.delete_project(project_id)
        except Exception as e:
            self.logger.error(f"Error deleting project: {e}")
            return False
    
    def create_implementation_plan(self, project_id, features):
        """Create an implementation plan for a project."""
        try:
            return self.planning_manager.create_plan_from_features(project_id, features)
        except Exception as e:
            self.logger.error(f"Error creating implementation plan: {e}")
            return None
    
    def generate_gantt_chart_data(self, project_id):
        """Generate Gantt chart data for a project."""
        try:
            return self.planning_manager.generate_gantt_chart_data(project_id)
        except Exception as e:
            self.logger.error(f"Error generating Gantt chart data: {e}")
            return None
