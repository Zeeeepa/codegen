import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import re
import base64

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import API connectors
from api.api_connectors import BackendConnector
from backend.utils import get_priority_emoji, get_status_emoji

def render_sidebar():
    """Render the sidebar navigation."""
    st.sidebar.title("MultiThread Slack GitHub")
    
    # Profile section with connection status
    with st.sidebar.expander("👤 Connection Status", expanded=True):
        if st.session_state.authenticated:
            st.success("✅ **Authenticated**")
            
            # Slack status
            if st.session_state.slack_connected:
                st.success("Connected to Slack")
            else:
                st.error("Disconnected from Slack")
                
            # GitHub status
            if st.session_state.github_connected:
                st.success("Connected to GitHub")
            else:
                st.error("Disconnected from GitHub")
                
            if st.button("Logout", key="logout"):
                st.session_state.authenticated = False
                st.experimental_rerun()
        else:
            st.warning("❌ **Not Authenticated**")
    
    # Navigation
    st.sidebar.header("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Dashboard", "Document Management", "Thread Management", "GitHub Integration", 
         "Project Planning", "AI Assistant"]
    )
    
    # Project selector (if authenticated)
    if st.session_state.authenticated and hasattr(st.session_state, "backend_connector"):
        with st.sidebar.expander("📂 Projects", expanded=True):
            projects = st.session_state.backend_connector.list_projects()
            project_names = ["Select Project"] + [p.name for p in projects]
            
            selected_index = 0
            if st.session_state.get("current_project_id"):
                for i, project in enumerate(projects):
                    if project.id == st.session_state.current_project_id:
                        selected_index = i + 1  # +1 because of "Select Project"
                        break
            
            selected_project = st.selectbox(
                "Active Project", 
                project_names, 
                index=selected_index
            )
            
            if selected_project != "Select Project":
                for project in projects:
                    if project.name == selected_project:
                        st.session_state.current_project_id = project.id
                        break
            
            if st.button("New Project"):
                st.session_state.show_new_project_form = True
    
    # Statistics in sidebar
    if st.session_state.authenticated:
        with st.sidebar.expander("📊 Statistics", expanded=False):
            st.metric("Active Threads", st.session_state.get("thread_count", 0))
            st.metric("Features in Progress", st.session_state.get("features_count", 0))
            st.metric("Documents", st.session_state.get("documents_count", 0))
            st.metric("Open PRs", st.session_state.get("open_prs_count", 0))
    
    return page

def render_auth_page():
    """Render the authentication page."""
    st.title("🔐 Authentication")
    
    with st.form("auth_form"):
        # Slack Authentication
        st.subheader("Slack Authentication")
        slack_token = st.text_input(
            "Slack User Token (xoxp-...)",
            type="password",
            value=st.session_state.get("slack_token", "")
        )
        slack_channel = st.text_input(
            "Default Slack Channel",
            value=st.session_state.get("slack_channel", "general")
        )
        
        # GitHub Authentication
        st.subheader("GitHub Authentication")
        github_token = st.text_input(
            "GitHub Personal Access Token",
            type="password",
            value=st.session_state.get("github_token", "")
        )
        github_username = st.text_input(
            "GitHub Username",
            value=st.session_state.get("github_username", "")
        )
        github_repo = st.text_input(
            "Default GitHub Repository",
            value=st.session_state.get("github_repo", "")
        )
        
        # AI Settings
        st.subheader("AI Assistant Settings")
        ai_enabled = st.checkbox(
            "Enable AI Features",
            value=st.session_state.get("ai_enabled", False)
        )
        openai_api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.get("openai_api_key", ""),
            disabled=not ai_enabled
        )
        
        submitted = st.form_submit_button("Connect")
        
        if submitted:
            if not slack_token or not github_token or not github_username:
                st.error("Please fill in all required fields")
            elif ai_enabled and not openai_api_key:
                st.error("OpenAI API Key is required when AI features are enabled")
            else:
                with st.spinner("Testing connections..."):
                    # Initialize the backend connector
                    connector = BackendConnector(
                        slack_token=slack_token,
                        slack_channel=slack_channel,
                        github_token=github_token,
                        github_username=github_username,
                        github_repo=github_repo,
                        openai_api_key=openai_api_key if ai_enabled else None,
                        ai_enabled=ai_enabled
                    )
                    
                    # Test connections
                    slack_ok = connector.test_slack_connection()
                    github_ok = connector.test_github_connection()
                    
                    # Update session state
                    st.session_state.slack_token = slack_token
                    st.session_state.slack_channel = slack_channel
                    st.session_state.github_token = github_token
                    st.session_state.github_username = github_username
                    st.session_state.github_repo = github_repo
                    st.session_state.openai_api_key = openai_api_key
                    st.session_state.ai_enabled = ai_enabled
                    
                    st.session_state.slack_connected = slack_ok
                    st.session_state.github_connected = github_ok
                    st.session_state.backend_connector = connector
                    
                    if slack_ok and github_ok:
                        st.session_state.authenticated = True
                        st.success("Authentication successful! Redirecting...")
                        time.sleep(1)
                        st.experimental_rerun()
                    else:
                        if not slack_ok:
                            st.error("Failed to connect to Slack. Please check your token.")
                        if not github_ok:
                            st.error("Failed to connect to GitHub. Please check your credentials.")

def render_dashboard():
    """Render the main dashboard."""
    st.title("📊 Dashboard")
    
    # Create columns for KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Threads", st.session_state.get("thread_count", 0))
    with col2:
        st.metric("Features", st.session_state.get("features_count", 0))
    with col3:
        st.metric("Open PRs", st.session_state.get("open_prs_count", 0))
    with col4:
        st.metric("Documents", st.session_state.get("documents_count", 0))
    
    # Create columns for charts
    col1, col2 = st.columns(2)
    
    if hasattr(st.session_state, "backend_connector"):
        connector = st.session_state.backend_connector
        features = connector.get_features()
        
        with col1:
            st.subheader("Feature Status")
            
            if features:
                # Count features by status
                status_counts = {}
                for feature_name, feature_data in features.items():
                    status = feature_data.get("status", "unknown")
                    if status not in status_counts:
                        status_counts[status] = 0
                    status_counts[status] += 1
                
                # Create dataframe for chart
                status_df = pd.DataFrame({
                    "Status": list(status_counts.keys()),
                    "Count": list(status_counts.values())
                })
                
                # Create bar chart
                fig = px.bar(
                    status_df, 
                    x="Status", 
                    y="Count", 
                    title="Feature Status Distribution",
                    color="Status",
                    color_discrete_map={
                        "completed": "green",
                        "in_progress": "blue",
                        "not_started": "gray",
                        "blocked": "red",
                        "testing": "purple",
                        "review": "orange"
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No features found. Process documents to extract features.")
        
        with col2:
            st.subheader("Recent Activity")
            
            # Get recent activities
            activity_data = []
            
            # Check recent thread updates
            threads = connector.get_threads()
            for topic, thread_info in threads.items():
                activity_data.append({
                    "time": datetime.fromtimestamp(thread_info.get("last_updated", 0)),
                    "type": "Thread",
                    "description": f"Update in {topic} thread"
                })
            
            # Check recent PR updates
            pull_requests = connector.list_pull_requests()
            for pr in pull_requests:
                activity_data.append({
                    "time": datetime.fromisoformat(pr.get("created_at").replace("Z", "+00:00")),
                    "type": "GitHub",
                    "description": f"PR #{pr.get('number')}: {pr.get('title')}"
                })
            
            # Sort by time (most recent first)
            activity_data.sort(key=lambda x: x["time"], reverse=True)
            
            # Display recent activities
            if activity_data:
                for activity in activity_data[:5]:  # Show only 5 most recent
                    time_str = activity["time"].strftime("%m/%d %H:%M")
                    icon = "💬" if activity["type"] == "Thread" else "🔄" if activity["type"] == "GitHub" else "📄"
                    st.markdown(f"{time_str} | {icon} **{activity['type']}**: {activity['description']}")
            else:
                st.info("No recent activity.")
    
    # Create columns for active threads and features
    st.subheader("Active Features & Threads")
    col1, col2 = st.columns(2)
    
    if hasattr(st.session_state, "backend_connector"):
        connector = st.session_state.backend_connector
        
        with col1:
            st.markdown("#### Current Features")
            features = connector.get_features()
            if features:
                for feature_name, feature_data in features.items():
                    status = feature_data.get("status", "unknown")
                    status_emoji = get_status_emoji(status)
                    priority = feature_data.get("priority", "medium")
                    priority_emoji = get_priority_emoji(priority)
                    
                    st.markdown(f"{status_emoji} {priority_emoji} **{feature_name}** - *{status}*")
                    
                    # Add action buttons
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button(f"View Details", key=f"view_{feature_name}"):
                            st.session_state.selected_feature = feature_name
                    with col_b:
                        if status != "completed" and st.button(f"Complete", key=f"complete_{feature_name}"):
                            with st.spinner(f"Completing {feature_name}..."):
                                connector.complete_feature(feature_name)
                                st.success(f"Feature {feature_name} completed!")
                                st.experimental_rerun()
                    with col_c:
                        if st.button(f"Generate Code", key=f"gen_{feature_name}"):
                            with st.spinner(f"Generating code for {feature_name}..."):
                                result = connector.generate_code(feature_name)
                                if result:
                                    st.success(f"Code generated for {feature_name}!")
                                else:
                                    st.error(f"Failed to generate code for {feature_name}")
            else:
                st.info("No active features yet.")
        
        with col2:
            st.markdown("#### Recent Threads")
            threads = connector.get_threads()
            if threads:
                for topic, thread_info in list(sorted(threads.items(), key=lambda x: x[1].get("last_updated", 0), reverse=True))[:5]:
                    last_updated = datetime.fromtimestamp(thread_info.get("last_updated", time.time())).strftime("%m/%d %H:%M")
                    
                    # Check if feature exists
                    feature = connector.get_feature(topic)
                    if feature:
                        status = feature.get("status", "unknown")
                        status_emoji = get_status_emoji(status)
                        st.markdown(f"{status_emoji} **{topic}** - Last updated: {last_updated}")
                    else:
                        st.markdown(f"**{topic}** - Last updated: {last_updated}")
                    
                    # Add action button
                    if st.button(f"View Thread", key=f"thread_{topic}"):
                        st.session_state.selected_thread = topic
                        st.session_state.current_page = "Thread Management"
                        st.experimental_rerun()
            else:
                st.info("No active threads yet.")

def render_document_management():
    """Render the document management page."""
    st.title("📄 Document Management")
    
    # Create tabs for different document management functions
    tab1, tab2, tab3 = st.tabs(["Upload Document", "Create Document", "View Documents"])
    
    # Upload Document Tab
    with tab1:
        st.header("Upload Markdown Document")
        uploaded_file = st.file_uploader("Choose a markdown file", type="md")
        
        if uploaded_file is not None:
            # Get the file content
            content = uploaded_file.read().decode("utf-8")
            
            # Display file preview
            st.subheader("Document Preview")
            st.markdown(content)
            
            # Get document name
            doc_name = uploaded_file.name
            
            # Save button
            if st.button("Save Document"):
                if hasattr(st.session_state, "backend_connector"):
                    with st.spinner("Saving document..."):
                        connector = st.session_state.backend_connector
                        success = connector.save_document(doc_name, content)
                        
                        if success:
                            # Update document count
                            if "documents_count" not in st.session_state:
                                st.session_state.documents_count = 0
                            st.session_state.documents_count += 1
                            
                            st.success(f"Document '{doc_name}' saved successfully!")
                            
                            # Process document to extract requirements
                            with st.spinner("Processing document..."):
                                requirements = connector.process_document(doc_name)
                                if requirements:
                                    st.success(f"Document processed successfully. Found {len(requirements.get('features', []))} features.")
                        else:
                            st.error("Failed to save document.")
    
    # Create Document Tab
    with tab2:
        st.header("Create New Document")
        
        doc_title = st.text_input("Document Title")
        
        # Check if document title is provided and add .md extension if missing
        if doc_title and not doc_title.endswith(".md"):
            doc_title += ".md"
        
        doc_content = st.text_area("Document Content", height=300, 
            help="Use markdown format. Start feature sections with ## headings.")
        
        # Preview button
        if st.button("Preview", key="preview_doc") and doc_content:
            st.subheader("Preview")
            st.markdown(doc_content)
        
# Save button
        if st.button("Save", key="save_new_doc") and doc_title and doc_content:
            if hasattr(st.session_state, "backend_connector"):
                with st.spinner("Saving document..."):
                    connector = st.session_state.backend_connector
                    success = connector.save_document(doc_title, doc_content)
                    
                    if success:
                        # Update document count
                        if "documents_count" not in st.session_state:
                            st.session_state.documents_count = 0
                        st.session_state.documents_count += 1
                        
                        st.success(f"Document '{doc_title}' saved successfully!")
                        
                        # Process document to extract requirements
                        with st.spinner("Processing document..."):
                            requirements = connector.process_document(doc_title)
                            if requirements:
                                st.success(f"Document processed successfully. Found {len(requirements.get('features', []))} features.")
                    else:
                        st.error("Failed to save document.")
    
                    pr_data.append({
                        "Number": pr.get("number"),
                        "Title": pr.get("title"),
                        "Status": pr.get("state"),
                        "Branch": pr.get("head").get("ref"),
                        "Created": datetime.fromisoformat(pr.get("created_at").replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
                    })
                
                df = pd.DataFrame(pr_data)
                st.dataframe(df)
                
                # View PR details
                pr_number = st.selectbox("Select PR to view details", [pr.get("number") for pr in pull_requests])
                
                if pr_number:
                    # Find the selected PR
                    selected_pr = next((pr for pr in pull_requests if pr.get("number") == pr_number), None)
                    
                    if selected_pr:
                        st.subheader(f"PR #{pr_number}: {selected_pr.get('title')}")
                        
                        # PR details
                        st.markdown(f"**Status:** {selected_pr.get('state').title()}")
                        st.markdown(f"**Author:** {selected_pr.get('user').get('login')}")
                        st.markdown(f"**Branch:** {selected_pr.get('head').get('ref')} → {selected_pr.get('base').get('ref')}")
                        
                        # PR description
                        st.markdown("#### Description")
                        st.markdown(selected_pr.get("body", "*No description provided*"))
                        
                        # PR actions
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if selected_pr.get("state") == "open" and st.button("Merge PR"):
                                with st.spinner("Merging pull request..."):
                                    success = connector.merge_pull_request(pr_number)
                                    if success:
                                        st.success(f"Pull request #{pr_number} merged successfully!")
                                        st.experimental_rerun()
                                    else:
                                        st.error("Failed to merge pull request.")
                        
                        with col2:
                            if st.button("View on GitHub"):
                                st.markdown(f"[Open PR on GitHub]({selected_pr.get('html_url')})")
            else:
                st.info("No pull requests found.")
    
    # Code Explorer Tab
    with tab3:
        st.header("Code Explorer")
        
        # Get repository information
        if hasattr(st.session_state, "backend_connector"):
            connector = st.session_state.backend_connector
            
            # Get repo name
            repo_name = st.session_state.github_repo
            st.markdown(f"**Repository:** {st.session_state.github_username}/{repo_name}")
            
            # Select branch
            branches = connector.list_branches()
            selected_branch = st.selectbox("Select Branch", branches, index=branches.index("main") if "main" in branches else 0)
            
            if selected_branch:
                # List files in the repository for the selected branch
                files = connector.list_repository_files(selected_branch)
                
                if files:
                    # Display files in a tree-like structure
                    st.markdown("#### Files")
                    
                    selected_file = st.selectbox("Select a file to view", ["<Select a file>"] + files)
                    
                    if selected_file and selected_file != "<Select a file>":
                        # Get file content
                        file_content = connector.get_file_content(selected_file, selected_branch)
                        
                        if file_content:
                            st.markdown(f"**File:** {selected_file}")
                            
                            # Determine file type for syntax highlighting
                            file_extension = selected_file.split(".")[-1] if "." in selected_file else ""
                            
                            # Display file content with proper formatting
                            st.code(file_content, language=file_extension)
                            
                            # File actions
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("Edit File"):
                                    st.session_state.editing_file = selected_file
                                    st.session_state.editing_file_content = file_content
                                    st.session_state.editing_file_branch = selected_branch
                                    st.experimental_rerun()
                            
                            with col2:
                                if st.button("Download File"):
                                    # Create download link
                                    b64 = base64.b64encode(file_content.encode()).decode()
                                    href = f'<a href="data:file/txt;base64,{b64}" download="{selected_file}">Download File</a>'
                                    st.markdown(href, unsafe_allow_html=True)
                        else:
                            st.error("Failed to retrieve file content.")
                else:
                    st.info("No files found in this repository.")
            
            # Check if we're editing a file
            if hasattr(st.session_state, "editing_file") and st.session_state.editing_file:
                st.subheader(f"Editing: {st.session_state.editing_file}")
                
                # Show editor
                edited_content = st.text_area("Edit File", 
                    value=st.session_state.editing_file_content, 
                    height=300)
                
                # Commit message
                commit_message = st.text_input("Commit Message", 
                    value=f"Update {st.session_state.editing_file}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Save Changes"):
                        with st.spinner("Committing changes..."):
                            success = connector.commit_file(
                                st.session_state.editing_file,
                                commit_message,
                                st.session_state.editing_file_branch,
                                edited_content
                            )
                            
                            if success:
                                st.success("Changes committed successfully!")
                                
                                # Clear editing state
                                st.session_state.editing_file = None
                                st.session_state.editing_file_content = None
                                st.session_state.editing_file_branch = None
                                st.experimental_rerun()
                            else:
                                st.error("Failed to commit changes.")
                
                with col2:
                    if st.button("Cancel Editing"):
                        # Clear editing state
                        st.session_state.editing_file = None
                        st.session_state.editing_file_content = None
                        st.session_state.editing_file_branch = None
                        st.experimental_rerun()

def render_planning_page(planning_manager, project_database):
    """Render the planning management page."""
    st.title("📅 Project Planning")
    
    # Create tabs for different planning views
    tab1, tab2, tab3 = st.tabs(["Gantt Chart", "Feature Status", "Create Plan"])
    
    # Check if we have a current project
    if not st.session_state.get("current_project_id"):
        st.warning("Please select or create a project from the sidebar first.")
        return
    
    # Get current project
    project = project_database.get_project(st.session_state.current_project_id)
    if not project:
        st.error("Selected project not found. Please select another project.")
        return
    
    st.subheader(f"Project: {project.name}")
    
    # Gantt Chart Tab
    with tab1:
        st.header("Project Timeline")
        
        if not project.implementation_plan:
            st.info("No implementation plan found for this project. Create a plan in the 'Create Plan' tab.")
        else:
            gantt_data = planning_manager.generate_gantt_chart_data(project.id)
            if gantt_data:
                df = pd.DataFrame(gantt_data)
                
                # Convert string dates to datetime
                df["Start"] = pd.to_datetime(df["Start"])
                df["Finish"] = pd.to_datetime(df["Finish"])
                
                # Create Gantt chart
                fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Status",
                                hover_data=["Priority", "Dependencies", "AssignedTo"])
                fig.update_layout(title="Project Timeline", xaxis_title="Date", yaxis_title="Feature")
                st.plotly_chart(fig, use_container_width=True)
                
                # Legend for status colors
                st.markdown("**Status Legend:**")
                status_colors = {
                    "not_started": "rgb(99, 110, 250)",
                    "in_progress": "rgb(239, 85, 59)",
                    "completed": "rgb(0, 204, 150)",
                    "blocked": "rgb(171, 99, 250)"
                }
                for status, color in status_colors.items():
                    st.markdown(f"<span style='color:{color}'>●</span> {status.replace('_', ' ').title()}", unsafe_allow_html=True)
    
    # Feature Status Tab
    with tab2:
        st.header("Feature Status")
        
        if not project.implementation_plan:
            st.info("No implementation plan found for this project. Create a plan in the 'Create Plan' tab.")
        else:
            # Create feature status table
            feature_data = []
            for feature in project.implementation_plan:
                feature_data.append({
                    "Feature": feature["feature"],
                    "Status": feature["status"],
                    "Priority": feature["priority"],
                    "Start Date": datetime.fromisoformat(feature["start_date"]).strftime("%Y-%m-%d"),
                    "End Date": datetime.fromisoformat(feature["end_date"]).strftime("%Y-%m-%d"),
                    "Duration (days)": feature["duration_days"],
                    "Assigned To": feature.get("assigned_to", "Unassigned"),
                    "ID": feature["id"]
                })
            
            df = pd.DataFrame(feature_data)
            st.dataframe(df)
            
            # Feature assignment section
            st.subheader("Feature Assignment")
            
            # Select feature
            feature_options = [f["feature"] for f in project.implementation_plan]
            selected_feature = st.selectbox("Select Feature", feature_options)
            
            if selected_feature:
                # Find selected feature
                selected_feature_data = next((f for f in project.implementation_plan if f["feature"] == selected_feature), None)
                
                if selected_feature_data:
                    # Display current assigned to
                    st.markdown(f"Currently assigned to: **{selected_feature_data.get('assigned_to', 'Unassigned')}**")
                    
                    # New assignee
                    new_assignee = st.text_input("Assign to")
                    
                    if st.button("Update Assignment") and new_assignee:
                        with st.spinner("Updating assignment..."):
                            success = planning_manager.assign_feature(
                                project.id,
                                selected_feature_data["id"],
                                new_assignee
                            )
                            
                            if success:
                                st.success(f"Feature '{selected_feature}' assigned to {new_assignee} successfully!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to update feature assignment.")
    
    # Create Plan Tab
    with tab3:
        st.header("Create Implementation Plan")
        
        if project.implementation_plan:
            st.warning("This project already has an implementation plan. Creating a new plan will replace the existing one.")
        
        # Get features
        if hasattr(st.session_state, "backend_connector"):
            connector = st.session_state.backend_connector
            features = connector.get_features()
            
            if features:
                st.markdown("### Available Features")
                
                # Display features with checkboxes
                selected_features = []
                for feature_name, feature_data in features.items():
                    if st.checkbox(feature_name, key=f"feature_{feature_name}"):
                        selected_features.append({
                            "name": feature_name,
                            "description": feature_data.get("description", ""),
                            "priority": feature_data.get("priority", "medium"),
                            "dependencies": feature_data.get("dependencies", [])
                        })
                
                if st.button("Create Plan") and selected_features:
                    with st.spinner("Creating implementation plan..."):
                        plan = planning_manager.create_plan_from_features(project.id, selected_features)
                        
                        if plan:
                            st.success("Implementation plan created successfully!")
                            
                            # Create threads for each feature
                            if st.checkbox("Create Slack threads for features", value=True):
                                with st.spinner("Creating Slack threads..."):
                                    thread_results = planning_manager.create_slack_threads_for_features(
                                        project.id,
                                        connector.slack_manager
                                    )
                                    
                                    success_count = sum(1 for result in thread_results.values() if result == "Created")
                                    st.success(f"Created {success_count} Slack threads for features.")
                            
                            # Create GitHub branches for features
                            if st.checkbox("Create GitHub branches for features", value=True):
                                with st.spinner("Creating GitHub branches..."):
                                    branch_results = planning_manager.sync_github_branches_with_features(
                                        project.id,
                                        connector.github_manager
                                    )
                                    
                                    success_count = sum(1 for result in branch_results.values() if result == "Created")
                                    st.success(f"Created {success_count} GitHub branches for features.")
                            
                            st.experimental_rerun()
                        else:
                            st.error("Failed to create implementation plan.")
            else:
                st.info("No features found. Process documents to extract features.")
        else:
            st.error("Backend connector not available.")

def render_thread_management(threads=None, current_thread_id=None, on_thread_select=None, on_thread_create=None, on_thread_delete=None):
    """
    Renders a thread management interface that allows users to view, select, create, and delete conversation threads.
    
    Parameters:
    -----------
    threads : list
        List of thread objects. Each thread should have at least 'id' and 'title' attributes.
    current_thread_id : str or int
        The ID of the currently selected thread.
    on_thread_select : function
        Callback function to be called when a thread is selected. Takes thread_id as parameter.
    on_thread_create : function
        Callback function to be called when a new thread is created. Takes thread_title as parameter.
    on_thread_delete : function
        Callback function to be called when a thread is deleted. Takes thread_id as parameter.
        
    Returns:
    --------
    tuple
        (selected_thread_id, action_performed)
        - selected_thread_id: The ID of the selected thread after user interactions
        - action_performed: String indicating what action was performed ('select', 'create', 'delete', or None)
    """
    import streamlit as st
    from datetime import datetime
    

    # Initialize state variables if needed
    if 'thread_management_expanded' not in st.session_state:
        st.session_state.thread_management_expanded = False
    
    # Default threads list if none provided
    if threads is None:
        threads = []
    
    # Create container for thread management
    thread_container = st.container()
    action_performed = None
    selected_thread_id = current_thread_id
    
    with thread_container:
        # Header with expand/collapse control
        col1, col2 = st.columns([5, 1])
        with col1:
            st.subheader("Thread Management")
        with col2:
            if st.button("➕" if not st.session_state.thread_management_expanded else "➖"):
                st.session_state.thread_management_expanded = not st.session_state.thread_management_expanded
                st.rerun()
        
        # Main thread management interface
        if st.session_state.thread_management_expanded:
            # New thread creation
            with st.expander("Create New Thread", expanded=False):
                with st.form("new_thread_form"):
                    thread_title = st.text_input("Thread Title", placeholder="Enter a title for your new thread")
                    thread_description = st.text_area("Description (optional)", placeholder="Enter an optional description")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        create_submitted = st.form_submit_button("Create Thread")
                    with col2:
                        cancel_create = st.form_submit_button("Cancel")
                    
                    if create_submitted and thread_title:
                        # Call the create callback if provided
                        if on_thread_create:
                            new_thread_id = on_thread_create(thread_title, thread_description)
                            selected_thread_id = new_thread_id
                            action_performed = 'create'
                        st.success(f"Thread '{thread_title}' created successfully!")
                        # Close the expander by rerunning
                        st.rerun()
            
            # Thread listing
            st.write("Your Threads:")
            
            # Display message if no threads exist
            if not threads:
                st.info("You don't have any threads yet. Create one to get started!")
            
            # List all threads with selection and deletion options
            for thread in threads:
                thread_id = thread.get('id')
                thread_title = thread.get('title', f"Thread {thread_id}")
                thread_date = thread.get('created_at', datetime.now()).strftime("%Y-%m-%d %H:%M")
                
                # Highlight the current thread
                highlight = thread_id == current_thread_id
                
                # Create a container for each thread with background color based on selection
                thread_style = f"""
                <style>
                div[data-testid="stHorizontalBlock"].thread-{thread_id} {{
                    background-color: {'#f0f7ff' if highlight else '#ffffff'};
                    border-radius: 5px;
                    padding: 5px;
                    margin-bottom: 5px;
                    border: 1px solid {'#7ab3ef' if highlight else '#e6e6e6'};
                }}
                </style>
                """
                st.markdown(thread_style, unsafe_allow_html=True)
                
                # Thread row with multiple columns
                col1, col2, col3 = st.columns([5, 3, 2])
                
                # Apply custom CSS class for the container
                st.markdown(f'<div class="thread-{thread_id}"></div>', unsafe_allow_html=True)
                
                with col1:
                    if st.button(f"{thread_title}", key=f"select_thread_{thread_id}"):
                        if on_thread_select:
                            on_thread_select(thread_id)
                        selected_thread_id = thread_id
                        action_performed = 'select'
                
                with col2:
                    st.caption(f"Created: {thread_date}")
                
                with col3:
                    if st.button("🗑️", key=f"delete_thread_{thread_id}", help="Delete this thread"):
                        if st.session_state.get(f"confirm_delete_{thread_id}", False):
                            if on_thread_delete:
                                on_thread_delete(thread_id)
                            selected_thread_id = None if selected_thread_id == thread_id else selected_thread_id
                            action_performed = 'delete'
                            # Reset confirmation state
                            st.session_state[f"confirm_delete_{thread_id}"] = False
                            st.rerun()
                        else:
                            # Set confirmation state
                            st.session_state[f"confirm_delete_{thread_id}"] = True
                            st.warning(f"Are you sure you want to delete '{thread_title}'? Click the delete button again to confirm.")
                            st.rerun()
    
    return selected_thread_id, action_performed

def render_github_panel(
    repos=None, 
    current_repo=None, 
    branches=None, 
    current_branch=None, 
    files=None, 
    current_file=None,
    on_repo_select=None,
    on_branch_select=None,
    on_file_select=None,
    on_repo_create=None,
    on_file_create=None,
    on_file_update=None,
    github_token=None
):
    """
    Renders a GitHub panel that allows users to browse repositories, branches, and files.
    Also provides functionality to create/update repositories and files.
    
    Parameters:
    -----------
    repos : list
        List of repository objects. Each repo should have at least 'name' and 'full_name' attributes.
    current_repo : str
        The name of the currently selected repository.
    branches : list
        List of branch objects for the current repository. Each branch should have at least 'name' attribute.
    current_branch : str
        The name of the currently selected branch.
    files : list
        List of file objects for the current branch. Each file should have at least 'name', 'path', and 'type' attributes.
    current_file : str
        The path of the currently selected file.
    on_repo_select : function
        Callback function to be called when a repository is selected. Takes repo_name as parameter.
    on_branch_select : function
        Callback function to be called when a branch is selected. Takes branch_name as parameter.
    on_file_select : function
        Callback function to be called when a file is selected. Takes file_path as parameter.
    on_repo_create : function
        Callback function to be called when a new repository is created. Takes repo_name and is_private as parameters.
    on_file_create : function
        Callback function to be called when a new file is created. Takes file_name, file_content, and commit_message as parameters.
    on_file_update : function
        Callback function to be called when a file is updated. Takes file_path, file_content, and commit_message as parameters.
    github_token : str
        GitHub token for authentication. If not provided, the function will attempt to use the token from config.
        
    Returns:
    --------
    dict
        A dictionary containing the selected repository, branch, and file after user interactions.
    """
    import streamlit as st
    import os
    from datetime import datetime
    
    # Try to get GitHub token from config if not provided
    if github_token is None:
        try:
            from backend.config import get_config
            github_token = get_config("GITHUB_TOKEN")
        except:
            pass
    
    # Initialize state variables if needed
    if 'github_panel_expanded' not in st.session_state:
        st.session_state.github_panel_expanded = True
    if 'create_repo_expanded' not in st.session_state:
        st.session_state.create_repo_expanded = False
    if 'create_file_expanded' not in st.session_state:
        st.session_state.create_file_expanded = False
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'file_content' not in st.session_state:
        st.session_state.file_content = ""
    if 'commit_message' not in st.session_state:
        st.session_state.commit_message = ""
    
    # Default empty lists if none provided
    repos = repos or []
    branches = branches or []
    files = files or []
    
    # Track current selections
    selected_repo = current_repo
    selected_branch = current_branch
    selected_file = current_file
    
    # Create the main container
    github_container = st.container()
    
    with github_container:
        # Header with expand/collapse control
        col1, col2 = st.columns([5, 1])
        with col1:
            st.subheader("GitHub Integration")
        with col2:
            if st.button("➕" if not st.session_state.github_panel_expanded else "➖", key="toggle_github_panel"):
                st.session_state.github_panel_expanded = not st.session_state.github_panel_expanded
                st.rerun()
        
        # Check if GitHub token is available
        if not github_token:
            st.warning("GitHub token not found. Please add a valid GitHub token in your secrets.toml file.")
        
        # Main GitHub panel
        if st.session_state.github_panel_expanded:
            # Repository Management
            st.markdown("### Repositories")
            
            # Create new repository expander
            with st.expander("Create New Repository", expanded=st.session_state.create_repo_expanded):
                with st.form("new_repo_form"):
                    repo_name = st.text_input("Repository Name", placeholder="my-awesome-repo")
                    repo_description = st.text_area("Description (optional)", placeholder="Description of your repository")
                    is_private = st.checkbox("Private Repository", value=True)
                    init_with_readme = st.checkbox("Initialize with README", value=True)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        create_submitted = st.form_submit_button("Create Repository")
                    with col2:
                        cancel_create = st.form_submit_button("Cancel")
                    
                    if create_submitted and repo_name:
                        if on_repo_create:
                            try:
                                new_repo = on_repo_create(repo_name, repo_description, is_private, init_with_readme)
                                st.success(f"Repository '{repo_name}' created successfully!")
                                selected_repo = repo_name
                                # Close the expander
                                st.session_state.create_repo_expanded = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to create repository: {str(e)}")
            
            # Repository selection
            if repos:
                repo_options = [repo.get('name', repo.get('full_name', 'Unknown')) for repo in repos]
                selected_repo_index = 0
                if selected_repo:
                    for i, repo in enumerate(repos):
                        if repo.get('name') == selected_repo or repo.get('full_name') == selected_repo:
                            selected_repo_index = i
                            break
                
                selected_repo_name = st.selectbox(
                    "Select Repository",
                    options=repo_options,
                    index=selected_repo_index,
                    key="repo_selector"
                )
                
                if selected_repo_name != selected_repo:
                    selected_repo = selected_repo_name
                    if on_repo_select:
                        on_repo_select(selected_repo)
                    selected_branch = None
                    selected_file = None
                    st.rerun()
            else:
                st.info("No repositories found. Create a new repository to get started.")
            
            # Branch selection (if a repository is selected)
            if selected_repo and branches:
                st.markdown("### Branches")
                branch_options = [branch.get('name', 'Unknown') for branch in branches]
                selected_branch_index = 0
                if selected_branch:
                    for i, branch in enumerate(branches):
                        if branch.get('name') == selected_branch:
                            selected_branch_index = i
                            break
                
                selected_branch_name = st.selectbox(
                    "Select Branch",
                    options=branch_options,
                    index=selected_branch_index,
                    key="branch_selector"
                )
                
                if selected_branch_name != selected_branch:
                    selected_branch = selected_branch_name
                    if on_branch_select:
                        on_branch_select(selected_branch)
                    selected_file = None
                    st.rerun()
            
            # File browser (if a branch is selected)
            if selected_repo and selected_branch:
                st.markdown("### Files")
                
                # Create new file expander
                with st.expander("Create New File", expanded=st.session_state.create_file_expanded):
                    with st.form("new_file_form"):
                        file_name = st.text_input("File Name", placeholder="example.md")
                        file_content = st.text_area("File Content", height=200)
                        commit_message = st.text_input("Commit Message", placeholder="Add new file")
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            create_file_submitted = st.form_submit_button("Create File")
                        with col2:
                            cancel_file_create = st.form_submit_button("Cancel")
                        
                        if create_file_submitted and file_name and commit_message:
                            if on_file_create:
                                try:
                                    path = file_name
                                    result = on_file_create(selected_repo, selected_branch, path, file_content, commit_message)
                                    st.success(f"File '{file_name}' created successfully!")
                                    # Close the expander
                                    st.session_state.create_file_expanded = False
                                    # Select the new file
                                    selected_file = path
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to create file: {str(e)}")
                
                # File listing
                if files:
                    # Create collapsible tree structure for files
                    file_tree = {}
                    for file in files:
                        path = file.get('path', '')
                        parts = path.split('/')
                        current_level = file_tree
                        for i, part in enumerate(parts):
                            if i == len(parts) - 1:  # Leaf node (file)
                                if part not in current_level:
                                    current_level[part] = {
                                        '_type': file.get('type', 'file'),
                                        '_path': path,
                                        '_size': file.get('size', 0),
                                        '_sha': file.get('sha', '')
                                    }
                            else:  # Directory
                                if part not in current_level:
                                    current_level[part] = {'_type': 'dir', '_path': '/'.join(parts[:i+1])}
                                current_level = current_level[part]
                    
                    # Recursive function to display file tree
                    def display_file_tree(tree, level=0, parent_path=''):
                        for key, value in sorted(tree.items(), key=lambda x: (0 if x[1].get('_type') == 'dir' else 1, x[0])):
                            if key.startswith('_'):  # Skip metadata keys
                                continue
                            
                            is_dir = value.get('_type') == 'dir'
                            path = value.get('_path', f"{parent_path}/{key}" if parent_path else key)
                            
                            # Indentation for visual hierarchy
                            indent = "&nbsp;" * 4 * level
                            icon = "📁" if is_dir else "📄"
                            
                            # File/directory entry
                            col1, col2 = st.columns([9, 1])
                            with col1:
                                if st.button(
                                    f"{indent}{icon} {key}",
                                    key=f"file_{path}",
                                    help=path
                                ):
                                    if not is_dir and on_file_select:
                                        selected_file = path
                                        on_file_select(path)
                                        st.rerun()
                            
                            # For directories, recursively show contents
                            if is_dir:
                                if path == selected_file or any(selected_file and selected_file.startswith(f"{path}/") for file in files if file.get('path') == selected_file):
                                    display_file_tree(value, level + 1, path)
                    
                    # Display the file tree
                    display_file_tree(file_tree)
                else:
                    st.info(f"No files found in {selected_repo}/{selected_branch}.")
            
            # File content display and editing (if a file is selected)
            if selected_file:
                st.markdown("---")
                st.markdown(f"### File: {selected_file}")
                
                # Find current file details
                current_file_details = None
                for file in files:
                    if file.get('path') == selected_file:
                        current_file_details = file
                        break
                
                if current_file_details:
                    file_type = current_file_details.get('type')
                    file_size = current_file_details.get('size', 0)
                    file_sha = current_file_details.get('sha', '')
                    
                    # File metadata
                    st.markdown(f"**Type:** {file_type} | **Size:** {file_size} bytes")
                    
                    # Toggle edit mode
                    edit_mode = st.checkbox("Edit Mode", value=st.session_state.edit_mode, key="toggle_edit_mode")
                    if edit_mode != st.session_state.edit_mode:
                        st.session_state.edit_mode = edit_mode
                        if edit_mode and on_file_select:
                            # Load the file content when entering edit mode
                            on_file_select(selected_file)
                        st.rerun()
                    
                    # Display/edit file content
                    if st.session_state.edit_mode:
                        # Edit mode
                        file_content = st.text_area(
                            "Edit File Content",
                            value=st.session_state.file_content,
                            height=400,
                            key="file_editor"
                        )
                        
                        commit_message = st.text_input(
                            "Commit Message",
                            value=st.session_state.commit_message,
                            placeholder="Update file content",
                            key="commit_msg"
                        )
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("Save Changes", key="save_file"):
                                if file_content and commit_message:
                                    if on_file_update:
                                        try:
                                            result = on_file_update(
                                                selected_repo,
                                                selected_branch,
                                                selected_file,
                                                file_content,
                                                commit_message,
                                                file_sha
                                            )
                                            st.success(f"File '{selected_file}' updated successfully!")
                                            # Exit edit mode
                                            st.session_state.edit_mode = False
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Failed to update file: {str(e)}")
                                else:
                                    st.warning("Please provide both file content and a commit message.")
                        
                        with col2:
                            if st.button("Cancel", key="cancel_edit"):
                                st.session_state.edit_mode = False
                                st.rerun()
                    else:
                        # View mode
                        if st.session_state.file_content:
                            # Determine file extension
                            _, file_extension = os.path.splitext(selected_file)
                            file_extension = file_extension.lstrip('.')
                            
                            # Handle different file types
                            if file_extension.lower() in ['md', 'markdown']:
                                st.markdown("**Preview:**")
                                st.markdown(st.session_state.file_content)
                                st.markdown("**Raw Content:**")
                                st.code(st.session_state.file_content, language="markdown")
                            elif file_extension.lower() in ['py', 'python']:
                                st.code(st.session_state.file_content, language="python")
                            elif file_extension.lower() in ['js', 'javascript']:
                                st.code(st.session_state.file_content, language="javascript")
                            elif file_extension.lower() in ['html', 'htm']:
                                st.code(st.session_state.file_content, language="html")
                            elif file_extension.lower() in ['css']:
                                st.code(st.session_state.file_content, language="css")
                            elif file_extension.lower() in ['json']:
                                st.code(st.session_state.file_content, language="json")
                            else:
                                st.code(st.session_state.file_content)
                        else:
                            if on_file_select:
                                # Load file content
                                on_file_select(selected_file)
                                st.info("Loading file content...")
                                st.rerun()
                else:
                    st.warning(f"File '{selected_file}' not found in the current branch.")
    
    # Return current selections
    return {
        "repo": selected_repo,
        "branch": selected_branch,
        "file": selected_file
    }

def render_ai_assistant_panel(ai_assistant):
    """Render the AI assistant panel."""
    st.title("🤖 AI Assistant")
    
    # Check if AI features are enabled
    if not st.session_state.get("ai_enabled", False):
        st.warning("AI features are not enabled. Please enable them in the authentication page.")
        return
    
    # Create tabs for different AI assistant functions
    tab1, tab2, tab3 = st.tabs(["Document Analysis", "Code Generation", "Repository Analysis"])
    
    # Document Analysis Tab
    with tab1:
        st.header("Document Analysis")
        
        # Select document
        if hasattr(st.session_state, "backend_connector"):
            connector = st.session_state.backend_connector
            documents = connector.list_documents()
            
            if documents:
                selected_doc = st.selectbox("Select Document", ["Select a document"] + documents)
                
                if selected_doc != "Select a document":
                    # Get document content
                    content = connector.get_document_content(selected_doc)
                    
                    # Display document content
                    with st.expander("Document Content", expanded=False):
                        st.markdown(content)
                    
                    # Analyze button
                    if st.button("Analyze Document"):
                        with st.spinner("Analyzing document..."):
                            requirements = connector.process_document(selected_doc)
                            
                            if requirements:
                                st.success(f"Document analyzed successfully. Found {len(requirements.get('features', []))} features.")
                                
                                # Display features
                                st.subheader("Extracted Features")
                                
                                for feature in requirements.get("features", []):
                                    feature_name = feature.get("name", "Unnamed Feature")
                                    priority = feature.get("priority", "medium")
                                    description = feature.get("description", "No description provided.")
                                    
                                    priority_emoji = get_priority_emoji(priority)
                                    
                                    st.markdown(f"{priority_emoji} **{feature_name}** - *{priority}*")
                                    st.markdown(description)
                                    st.markdown("---")
                            else:
                                st.error("Failed to analyze document.")
            else:
                st.info("No documents found. Upload or create a new document to get started.")
    
    # Code Generation Tab
    with tab2:
        st.header("Code Generation")
        
        # Select feature
        if hasattr(st.session_state, "backend_connector"):
            connector = st.session_state.backend_connector
            features = connector.get_features()
            
            if features:
                feature_options = list(features.keys())
                selected_feature = st.selectbox("Select Feature", ["Select a feature"] + feature_options)
                
                if selected_feature != "Select a feature":
                    # Get feature details
                    feature = features[selected_feature]
                    
                    # Display feature details
                    st.markdown(f"**Priority:** {feature.get('priority', 'medium')}")
                    st.markdown(f"**Status:** {feature.get('status', 'not_started')}")
                    st.markdown(f"**Description:** {feature.get('description', 'No description provided.')}")
                    
                    # Generate code button
                    if st.button("Generate Code"):
                        with st.spinner("Generating code..."):
                            result = connector.generate_code(selected_feature)
                            
                            if result:
                                st.success(f"Code generated for {selected_feature}!")
                                
                                # Display generated files
                                st.subheader("Generated Files")
                                
                                for file_path in result.get("files", []):
                                    st.markdown(f"- `{file_path}`")
                            else:
                                st.error(f"Failed to generate code for {selected_feature}")
            else:
                st.info("No features found. Process documents to extract features.")
    
    # Repository Analysis Tab
    with tab3:
        st.header("Repository Analysis")
        
        # Analyze button
        if st.button("Analyze Repository"):
            if hasattr(st.session_state, "backend_connector"):
                connector = st.session_state.backend_connector
                
                with st.spinner("Analyzing repository..."):
                    result = connector.analyze_repository()
                    
                    if result:
                        st.success("Repository analyzed successfully!")
                        
                        # Display analysis results
                        st.subheader("Analysis Results")
                        
                        # Structure overview
                        st.markdown("#### Structure Overview")
                        st.markdown(f"- Total Classes: {len(result.get('structure', {}).get('classes', []))}")
                        st.markdown(f"- Total Functions: {len(result.get('structure', {}).get('functions', []))}")
                        
                        # Complexity metrics
                        st.markdown("#### Complexity Metrics")
                        metrics = result.get("structure", {}).get("complexity_metrics", {})
                        st.markdown(f"- Average Function Length: {metrics.get('avg_function_length', 0):.2f} lines")
                        st.markdown(f"- Average Class Length: {metrics.get('avg_class_length', 0):.2f} lines")
                        st.markdown(f"- Maximum Nesting Depth: {metrics.get('max_nesting_depth', 0)}")
                        
                        # Suggestions
                        st.markdown("#### Improvement Suggestions")
                        for suggestion in result.get("suggestions", []):
                            st.markdown(f"- {suggestion}")
                        
                        # Class diagram
                        st.markdown("#### Class Diagram")
                        st.markdown(f"```mermaid\n{result.get('class_diagram', '')}\n```")
                    else:
                        st.error("Failed to analyze repository.")