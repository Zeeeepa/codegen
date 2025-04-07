"""
Project Management UI component for the Projector application.
This module implements the UI for the project management feature.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import time
from .session_state import set_error_message, set_success_message

def render_project_management_ui():
    """Render the project management UI."""
    st.title("Project Management")
    
    # Create tabs for different views
    tabs = st.tabs(["Overview", "Tree Structure", "Diagram View", "Chat Interface"])
    
    with tabs[0]:
        render_overview_tab()
    
    with tabs[1]:
        render_tree_structure_tab()
    
    with tabs[2]:
        render_diagram_view_tab()
    
    with tabs[3]:
        render_chat_interface_tab()

def render_overview_tab():
    """Render the overview tab."""
    st.header("Project Overview")
    
    # Project creation form
    with st.expander("Create New Project", expanded=not st.session_state.get("current_project_id")):
        col1, col2 = st.columns(2)
        
        with col1:
            project_name = st.text_input("Project Name", key="new_project_name")
            github_url = st.text_input("GitHub URL", key="new_project_github_url")
        
        with col2:
            slack_channel = st.text_input("Slack Channel", key="new_project_slack_channel")
            documentation_url = st.text_input("Documentation URL", key="new_project_docs_url")
        
        # File uploader for documentation
        uploaded_file = st.file_uploader("Upload Documentation", type=["md", "txt", "pdf"])
        
        if st.button("Initialize Project"):
            if not project_name:
                set_error_message("Project name is required")
            elif not github_url:
                set_error_message("GitHub URL is required")
            elif not slack_channel:
                set_error_message("Slack channel is required")
            else:
                # Show a spinner while "processing"
                with st.spinner("Initializing project..."):
                    # Simulate processing time
                    time.sleep(2)
                    
                    # In a real implementation, this would call the backend to create the project
                    # For now, we'll just update the session state
                    st.session_state.current_project_id = "proj-" + str(int(time.time()))
                    st.session_state.show_new_project_form = False
                    
                    # Update project counters
                    if "team_members_count" not in st.session_state:
                        st.session_state.team_members_count = 0
                    
                    set_success_message(f"Project '{project_name}' initialized successfully!")
                    st.experimental_rerun()
    
    # If a project is selected, show project details
    if st.session_state.get("current_project_id"):
        # Project status card
        st.subheader("Project Status")
        
        # Create metrics in a row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Completion", "42%", "+5%")
        
        with col2:
            st.metric("Features", "12", "+2")
        
        with col3:
            st.metric("Open PRs", "5", "-1")
        
        with col4:
            st.metric("Team Members", st.session_state.get("team_members_count", 0))
        
        # Project timeline
        st.subheader("Implementation Timeline")
        
        # Sample data for the timeline
        df = pd.DataFrame([
            {"Task": "Requirements Analysis", "Start": "2025-03-01", "End": "2025-03-15", "Completion": 100},
            {"Task": "Architecture Design", "Start": "2025-03-10", "End": "2025-03-25", "Completion": 85},
            {"Task": "Frontend Development", "Start": "2025-03-20", "End": "2025-04-15", "Completion": 60},
            {"Task": "Backend Development", "Start": "2025-03-20", "End": "2025-04-20", "Completion": 45},
            {"Task": "Integration", "Start": "2025-04-10", "End": "2025-04-30", "Completion": 20},
            {"Task": "Testing", "Start": "2025-04-15", "End": "2025-05-10", "Completion": 10},
            {"Task": "Deployment", "Start": "2025-05-05", "End": "2025-05-15", "Completion": 0}
        ])
        
        # Convert dates to datetime
        df["Start"] = pd.to_datetime(df["Start"])
        df["End"] = pd.to_datetime(df["End"])
        
        # Create a Gantt chart
        fig = px.timeline(
            df, 
            x_start="Start", 
            x_end="End", 
            y="Task",
            color="Completion",
            color_continuous_scale="Viridis",
            title="Project Timeline"
        )
        
        # Add completion markers
        for i, row in df.iterrows():
            if row["Completion"] > 0:
                # Calculate the position based on completion percentage
                position = row["Start"] + (row["End"] - row["Start"]) * row["Completion"] / 100
                
                fig.add_trace(
                    go.Scatter(
                        x=[position],
                        y=[row["Task"]],
                        mode="markers",
                        marker=dict(symbol="line-ns", size=20, color="red"),
                        name=f"{row['Completion']}% Complete",
                        showlegend=False
                    )
                )
        
        # Update layout
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Task",
            height=400,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity
        st.subheader("Recent Activity")
        
        # Sample data for recent activity
        activities = [
            {"time": "Today 10:30 AM", "user": "AI Assistant", "action": "Generated implementation plan for user authentication"},
            {"time": "Today 09:15 AM", "user": "John Doe", "action": "Merged PR #42: Add login form"},
            {"time": "Yesterday 4:20 PM", "user": "Jane Smith", "action": "Created new feature request: Password reset"},
            {"time": "Yesterday 2:10 PM", "user": "AI Assistant", "action": "Analyzed requirements document"},
            {"time": "2025-04-05", "user": "Mike Johnson", "action": "Initialized project repository"}
        ]
        
        for activity in activities:
            st.markdown(f"**{activity['time']}** - {activity['user']}: {activity['action']}")
            st.markdown("---")

def render_tree_structure_tab():
    """Render the tree structure tab."""
    st.header("Project Structure")
    
    # Create a two-column layout
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Tree View")
        
        # Sample tree data
        tree_data = {
            "Project Name": {
                "Frontend": {
                    "Components": {
                        "Header": {},
                        "Sidebar": {},
                        "Main Content": {},
                        "Footer": {}
                    },
                    "Pages": {
                        "Home": {},
                        "Dashboard": {},
                        "Settings": {}
                    },
                    "State Management": {
                        "Context": {},
                        "Redux Store": {}
                    }
                },
                "Backend": {
                    "API Endpoints": {
                        "User Management": {},
                        "Project Management": {},
                        "Data Services": {}
                    },
                    "Database Models": {
                        "User": {},
                        "Project": {},
                        "Diagram": {}
                    },
                    "Services": {
                        "Authentication": {},
                        "Planning": {},
                        "Diagram Generation": {}
                    }
                },
                "Deployment": {
                    "Development": {},
                    "Staging": {},
                    "Production": {}
                }
            }
        }
        
        # Function to recursively render the tree
        def render_tree(data, indent=0):
            for key, value in data.items():
                is_expanded = st.checkbox(
                    "  " * indent + ("▶ " if value else "  ") + key,
                    value=indent < 1,  # Auto-expand first level
                    key=f"tree_{key}_{indent}"
                )
                if value and is_expanded:
                    render_tree(value, indent + 1)
        
        render_tree(tree_data)
    
    with col2:
        st.subheader("Component Details")
        
        # Sample component details
        st.markdown("""
        ### Frontend Components
        
        The frontend is built using React with the following structure:
        
        - **Components**: Reusable UI elements
          - Header: Application header with navigation
          - Sidebar: Navigation sidebar with filters
          - Main Content: Primary content area
          - Footer: Application footer with links
        
        - **Pages**: Application views
          - Home: Landing page
          - Dashboard: Main dashboard with metrics
          - Settings: User and application settings
        
        - **State Management**: Application state
          - Context: React Context for state
          - Redux Store: Global state management
        
        ### Backend Components
        
        The backend is built using Node.js with Express:
        
        - **API Endpoints**: RESTful API routes
          - User Management: Authentication and user operations
          - Project Management: Project CRUD operations
          - Data Services: Data processing and analytics
        
        - **Database Models**: Data schemas
          - User: User profile and authentication
          - Project: Project metadata and relationships
          - Diagram: Diagram storage and versioning
        
        - **Services**: Business logic
          - Authentication: User authentication and authorization
          - Planning: Project planning and scheduling
          - Diagram Generation: Automated diagram creation
        
        ### Deployment
        
        The application is deployed using a CI/CD pipeline:
        
        - **Development**: Local development environment
        - **Staging**: Pre-production testing environment
        - **Production**: Live production environment
        """)

def render_diagram_view_tab():
    """Render the diagram view tab."""
    st.header("Diagram View")
    
    # Create tabs for different diagram types
    diagram_tabs = st.tabs(["Architecture", "Components", "Sequence", "Data Model"])
    
    with diagram_tabs[0]:
        st.subheader("Architecture Diagram")
        
        # Display the architecture diagram using Mermaid
        mermaid_code = """
        flowchart TD
            Client[Client Browser] --> LB[Load Balancer]
            LB --> FE[Frontend Server]
            FE --> API[API Server]
            API --> AI[AI Planning Service]
            API --> DG[Diagram Generator]
            API --> DB[(Database)]
            API --> FS[File Storage]
            AI <--> LLM[LLM Service]

            subgraph "Frontend Layer"
                FE
            end

            subgraph "API Layer"
                LB
                API
            end

            subgraph "Service Layer"
                AI
                DG
            end

            subgraph "Data Layer"
                DB
                FS
            end

            subgraph "External Services"
                LLM
            end

            classDef frontend fill:#f9f,stroke:#333,stroke-width:2px;
            classDef api fill:#bbf,stroke:#333,stroke-width:2px;
            classDef service fill:#bfb,stroke:#333,stroke-width:2px;
            classDef data fill:#fbb,stroke:#333,stroke-width:2px;
            classDef external fill:#ddd,stroke:#333,stroke-width:2px;

            class FE frontend;
            class LB,API api;
            class AI,DG service;
            class DB,FS data;
            class LLM external;
        """
        
        st.markdown(f"```mermaid\n{mermaid_code}\n```")
        
        # Add diagram controls
        st.markdown("### Diagram Controls")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.slider("Zoom", min_value=50, max_value=150, value=100, step=10, key="arch_zoom")
        
        with col2:
            st.selectbox("Export", ["PNG", "SVG", "URL"], key="arch_export")
    
    with diagram_tabs[1]:
        st.subheader("Component Diagram")
        
        # Display the component diagram using Mermaid
        component_code = """
        classDiagram
            class Application {
                +components: Component[]
                +initialize()
                +render()
            }

            class Component {
                <<abstract>>
                +props: Object
                +state: Object
                +render()
                +update()
            }

            class LayoutComponent {
                +header: HeaderComponent
                +sidebar: SidebarComponent
                +content: ContentComponent
                +footer: FooterComponent
                +render()
            }

            class TreeViewComponent {
                +nodes: TreeNode[]
                +expandNode(nodeId)
                +collapseNode(nodeId)
                +selectNode(nodeId)
                +render()
            }

            class DiagramComponent {
                +tabs: Tab[]
                +activeTab: Tab
                +diagrams: Diagram[]
                +switchTab(tabId)
                +renderDiagram()
                +exportDiagram(format)
            }

            class ChatComponent {
                +messages: Message[]
                +sendMessage(text)
                +receiveMessage(message)
                +render()
            }

            Application --> LayoutComponent
            LayoutComponent --> TreeViewComponent
            LayoutComponent --> DiagramComponent
            LayoutComponent --> ChatComponent
            Component <|-- LayoutComponent
            Component <|-- TreeViewComponent
            Component <|-- DiagramComponent
            Component <|-- ChatComponent
        """
        
        st.markdown(f"```mermaid\n{component_code}\n```")
        
        # Add diagram controls
        st.markdown("### Diagram Controls")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.slider("Zoom", min_value=50, max_value=150, value=100, step=10, key="comp_zoom")
        
        with col2:
            st.selectbox("Export", ["PNG", "SVG", "URL"], key="comp_export")
    
    with diagram_tabs[2]:
        st.subheader("Sequence Diagram")
        
        # Display the sequence diagram using Mermaid
        sequence_code = """
        sequenceDiagram
            participant User
            participant UI as Frontend UI
            participant API as Backend API
            participant AI as AI Service
            participant DB as Database
            
            User->>UI: Enter project requirements
            UI->>API: Submit requirements
            API->>AI: Process requirements
            AI->>AI: Generate implementation plan
            AI->>API: Return implementation plan
            API->>DB: Store implementation plan
            API->>UI: Return success
            UI->>User: Display implementation plan
            
            User->>UI: Request code generation
            UI->>API: Submit code generation request
            API->>AI: Generate code
            AI->>API: Return generated code
            API->>DB: Store generated code
            API->>UI: Return code
            UI->>User: Display generated code
        """
        
        st.markdown(f"```mermaid\n{sequence_code}\n```")
        
        # Add diagram controls
        st.markdown("### Diagram Controls")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.slider("Zoom", min_value=50, max_value=150, value=100, step=10, key="seq_zoom")
        
        with col2:
            st.selectbox("Export", ["PNG", "SVG", "URL"], key="seq_export")
    
    with diagram_tabs[3]:
        st.subheader("Data Model")
        
        # Display the data model diagram using Mermaid
        data_model_code = """
        erDiagram
            PROJECT ||--o{ FEATURE : contains
            PROJECT ||--o{ DOCUMENT : includes
            PROJECT ||--o{ IMPLEMENTATION_PLAN : has
            FEATURE ||--o{ TASK : breaks_down_into
            FEATURE }|--|| STATUS : has
            TASK }|--|| STATUS : has
            USER ||--o{ PROJECT : owns
            USER ||--o{ TASK : assigned
            
            PROJECT {
                string id PK
                string name
                string description
                date created_at
                string github_url
                string slack_channel
            }
            
            FEATURE {
                string id PK
                string project_id FK
                string name
                string description
                int priority
                date due_date
            }
            
            TASK {
                string id PK
                string feature_id FK
                string name
                string description
                string assigned_to FK
                date due_date
            }
            
            STATUS {
                string id PK
                string name
                string color
                int order
            }
            
            USER {
                string id PK
                string name
                string email
                string github_username
                string slack_id
            }
            
            DOCUMENT {
                string id PK
                string project_id FK
                string name
                string content
                string type
                date uploaded_at
            }
            
            IMPLEMENTATION_PLAN {
                string id PK
                string project_id FK
                string content
                date generated_at
                date updated_at
            }
        """
        
        st.markdown(f"```mermaid\n{data_model_code}\n```")
        
        # Add diagram controls
        st.markdown("### Diagram Controls")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.slider("Zoom", min_value=50, max_value=150, value=100, step=10, key="data_zoom")
        
        with col2:
            st.selectbox("Export", ["PNG", "SVG", "URL"], key="data_export")

def render_chat_interface_tab():
    """Render the chat interface tab."""
    st.header("Chat Interface")
    
    # Initialize chat history if it doesn't exist
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "ai", "content": "Hello! How can I help with your project today?"},
            {"role": "user", "content": "I need to create a web application for inventory management."},
            {"role": "ai", "content": "I'll help you plan that. Let me create a basic project structure and some diagrams for you."},
            {"role": "system", "content": "Creating project structure..."},
            {"role": "system", "content": "Generating architecture diagram..."}
        ]
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        if message["role"] == "user":
            st.markdown(f"**You**: {message['content']}")
        elif message["role"] == "ai":
            st.markdown(f"**AI**: {message['content']}")
        elif message["role"] == "system":
            st.markdown(f"**System**: *{message['content']}*")
    
    # Chat input
    with st.container():
        st.markdown("---")
        
        # Create a form for the chat input
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_area("Type your message...", height=100, key="chat_input")
            col1, col2 = st.columns([5, 1])
            
            with col2:
                submit_button = st.form_submit_button("Send")
        
        # Process the form submission
        if submit_button and user_input:
            # Add user message to chat history
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            
            # Simulate AI response
            with st.spinner("AI is thinking..."):
                # In a real implementation, this would call an AI service
                time.sleep(1)
                
                # Add AI response to chat history
                st.session_state.chat_messages.append({
                    "role": "ai", 
                    "content": "I'm analyzing your request. Let me work on that for you."
                })
                
                # Add a system message
                st.session_state.chat_messages.append({
                    "role": "system", 
                    "content": "Processing request..."
                })
            
            # Rerun to update the UI
            st.experimental_rerun()