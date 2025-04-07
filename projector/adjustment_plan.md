# Projector: Adjustment Plan

## Overview

This document outlines a comprehensive adjustment plan for the Projector program based on the UI mockup and additional feature requirements. The plan includes detailed UI adjustments and implementation strategies for core features.

## Core Features Implementation Plan

### 1. Multi-Project Tab Creation

#### Current State
The current Projector implementation allows managing multiple projects but doesn't support a tabbed interface for switching between projects in the main UI.

#### Implementation Plan
1. **Frontend Changes**:
   - Modify `streamlit_app.py` to implement a tabbed interface using Streamlit's tab components
   - Create a dynamic tab generation system based on active projects
   - Implement tab state persistence using session state

2. **Backend Changes**:
   - Enhance `ProjectDatabase` to support efficient retrieval of multiple projects
   - Implement caching for project data to improve performance with many projects
   - Add support for project grouping and categorization

3. **UI Components**:
   - Create a new `TabManager` class to handle tab creation and switching
   - Implement tab-specific context management
   - Add visual indicators for project status in tabs

```python
# Example implementation in streamlit_app.py
def render_project_tabs():
    """Render tabs for all active projects."""
    project_database = ProjectDatabase()
    projects = project_database.list_projects()
    
    if not projects:
        st.info("No projects found. Create a new project to get started.")
        return
    
    # Create tabs for each project
    tabs = st.tabs([p.name for p in projects])
    
    # Render content for each tab
    for i, tab in enumerate(tabs):
        with tab:
            render_project_content(projects[i])
```

### 2. Dynamic Concurrency Settings

#### Current State
The current implementation has a fixed concurrency setting (`max_parallel_tasks`) in the Project class, but it's not dynamically adjustable through the UI.

#### Implementation Plan
1. **Frontend Changes**:
   - Add a concurrency settings panel to the project settings page
   - Implement a slider or input field for adjusting concurrency (1-10)
   - Add visual feedback showing current concurrent tasks

2. **Backend Changes**:
   - Modify `ThreadPool` to support dynamic resizing
   - Implement project-specific thread pools
   - Add concurrency monitoring and throttling

3. **UI Components**:
   - Create a concurrency dashboard showing active tasks
   - Implement visual indicators for thread utilization
   - Add performance metrics for concurrent operations

```python
# Example implementation in project_ui.py
def render_concurrency_settings(project_id):
    """Render concurrency settings for a project."""
    project_database = ProjectDatabase()
    project = project_database.get_project(project_id)
    
    if not project:
        st.error("Project not found.")
        return
    
    st.subheader("Concurrency Settings")
    
    # Concurrency slider
    new_concurrency = st.slider(
        "Maximum Concurrent Tasks",
        min_value=1,
        max_value=10,
        value=project.max_parallel_tasks,
        help="Set the maximum number of tasks that can be processed concurrently."
    )
    
    if new_concurrency != project.max_parallel_tasks:
        project.max_parallel_tasks = new_concurrency
        if project_database.save_project(project):
            st.success(f"Concurrency updated to {new_concurrency} tasks.")
        else:
            st.error("Failed to update concurrency settings.")
    
    # Display current concurrent tasks
    st.subheader("Active Concurrent Tasks")
    active_tasks = len(project.active_threads)
    st.progress(min(1.0, active_tasks / new_concurrency))
    st.write(f"Currently running: {active_tasks}/{new_concurrency} tasks")
```

### 3. Custom Document Management

#### Current State
The current implementation allows adding documents to projects but lacks comprehensive document management features.

#### Implementation Plan
1. **Frontend Changes**:
   - Create a dedicated document management page
   - Implement document upload, viewing, and organization
   - Add document categorization and tagging

2. **Backend Changes**:
   - Enhance `ProjectDatabase` to support document metadata
   - Implement document parsing and indexing
   - Add support for different document types (Markdown, PDF, etc.)

3. **UI Components**:
   - Create a document browser with preview capabilities
   - Implement a document editor for in-app modifications
   - Add document version control

```python
# Example implementation in document_management_ui.py
def render_document_management(project_id):
    """Render document management UI for a project."""
    project_database = ProjectDatabase()
    project = project_database.get_project(project_id)
    
    if not project:
        st.error("Project not found.")
        return
    
    st.subheader(f"Document Management for: {project.name}")
    
    # Document upload
    st.write("### Upload New Document")
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=["md", "txt", "pdf", "docx"],
        help="Upload project documentation, requirements, or specifications."
    )
    
    if uploaded_file:
        # Process and save the document
        doc_type = uploaded_file.name.split(".")[-1]
        doc_category = st.selectbox(
            "Document Category",
            ["Requirements", "Architecture", "Implementation", "Testing", "Other"]
        )
        
        if st.button("Save Document"):
            # Save document logic
            docs_dir = os.path.join("docs", project.name, doc_category.lower())
            os.makedirs(docs_dir, exist_ok=True)
            
            file_path = os.path.join(docs_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Add document metadata
            doc_metadata = {
                "path": file_path,
                "type": doc_type,
                "category": doc_category,
                "uploaded_at": datetime.now().isoformat(),
                "size": len(uploaded_file.getbuffer())
            }
            
            # Add to project
            if project_database.add_document_to_project(project_id, file_path, metadata=doc_metadata):
                st.success(f"Document '{uploaded_file.name}' uploaded successfully!")
            else:
                st.error("Failed to add document to project.")
    
    # Document browser
    st.write("### Project Documents")
    if not project.documents:
        st.info("No documents found. Upload documents to get started.")
    else:
        # Group documents by category
        docs_by_category = {}
        for doc in project.documents:
            if isinstance(doc, dict) and "category" in doc:
                category = doc["category"]
                if category not in docs_by_category:
                    docs_by_category[category] = []
                docs_by_category[category].append(doc)
            else:
                # Legacy document format
                if "Other" not in docs_by_category:
                    docs_by_category["Other"] = []
                docs_by_category["Other"].append({"path": doc})
        
        # Display documents by category
        for category, docs in docs_by_category.items():
            with st.expander(f"{category} ({len(docs)})"):
                for doc in docs:
                    doc_path = doc["path"] if isinstance(doc, dict) else doc
                    doc_name = os.path.basename(doc_path)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{doc_name}**")
                    with col2:
                        if st.button(f"View {doc_name}", key=f"view_{doc_path}"):
                            # View document logic
                            try:
                                with open(doc_path, "r") as f:
                                    content = f.read()
                                st.markdown(content)
                            except Exception as e:
                                st.error(f"Error reading document: {e}")
                    with col3:
                        if st.button(f"Delete {doc_name}", key=f"delete_{doc_path}"):
                            # Delete document logic
                            if project_database.remove_document_from_project(project_id, doc_path):
                                st.success(f"Document '{doc_name}' deleted successfully!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to delete document.")
```

### 4. Implementation Tree View

#### Current State
The current implementation lacks a hierarchical tree view for visualizing project structure and task completion status.

#### Implementation Plan
1. **Frontend Changes**:
   - Create a dedicated tree view component
   - Implement expandable/collapsible nodes
   - Add checkboxes for completion status

2. **Backend Changes**:
   - Enhance `Project` class to support hierarchical task structure
   - Implement task dependency tracking
   - Add completion status validation

3. **UI Components**:
   - Create a tree renderer with custom styling
   - Implement interactive node management
   - Add progress indicators for each level

```python
# Example implementation in tree_view.py
def render_implementation_tree(project_id):
    """Render the implementation tree for a project."""
    project_database = ProjectDatabase()
    project = project_database.get_project(project_id)
    
    if not project:
        st.error("Project not found.")
        return
    
    st.subheader(f"Implementation Tree for: {project.name}")
    
    # Check if the project has an implementation plan
    implementation_plan = getattr(project, 'implementation_plan', None)
    
    if not implementation_plan:
        st.info("No implementation plan found. Generate a plan to get started.")
        return
    
    # Get tasks
    tasks = implementation_plan.get('tasks', [])
    
    if not tasks:
        st.info("No tasks found in the implementation plan.")
        return
    
    # Build task hierarchy
    task_hierarchy = build_task_hierarchy(tasks)
    
    # Render the tree
    render_task_tree(task_hierarchy, project_id, project_database)

def build_task_hierarchy(tasks):
    """Build a hierarchical structure from flat task list."""
    # Create a dictionary of tasks by ID
    task_dict = {task['id']: task for task in tasks}
    
    # Create a dictionary to store children
    children = {task['id']: [] for task in tasks}
    
    # Identify root tasks and build parent-child relationships
    root_tasks = []
    for task in tasks:
        dependencies = task.get('dependencies', [])
        if not dependencies:
            root_tasks.append(task)
        else:
            for dep_id in dependencies:
                if dep_id in children:
                    children[dep_id].append(task['id'])
    
    # Build the hierarchy
    def build_subtree(task_id):
        task = task_dict[task_id].copy()
        task['children'] = [build_subtree(child_id) for child_id in children[task_id]]
        return task
    
    return [build_subtree(task['id']) for task in root_tasks]

def render_task_tree(task_hierarchy, project_id, project_database, level=0):
    """Recursively render the task tree."""
    for task in task_hierarchy:
        # Calculate completion status
        status = task.get('status', 'pending')
        has_children = bool(task.get('children', []))
        
        # Determine if all children are complete
        all_children_complete = True
        if has_children:
            for child in task['children']:
                if child.get('status', 'pending') != 'completed':
                    all_children_complete = False
                    break
        
        # Create indentation
        indent = "│   " * level
        prefix = "├── " if level > 0 else ""
        
        # Render task with checkbox
        col1, col2 = st.columns([10, 1])
        with col1:
            if has_children:
                expander = st.expander(f"{indent}{prefix}{task['title']}")
                with expander:
                    render_task_tree(task['children'], project_id, project_database, level + 1)
            else:
                st.write(f"{indent}{prefix}{task['title']}")
        
        with col2:
            # Only allow marking as complete if all children are complete
            checkbox_disabled = has_children and not all_children_complete
            
            # Create a unique key for the checkbox
            checkbox_key = f"task_{task['id']}_checkbox"
            
            # Render the checkbox
            checked = st.checkbox(
                "",
                value=(status == 'completed'),
                key=checkbox_key,
                disabled=checkbox_disabled,
                help="Mark task as completed" if not checkbox_disabled else "Complete all subtasks first"
            )
            
            # Update task status if checkbox changed
            if checked != (status == 'completed'):
                new_status = 'completed' if checked else 'pending'
                update_task_status(task['id'], new_status, project_id, project_database)
                st.experimental_rerun()

def update_task_status(task_id, status, project_id, project_database):
    """Update the status of a task."""
    project = project_database.get_project(project_id)
    
    if not project or not project.implementation_plan:
        return False
    
    # Update the task status
    tasks = project.implementation_plan.get('tasks', [])
    for task in tasks:
        if task['id'] == task_id:
            task['status'] = status
            if status == 'completed':
                task['completed_at'] = datetime.now().timestamp()
            break
    
    # Save the updated project
    project.implementation_plan['tasks'] = tasks
    return project_database.save_project(project)
```

### 5. Enhanced Chat Interface

#### Current State
The current implementation has a basic chat interface but lacks project-specific context and advanced features.

#### Implementation Plan
1. **Frontend Changes**:
   - Create a dedicated chat interface component
   - Implement project-specific chat contexts
   - Add support for code snippets and file attachments

2. **Backend Changes**:
   - Enhance AI integration for context-aware responses
   - Implement chat history persistence
   - Add support for command shortcuts

3. **UI Components**:
   - Create a chat window with message threading
   - Implement syntax highlighting for code
   - Add typing indicators and presence awareness

```python
# Example implementation in chat_interface.py
def render_chat_interface(project_id=None):
    """Render the chat interface."""
    st.subheader("Project Assistant")
    
    # Initialize chat history in session state if not exists
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    
    # Get project-specific chat history
    if project_id:
        if project_id not in st.session_state.chat_history:
            st.session_state.chat_history[project_id] = []
        chat_history = st.session_state.chat_history[project_id]
    else:
        # Global chat history
        if "global" not in st.session_state.chat_history:
            st.session_state.chat_history["global"] = []
        chat_history = st.session_state.chat_history["global"]
    
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
                from projector.backend.slack_manager import SlackManager
                from projector.backend.github_manager import GitHubManager
                from projector.backend.thread_pool import ThreadPool
                from projector.backend.project_manager import ProjectManager
                from projector.backend.config import (
                    SLACK_USER_TOKEN, GITHUB_TOKEN, GITHUB_USERNAME,
                    SLACK_DEFAULT_CHANNEL, GITHUB_DEFAULT_REPO
                )
                
                # Initialize components
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
                    response = ai_user_agent.get_chat_response(
                        project_id=project_id,
                        message=user_input,
                        chat_history=chat_history
                    )
            else:
                response = "Error: Project not found."
        else:
            # Generic response without project context
            response = "I'm here to help with your projects. Please select a project to get context-aware assistance."
        
        # Add AI response to chat history
        chat_history.append({"role": "assistant", "content": response})
        
        # Force a rerun to update the chat display
        st.experimental_rerun()
```

## UI Mockup Adjustments

### Main Dashboard Layout

```
+---------------------------------------------------------+
|             [Dashboard]                 [Add_Project]+  |
+---------------+-----------------------------------------+
|               | [Project1]|[Project2]|...|[ProjectN]    |
|               |                         |              |
|               | Project's context       |Tree Structure|
|  Step by step |   document View         |   View       |
|  Structure    |   (Tabbed Interface)    |   Component  |
| View generated|                         | Integration   |
|  from user's  |                         | Completion   |
|   documents   |Concurrency      project |   Check map  |
|               |[1-10]         [Settings]| [✓] -done    |
+---------------+-------------------------+--------------+
|                                                        |
|                  Chat Interface                        |
|                                                        |
+--------------------------------------------------------+
```

### Implementation Changes

1. **Main Layout Structure**:
   - Modify `streamlit_app.py` to implement the three-panel layout
   - Create collapsible sidebars for the left and right panels
   - Implement responsive design for different screen sizes

2. **Project Tabs**:
   - Implement horizontal scrolling for many project tabs
   - Add visual indicators for project status in tabs
   - Implement tab persistence across sessions

3. **Tree Structure View**:
   - Create a custom tree component with checkboxes
   - Implement hierarchical task visualization
   - Add progress indicators for each level

4. **Chat Interface**:
   - Implement a fixed-position chat panel at the bottom
   - Add support for markdown, code snippets, and file attachments
   - Implement context-aware responses based on selected project

## Implementation Roadmap

### Phase 1: Core Infrastructure (Weeks 1-2)
1. Enhance `Project` and `ProjectDatabase` classes to support new features
2. Implement dynamic thread pool management
3. Create the basic three-panel layout structure

### Phase 2: Multi-Project Support (Weeks 3-4)
1. Implement project tabs with context switching
2. Enhance project creation and management
3. Add project grouping and filtering

### Phase 3: Implementation Tree View (Weeks 5-6)
1. Create the hierarchical task structure
2. Implement the tree visualization component
3. Add task completion tracking and validation

### Phase 4: Enhanced Chat Interface (Weeks 7-8)
1. Implement the chat UI component
2. Add context-aware AI responses
3. Integrate with project-specific actions

### Phase 5: Document Management (Weeks 9-10)
1. Enhance document upload and organization
2. Implement document parsing and indexing
3. Add document version control

### Phase 6: Testing and Refinement (Weeks 11-12)
1. Comprehensive testing with multiple projects
2. Performance optimization for large projects
3. UI refinements based on user feedback

## Conclusion

This adjustment plan provides a comprehensive roadmap for enhancing the Projector program to meet the requirements specified in the UI mockup. The implementation focuses on core features like multi-project tab creation, dynamic concurrency settings, custom document management, implementation tree view, and enhanced chat interface.

By following this plan, the Projector program will be transformed into a powerful project management tool that can handle multiple projects simultaneously, provide clear visualization of project progress, and facilitate collaboration through an intuitive interface.