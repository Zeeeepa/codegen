"""
AI User Agent for the Projector system.

This agent is responsible for:
1. Analyzing project requirements from markdown documents
2. Creating implementation plans
3. Sending requests to the Assistant Agent via Slack
4. Monitoring project progress and comparing with requirements
5. Formulating follow-up requests when needed
"""
import os
import re
import json
import logging
import time
import threading
from typing import Dict, List, Optional, Any
import uuid

from codegen.agents.chat_agent import ChatAgent
from codegen.agents.planning_agent import PlanningAgent
from codegen.agents.code_agent import CodeAgent

from projector.backend.slack_manager import SlackManager
from projector.backend.github_manager import GitHubManager
from projector.backend.project_database import ProjectDatabase
from projector.backend.project import Project
from projector.backend.planning_manager import PlanningManager
from projector.backend.thread_pool import ThreadPool
from projector.backend.project_manager import ProjectManager

class AIUserAgent:
    """
    AI User Agent that analyzes project requirements, creates implementation plans,
    and sends requests to the Assistant Agent via Slack.
    """
    
    def __init__(
        self,
        slack_manager: SlackManager,
        github_manager: GitHubManager,
        project_database: ProjectDatabase,
        project_manager: ProjectManager,
        thread_pool: ThreadPool,
        docs_path: str = "docs"
    ):
        """Initialize the AI User Agent."""
        self.slack_manager = slack_manager
        self.github_manager = github_manager
        self.project_database = project_database
        self.project_manager = project_manager
        self.thread_pool = thread_pool
        self.docs_path = docs_path
        self.logger = logging.getLogger(__name__)
        
        # Initialize planning manager
        self.planning_manager = PlanningManager(github_manager)
        
        # Initialize codegen agents
        self.planning_agent = None
        self.code_agent = None
        self.chat_agent = None
        
        # Track active projects and their implementation status
        self.active_projects = {}
        self.implementation_status = {}
        
        # Initialize agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize the codegen agents."""
        try:
            # Initialize planning agent
            self.planning_agent = PlanningAgent()
            
            # Initialize code agent
            self.code_agent = CodeAgent()
            
            # Initialize chat agent
            self.chat_agent = ChatAgent()
            
            self.logger.info("AI User Agent initialized successfully.")
        except Exception as e:
            self.logger.error(f"Error initializing AI User Agent: {e}")

    def get_chat_response(self, project_id: str, message: str, chat_history: List[Dict[str, Any]] = None) -> str:
        """
        Get a response from the AI assistant for a chat message.
        
        Args:
            project_id: The ID of the project.
            message: The user message.
            chat_history: Optional chat history.
            
        Returns:
            The AI response.
        """
        project = self.project_database.get_project(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return "Error: Project not found."
        
        try:
            # Initialize chat agent if needed
            if not self.chat_agent:
                self._initialize_agents()
            
            # Get project context
            context = self._get_project_context(project)
            
            # Format the prompt
            prompt = f"""
            Project: {project.name}
            Repository: {project.git_url}
            
            {context}
            
            User message: {message}
            """
            
            # Get response from chat agent
            response = self.chat_agent.run(prompt)
            
            return response
        except Exception as e:
            self.logger.error(f"Error getting chat response: {e}")
            return f"Error: {str(e)}"
    
    def _get_project_context(self, project: Project) -> str:
        """
        Get the context for a project.
        
        Args:
            project: The project.
            
        Returns:
            The project context as a string.
        """
        context = ""
        
        # Add requirements
        if hasattr(project, 'requirements') and project.requirements:
            context += "Requirements:\n"
            for req_key, req_value in project.requirements.items():
                context += f"- {req_key}: {req_value}\n"
        
        # Add implementation plan
        if project.implementation_plan:
            context += "\nImplementation Plan:\n"
            
            # Add plan description
            if 'description' in project.implementation_plan:
                context += f"{project.implementation_plan['description']}\n\n"
            
            # Add tasks
            tasks = project.implementation_plan.get('tasks', [])
            if tasks:
                context += "Tasks:\n"
                for task in tasks:
                    status = task.get('status', 'pending')
                    context += f"- {task.get('title')} ({status})\n"
        
        # Add documents
        if project.documents:
            context += "\nDocuments:\n"
            for doc in project.documents:
                context += f"- {os.path.basename(doc)}\n"
        
        return context
    
    def analyze_project_requirements(self, project_id: str) -> Dict[str, Any]:
        """
        Analyze project requirements from markdown documents.
        
        Args:
            project_id: The ID of the project to analyze.
            
        Returns:
            A dictionary containing the analyzed requirements.
        """
        project = self.project_database.get_project(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return {}
        
        requirements = {}
        
        try:
            # Process each document in the project
            for doc_path in project.documents:
                if not os.path.exists(doc_path):
                    self.logger.warning(f"Document not found: {doc_path}")
                    continue
                
                # Read the document
                with open(doc_path, 'r') as f:
                    content = f.read()
                
                # Extract requirements using the planning agent
                doc_requirements = self.planning_agent.extract_requirements(content)
                
                # Merge with existing requirements
                requirements.update(doc_requirements)
            
            # Store the requirements in the project
            project.requirements = requirements
            self.project_database.save_project(project)
            
            return requirements
        except Exception as e:
            self.logger.error(f"Error analyzing project requirements: {e}")
            return {}
    
    def create_implementation_plan(self, project_id: str) -> Dict[str, Any]:
        """
        Create an implementation plan for the project.
        
        Args:
            project_id: The ID of the project to create a plan for.
            
        Returns:
            The implementation plan as a dictionary.
        """
        project = self.project_database.get_project(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return {}
        
        try:
            # Get the requirements
            requirements = getattr(project, 'requirements', {})
            if not requirements:
                # If requirements not already analyzed, do it now
                requirements = self.analyze_project_requirements(project_id)
            
            # Create the implementation plan
            implementation_plan = self.planning_agent.create_implementation_plan(
                project_name=project.name,
                requirements=requirements,
                max_parallel_tasks=project.max_parallel_tasks
            )
            
            # Store the implementation plan in the project
            project.implementation_plan = implementation_plan
            self.project_database.save_project(project)
            
            # Track the implementation status
            self.implementation_status[project_id] = {
                'plan': implementation_plan,
                'status': 'created',
                'progress': 0,
                'last_updated': time.time()
            }
            
            return implementation_plan
        except Exception as e:
            self.logger.error(f"Error creating implementation plan: {e}")
            return {}
    
    def send_implementation_request(self, project_id: str, task_id: Optional[str] = None) -> bool:
        """
        Send an implementation request to the Assistant Agent via Slack.
        
        Args:
            project_id: The ID of the project to implement.
            task_id: Optional ID of a specific task to implement.
            
        Returns:
            True if the request was sent successfully, False otherwise.
        """
        project = self.project_database.get_project(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return False
        
        try:
            # Get the implementation plan
            implementation_plan = getattr(project, 'implementation_plan', None)
            if not implementation_plan:
                # If plan not already created, create it now
                implementation_plan = self.create_implementation_plan(project_id)
            
            # Determine what to implement
            if task_id:
                # Implement a specific task
                task = next((t for t in implementation_plan.get('tasks', []) 
                           if t.get('id') == task_id), None)
                if not task:
                    self.logger.error(f"Task not found: {task_id}")
                    return False
                
                tasks_to_implement = [task]
            else:
                # Implement all pending tasks
                tasks_to_implement = [
                    t for t in implementation_plan.get('tasks', [])
                    if t.get('status') != 'completed'
                ]
            
            # Send implementation requests for each task
            for task in tasks_to_implement:
                # Format the request message
                message = self._format_implementation_request(project, task)
                
                # Send the message to Slack
                channel = project.slack_channel or self.slack_manager.default_channel
                self.slack_manager.send_message(channel, message)
                
                # Update task status
                task['status'] = 'in_progress'
                task['started_at'] = time.time()
            
            # Update the project
            self.project_database.save_project(project)
            
            return True
        except Exception as e:
            self.logger.error(f"Error sending implementation request: {e}")
            return False
    
    def _format_implementation_request(self, project: Project, task: Dict[str, Any]) -> str:
        """
        Format an implementation request message.
        
        Args:
            project: The project to implement.
            task: The task to implement.
            
        Returns:
            The formatted message.
        """
        # Format the message
        message = f"*Implementation Request*\n\n"
        message += f"*Project:* {project.name}\n"
        message += f"*Task:* {task.get('title')}\n\n"
        message += f"*Description:* {task.get('description')}\n\n"
        
        # Add requirements
        message += "*Requirements:*\n"
        for req in task.get('requirements', []):
            message += f"- {req}\n"
        
        # Add dependencies
        if task.get('dependencies'):
            message += "\n*Dependencies:*\n"
            for dep in task.get('dependencies'):
                message += f"- {dep}\n"
        
        # Add implementation details
        if task.get('implementation_details'):
            message += f"\n*Implementation Details:*\n{task.get('implementation_details')}\n"
        
        # Add GitHub info
        message += f"\n*GitHub Repository:* {project.git_url}\n"
        
        # Add task ID for tracking
        message += f"\n*Task ID:* {task.get('id')}\n"
        
        return message
    
    def monitor_project_progress(self, project_id: str) -> Dict[str, Any]:
        """
        Monitor the progress of a project implementation.
        
        Args:
            project_id: The ID of the project to monitor.
            
        Returns:
            A dictionary containing the project progress.
        """
        project = self.project_database.get_project(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return {}
        
        try:
            # Get the implementation plan
            implementation_plan = getattr(project, 'implementation_plan', {})
            if not implementation_plan:
                return {'status': 'no_plan', 'progress': 0}
            
            # Calculate progress
            tasks = implementation_plan.get('tasks', [])
            if not tasks:
                return {'status': 'no_tasks', 'progress': 0}
            
            completed_tasks = [t for t in tasks if t.get('status') == 'completed']
            in_progress_tasks = [t for t in tasks if t.get('status') == 'in_progress']
            
            progress = len(completed_tasks) / len(tasks) * 100
            
            # Determine status
            if progress == 100:
                status = 'completed'
            elif len(in_progress_tasks) > 0:
                status = 'in_progress'
            elif len(completed_tasks) > 0:
                status = 'partially_completed'
            else:
                status = 'not_started'
            
            # Update implementation status
            self.implementation_status[project_id] = {
                'plan': implementation_plan,
                'status': status,
                'progress': progress,
                'completed_tasks': len(completed_tasks),
                'total_tasks': len(tasks),
                'last_updated': time.time()
            }
            
            return self.implementation_status[project_id]
        except Exception as e:
            self.logger.error(f"Error monitoring project progress: {e}")
            return {}
    
    def compare_with_requirements(self, project_id: str) -> Dict[str, Any]:
        """
        Compare the current project state with the requirements.
        
        Args:
            project_id: The ID of the project to compare.
            
        Returns:
            A dictionary containing the comparison results.
        """
        project = self.project_database.get_project(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return {}
        
        try:
            # Get the requirements and implementation plan
            requirements = getattr(project, 'requirements', {})
            implementation_plan = getattr(project, 'implementation_plan', {})
            
            if not requirements or not implementation_plan:
                return {'status': 'missing_data'}
            
            # Get the current project state from GitHub
            repo_name = project.git_url.split('/')[-1].replace('.git', '')
            repo_owner = project.git_url.split('/')[-2]
            
            # Get the repository contents
            repo_contents = self.github_manager.get_repository_contents(
                owner=repo_owner,
                repo=repo_name
            )
            
            # Compare with requirements
            comparison_results = self.code_agent.compare_with_requirements(
                requirements=requirements,
                implementation=repo_contents
            )
            
            # Store the comparison results
            project.comparison_results = comparison_results
            self.project_database.save_project(project)
            
            return comparison_results
        except Exception as e:
            self.logger.error(f"Error comparing with requirements: {e}")
            return {}
    
    def formulate_follow_up_request(self, project_id: str) -> Optional[str]:
        """
        Formulate a follow-up request based on the comparison results.
        
        Args:
            project_id: The ID of the project to formulate a request for.
            
        Returns:
            The follow-up request message, or None if no follow-up is needed.
        """
        project = self.project_database.get_project(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return None
        
        try:
            # Get the comparison results
            comparison_results = getattr(project, 'comparison_results', {})
            if not comparison_results:
                comparison_results = self.compare_with_requirements(project_id)
            
            # Check if follow-up is needed
            missing_requirements = comparison_results.get('missing_requirements', [])
            incomplete_features = comparison_results.get('incomplete_features', [])
            
            if not missing_requirements and not incomplete_features:
                return None
            
            # Formulate the follow-up request
            message = f"*Follow-up Implementation Request*\n\n"
            message += f"*Project:* {project.name}\n\n"
            
            if missing_requirements:
                message += "*Missing Requirements:*\n"
                for req in missing_requirements:
                    message += f"- {req}\n"
            
            if incomplete_features:
                message += "\n*Incomplete Features:*\n"
                for feature in incomplete_features:
                    message += f"- {feature}\n"
            
            # Add GitHub info
            message += f"\n*GitHub Repository:* {project.git_url}\n"
            
            # Add request ID for tracking
            request_id = str(uuid.uuid4())
            message += f"\n*Request ID:* {request_id}\n"
            
            return message
        except Exception as e:
            self.logger.error(f"Error formulating follow-up request: {e}")
            return None
    
    def handle_merge_event(self, project_id: str, pr_number: int) -> bool:
        """
        Handle a merge event for a project.
        
        Args:
            project_id: The ID of the project.
            pr_number: The PR number that was merged.
            
        Returns:
            True if handled successfully, False otherwise.
        """
        project = self.project_database.get_project(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return False
        
        try:
            # Get PR details
            repo_name = project.git_url.split('/')[-1].replace('.git', '')
            repo_owner = project.git_url.split('/')[-2]
            
            pr_details = self.github_manager.get_pull_request(
                owner=repo_owner,
                repo=repo_name,
                pr_number=pr_number
            )
            
            if not pr_details:
                self.logger.error(f"PR not found: {pr_number}")
                return False
            
            # Update task status if task ID is in PR description
            implementation_plan = getattr(project, 'implementation_plan', {})
            if implementation_plan:
                tasks = implementation_plan.get('tasks', [])
                
                # Look for task ID in PR description
                task_id_match = re.search(r'Task ID: ([a-zA-Z0-9-]+)', pr_details.get('body', ''))
                if task_id_match:
                    task_id = task_id_match.group(1)
                    
                    # Update task status
                    for task in tasks:
                        if task.get('id') == task_id:
                            task['status'] = 'completed'
                            task['completed_at'] = time.time()
                            break
                
                # Update implementation plan
                project.implementation_plan = implementation_plan
                self.project_database.save_project(project)
            
            # Compare with requirements
            comparison_results = self.compare_with_requirements(project_id)
            
            # Send follow-up request if needed
            follow_up_request = self.formulate_follow_up_request(project_id)
            if follow_up_request:
                channel = project.slack_channel or self.slack_manager.default_channel
                self.slack_manager.send_message(channel, follow_up_request)
            
            return True
        except Exception as e:
            self.logger.error(f"Error handling merge event: {e}")
            return False
    
    def start_project_implementation(self, project_id: str) -> bool:
        """
        Start the implementation of a project.
        
        Args:
            project_id: The ID of the project to implement.
            
        Returns:
            True if started successfully, False otherwise.
        """
        project = self.project_database.get_project(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return False
        
        try:
            # Analyze requirements if not already done
            requirements = getattr(project, 'requirements', {})
            if not requirements:
                requirements = self.analyze_project_requirements(project_id)
            
            # Create implementation plan if not already done
            implementation_plan = getattr(project, 'implementation_plan', {})
            if not implementation_plan:
                implementation_plan = self.create_implementation_plan(project_id)
            
            # Send implementation request
            success = self.send_implementation_request(project_id)
            
            # Track active project
            if success:
                self.active_projects[project_id] = {
                    'started_at': time.time(),
                    'status': 'in_progress'
                }
            
            return success
        except Exception as e:
            self.logger.error(f"Error starting project implementation: {e}")
            return False
    
    def add_document_to_project(self, project_id: str, document_path: str) -> bool:
        """
        Add a document to a project.
        
        Args:
            project_id: The ID of the project.
            document_path: The path to the document.
            
        Returns:
            True if added successfully, False otherwise.
        """
        if not os.path.exists(document_path):
            self.logger.error(f"Document not found: {document_path}")
            return False
        
        return self.project_database.add_document_to_project(project_id, document_path)
    
    def initialize_project(self, name: str, git_url: str, slack_channel: Optional[str] = None) -> Optional[str]:
        """
        Initialize a new project.
        
        Args:
            name: The name of the project.
            git_url: The Git URL of the project.
            slack_channel: Optional Slack channel for the project.
            
        Returns:
            The project ID if initialized successfully, None otherwise.
        """
        try:
            # Create the project
            project_id = self.project_database.create_project(name, git_url, slack_channel)
            
            if not project_id:
                self.logger.error("Failed to create project")
                return None
            
            # Initialize project directory
            project_dir = os.path.join(self.docs_path, name)
            os.makedirs(project_dir, exist_ok=True)
            
            # Send initialization message to Slack
            channel = slack_channel or self.slack_manager.default_channel
            message = f"*Project Initialized*\n\n"
            message += f"*Project:* {name}\n"
            message += f"*GitHub Repository:* {git_url}\n"
            message += f"*Project ID:* {project_id}\n\n"
            message += "To add documents to this project, use the UI or API."
            
            self.slack_manager.send_message(channel, message)
            
            return project_id
        except Exception as e:
            self.logger.error(f"Error initializing project: {e}")
            return None