"""
AI User Agent for the Projector system.

This agent is responsible for:
1. Analyzing project requirements from markdown documents
2. Creating implementation plans
3. Sending requests to the Assistant Agent via Slack
4. Monitoring project progress and comparing with requirements
5. Formulating follow-up requests when needed
6. Providing chat responses for project-specific questions
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
                
                # Add document content for context
                try:
                    with open(doc, 'r') as f:
                        content = f.read()
                        # Add a summary or excerpt of the document
                        excerpt = content[:500] + "..." if len(content) > 500 else content
                        context += f"\nExcerpt from {os.path.basename(doc)}:\n{excerpt}\n"
                except Exception as e:
                    self.logger.error(f"Error reading document {doc}: {e}")
        
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