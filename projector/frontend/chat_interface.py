"""
Chat interface component for the Projector system.
"""
import streamlit as st
import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backend components
from projector.backend.project_database import ProjectDatabase
from projector.backend.slack_manager import SlackManager
from projector.backend.github_manager import GitHubManager
from projector.backend.thread_pool import ThreadPool
from projector.backend.project_manager import ProjectManager
from projector.backend.ai_user_agent import AIUserAgent
from projector.backend.config import (
    SLACK_USER_TOKEN, GITHUB_TOKEN, GITHUB_USERNAME,
    SLACK_DEFAULT_CHANNEL, GITHUB_DEFAULT_REPO
)

def render_chat_interface(project_id=None):
    """Render the chat interface.
    
    Args:
        project_id: The ID of the project to render the chat for.
    """
    st.subheader("Project Assistant")
    
    # Initialize chat history in session state if not exists
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    
    # Get project-specific chat history
    if project_id:
        if project_id not in st.session_state.chat_history:
            st.session_state.chat_history[project_id] = []
        chat_history = st.session_state.chat_history[project_id]
        
        # Get project details
        project_database = ProjectDatabase()
        project = project_database.get_project(project_id)
        if project:
            st.write(f"Chatting about project: **{project.name}**")
    else:
        # Global chat history
        if "global" not in st.session_state.chat_history:
            st.session_state.chat_history["global"] = []
        chat_history = st.session_state.chat_history["global"]
        st.write("General chat (no project selected)")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in chat_history:
            if message["role"] == "user":
                st.markdown(f"**You:** {message['content']}")
            elif message["role"] == "assistant":
                st.markdown(f"**Assistant:** {message['content']}")
            elif message["role"] == "system":
                st.info(message["content"])
    
    # Chat input
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area("Type your message:", key="chat_input", height=100)
        cols = st.columns([1, 1, 6])
        with cols[0]:
            upload_file = st.file_uploader("Attach File", key="chat_file_upload")
        with cols[1]:
            code_snippet = st.checkbox("Code Snippet", key="chat_code_snippet")
        with cols[2]:
            submit_button = st.form_submit_button("Send")
    
    if submit_button and user_input:
        # Add user message to chat history
        chat_history.append({"role": "user", "content": user_input})
        
        # Process file upload
        if upload_file:
            file_content = upload_file.getvalue()
            file_name = upload_file.name
            chat_history.append({
                "role": "system",
                "content": f"File uploaded: {file_name}"
            })
        
        # Process code snippet
        if code_snippet:
            user_input = f"```\n{user_input}\n```"
        
        # Get AI response
        if project_id:
            # Get project context
            project_database = ProjectDatabase()
            project = project_database.get_project(project_id)
            
            if project:
                # Initialize AI User Agent
                github_manager = GitHubManager(
                    github_token=GITHUB_TOKEN,
                    github_username=GITHUB_USERNAME,
                    default_repo=GITHUB_DEFAULT_REPO
                )
                
                slack_manager = SlackManager(
                    slack_token=SLACK_USER_TOKEN,
                    default_channel=SLACK_DEFAULT_CHANNEL
                )
                
                thread_pool = ThreadPool(max_threads=10)
                
                project_manager = ProjectManager(
                    github_manager=github_manager,
                    slack_manager=slack_manager,
                    thread_pool=thread_pool
                )
                
                ai_user_agent = AIUserAgent(
                    slack_manager=slack_manager,
                    github_manager=github_manager,
                    project_database=project_database,
                    project_manager=project_manager,
                    thread_pool=thread_pool,
                    docs_path="docs"
                )
                
                # Get AI response with project context
                with st.spinner("Thinking..."):
                    try:
                        response = ai_user_agent.get_chat_response(
                            project_id=project_id,
                            message=user_input,
                            chat_history=chat_history
                        )
                    except Exception as e:
                        response = f"Error: {str(e)}"
            else:
                response = "Error: Project not found."
        else:
            # Generic response without project context
            response = "I'm here to help with your projects. Please select a project to get context-aware assistance."
        
        # Add AI response to chat history
        chat_history.append({"role": "assistant", "content": response})
        
        # Force a rerun to update the chat display
        st.experimental_rerun()

def get_chat_response(project_id, message, chat_history):
    """Get a response from the AI assistant.
    
    Args:
        project_id: The ID of the project.
        message: The user message.
        chat_history: The chat history.
        
    Returns:
        The AI response.
    """
    # This is a placeholder for the actual AI response logic
    # In a real implementation, this would call an LLM API
    return f"I received your message about project {project_id}: {message}"