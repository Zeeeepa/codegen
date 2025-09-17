# Codegen Dashboard with AI Integration

A comprehensive Tkinter-based dashboard for managing Codegen agent runs with advanced AI-powered features including chat interface, code analysis, and automated workflow orchestration.

## 🚀 Features

### Core Dashboard Features
- **Real-time Agent Run Monitoring**: Live tracking of running instances with status updates
- **Project Management**: Starred projects with PR monitoring and validation gates
- **Notification System**: Cross-platform notifications for important events
- **Star System**: Mark important agent runs and projects for easy access

### 🤖 AI-Powered Chat Interface
- **RepoMaster Integration**: Intelligent code context detection and analysis
- **Z.AI Client**: Advanced language model for natural conversations
- **Automatic Agent Creation**: Create Codegen agent runs directly from chat
- **Context-Aware Responses**: Uses project and code context for relevant answers

### 📊 Advanced Code Analysis
- **Graph-Sitter Visualization**: Interactive dependency graphs and code structure
- **Blast Radius Analysis**: Understand impact of code changes
- **Call Trace Visualization**: Track function call relationships
- **Complexity Metrics**: Code quality and maintainability insights

### 🔍 PRD Validation & Automation
- **Automatic PRD Validation**: AI validates if agent runs meet requirements
- **Smart Follow-up Agents**: Automatically creates follow-up agents when goals aren't met
- **Confidence Scoring**: AI confidence levels for validation results
- **Missing Requirements Detection**: Identifies what still needs to be implemented

### ⚙️ Workflow Orchestration
- **Validation Gates**: Custom validation scripts for PR events
- **Sequential Workflows**: Template-based multi-step automation
- **Background Monitoring**: Continuous polling of agent runs and PRs
- **Error Recovery**: Intelligent error handling and retry mechanisms

### 💾 Memory & Persistence
- **Multiple Database Backends**: SQLite, Supabase, or InfinitySQL support
- **Conversation Memory**: AI remembers context across chat sessions
- **Embedding-based Search**: Semantic search through conversation history
- **Local Caching**: Efficient caching for improved performance

## 🏗️ Architecture

### Core Components

```
src/codegen_dashboard/
├── __init__.py                 # Package initialization
├── main.py                     # Main application entry point
├── config.py                   # Configuration management
├── models.py                   # Enhanced data models
├── services/                   # Core services
│   ├── chat_service.py        # AI-powered chat with RepoMaster + Z.AI
│   ├── codegen_client.py      # Codegen API integration
│   ├── state_manager.py       # Application state management
│   └── notification_service.py # Notification handling
├── integrations/               # External service integrations
│   ├── zai_client.py          # Z.AI API client
│   └── repomaster_client.py   # RepoMaster code analysis
├── ui/                        # User interface components
│   ├── main_window.py         # Main dashboard window
│   ├── components/            # Reusable UI components
│   └── views/                 # Specific view implementations
├── storage/                   # Data persistence
│   ├── database_manager.py    # Multi-backend database support
│   └── memory_manager.py      # AI memory management
└── utils/                     # Utility functions
    └── logger.py              # Logging configuration
```

### Key Integrations

1. **Codegen API**: Leverages existing CLI authentication and API clients
2. **RepoMaster**: Intelligent code context detection using tree-sitter analysis
3. **Z.AI Client**: Advanced language model for chat and analysis
4. **Graph-Sitter**: Code visualization and dependency analysis
5. **Database Backends**: Flexible storage with SQLite, Supabase, or InfinitySQL

## 🎯 AI Chat Interface

The chat interface is the centerpiece of the dashboard, combining multiple AI technologies:

### Context Detection
- **File Analysis**: Automatically detects when users mention files or code
- **Symbol Recognition**: Identifies functions, classes, and variables in conversations
- **Project Context**: Maintains awareness of the current project being discussed
- **Memory Integration**: Remembers previous conversations and context

### Intelligent Agent Creation
```python
# Example chat interaction:
User: "Can you create an agent to add input validation to the login form?"
