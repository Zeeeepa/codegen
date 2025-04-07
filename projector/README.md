# Projector

A project management and code improvement tool with FastAPI backend and Next.js frontend.

## Features

- Multi-project tab creation (supporting 1-50 projects simultaneously)
- Dynamic concurrency settings (1-10 tasks per project)
- Project-specific chat interface
- Implementation tree view with sequential task completion tracking
- Recent activity dashboard with last merges
- Code improvement with AI-powered suggestions

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
|  from user's  |                         |   Chek map   |
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

- Python 3.8+ (Python 3.13+ requires updated dependencies - see below)
- Node.js 14+ and npm
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Zeeeepa/codegen.git
   cd codegen/projector
   ```

2. Run the setup script:
   ```bash
   ./setup_symlink.py
   ```

3. If you're using Python 3.13+, update the dependencies:
   ```bash
   ./scripts/update_dependencies.sh
   ```

## Running the Application

### Option 1: Run Everything at Once (Recommended)

```bash
./scripts/start_all.sh
```

This script will:
- Start the FastAPI backend on port 8000
- Start the Next.js frontend on port 3000
- Open both in a tmux session (or separate terminals if tmux is not available)

### Option 2: Run Backend and Frontend Separately

#### Start the Backend

```bash
./scripts/start_backend.sh
```

This will:
- Create a virtual environment if it doesn't exist
- Install Python dependencies
- Start the FastAPI server on port 8000

#### Start the Frontend

```bash
./scripts/start_frontend.sh
```

This will:
- Install Node.js dependencies
- Start the Next.js development server on port 3000

## Accessing the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Project Configuration

Configure your projects in the Settings dialog:

```
+------------------------------------------------------------------+
|   Project SETTINGS                                               |
+------------------------------------------------------------------+
| Slack Channel:            [#pr-reviews]                          |
| Project Github URL:      [https://github.com/Zeeeepa/codegen]    |
| Notify on:                                                       |
| [✓] New branch detected                                          |
| [✓] PR created                                                   |
| [✓] PR reviewed                                                  |
| [✓] PR merged                                                    |
| [✓] Errors                                                       |
+------------------------------------------------------------------+
```

## Troubleshooting

### Python 3.13 Compatibility

If you're using Python 3.13, you may encounter the following errors:

```
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
```

Or:

```
ModuleNotFoundError: No module named 'langgraph'
```

To fix these issues:

1. Run the update dependencies script:
   ```bash
   ./scripts/update_dependencies.sh
   ```

2. Make sure both the backend and frontend are stopped before running the update script

3. After updating dependencies, start the backend first:
   ```bash
   ./scripts/start_backend.sh
   ```

4. Then start the frontend in a separate terminal:
   ```bash
   ./scripts/start_frontend.sh
   ```

The update script will:
- Install the correct versions of dependencies compatible with Python 3.13
- Set up the proper PYTHONPATH to find the codegen modules
- Create a .env file with the necessary environment variables

### PYTHONPATH Issues

If you see errors related to missing modules like `langgraph` or `codegen`, it's likely a PYTHONPATH issue:

1. Make sure the update_dependencies.sh script has been run
2. Check that the .env file in the projector directory contains the correct PYTHONPATH
3. If needed, manually set the PYTHONPATH before starting the backend:
   ```bash
   export PYTHONPATH="/path/to/codegen/src:$PYTHONPATH"
   ./scripts/start_backend.sh
   ```

### Connection Refused Errors

If you see "Failed to proxy http://localhost:8000/api/projects Error: connect ECONNREFUSED 127.0.0.1:8000" errors:

1. Make sure the backend is running on port 8000
2. Check if there are any Python compatibility issues (especially with Python 3.13)
3. Run the update dependencies script and restart both the backend and frontend
4. Verify the backend is running by visiting http://localhost:8000 directly
5. Check the backend logs for any errors (they should be displayed in the terminal)

### Dependency Conflicts

If you encounter dependency conflicts, make sure you're using the correct versions for your Python version:
- For Python 3.8-3.12: The default dependencies should work fine
- For Python 3.13+: You need updated dependencies (pydantic>=2.4.0, fastapi>=0.103.1, uvicorn>=0.23.2, langgraph>=0.3.20)

### Virtual Environment Issues

If you're having issues with the virtual environment:

1. Delete the existing virtual environment:
   ```bash
   rm -rf venv
   ```

2. Create a new virtual environment:
   ```bash
   python3 -m venv venv
   ```

3. Run the update dependencies script:
   ```bash
   ./scripts/update_dependencies.sh
   ```

### Streamlit Warnings

If you see warnings like "Warning: Could not access Streamlit secrets: name 'st' is not defined", these can be safely ignored. They're related to an optional feature and don't affect the core functionality.
