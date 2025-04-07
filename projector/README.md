# Projector

A simple project management system with a focus on tracking implementation progress.

## Overview

Projector is a streamlined project management tool that helps teams track the implementation progress of their projects. It provides a visual representation of project tasks, their dependencies, and completion status.

## Features

- **Project Management**: Create and manage multiple projects
- **Task Tracking**: Track tasks and subtasks with completion status
- **Implementation Tree**: Visualize project structure and progress
- **Chat Interface**: Communicate about project details
- **GitHub Integration**: Link projects to GitHub repositories
- **Slack Integration**: Connect projects to Slack channels

## Simplified Implementation

This is a simplified implementation of the Projector system, with all functionality contained in a single Streamlit application. The frontend/backend separation has been removed to make the codebase more maintainable and easier to understand.

## Getting Started

### Prerequisites

- Python 3.8+
- Streamlit

### Installation

1. Clone the repository
2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

### Running the Application

Run the application using the CLI:

```
python -m projector.cli
```

Or directly with Streamlit:

```
streamlit run projector/frontend/streamlit_app.py
```

## Usage

1. Create a new project by clicking the "Add Project" button
2. Fill in the project details (name, GitHub URL, Slack channel)
3. Initialize the project to generate a sample implementation plan
4. View the step-by-step structure and implementation tree
5. Use the chat interface to discuss project details

## Project Structure

- `frontend/streamlit_app.py`: Main Streamlit application
- `cli.py`: Command-line interface
- `main.py`: Main entry point
- `projects_db.json`: Project database file

## License

This project is licensed under the MIT License - see the LICENSE file for details.
