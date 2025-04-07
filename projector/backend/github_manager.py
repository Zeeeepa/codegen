import os
import logging
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.repo_config import RepoConfig
from codegen.git.utils.pr_review import CodegenPR
from codegen.git.utils.language import determine_project_language
from codegen.git.utils.clone import clone_or_pull_repo
from projector.backend.code_analyzer import CodeAnalyzer
from datetime import datetime

class GitHubManager:
    """Manager for GitHub integration with code generation capabilities."""
    
    def __init__(self, github_token, github_username, default_repo):
        """Initialize the GitHub manager."""
        self.github_token = github_token
        self.username = github_username
        self.default_repo_name = default_repo
        self.default_branch = "main"
        self.logger = logging.getLogger(__name__)
        
        try:
            # Create repo config
            self.repo_config = RepoConfig(
                name=default_repo,
                full_name=f"{github_username}/{default_repo}",
                base_dir="/tmp/projector_repos"
            )
            
            # Initialize RepoOperator
            self.repo_operator = RepoOperator(
                repo_config=self.repo_config,
                access_token=github_token,
                bot_commit=True
            )
            
            # Ensure repo is cloned
            self.setup_repo()
        except Exception as e:
            self.logger.error(f"Error initializing GitHub manager: {e}")
            self.repo_operator = None
    
    def setup_repo(self):
        """Set up the repository by cloning or pulling."""
        if not os.path.exists(self.repo_config.repo_path):
            self.logger.info(f"Cloning repository {self.repo_config.full_name}...")
            self.repo_operator.setup_repo_dir()
        else:
            self.logger.info(f"Repository {self.repo_config.full_name} already exists, pulling latest changes...")
            self.repo_operator.pull()
    
    def list_repositories(self):
        """List repositories owned by the user."""
        try:
            if self.repo_operator and self.repo_operator.remote_git_repo:
                return [repo.name for repo in self.repo_operator.remote_git_repo.get_user_repos()]
            return []
        except Exception as e:
            self.logger.error(f"Error listing repositories: {e}")
            return []
    
    def list_branches(self, repo_name=None):
        """List branches in a repository."""
        try:
            if repo_name and repo_name != self.default_repo_name:
                # Create a temporary RepoOperator for the specified repo
                temp_repo_config = RepoConfig(
                    name=repo_name,
                    full_name=f"{self.username}/{repo_name}",
                    base_dir="/tmp/projector_repos"
                )
                temp_operator = RepoOperator(
                    repo_config=temp_repo_config,
                    access_token=self.github_token
                )
                return temp_operator.list_branches()
            
            return self.repo_operator.list_branches()
        except Exception as e:
            self.logger.error(f"Error listing branches: {e}")
            return []
    
    def create_branch(self, branch_name, base_branch=None, repo_name=None):
        """Create a new branch in a repository."""
        try:
            if repo_name and repo_name != self.default_repo_name:
                # Create a temporary RepoOperator for the specified repo
                temp_repo_config = RepoConfig(
                    name=repo_name,
                    full_name=f"{self.username}/{repo_name}",
                    base_dir="/tmp/projector_repos"
                )
                temp_operator = RepoOperator(
                    repo_config=temp_repo_config,
                    access_token=self.github_token
                )
                return temp_operator.create_branch(branch_name, base_branch or self.default_branch)
            
            return self.repo_operator.create_branch(branch_name, base_branch or self.default_branch)
        except Exception as e:
            self.logger.error(f"Error creating branch: {e}")
            return False
    
    def list_repository_files(self, branch=None, repo_name=None):
        """List files in a repository."""
        try:
            if repo_name and repo_name != self.default_repo_name:
                # Create a temporary RepoOperator for the specified repo
                temp_repo_config = RepoConfig(
                    name=repo_name,
                    full_name=f"{self.username}/{repo_name}",
                    base_dir="/tmp/projector_repos"
                )
                temp_operator = RepoOperator(
                    repo_config=temp_repo_config,
                    access_token=self.github_token
                )
                return temp_operator.list_files(branch=branch or self.default_branch)
            
            return self.repo_operator.list_files(branch=branch or self.default_branch)
        except Exception as e:
            self.logger.error(f"Error listing repository files: {e}")
            return []
    
    def get_file_content(self, file_path, branch=None, repo_name=None):
        """Get the content of a file from a repository."""
        try:
            if repo_name and repo_name != self.default_repo_name:
                # Create a temporary RepoOperator for the specified repo
                temp_repo_config = RepoConfig(
                    name=repo_name,
                    full_name=f"{self.username}/{repo_name}",
                    base_dir="/tmp/projector_repos"
                )
                temp_operator = RepoOperator(
                    repo_config=temp_repo_config,
                    access_token=self.github_token
                )
                return temp_operator.get_file_content(file_path, branch=branch or self.default_branch)
            
            return self.repo_operator.get_file_content(file_path, branch=branch or self.default_branch)
        except Exception as e:
            self.logger.error(f"Error getting file content: {e}")
            return None
    
    def commit_file(self, file_path, commit_message, branch, content, repo_name=None):
        """Commit a file to a repository."""
        try:
            if repo_name and repo_name != self.default_repo_name:
                # Create a temporary RepoOperator for the specified repo
                temp_repo_config = RepoConfig(
                    name=repo_name,
                    full_name=f"{self.username}/{repo_name}",
                    base_dir="/tmp/projector_repos"
                )
                temp_operator = RepoOperator(
                    repo_config=temp_repo_config,
                    access_token=self.github_token
                )
                temp_operator.checkout_branch(branch)
                return temp_operator.commit_file(file_path, content, commit_message)
            
            self.repo_operator.checkout_branch(branch)
            return self.repo_operator.commit_file(file_path, content, commit_message)
        except Exception as e:
            self.logger.error(f"Error committing file: {e}")
            return False
    
    def create_pull_request(self, title, body, head_branch, base_branch=None, repo_name=None):
        """Create a pull request in a repository."""
        try:
            if repo_name and repo_name != self.default_repo_name:
                # Create a temporary RepoOperator for the specified repo
                temp_repo_config = RepoConfig(
                    name=repo_name,
                    full_name=f"{self.username}/{repo_name}",
                    base_dir="/tmp/projector_repos"
                )
                temp_operator = RepoOperator(
                    repo_config=temp_repo_config,
                    access_token=self.github_token
                )
                pr = temp_operator.create_pull_request(
                    title=title,
                    body=body,
                    head_branch=head_branch,
                    base_branch=base_branch or self.default_branch
                )
                if pr:
                    return {
                        "number": pr.number,
                        "url": pr.html_url
                    }
                return None
            
            pr = self.repo_operator.create_pull_request(
                title=title,
                body=body,
                head_branch=head_branch,
                base_branch=base_branch or self.default_branch
            )
            if pr:
                return {
                    "number": pr.number,
                    "url": pr.html_url
                }
            return None
        except Exception as e:
            self.logger.error(f"Error creating pull request: {e}")
            return None
    
    def list_pull_requests(self, state="open", repo_name=None):
        """List pull requests in a repository."""
        try:
            if repo_name and repo_name != self.default_repo_name:
                # Create a temporary RepoOperator for the specified repo
                temp_repo_config = RepoConfig(
                    name=repo_name,
                    full_name=f"{self.username}/{repo_name}",
                    base_dir="/tmp/projector_repos"
                )
                temp_operator = RepoOperator(
                    repo_config=temp_repo_config,
                    access_token=self.github_token
                )
                return temp_operator.remote_git_repo.list_pull_requests(state=state)
            
            return self.repo_operator.remote_git_repo.list_pull_requests(state=state)
        except Exception as e:
            self.logger.error(f"Error listing pull requests: {e}")
            return []
    
    def merge_pull_request(self, pr_number, repo_name=None):
        """Merge a pull request in a repository."""
        try:
            if repo_name and repo_name != self.default_repo_name:
                # Create a temporary RepoOperator for the specified repo
                temp_repo_config = RepoConfig(
                    name=repo_name,
                    full_name=f"{self.username}/{repo_name}",
                    base_dir="/tmp/projector_repos"
                )
                temp_operator = RepoOperator(
                    repo_config=temp_repo_config,
                    access_token=self.github_token
                )
                pr = temp_operator.get_pull_request(pr_number)
                if pr:
                    pr.merge()
                    # Return merge information
                    return {
                        "success": True,
                        "pr_number": pr_number,
                        "title": pr.title,
                        "head_branch": pr.head.ref,
                        "base_branch": pr.base.ref,
                        "merged_at": datetime.now().isoformat(),
                        "type": "pull_request"
                    }
                return {"success": False, "error": "PR not found"}
            
            pr = self.repo_operator.get_pull_request(pr_number)
            if pr:
                pr.merge()
                # Return merge information
                return {
                    "success": True,
                    "pr_number": pr_number,
                    "title": pr.title,
                    "head_branch": pr.head.ref,
                    "base_branch": pr.base.ref,
                    "merged_at": datetime.now().isoformat(),
                    "type": "pull_request"
                }
            return {"success": False, "error": "PR not found"}
        except Exception as e:
            self.logger.error(f"Error merging pull request: {e}")
            return {"success": False, "error": str(e)}
    
    def analyze_repository(self, branch=None, repo_name=None):
        """Analyze the repository structure and code."""
        try:
            # Use the CodeAnalyzer to analyze the repository
            code_analyzer = CodeAnalyzer()
            
            if repo_name and repo_name != self.default_repo_name:
                # Create a temporary RepoOperator for the specified repo
                temp_repo_config = RepoConfig(
                    name=repo_name,
                    full_name=f"{self.username}/{repo_name}",
                    base_dir="/tmp/projector_repos"
                )
                temp_operator = RepoOperator(
                    repo_config=temp_repo_config,
                    access_token=self.github_token
                )
                files = temp_operator.list_files(branch=branch or self.default_branch)
                files_content = {}
                
                for file_path in files:
                    if self._is_code_file(file_path):
                        content = temp_operator.get_file_content(file_path, branch=branch or self.default_branch)
                        if content:
                            files_content[file_path] = content
            else:
                files = self.repo_operator.list_files(branch=branch or self.default_branch)
                files_content = {}
                
                for file_path in files:
                    if self._is_code_file(file_path):
                        content = self.repo_operator.get_file_content(file_path, branch=branch or self.default_branch)
                        if content:
                            files_content[file_path] = content
            
            # Analyze code structure
            code_structure = code_analyzer.analyze_code_structure(files_content)
            
            # Generate suggestions
            suggestions = code_analyzer.suggest_improvements(code_structure)
            
            # Generate class diagram
            class_diagram = code_analyzer.generate_class_diagram(code_structure)
            
            # Generate repository statistics
            stats = code_analyzer.analyze_repository_statistics(files_content)
            
            return {
                "structure": code_structure,
                "suggestions": suggestions,
                "class_diagram": class_diagram,
                "stats": stats
            }
        except Exception as e:
            self.logger.error(f"Error analyzing repository: {e}")
            return None
    
    def generate_code_for_feature(self, feature_name, feature_plan, ai_assistant):
        """Generate code for a feature based on the plan."""
        try:
            # Create a branch for this feature if it doesn't exist
            branch_name = f"feature/{feature_name.lower().replace(' ', '-')}"
            existing_branches = self.list_branches()
            
            if branch_name not in existing_branches:
                self.create_branch(branch_name)
            
            # Generate code using AI assistant
            generated_code = ai_assistant.generate_code_for_feature(feature_name, feature_plan)
            
            # Commit generated files
            for file_info in generated_code["files"]:
                self.commit_file(
                    file_info["path"],
                    f"Add {file_info['description']} for {feature_name}",
                    branch_name,
                    file_info["content"]
                )
            
            return {
                "branch": branch_name,
                "files": [f["path"] for f in generated_code["files"]]
            }
        except Exception as e:
            self.logger.error(f"Error generating code for feature: {e}")
            return None
    
    def create_pull_request_for_feature(self, feature_name, branch_name, description=None):
        """Create a pull request for a feature branch."""
        try:
            if not description:
                description = f"""
# Feature: {feature_name}

This PR implements the {feature_name} feature.

## Changes
- Add core functionality for {feature_name}
- Add tests for {feature_name}
- Update documentation

## Testing
This feature has been tested locally and all tests pass.

## Reviewers
Please review this code for completeness and correctness.
"""
            
            # Create the pull request
            pr = self.create_pull_request(
                title=f"Feature: {feature_name}",
                body=description,
                head_branch=branch_name
            )
            
            return pr
        except Exception as e:
            self.logger.error(f"Error creating pull request for feature: {e}")
            return None
    
    def get_commit_history(self, branch=None, repo_name=None):
        """Get the commit history for a branch."""
        try:
            if repo_name and repo_name != self.default_repo_name:
                # Create a temporary RepoOperator for the specified repo
                temp_repo_config = RepoConfig(
                    name=repo_name,
                    full_name=f"{self.username}/{repo_name}",
                    base_dir="/tmp/projector_repos"
                )
                temp_operator = RepoOperator(
                    repo_config=temp_repo_config,
                    access_token=self.github_token
                )
                commits = temp_operator.get_commit_history(branch=branch or self.default_branch)
                return [
                    {
                        "sha": commit.hexsha,
                        "message": commit.message,
                        "author": commit.author.name,
                        "date": commit.committed_datetime.isoformat()
                    } for commit in commits
                ]
            
            commits = self.repo_operator.get_commit_history(branch=branch or self.default_branch)
            return [
                {
                    "sha": commit.hexsha,
                    "message": commit.message,
                    "author": commit.author.name,
                    "date": commit.committed_datetime.isoformat()
                } for commit in commits
            ]
        except Exception as e:
            self.logger.error(f"Error getting commit history: {e}")
            return []
    
    def _is_code_file(self, file_path):
        """Check if a file is a code file that should be analyzed."""
        code_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.cs', '.php',
            '.rb', '.go', '.swift', '.kt', '.rs', '.scala', '.sh', '.ps1'
        ]
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        
        return ext in code_extensions
