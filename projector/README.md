# Projector

A comprehensive project management tool that integrates Slack, GitHub, and AI capabilities to streamline software development workflows.

## Overview

Projector is a powerful application designed to bridge the gap between project planning, communication, and code development. It provides a unified interface for managing software projects by integrating with Slack for team communication, GitHub for code management, and leveraging AI capabilities for feature extraction, planning, and code generation.

## Key Features

- **Document Analysis**: Automatically extract features and requirements from markdown documents
- **Project Planning**: Generate implementation plans with timelines and dependencies
- **Slack Integration**: Create and monitor threads for feature discussions
- **GitHub Integration**: Manage branches, commits, and pull requests
- **AI Assistance**: Generate code, analyze repositories, and provide intelligent responses
- **Dashboard Visualization**: Track project progress with metrics and Gantt charts
- **Multi-threaded Processing**: Handle concurrent operations efficiently
- **PR Validation**: Validate pull requests against project requirements
- **Research Capabilities**: Research topics related to project requirements
- **Reflection**: Self-improve responses over time

## Architecture

Projector follows a modular architecture with clear separation of concerns:

### Backend Components

- **Project Database**: Persistent storage for project data
- **Assistant Agent**: Coordinates between Slack, GitHub, and AI services
- **Planning Manager**: Handles project planning and timeline visualization
- **Slack Manager**: Manages Slack communication
- **GitHub Manager**: Handles GitHub repository operations using codegen's RepoOperator
- **Thread Pool**: Manages concurrent operations
- **AI Agents**:
  - **Chat Agent**: Handles natural language conversations
  - **Planning Agent**: Creates implementation plans
  - **PR Review Agent**: Reviews pull requests
  - **Code Agent**: Generates code
  - **Reflector**: Improves responses through reflection
  - **Web Searcher**: Researches topics online
  - **Context Understanding**: Analyzes document context

### Frontend Components

- **Streamlit UI**: Web-based user interface
- **Dashboard**: Visualizes project metrics and progress
- **Document Management**: Interface for uploading and analyzing documents
- **Thread Management**: Interface for monitoring and responding to Slack threads
- **GitHub Panel**: Interface for managing GitHub operations
- **Planning Page**: Interface for creating and visualizing project plans

## Workflow

1. **Project Setup**: Create a new project with GitHub repository and Slack channel
2. **Document Analysis**: Upload project requirements as markdown documents
3. **Feature Extraction**: AI analyzes documents to extract features and requirements
4. **Implementation Planning**: Generate a plan with timelines and dependencies
5. **Development Tracking**: Monitor progress through Slack threads and GitHub branches
6. **Code Generation**: Generate code templates for features
7. **Pull Request Management**: Create and manage pull requests for completed features
8. **PR Validation**: Validate pull requests against project requirements

## Technical Details

### Integration with agentgen

Projector leverages several components from the agentgen framework:

- **Chat Agent**: For natural language conversations
- **Planning Agent**: For creating implementation plans
- **PR Review Agent**: For reviewing pull requests
- **Code Agent**: For generating code
- **Reflector**: For self-improvement through reflection
- **Web Searcher**: For researching topics online
- **Context Understanding**: For analyzing document context

### Integration with codegen

Projector uses codegen's Git utilities:

- **RepoOperator**: For Git operations
- **RepoConfig**: For repository configuration
- **CodegenPR**: For pull request management
- **Language Detection**: For detecting programming languages

### Multi-threaded Implementation

Projector uses a thread pool to handle concurrent operations:

- **Thread Pool**: Manages worker threads for concurrent task execution
- **Thread-safe Operations**: Ensures thread safety with locks
- **Asynchronous Processing**: Processes Slack messages and GitHub operations asynchronously

## Configuration

Projector uses environment variables for configuration:

```
SLACK_USER_TOKEN=xoxp-...
SLACK_DEFAULT_CHANNEL=general
GITHUB_TOKEN=ghp_...
GITHUB_USERNAME=username
GITHUB_DEFAULT_REPO=organization/repository
```

## Running the Application

### Prerequisites

- Python 3.8+
- Slack API token
- GitHub API token

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your configuration
4. Run the application:
   ```
   python main.py
   ```

### Running the Streamlit UI

To run the Streamlit UI:

1. Set up the symbolic link for the agentgen module structure:
   ```
   python projector/setup_symlink.py
   ```
   This creates a symbolic link structure that allows the projector module to be imported as `agentgen.application.projector`.

2. Run the Streamlit app:
   ```
   cd projector/frontend
   streamlit run streamlit_app.py
   ```

### Command Line Options

- `--ui`: Launch the Streamlit UI
- `--backend`: Run the backend service only
- `--docs`: Path to markdown documents folder
- `--debug`: Enable debug logging
- `--threads`: Maximum number of concurrent threads
- `--monitor`: Enable automatic Slack thread monitoring

## Use Cases

- **Project Managers**: Track project progress and manage timelines
- **Developers**: Collaborate on features and track implementation
- **Product Owners**: Convert requirements into actionable features
- **Teams**: Streamline communication between planning and development

## Data Flow

1. Documents → AI Analysis → Feature Extraction
2. Features → Planning Manager → Implementation Plan
3. Implementation Plan → Slack & GitHub → Development Tracking
4. Development Progress → Dashboard → Visualization
5. Pull Requests → PR Review Agent → Validation
6. User Queries → Chat Agent → Intelligent Responses

## Security Considerations

- API tokens are stored in environment variables
- Authentication is required for UI access
- Communication with external services uses secure protocols