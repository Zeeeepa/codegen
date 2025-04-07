import os
import re
import json
import logging
import time
import threading
from typing import Dict, List, Optional, Any

from agentgen.agents.chat_agent import ChatAgent
from agentgen.agents.planning_agent import PlanningAgent
from agentgen.agents.pr_review_agent import PRReviewAgent
from agentgen.agents.code_agent import CodeAgent
from agentgen.utils.reflection import Reflector
from agentgen.utils.web_search import WebSearcher
from agentgen.utils.context_understanding import ContextUnderstanding

from agentgen.application.projector.backend.slack_manager import SlackManager
from agentgen.application.projector.backend.github_manager import GitHubManager
from agentgen.application.projector.backend.project_database import ProjectDatabase
from agentgen.application.projector.backend.project import Project
from agentgen.application.projector.backend.planning_manager import PlanningManager
from agentgen.application.projector.backend.thread_pool import ThreadPool
from agentgen.application.projector.backend.project_manager import ProjectManager

class AssistantAgent:
    """Agent that processes markdown documents and responds to Slack messages."""
    
    def __init__(
        self,
        slack_manager: SlackManager,
        github_manager: GitHubManager,
        docs_path: str,
        project_database: ProjectDatabase,
        project_manager: ProjectManager,
        max_threads: int = 10
    ):
        """Initialize the assistant agent."""
        self.slack_manager = slack_manager
        self.github_manager = github_manager
        self.docs_path = docs_path
        self.project_database = project_database
        self.project_manager = project_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize thread pool for concurrent processing
        self.thread_pool = ThreadPool(max_threads)
        
        # Initialize planning manager
        self.planning_manager = PlanningManager(github_manager)
        
        # Initialize agentgen agents
        self.chat_agent = None
        self.planning_agent = None
        self.pr_review_agent = None
        self.code_agent = None
        self.reflector = None
        self.web_searcher = None
        self.context_understanding = None
        
        # Initialize agentgen agents if possible
        try:
            # We'll initialize these on demand to save resources
            self.logger.info("Agent initialization ready")
        except Exception as e:
            self.logger.error(f"Error initializing agentgen agents: {e}")
        
        # Track processed threads to avoid duplicate responses
        self.processed_threads = set()
        self.thread_lock = threading.Lock()
    
    def _initialize_chat_agent(self):
        """Initialize the chat agent on demand."""
        if self.chat_agent is None:
            try:
                # For now, we'll use a mock codebase since we're not directly using code analysis
                # In a real implementation, you'd create a proper codebase object
                mock_codebase = type('MockCodebase', (), {})()
                self.chat_agent = ChatAgent(
                    codebase=mock_codebase,
                    model_provider="anthropic",
                    model_name="claude-3-5-sonnet-latest"
                )
                self.logger.info("Chat agent initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing chat agent: {e}")
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
    
    def _initialize_pr_review_agent(self):
        """Initialize the PR review agent on demand."""
        if self.pr_review_agent is None:
            try:
                # For now, we'll use a mock codebase since we're not directly using code analysis
                # In a real implementation, you'd create a proper codebase object
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
    
    def _initialize_code_agent(self):
        """Initialize the code agent on demand."""
        if self.code_agent is None:
            try:
                # For now, we'll use a mock codebase since we're not directly using code analysis
                mock_codebase = type('MockCodebase', (), {})()
                self.code_agent = CodeAgent(
                    codebase=mock_codebase,
                    model_provider="anthropic",
                    model_name="claude-3-5-sonnet-latest"
                )
                self.logger.info("Code agent initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing code agent: {e}")
                raise
    
    def _initialize_reflector(self):
        """Initialize the reflector on demand."""
        if self.reflector is None:
            try:
                self.reflector = Reflector(
                    model_provider="anthropic",
                    model_name="claude-3-5-sonnet-latest"
                )
                self.logger.info("Reflector initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing reflector: {e}")
                raise
    
    def _initialize_web_searcher(self):
        """Initialize the web searcher on demand."""
        if self.web_searcher is None:
            try:
                self.web_searcher = WebSearcher()
                self.logger.info("Web searcher initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing web searcher: {e}")
                raise
    
    def _initialize_context_understanding(self):
        """Initialize the context understanding on demand."""
        if self.context_understanding is None:
            try:
                self.context_understanding = ContextUnderstanding(
                    model_provider="anthropic",
                    model_name="claude-3-5-sonnet-latest"
                )
                self.logger.info("Context understanding initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing context understanding: {e}")
                raise

    def process_all_documents(self):
        """Process all markdown documents in the docs directory."""
        if not os.path.exists(self.docs_path):
            self.logger.warning(f"Docs path {self.docs_path} does not exist")
            return
        
        for filename in os.listdir(self.docs_path):
            if filename.endswith(".md"):
                file_path = os.path.join(self.docs_path, filename)
                self.process_document(file_path)
    
    def process_document(self, file_path: str):
        """Process a markdown document and create a project plan."""
        try:
            self.logger.info(f"Processing document: {file_path}")
            
            # Read the document
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract project name from filename
            project_name = os.path.basename(file_path).replace(".md", "")
            
            # Initialize planning agent if needed
            self._initialize_planning_agent()
            
            # Initialize context understanding if needed
            self._initialize_context_understanding()
            
            # Use context understanding to extract key information
            context_info = self.context_understanding.analyze_document(content)
            
            # Generate a plan using the planning agent
            thread_id = f"doc_{project_name}"
            plan_prompt = f"""
            Create a detailed implementation plan for the following project requirements:
            
            {content}
            
            Context information:
            {json.dumps(context_info, indent=2)}
            
            The plan should include:
            1. A breakdown of the main features
            2. Step-by-step implementation tasks
            3. Technical requirements
            4. GitHub branch structure
            5. Timeline estimates
            """
            
            plan_response = self.planning_agent.run(plan_prompt, thread_id=thread_id)
            
            # Extract GitHub repository URL from content if available
            git_url = None
            git_url_match = re.search(r"(github\.com/[\w-]+/[\w-]+)", content)
            if git_url_match:
                git_url = f"https://{git_url_match.group(1)}"
            else:
                git_url = f"https://github.com/{self.github_manager.username}/{project_name.lower()}"
            
            # Extract Slack channel from content if available
            slack_channel = None
            slack_channel_match = re.search(r"slack channel[:\s]+#?([\w-]+)", content, re.IGNORECASE)
            if slack_channel_match:
                slack_channel = slack_channel_match.group(1)
            else:
                slack_channel = self.slack_manager.default_channel
            
            # Create a new project using the project manager
            project_id = self.project_manager.add_project(
                name=project_name,
                git_url=git_url,
                slack_channel=slack_channel,
                requirements=content,
                plan=plan_response
            )
            
            self.logger.info(f"Created project plan for {project_name} with ID {project_id}")
            return project_id
        
        except Exception as e:
            self.logger.error(f"Error processing document {file_path}: {e}")
            return None
    
    def handle_slack_message(self, channel_id: str, thread_ts: Optional[str], user_id: str, text: str):
        """Handle a Slack message and generate a response."""
        try:
            # Check if we've already processed this thread
            thread_key = f"{channel_id}:{thread_ts or 'new'}"
            with self.thread_lock:
                if thread_key in self.processed_threads:
                    self.logger.info(f"Skipping already processed thread: {thread_key}")
                    return
                self.processed_threads.add(thread_key)
            
            # Submit the task to the thread pool
            self.thread_pool.submit(
                self._process_slack_message,
                channel_id,
                thread_ts,
                user_id,
                text
            )
        
        except Exception as e:
            self.logger.error(f"Error handling Slack message: {e}")
            self.slack_manager.send_message(
                channel_id,
                "I encountered an error processing your request. Please try again later.",
                thread_ts=thread_ts
            )
    
    def _process_slack_message(self, channel_id: str, thread_ts: Optional[str], user_id: str, text: str):
        """Process a Slack message in a separate thread."""
        try:
            # Initialize chat agent if needed
            self._initialize_chat_agent()
            
            # Get user info
            user_info = self.slack_manager.get_user_info(user_id)
            user_name = user_info.get("real_name", "User")
            
            # Generate a thread ID for the chat agent
            thread_id = thread_ts or f"slack_{channel_id}_{int(time.time())}"
            
            # Check for specific command patterns
            
            # Project creation command
            project_match = re.search(r"create\s+project\s+(?:called\s+)?[\"\']?([^\"\']+)[\"\']?", text, re.IGNORECASE)
            if project_match:
                project_name = project_match.group(1).strip()
                self._handle_project_creation(channel_id, thread_ts, user_name, project_name, text)
                return
            
            # PR tracking command
            pr_track_match = re.search(r"track\s+PR\s+#?(\d+)", text, re.IGNORECASE)
            if pr_track_match:
                pr_number = int(pr_track_match.group(1))
                self._handle_pr_tracking(channel_id, thread_ts, pr_number, text)
                return
            
            # PR validation command
            pr_validate_match = re.search(r"validate\s+PR\s+#?(\d+)", text, re.IGNORECASE)
            if pr_validate_match:
                pr_number = int(pr_validate_match.group(1))
                self._handle_pr_validation(channel_id, thread_ts, pr_number)
                return
            
            # PR review command
            pr_review_match = re.search(r"review\s+PR\s+#?(\d+)", text, re.IGNORECASE)
            if pr_review_match:
                pr_number = int(pr_review_match.group(1))
                self._handle_pr_review(channel_id, thread_ts, pr_number)
                return
            
            # Progress report command
            progress_match = re.search(r"progress\s+report\s+(?:for\s+)?[\"\']?([^\"\']+)[\"\']?", text, re.IGNORECASE)
            if progress_match:
                project_name = progress_match.group(1).strip()
                self._handle_progress_report(channel_id, thread_ts, project_name)
                return
            
            # Next requirement command
            next_req_match = re.search(r"next\s+requirement\s+(?:for\s+)?[\"\']?([^\"\']+)[\"\']?", text, re.IGNORECASE)
            if next_req_match:
                project_name = next_req_match.group(1).strip()
                self._handle_next_requirement(channel_id, thread_ts, project_name)
                return
            
            # Research command
            research_match = re.search(r"research\s+(?:about\s+)?[\"\']?([^\"\']+)[\"\']?", text, re.IGNORECASE)
            if research_match:
                topic = research_match.group(1).strip()
                self._handle_research_request(channel_id, thread_ts, topic)
                return
            
            # Project planning command
            if "plan" in text.lower() and "project" in text.lower():
                self._handle_project_planning(channel_id, thread_ts, user_name, text)
                return
            
            # If no specific command is detected, use the chat agent to generate a response
            self._initialize_reflector()
            
            # First, reflect on the message to understand the intent
            reflection = self.reflector.reflect(text)
            
            # Generate a response using the chat agent
            response = self.chat_agent.run(
                f"""
                User message: {text}
                
                Reflection on intent: {reflection}
                
                Please provide a helpful response to the user's message.
                """,
                thread_id=thread_id
            )
            
            # Send the response
            self.slack_manager.send_message(
                channel_id,
                response,
                thread_ts=thread_ts
            )
        
        except Exception as e:
            self.logger.error(f"Error processing Slack message: {e}")
            self.slack_manager.send_message(
                channel_id,
                f"I encountered an error processing your message: {str(e)}",
                thread_ts=thread_ts
            )
    
    def _handle_project_creation(self, channel_id: str, thread_ts: Optional[str], user_name: str, project_name: str, text: str):
        """Handle a project creation request."""
        try:
            # Extract requirements from the message
            requirements = text
            
            # Initialize planning agent if needed
            self._initialize_planning_agent()
            
            # Generate a plan
            thread_id = f"project_{project_name}_{int(time.time())}"
            plan_prompt = f"""
            Create a detailed implementation plan for the following project:
            
            Project Name: {project_name}
            Requirements: {requirements}
            
            The plan should include:
            1. A breakdown of the main features
            2. Step-by-step implementation tasks
            3. Technical requirements
            4. GitHub branch structure
            5. Timeline estimates
            """
            
            # Send acknowledgment
            self.slack_manager.send_message(
                channel_id,
                f"Creating project plan for '{project_name}'. This may take a moment...",
                thread_ts=thread_ts
            )
            
            plan_response = self.planning_agent.run(plan_prompt, thread_id=thread_id)
            
            # Create a default GitHub URL
            git_url = f"https://github.com/{self.github_manager.username}/{project_name.lower().replace(' ', '-')}"
            
            # Create the project
            project_id = self.project_manager.add_project(
                name=project_name,
                git_url=git_url,
                slack_channel=channel_id,
                requirements=requirements,
                plan=plan_response
            )
            
            # Send the response
            self.slack_manager.send_message(
                channel_id,
                f"✅ Project '{project_name}' created successfully!\n\nProject ID: {project_id}\nGitHub URL: {git_url}\n\n**Project Plan:**\n\n{plan_response}",
                thread_ts=thread_ts
            )
        
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            self.slack_manager.send_message(
                channel_id,
                f"I encountered an error creating the project: {str(e)}",
                thread_ts=thread_ts
            )
    
    def _handle_pr_tracking(self, channel_id: str, thread_ts: Optional[str], pr_number: int, text: str):
        """Handle a PR tracking request."""
        try:
            # Find the project by name
            project_id = None
            for p_id, project in self.project_manager.projects.items():
                if project.name.lower() == project_name.lower():
                    project_id = p_id
                    break
            
            if not project_id:
                self.slack_manager.send_message(
                    channel_id,
                    f"❌ Project '{project_name}' not found. Please check the project name and try again.",
                    thread_ts=thread_ts
                )
                return
            
            # Get repository name from git_url
            project = self.project_manager.get_project(project_id)
            repo_parts = project.git_url.split("/")
            repo_name = repo_parts[-1].replace(".git", "") if repo_parts[-1].endswith(".git") else repo_parts[-1]
            
            # Get PR details from GitHub
            pr_details = self.github_manager.get_pull_request(pr_number, repo_name)
            
            if not pr_details:
                self.slack_manager.send_message(
                    channel_id,
                    f"❌ PR #{pr_number} not found in repository {repo_name}.",
                    thread_ts=thread_ts
                )
                return
            
            # Extract feature name from PR title
            feature_name = pr_details.get("title", f"Feature from PR #{pr_number}")
            
            # Track the PR
            result = self.project_manager.track_pr(
                project_id,
                pr_number,
                pr_details.get("url", f"https://github.com/{self.github_manager.username}/{repo_name}/pull/{pr_number}"),
                feature_name,
                pr_details.get("state", "open")
            )
            
            if result:
                self.slack_manager.send_message(
                    channel_id,
                    f"✅ PR #{pr_number} is now being tracked for project '{project_name}'.\n\nFeature: {feature_name}\nStatus: {pr_details.get('state', 'open').upper()}",
                    thread_ts=thread_ts
                )
            else:
                self.slack_manager.send_message(
                    channel_id,
                    f"❌ Failed to track PR #{pr_number} for project '{project_name}'.",
                    thread_ts=thread_ts
                )
        
        except Exception as e:
            self.logger.error(f"Error tracking PR: {e}")
            self.slack_manager.send_message(
                channel_id,
                f"I encountered an error tracking the PR: {str(e)}",
                thread_ts=thread_ts
            )
    
    def _handle_pr_validation(self, channel_id: str, thread_ts: Optional[str], pr_number: int):
        """Handle a PR validation request."""
        try:
            # Find the project by name
            project_id = None
            for p_id, project in self.project_manager.projects.items():
                if project.name.lower() == project_name.lower():
                    project_id = p_id
                    break
            
            if not project_id:
                self.slack_manager.send_message(
                    channel_id,
                    f"❌ Project '{project_name}' not found. Please check the project name and try again.",
                    thread_ts=thread_ts
                )
                return
            
            # Send acknowledgment
            self.slack_manager.send_message(
                channel_id,
                f"🔍 Validating PR #{pr_number} for project '{project_name}'. This may take a moment...",
                thread_ts=thread_ts
            )
            
            # Start validation
            result = self.project_manager.validate_pr_against_requirements(project_id, pr_number)
            
            if result.get("error"):
                self.slack_manager.send_message(
                    channel_id,
                    f"❌ Error validating PR: {result['error']}",
                    thread_ts=thread_ts
                )
            else:
                self.slack_manager.send_message(
                    channel_id,
                    f"✅ Validation started for PR #{pr_number}. You will be notified when the validation is complete.",
                    thread_ts=thread_ts
                )
        
        except Exception as e:
            self.logger.error(f"Error validating PR: {e}")
            self.slack_manager.send_message(
                channel_id,
                f"I encountered an error validating the PR: {str(e)}",
                thread_ts=thread_ts
            )
    
    def _handle_progress_report(self, channel_id: str, thread_ts: Optional[str], project_name: str):
        """Handle a progress report request."""
        try:
            # Find the project by name
            project_id = None
            for p_id, project in self.project_manager.projects.items():
                if project.name.lower() == project_name.lower():
                    project_id = p_id
                    break
            
            if not project_id:
                self.slack_manager.send_message(
                    channel_id,
                    f"❌ Project '{project_name}' not found. Please check the project name and try again.",
                    thread_ts=thread_ts
                )
                return
            
            # Generate progress report
            result = self.project_manager.generate_progress_report(project_id)
            
            if result.get("error"):
                self.slack_manager.send_message(
                    channel_id,
                    f"❌ Error generating progress report: {result['error']}",
                    thread_ts=thread_ts
                )
            else:
                self.slack_manager.send_message(
                    channel_id,
                    result["report"],
                    thread_ts=thread_ts
                )
        
        except Exception as e:
            self.logger.error(f"Error generating progress report: {e}")
            self.slack_manager.send_message(
                channel_id,
                f"I encountered an error generating the progress report: {str(e)}",
                thread_ts=thread_ts
            )
    
    def _handle_next_requirement(self, channel_id: str, thread_ts: Optional[str], project_name: str):
        """Handle a next requirement request."""
        try:
            # Find the project by name
            project_id = None
            for p_id, project in self.project_manager.projects.items():
                if project.name.lower() == project_name.lower():
                    project_id = p_id
                    break
            
            if not project_id:
                self.slack_manager.send_message(
                    channel_id,
                    f"❌ Project '{project_name}' not found. Please check the project name and try again.",
                    thread_ts=thread_ts
                )
                return
            
            # Send next requirement
            result = self.project_manager.send_next_requirement(project_id)
            
            if result.get("error"):
                self.slack_manager.send_message(
                    channel_id,
                    f"❌ Error sending next requirement: {result['error']}",
                    thread_ts=thread_ts
                )
            else:
                # The requirement is sent directly by the project manager
                pass
        
        except Exception as e:
            self.logger.error(f"Error sending next requirement: {e}")
            self.slack_manager.send_message(
                channel_id,
                f"I encountered an error sending the next requirement: {str(e)}",
                thread_ts=thread_ts
            )
    
    def _handle_pr_review(self, channel_id: str, thread_ts: Optional[str], pr_number: int):
        """Handle a PR review request."""
        try:
            # Initialize PR review agent if needed
            self._initialize_pr_review_agent()
            
            # Get the repository name from the GitHub manager
            repo_name = f"{self.github_manager.username}/{self.github_manager.default_repo_name}"
            
            # Send an acknowledgment message
            self.slack_manager.send_message(
                channel_id,
                f"I'm reviewing PR #{pr_number} now. This may take a few moments...",
                thread_ts=thread_ts
            )
            
            # Review the PR
            review_result = self.pr_review_agent.review_pr(repo_name, pr_number)
            
            # Format the review result
            if review_result.get("compliant", False):
                status = "✅ This PR complies with project requirements."
            else:
                status = "❌ This PR does not fully comply with project requirements."
            
            issues = review_result.get("issues", [])
            issues_text = "\n".join([f"- {issue}" for issue in issues]) if issues else "No issues found."
            
            suggestions = review_result.get("suggestions", [])
            suggestions_text = ""
            if suggestions:
                for suggestion in suggestions:
                    if isinstance(suggestion, dict):
                        desc = suggestion.get("description", "")
                        file_path = suggestion.get("file_path")
                        line_number = suggestion.get("line_number")
                        
                        if file_path and line_number:
                            suggestions_text += f"- {desc} (in `{file_path}` at line {line_number})\n"
                        elif file_path:
                            suggestions_text += f"- {desc} (in `{file_path}`)\n"
                        else:
                            suggestions_text += f"- {desc}\n"
                    else:
                        suggestions_text += f"- {suggestion}\n"
            else:
                suggestions_text = "No suggestions."
            
            # Send the review result
            review_message = f"""
            # PR Review for #{pr_number}
            
            {status}
            
            ## Issues
            {issues_text}
            
            ## Suggestions
            {suggestions_text}
            
            ## Recommendation
            {review_result.get('approval_recommendation', 'No recommendation provided.')}
            """
            
            self.slack_manager.send_message(
                channel_id,
                review_message,
                thread_ts=thread_ts
            )
        
        except Exception as e:
            self.logger.error(f"Error handling PR review: {e}")
            self.slack_manager.send_message(
                channel_id,
                f"I encountered an error reviewing PR #{pr_number}. Please try again later.",
                thread_ts=thread_ts
            )
    
    def _handle_project_planning(self, channel_id: str, thread_ts: Optional[str], user_name: str, text: str):
        """Handle a project planning request."""
        try:
            # Initialize planning agent if needed
            self._initialize_planning_agent()
            
            # Generate a thread ID
            thread_id = f"plan_{int(time.time())}"
            
            # Generate a plan
            plan_prompt = f"""
            Create a detailed implementation plan for the following project requirements:
            
            {text}
            
            The plan should include:
            1. A breakdown of the main features
            2. Step-by-step implementation tasks
            3. Technical requirements
            4. GitHub branch structure
            5. Timeline estimates
            """
            
            # Send acknowledgment
            self.slack_manager.send_message(
                channel_id,
                "Generating a project plan. This may take a moment...",
                thread_ts=thread_ts
            )
            
            plan_response = self.planning_agent.run(plan_prompt, thread_id=thread_id)
            
            # Extract project name from text
            project_name_match = re.search(r"project\s+(?:called|named)\s+[\"']?([^\"']+)[\"']?", text, re.IGNORECASE)
            project_name = project_name_match.group(1).strip() if project_name_match else f"Project_{int(time.time())}"
            
            # Create a default GitHub URL
            git_url = f"https://github.com/{self.github_manager.username}/{project_name.lower().replace(' ', '-')}"
            
            # Create the project
            project_id = self.project_manager.add_project(
                name=project_name,
                git_url=git_url,
                slack_channel=channel_id,
                requirements=text,
                plan=plan_response
            )
            
            # Send the plan to Slack
            self.slack_manager.send_message(
                channel_id,
                f"I've created a project plan for you:\n\n{plan_response}\n\nThe project has been saved with ID: {project_id}",
                thread_ts=thread_ts
            )
        
        except Exception as e:
            self.logger.error(f"Error handling project planning: {e}")
            self.slack_manager.send_message(
                channel_id,
                f"I encountered an error generating the project plan: {str(e)}",
                thread_ts=thread_ts
            )
    
    def monitor_slack_threads(self):
        """Monitor Slack threads for new messages."""
        try:
            # Get recent messages from the default channel
            recent_messages = self.slack_manager.get_recent_messages()
            
            for message in recent_messages:
                # Skip messages from bots or the assistant itself
                if message.get("bot_id") or message.get("user") == self.slack_manager.bot_user_id:
                    continue
                
                channel_id = message.get("channel")
                thread_ts = message.get("thread_ts", message.get("ts"))
                user_id = message.get("user")
                text = message.get("text", "")
                
                # Handle the message
                self.handle_slack_message(channel_id, thread_ts, user_id, text)
        
        except Exception as e:
            self.logger.error(f"Error monitoring Slack threads: {e}")
    
    def _handle_research_request(self, channel_id: str, thread_ts: Optional[str], topic: str):
        """Handle a research request."""
        try:
            # Initialize web searcher if needed
            self._initialize_web_searcher()
            
            # Send acknowledgment
            self.slack_manager.send_message(
                channel_id,
                f"Researching information about '{topic}'. This may take a moment...",
                thread_ts=thread_ts
            )
            
            # Perform web search
            search_results = self.web_searcher.search(topic, max_results=5)
            
            # Format results
            if not search_results or len(search_results) == 0:
                self.slack_manager.send_message(
                    channel_id,
                    f"I couldn't find any information about '{topic}'. Please try a different search term.",
                    thread_ts=thread_ts
                )
                return
            
            # Format the search results
            message = f"# Research Results: {topic}\n\n"
            
            for i, result in enumerate(search_results):
                message += f"## {i+1}. {result.get('title', 'Untitled')}\n"
                message += f"Source: {result.get('url', 'No URL')}\n\n"
                message += f"{result.get('snippet', 'No snippet available')}\n\n"
            
            # Add a summary if we have a chat agent
            self._initialize_chat_agent()
            summary = self.chat_agent.run(
                f"""
                Summarize the following research results about '{topic}':
                
                {message}
                
                Provide a concise summary of the key points.
                """,
                thread_id=f"research_{topic}"
            )
            
            message += f"## Summary\n{summary}\n"
            
            # Send the results
            self.slack_manager.send_message(
                channel_id,
                message,
                thread_ts=thread_ts
            )
        
        except Exception as e:
            self.logger.error(f"Error handling research request: {e}")
            self.slack_manager.send_message(
                channel_id,
                f"I encountered an error researching '{topic}': {str(e)}",
                thread_ts=thread_ts
            )
