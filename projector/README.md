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
- **Accessibility Features**: Support for various accessibility needs including screen readers, keyboard navigation, and display preferences
- **Robust Error Handling**: Graceful error recovery and user-friendly error messages

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
- **Accessibility Panel**: Interface for customizing accessibility settings
- **Error Handling**: Robust error handling and user feedback

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

### Integration with codegen

Projector leverages several components from the codegen framework:

- **Chat Agent**: For natural language conversations
- **Planning Agent**: For creating implementation plans
- **PR Review Agent**: For reviewing pull requests
- **Code Agent**: For generating code
- **Reflector**: For self-improvement through reflection
- **Web Searcher**: For researching topics online
- **Context Understanding**: For analyzing document context

Projector also uses codegen's Git utilities:

- **RepoOperator**: For Git operations
- **RepoConfig**: For repository configuration
- **CodegenPR**: For pull request management
- **Language Detection**: For detecting programming languages

### Multi-threaded Implementation

Projector uses a thread pool to handle concurrent operations:

- **Thread Pool**: Manages worker threads for concurrent task execution
- **Thread-safe Operations**: Ensures thread safety with locks
- **Asynchronous Processing**: Processes Slack messages and GitHub operations asynchronously

### Accessibility Features

Projector includes comprehensive accessibility features:

- **Screen Reader Support**: All UI elements are properly labeled for screen readers
- **Keyboard Navigation**: Full keyboard navigation support with shortcuts
- **Font Size Adjustment**: Adjustable font sizes for better readability
- **High Contrast Mode**: High contrast display option for users with visual impairments
- **Reduced Motion**: Option to reduce animations for users with motion sensitivity
- **Error Messages**: Clear and descriptive error messages
- **Responsive Design**: Adapts to different screen sizes and devices

### Robustness Features

Projector includes several robustness features:

- **Error Boundary**: Catches and handles errors gracefully
- **Connection Monitoring**: Monitors connections to external services
- **Automatic Reconnection**: Attempts to reconnect to services when disconnected
- **Data Validation**: Validates input data to prevent errors
- **Logging**: Comprehensive logging for debugging and monitoring
- **Session Management**: Robust session state management
- **Graceful Degradation**: Continues to function with limited features when services are unavailable

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

1. Set up the symbolic link for the codegen module structure:
   ```
   python projector/setup_symlink.py
   ```
   This creates a symbolic link structure that allows the projector module to be imported as `codegen.application.projector`.

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
- **Users with Accessibility Needs**: Fully accessible interface for all users

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

## Keyboard Shortcuts

Projector supports the following keyboard shortcuts for improved accessibility:

- **Alt + 1-9**: Navigate to different pages
- **Alt + S**: Toggle sidebar
- **Alt + A**: Open accessibility settings
- **Alt + D**: Toggle dark/light mode
- **Alt + H**: Show help