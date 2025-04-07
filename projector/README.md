# Projector

A project management and code improvement tool with FastAPI backend and Next.js frontend.

## Features

- **Project Management**: Track and manage multiple projects simultaneously
- **Code Improvement**: AI-powered code analysis and improvement suggestions
- **GitHub Integration**: Connect with GitHub repositories
- **Slack Integration**: Send notifications and updates to Slack channels
- **Tree View**: Visualize project structure and implementation progress

## UI Layout

```
+---------------------------------------------------------+
|             [Dashboard]                 [Add_Project]+  |
+---------------+-----------------------------------------+
|               | [Project1]|[Project2]   |              |
|               |                         |Tree Structure|
|               | Project's context       |   View       |
|  Step by step |   document View         |   Component  |
|  Structure    |   (Tabbed Interface)    |Integration   |
| View generated|                         | Completion   |
|  from user's  |                         |   Check map  |
|   documents   |Concurrency      project | [✓] -done    |
|               |[2]           [Settings] | [ ] - to do  |
+---------------+-------------------------+---------- ---+
|                                                        |
|                  Chat Interface                        |
|                                                        |
+----------------------------------------------------- --+
```

## Installation

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm 6+

### Backend Setup

1. Clone the repository
2. Navigate to the project directory
3. Run the backend setup script:

```bash
./scripts/start_backend.sh
```

This will:
- Create a virtual environment if it doesn't exist
- Install the required Python dependencies
- Start the FastAPI backend on http://localhost:8000

### Frontend Setup

1. Run the frontend setup script:

```bash
./scripts/start_frontend.sh
```

This will:
- Install the required Node.js dependencies
- Start the Next.js development server on http://localhost:3000

## Usage

1. Open your browser and navigate to http://localhost:3000
2. Use the dashboard to create and manage projects
3. Configure project settings (GitHub URL, Slack channel, etc.)
4. Use the Code Improvement feature to analyze and improve your code
5. Track implementation progress using the Tree Structure View

## API Documentation

The API documentation is available at http://localhost:8000/docs when the backend is running.

## Project Structure

- `api/`: FastAPI backend routes and models
- `backend/`: Core backend functionality
- `frontend/`: Next.js frontend application
- `scripts/`: Utility scripts for setup and running the application