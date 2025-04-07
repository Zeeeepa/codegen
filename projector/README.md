# Projector

A simplified project management system with a focus on AI-assisted project planning and implementation.

## Features

- **Three-column Layout**: Step-by-step structure, tabbed project interface, and implementation tree view
- **Project Management**: Create, configure, and manage multiple projects
- **Concurrency Control**: Set how many concurrent feature lifecycles are processed at once (1-10)
- **Document Integration**: Upload and process project documents
- **AI-Assisted Planning**: Initialize projects to generate implementation plans
- **Chat Interface**: Discuss and adjust project requirements via natural language

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

Run the application:
```bash
./projector/start.sh
```

Or directly with Python:
```bash
python projector/main.py
```

For help with command-line options:
```bash
python projector/main.py --help
```

## UI Layout

The application follows a three-column layout:

1. **Left Column**: Step-by-step structure view generated from project documents
2. **Middle Column**: Tabbed project interface with closable tabs
3. **Right Column**: Implementation tree view showing project progress

Each project tab includes:
- Concurrency setting (1-10)
- Project settings button
- Document view
- Initialize button

## Implementation Details

- Built with Streamlit for a simple, interactive UI
- JSON-based project database for persistence
- Simulated AI processing for document ingestion and plan generation
- Chat interface for project-specific conversations
