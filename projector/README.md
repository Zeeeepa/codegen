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

- Python 3.8+
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
- Fix any compatibility issues
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

### ForwardRef._evaluate Error

If you encounter a `ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'` error, the `start_backend.sh` script should automatically fix this issue. If not, you can manually fix it by editing the `pydantic/typing.py` file in your virtual environment:

```python
# Change this line:
return cast(Any, type_)._evaluate(globalns, localns, set())

# To:
return cast(Any, type_)._evaluate(globalns, localns, set(), set())
```

### Dependency Conflicts

If you encounter dependency conflicts, make sure you're using the exact versions specified in `requirements.txt`. The `pydantic` version is particularly important - do not upgrade to version 2.x as it breaks compatibility with FastAPI 0.95.1.