import os
import re
import json
import logging
import time
import threading
from typing import Dict, List, Optional, Any

from codegen.agents.chat_agent import ChatAgent
from codegen.agents.planning_agent import PlanningAgent
from codegen.agents.pr_review_agent import PRReviewAgent
from codegen.agents.code_agent import CodeAgent
from codegen.agents.planning.planning import PlanStepStatus

from projector.backend.slack_manager import SlackManager
from projector.backend.github_manager import GitHubManager
from projector.backend.project_database import ProjectDatabase
from projector.backend.project import Project
from projector.backend.planning_manager import PlanningManager
from projector.backend.thread_pool import ThreadPool
from projector.backend.project_manager import ProjectManager

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
        
        # Initialize codegen agents
        self.chat_agent = None
        self.planning_agent = None
        self.pr_review_agent = None
        self.code_agent = None
        
        # Initialize codegen agents if possible
        try:
            # We'll initialize these on demand to save resources
            self.logger.info("Agent initialization ready")
        except Exception as e:
            self.logger.error(f"Error initializing codegen agents: {e}")
        
        # Track processed threads to avoid duplicate responses
        self.processed_threads = set()
        self.thread_lock = threading.Lock()
        
        # Track active projects and their implementation status
        self.active_projects = {}
        self.project_lock = threading.Lock()
    
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
                # For now, we'll use a mock codebase
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
    
    def _initialize_code_agent(self):
        """Initialize the code agent on demand."""
        if self.code_agent is None:
            try:
                # For now, we'll use a mock codebase
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
    
    def process_all_documents(self):
        """Process all markdown documents in the docs directory."""
        if not os.path.exists(self.docs_path):
            self.logger.warning(f"Docs path does not exist: {self.docs_path}")
            return
        
        # Get all markdown files
        md_files = []
        for root, _, files in os.walk(self.docs_path):
            for file in files:
                if file.endswith(".md"):
                    md_files.append(os.path.join(root, file))
        
        self.logger.info(f"Found {len(md_files)} markdown files")
        
        # Process each file
        for md_file in md_files:
            self.thread_pool.submit(self.process_document, md_file)
    
    def process_document(self, file_path):
        """Process a markdown document and extract project information."""
        try:
            self.logger.info(f"Processing document: {file_path}")
            
            # Read the file
            with open(file_path, "r") as f:
                content = f.read()
            
            # Extract project information
            project_info = self._extract_project_info(content, file_path)
            
            if project_info:
                # Check if project already exists
                existing_project = None
                for project in self.project_database.list_projects():
                    if project.name.lower() == project_info["name"].lower():
                        existing_project = project
                        break
                
                if existing_project:
                    # Update existing project
                    self.logger.info(f"Updating existing project: {project_info['name']}")
                    
                    # Update project with new information
                    self.project_manager.update_project(
                        existing_project.id,
                        requirements=project_info.get("requirements", ""),
                        git_url=project_info.get("git_url", existing_project.git_url)
                    )
                    
                    # Add document to project
                    if file_path not in existing_project.documents:
                        existing_project.documents.append(file_path)
                        self.project_database.save_project(existing_project)
                else:
                    # Create new project
                    self.logger.info(f"Creating new project: {project_info['name']}")
                    
                    # Create project
                    project = self.project_manager.add_project(
                        name=project_info["name"],
                        git_url=project_info.get("git_url", ""),
                        slack_channel=project_info.get("slack_channel"),
                        requirements=project_info.get("requirements", "")
                    )
                    
                    # Add document to project
                    project.documents.append(file_path)
                    self.project_database.save_project(project)
            else:
                self.logger.warning(f"No project information found in document: {file_path}")
        
        except Exception as e:
            self.logger.error(f"Error processing document {file_path}: {e}")
    
    def _extract_project_info(self, content, file_path):
        """Extract project information from markdown content."""
        # Initialize project info
        project_info = {}
        
        # Extract project name from filename or content
        filename = os.path.basename(file_path)
        project_name = os.path.splitext(filename)[0]
        
        # Look for project name in content
        name_match = re.search(r"# Project[:\s]+(.+)", content)
        if name_match:
            project_name = name_match.group(1).strip()
        
        project_info["name"] = project_name
        
        # Extract GitHub URL
        git_url_match = re.search(r"GitHub URL[:\s]+(.+)", content) or re.search(r"Repository[:\s]+(.+)", content)
        if git_url_match:
            project_info["git_url"] = git_url_match.group(1).strip()
        
        # Extract Slack channel
        slack_channel_match = re.search(r"Slack Channel[:\s]+(.+)", content)
        if slack_channel_match:
            project_info["slack_channel"] = slack_channel_match.group(1).strip()
        
        # Use the entire content as requirements
        project_info["requirements"] = content
        
        return project_info
    
    def create_implementation_plan(self, project_id):
        """Create an implementation plan for a project."""
        project = self.project_database.get_project(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return None
        
        # Initialize planning agent
        self._initialize_planning_agent()
        
        try:
            # Create plan
            self.logger.info(f"Creating implementation plan for project: {project.name}")
            
            # Generate plan using planning manager
            plan_result = self.project_manager.create_implementation_plan(project_id)
            
            if "error" in plan_result:
                self.logger.error(f"Error creating plan: {plan_result['error']}")
                return None
            
            # Notify in Slack if channel is specified
            if project.slack_channel:
                self.slack_manager.send_message(
                    channel=project.slack_channel,
                    text=f"Implementation plan created for project: *{project.name}*\n\n"
                         f"The plan includes {len(plan_result['features'])} features to implement."
                )
            
            return plan_result
        except Exception as e:
            self.logger.error(f"Error creating implementation plan: {e}")
            return None
    
    def start_project_implementation(self, project_id, max_concurrent_features=None):
        """Start implementing a project."""
        project = self.project_database.get_project(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return None
        
        # Check if project has a plan
        if not project.plan:
            self.logger.error(f"Project has no implementation plan: {project_id}")
            return None
        
        try:
            # Start implementation
            self.logger.info(f"Starting implementation for project: {project.name}")
            
            # Use project manager to start implementation
            result = self.project_manager.start_implementation(
                project_id, 
                max_concurrent_features=max_concurrent_features
            )
            
            if "error" in result:
                self.logger.error(f"Error starting implementation: {result['error']}")
                return None
            
            # Track active project
            with self.project_lock:
                self.active_projects[project_id] = {
                    "status": "implementing",
                    "started_at": time.time(),
                    "active_features": result["active_features"],
                    "pending_features": result["pending_features"]
                }
            
            # Notify in Slack if channel is specified
            if project.slack_channel:
                started_features = result.get("started_features", [])
                features_text = "\n".join([f"• *{feature}*" for feature in started_features])
                
                self.slack_manager.send_message(
                    channel=project.slack_channel,
                    text=f"Started implementation for project: *{project.name}*\n\n"
                         f"Features being implemented:\n{features_text}"
                )
            
            # Send tasks for each started feature
            for feature_name in result.get("started_features", []):
                self.thread_pool.submit(
                    self.project_manager.send_feature_tasks,
                    project_id,
                    feature_name
                )
            
            return result
        except Exception as e:
            self.logger.error(f"Error starting project implementation: {e}")
            return None
    
    def handle_pr_notification(self, project_id, feature_name, pr_url):
        """Handle a PR notification for a feature."""
        project = self.project_database.get_project(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return None
        
        try:
            # Handle PR
            self.logger.info(f"Handling PR for project {project.name}, feature {feature_name}")
            
            # Use project manager to handle PR
            result = self.project_manager.handle_pr_received(
                project_id,
                feature_name,
                pr_url
            )
            
            if "error" in result:
                self.logger.error(f"Error handling PR: {result['error']}")
                return None
            
            return result
        except Exception as e:
            self.logger.error(f"Error handling PR notification: {e}")
            return None
    
    def monitor_slack_threads(self):
        """Monitor Slack threads for new messages."""
        # Get active projects
        with self.project_lock:
            active_project_ids = list(self.active_projects.keys())
        
        for project_id in active_project_ids:
            project = self.project_database.get_project(project_id)
            if not project or not project.slack_channel:
                continue
            
            # Get active threads for this project
            active_threads = project.active_threads
            
            for feature_name, thread_ts in active_threads.items():
                try:
                    # Get messages in thread
                    messages = self.slack_manager.get_thread_messages(
                        channel=project.slack_channel,
                        thread_ts=thread_ts
                    )
                    
                    # Process new messages
                    for message in messages:
                        # Skip messages we've already processed
                        message_ts = message.get("ts")
                        if message_ts in self.processed_threads:
                            continue
                        
                        # Mark as processed
                        with self.thread_lock:
                            self.processed_threads.add(message_ts)
                        
                        # Check for PR links
                        text = message.get("text", "")
                        pr_urls = re.findall(r"https://github\.com/[^/]+/[^/]+/pull/\d+", text)
                        
                        if pr_urls:
                            # Handle PR notification
                            for pr_url in pr_urls:
                                self.thread_pool.submit(
                                    self.handle_pr_notification,
                                    project_id,
                                    feature_name,
                                    pr_url
                                )
                except Exception as e:
                    self.logger.error(f"Error monitoring thread for project {project_id}, feature {feature_name}: {e}")
    
    def process_slack_message(self, message):
        """Process a Slack message and respond if needed."""
        try:
            # Extract message details
            channel = message.get("channel")
            text = message.get("text", "")
            user = message.get("user")
            ts = message.get("ts")
            thread_ts = message.get("thread_ts", ts)
            
            # Skip messages we've already processed
            if ts in self.processed_threads:
                return
            
            # Mark as processed
            with self.thread_lock:
                self.processed_threads.add(ts)
            
            # Check for commands
            if text.startswith("!project"):
                self._handle_project_command(text, channel, thread_ts)
            elif text.startswith("!plan"):
                self._handle_plan_command(text, channel, thread_ts)
            elif text.startswith("!start"):
                self._handle_start_command(text, channel, thread_ts)
            elif text.startswith("!status"):
                self._handle_status_command(text, channel, thread_ts)
            elif text.startswith("!help"):
                self._handle_help_command(channel, thread_ts)
        
        except Exception as e:
            self.logger.error(f"Error processing Slack message: {e}")
    
    def _handle_project_command(self, text, channel, thread_ts):
        """Handle !project command."""
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            self.slack_manager.send_message(
                channel=channel,
                text="Usage: !project list | !project info <project_id>",
                thread_ts=thread_ts
            )
            return
        
        subcommand = parts[1].lower()
        
        if subcommand == "list":
            # List all projects
            projects = self.project_database.list_projects()
            
            if not projects:
                self.slack_manager.send_message(
                    channel=channel,
                    text="No projects found.",
                    thread_ts=thread_ts
                )
                return
            
            # Format project list
            project_list = "\n".join([
                f"• *{project.name}* (ID: {project.id})"
                for project in projects
            ])
            
            self.slack_manager.send_message(
                channel=channel,
                text=f"Projects:\n{project_list}",
                thread_ts=thread_ts
            )
        
        elif subcommand == "info" and len(parts) >= 3:
            # Get project info
            project_id = parts[2]
            project = self.project_database.get_project(project_id)
            
            if not project:
                self.slack_manager.send_message(
                    channel=channel,
                    text=f"Project not found: {project_id}",
                    thread_ts=thread_ts
                )
                return
            
            # Format project info
            info = f"*Project:* {project.name}\n"
            info += f"*ID:* {project.id}\n"
            info += f"*Git URL:* {project.git_url}\n"
            info += f"*Slack Channel:* {project.slack_channel or 'Not set'}\n"
            info += f"*Features:* {len(project.features)}\n"
            
            # Add plan status
            if project.plan:
                info += f"*Plan:* Available\n"
            else:
                info += f"*Plan:* Not created\n"
            
            self.slack_manager.send_message(
                channel=channel,
                text=info,
                thread_ts=thread_ts
            )
        
        else:
            self.slack_manager.send_message(
                channel=channel,
                text="Usage: !project list | !project info <project_id>",
                thread_ts=thread_ts
            )
    
    def _handle_plan_command(self, text, channel, thread_ts):
        """Handle !plan command."""
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            self.slack_manager.send_message(
                channel=channel,
                text="Usage: !plan <project_id>",
                thread_ts=thread_ts
            )
            return
        
        project_id = parts[1]
        project = self.project_database.get_project(project_id)
        
        if not project:
            self.slack_manager.send_message(
                channel=channel,
                text=f"Project not found: {project_id}",
                thread_ts=thread_ts
            )
            return
        
        # Send acknowledgement
        self.slack_manager.send_message(
            channel=channel,
            text=f"Creating implementation plan for project: *{project.name}*...",
            thread_ts=thread_ts
        )
        
        # Create plan in a separate thread
        self.thread_pool.submit(
            self._create_plan_and_notify,
            project_id,
            channel,
            thread_ts
        )
    
    def _create_plan_and_notify(self, project_id, channel, thread_ts):
        """Create a plan and notify in Slack."""
        try:
            # Create plan
            plan_result = self.create_implementation_plan(project_id)
            
            if not plan_result:
                self.slack_manager.send_message(
                    channel=channel,
                    text=f"Failed to create implementation plan for project: {project_id}",
                    thread_ts=thread_ts
                )
                return
            
            # Get project
            project = self.project_database.get_project(project_id)
            
            # Notify success
            features = plan_result.get("features", {})
            feature_list = "\n".join([
                f"• *{name}*: {feature.get('description', 'No description')}"
                for name, feature in features.items()
            ])
            
            self.slack_manager.send_message(
                channel=channel,
                text=f"Implementation plan created for project: *{project.name}*\n\n"
                     f"Features to implement:\n{feature_list}\n\n"
                     f"Use `!start {project_id}` to begin implementation.",
                thread_ts=thread_ts
            )
        
        except Exception as e:
            self.logger.error(f"Error creating plan and notifying: {e}")
            
            self.slack_manager.send_message(
                channel=channel,
                text=f"Error creating implementation plan: {str(e)}",
                thread_ts=thread_ts
            )
    
    def _handle_start_command(self, text, channel, thread_ts):
        """Handle !start command."""
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            self.slack_manager.send_message(
                channel=channel,
                text="Usage: !start <project_id> [max_concurrent_features]",
                thread_ts=thread_ts
            )
            return
        
        project_id = parts[1]
        max_concurrent = int(parts[2]) if len(parts) >= 3 else None
        
        project = self.project_database.get_project(project_id)
        
        if not project:
            self.slack_manager.send_message(
                channel=channel,
                text=f"Project not found: {project_id}",
                thread_ts=thread_ts
            )
            return
        
        # Send acknowledgement
        self.slack_manager.send_message(
            channel=channel,
            text=f"Starting implementation for project: *{project.name}*...",
            thread_ts=thread_ts
        )
        
        # Start implementation in a separate thread
        self.thread_pool.submit(
            self._start_implementation_and_notify,
            project_id,
            max_concurrent,
            channel,
            thread_ts
        )
    
    def _start_implementation_and_notify(self, project_id, max_concurrent, channel, thread_ts):
        """Start implementation and notify in Slack."""
        try:
            # Start implementation
            result = self.start_project_implementation(
                project_id,
                max_concurrent_features=max_concurrent
            )
            
            if not result:
                self.slack_manager.send_message(
                    channel=channel,
                    text=f"Failed to start implementation for project: {project_id}",
                    thread_ts=thread_ts
                )
                return
            
            # Get project
            project = self.project_database.get_project(project_id)
            
            # Notify success
            started_features = result.get("started_features", [])
            features_text = "\n".join([f"• *{feature}*" for feature in started_features])
            
            self.slack_manager.send_message(
                channel=channel,
                text=f"Started implementation for project: *{project.name}*\n\n"
                     f"Features being implemented:\n{features_text}\n\n"
                     f"Tasks will be sent to feature-specific threads.",
                thread_ts=thread_ts
            )
        
        except Exception as e:
            self.logger.error(f"Error starting implementation and notifying: {e}")
            
            self.slack_manager.send_message(
                channel=channel,
                text=f"Error starting implementation: {str(e)}",
                thread_ts=thread_ts
            )
    
    def _handle_status_command(self, text, channel, thread_ts):
        """Handle !status command."""
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            self.slack_manager.send_message(
                channel=channel,
                text="Usage: !status <project_id>",
                thread_ts=thread_ts
            )
            return
        
        project_id = parts[1]
        project = self.project_database.get_project(project_id)
        
        if not project:
            self.slack_manager.send_message(
                channel=channel,
                text=f"Project not found: {project_id}",
                thread_ts=thread_ts
            )
            return
        
        # Get project status
        status = self.project_manager.get_project_status(project_id)
        
        if "error" in status:
            self.slack_manager.send_message(
                channel=channel,
                text=f"Error getting project status: {status['error']}",
                thread_ts=thread_ts
            )
            return
        
        # Format status message
        progress = status.get("progress", {})
        implementation = status.get("implementation", {})
        
        total_features = progress.get("total_features", 0)
        completed_features = progress.get("completed_features", 0)
        in_progress_features = progress.get("in_progress_features", 0)
        pending_features = progress.get("pending_features", 0)
        
        progress_percentage = status.get("progress_percentage", 0)
        
        active_features = implementation.get("active_features", [])
        
        # Create status message
        status_message = f"*Status for project:* {project.name}\n\n"
        status_message += f"*Progress:* {progress_percentage:.1f}%\n"
        status_message += f"*Features:* {completed_features}/{total_features} completed\n"
        status_message += f"*In Progress:* {in_progress_features} features\n"
        status_message += f"*Pending:* {pending_features} features\n\n"
        
        if active_features:
            status_message += "*Currently implementing:*\n"
            for feature in active_features:
                status_message += f"• *{feature}*\n"
        
        self.slack_manager.send_message(
            channel=channel,
            text=status_message,
            thread_ts=thread_ts
        )
    
    def _handle_help_command(self, channel, thread_ts):
        """Handle !help command."""
        help_text = """
*Available Commands:*

• `!project list` - List all projects
• `!project info <project_id>` - Show project details
• `!plan <project_id>` - Create implementation plan for a project
• `!start <project_id> [max_concurrent_features]` - Start project implementation
• `!status <project_id>` - Show project implementation status
• `!help` - Show this help message
"""
        
        self.slack_manager.send_message(
            channel=channel,
            text=help_text,
            thread_ts=thread_ts
        )
