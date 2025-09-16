# 🚀 Codegen Project Management System

A comprehensive project management system integrated with the Codegen CLI that provides PRD (Product Requirements Document) management, task tracking, and seamless integration with Codegen's AI agents and GitHub workflows.

## 📋 Features

### ✨ Core Functionality
- **📄 PRD Management**: Create, view, and automatically update Product Requirements Documents
- **📝 Task Management**: Create, start, complete, and track project tasks
- **🤖 Agent Integration**: Start tasks with Codegen AI agents or Claude Code
- **📊 Progress Tracking**: Real-time project progress monitoring
- **🖥️ Interactive Dashboard**: Rich TUI dashboard for project visualization
- **🐙 GitHub Integration**: Sync with GitHub repositories and issues
- **🔄 Workflows Integration**: Compatible with workflows-py for advanced automation

### 🎯 Key Benefits
- **Unified Workflow**: Manage projects, tasks, and AI agents from one interface
- **Automatic Documentation**: PRD updates automatically with task progress
- **Real-time Monitoring**: Live dashboard with progress tracking
- **API Integration**: Full integration with Codegen's API services
- **Extensible**: Built on modular architecture for easy customization

## 🛠️ Installation

The project management system is included with the Codegen CLI. Ensure you have the latest version:

```bash
pip install codegen --upgrade
```

For the interactive dashboard, install additional dependencies:

```bash
pip install textual
```

## 🚀 Quick Start

### 1. Initialize a Project

```bash
# Navigate to your project directory
cd my-awesome-project

# Initialize project management
codegen project init --name "My Awesome Project"
```

This creates:
- `.codegen/project_state.json` - Project state and task tracking
- `PRD.md` - Product Requirements Document template

### 2. Create Tasks

```bash
# Add a new task
codegen project add-task \
  --title "Implement user authentication" \
  --description "Add JWT-based authentication system" \
  --priority high

# Add more tasks
codegen project add-task \
  --title "Create API endpoints" \
  --description "Build REST API for user management" \
  --priority medium
```

### 3. View Tasks and Status

```bash
# List all tasks
codegen project tasks

# View overall project status
codegen project status

# View the PRD (automatically updated with tasks)
codegen project prd
```

### 4. Start Working on Tasks

```bash
# Start a task with a Codegen agent
codegen project start-task 1

# Or start with Claude Code
codegen project start-task 1 --claude
```

### 5. Launch Interactive Dashboard

```bash
# Launch the rich TUI dashboard
codegen project dashboard
```

## 📖 Detailed Usage

### Project Initialization

```bash
# Basic initialization
codegen project init

# With custom name and org ID
codegen project init --name "My Project" --org-id 123
```

**What happens:**
- Creates project state file (`.codegen/project_state.json`)
- Generates PRD template (`PRD.md`)
- Detects GitHub repository if available
- Sets up organization context

### Task Management

#### Creating Tasks

```bash
codegen project add-task \
  --title "Task title" \
  --description "Detailed description" \
  --priority [low|medium|high]
```

#### Starting Tasks

```bash
# Start with Codegen agent
codegen project start-task <task_id>

# Start with Claude Code
codegen project start-task <task_id> --claude
```

**What happens:**
- Creates an agent run via Codegen API
- Updates task status to "running"
- Links task to agent run ID
- Updates PRD automatically

#### Completing Tasks

```bash
codegen project complete-task <task_id>
```

### PRD Management

The PRD (Product Requirements Document) is automatically managed:

```bash
# View current PRD
codegen project prd
```

**Features:**
- Auto-generated template with standard sections
- Automatic task section updates
- Markdown formatting for easy reading
- Integration with task status and progress

### Project Status and Monitoring

```bash
# View comprehensive project status
codegen project status

# List all tasks with details
codegen project tasks
```

**Status includes:**
- Total, completed, running, and pending tasks
- Progress percentage
- Recent activity
- Agent run information

### Interactive Dashboard

```bash
codegen project dashboard
```

**Dashboard Features:**
- Real-time project statistics
- Interactive task management
- PRD viewer with live updates
- Agent run monitoring
- Keyboard shortcuts for quick actions

**Keyboard Shortcuts:**
- `q` - Quit dashboard
- `r` - Refresh data
- `n` - Create new task
- `s` - Start selected task
- `c` - Complete selected task
- `p` - View PRD tab
- `g` - Sync with GitHub

### GitHub Integration

```bash
# Sync project with GitHub
codegen project sync-github
```

**Features:**
- Automatic GitHub repository detection
- Issue and PR synchronization (planned)
- Branch and commit tracking (planned)

## 🏗️ Architecture

### Core Components

#### 1. ProjectState Class
- Manages project state and persistence
- Handles task lifecycle (create, start, complete)
- Tracks agent runs and progress
- JSON-based storage in `.codegen/project_state.json`

#### 2. PRDManager Class
- Creates and manages PRD documents
- Auto-updates task sections
- Markdown formatting and templating
- Integration with project state

#### 3. CodegenAPIClient Class
- Interfaces with Codegen API
- Creates and monitors agent runs
- Handles authentication and organization context
- Error handling and retry logic

#### 4. Dashboard TUI
- Rich terminal user interface
- Real-time data updates
- Interactive task management
- Multi-tab layout (Tasks, PRD, Agent Runs)

### Data Flow

```
User Command → CLI Handler → ProjectState → API Client → Codegen API
                    ↓
              PRD Manager → PRD.md Update
                    ↓
              Dashboard → Real-time Display
```

### File Structure

```
project-directory/
├── .codegen/
│   └── project_state.json     # Project state and tasks
├── PRD.md                     # Product Requirements Document
└── [your project files]
```

## 🔧 Configuration

### Environment Variables

```bash
# Required for API integration
export CODEGEN_ORG_ID=your_org_id
export CODEGEN_API_TOKEN=your_api_token

# Optional GitHub integration
export GITHUB_TOKEN=your_github_token
```

### Project State Schema

```json
{
  "project_name": "My Project",
  "created_at": "2024-01-01T00:00:00",
  "org_id": 123,
  "github_repo": "https://github.com/user/repo.git",
  "project_status": "active",
  "tasks": [
    {
      "id": 1,
      "title": "Task Title",
      "description": "Task Description",
      "priority": "high",
      "status": "running",
      "agent_run_id": 12345,
      "created_at": "2024-01-01T00:00:00",
      "started_at": "2024-01-01T01:00:00"
    }
  ],
  "active_agents": {
    "12345": 1
  },
  "completed_tasks": []
}
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Set up test environment
export CODEGEN_ORG_ID=your_test_org_id
export CODEGEN_API_TOKEN=your_test_token

# Run tests
python test_project_management.py
```

**Test Coverage:**
- Project state management
- PRD creation and updates
- CLI command functionality
- API integration
- GitHub integration
- Dashboard components
- Workflows integration

## 🔄 Integration with Workflows-py

The project management system integrates seamlessly with workflows-py:

```python
from workflows import Workflow, step, StartEvent, StopEvent
from codegen.cli.commands.project.main import ProjectState, CodegenAPIClient

class ProjectWorkflow(Workflow):
    @step
    async def create_and_start_task(self, ev: StartEvent) -> StopEvent:
        project_state = ProjectState()
        
        # Create task
        task = {
            "title": ev.data["task_title"],
            "description": ev.data["task_description"],
            "priority": ev.data.get("priority", "medium")
        }
        project_state.add_task(task)
        
        # Start with agent
        api_client = CodegenAPIClient(project_state.state["org_id"])
        agent_run = api_client.create_agent_run(task["description"])
        project_state.start_task(task["id"], agent_run["id"])
        
        return StopEvent(result={"task_id": task["id"], "agent_run_id": agent_run["id"]})
```

## 📚 API Reference

### CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `init` | Initialize project | `codegen project init --name "My Project"` |
| `add-task` | Create new task | `codegen project add-task --title "Task" --description "Desc"` |
| `tasks` | List all tasks | `codegen project tasks` |
| `start-task` | Start a task | `codegen project start-task 1 --claude` |
| `complete-task` | Complete a task | `codegen project complete-task 1` |
| `status` | Show project status | `codegen project status` |
| `prd` | View PRD | `codegen project prd` |
| `dashboard` | Launch TUI dashboard | `codegen project dashboard` |
| `sync-github` | Sync with GitHub | `codegen project sync-github` |

### Python API

```python
from codegen.cli.commands.project.main import ProjectState, PRDManager, CodegenAPIClient

# Project state management
project = ProjectState()
project.add_task({"title": "Task", "description": "Desc", "priority": "high"})
project.start_task(1, agent_run_id)
project.complete_task(1)

# PRD management
prd = PRDManager(Path("PRD.md"))
prd.create_default_prd("Project Name")
prd.update_tasks_section(project.state["tasks"])

# API integration
api = CodegenAPIClient(org_id)
agent_run = api.create_agent_run("Task prompt")
status = api.get_agent_run(agent_run["id"])
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite
5. Submit a pull request

## 📄 License

This project is part of the Codegen CLI and follows the same license terms.

## 🆘 Support

- **Documentation**: See the main Codegen CLI documentation
- **Issues**: Report bugs via GitHub issues
- **Community**: Join the Codegen Discord community

---

**Built with ❤️ by the Codegen team**

