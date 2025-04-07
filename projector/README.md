# Projector

A simple project management system with LLM integration for generating implementation plans.

## Features

- Three-column layout with step-by-step structure, tabbed project interface, and tree structure view
- Project tabs with closable tabs
- Concurrency settings for each project (1-10)
- Project settings with GitHub URL and Slack channel ID
- Document upload functionality
- LLM-powered project initialization
- Chat interface for project-specific conversations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Zeeeepa/codegen.git
cd codegen
```

2. Install the required packages:
```bash
pip install -r projector/requirements.txt
```

## Usage

1. Start the application:
```bash
chmod +x projector/start.sh
./projector/start.sh
```

2. Open your browser and navigate to:
```
http://localhost:8501
```

## UI Layout

```
+---------------------------------------------------------+
| [Settings] [Dashboard]                 [Add_Project]+  |
+---------------+-----------------------------------------+
|               | [Project1]|[Project2][X]|              |
|               |                         |Tree Structure|
|               | Project's context       |   View       |
|  Step by step |   document View         |   Component  |
|  Structure    |   (Tabbed Interface)    |Integration   |
| View generated|                         |   Check map  |
|  from user's  |                         |   Completion   |
|   documents   |Concurrency    project-  | [✓] -done    |
|               |   [2]        [Settings] | [ ] - to do  |
+---------------+-------------------------+--------------+
|                                                        |
|                  Chat Interface                        |
|                                                        |
+--------------------------------------------------------+
```

## Implementation Details

- **Step-by-Step Structure**: Shows the high-level steps for project implementation
- **Tabbed Project Interface**: Allows managing multiple projects with closable tabs
- **Tree Structure View**: Displays the hierarchical implementation progress
- **Chat Interface**: Enables communication about specific projects
