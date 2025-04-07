# Projector

A simple project management system with LLM-powered document analysis and planning.

## Features

- **Three-column layout** with step-by-step structure, document view, and tree structure
- **Tabbed project interface** with closable tabs
- **Concurrency settings** for each project (1-10)
- **Project settings** with GitHub URL and Slack channel ID
- **Document upload** for requirements and specifications
- **LLM-powered initialization** to create structural trees and step-by-step plans
- **Chat interface** for project-specific conversations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/projector
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install the requirements:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
chmod +x start.sh
./start.sh
```

Or directly:
```bash
python main.py
```

2. Open your browser and navigate to:
```
http://localhost:8501
```

3. Create a new project by entering a name and clicking the "Add Project" button.

4. Upload documents to the project.

5. Initialize the project to generate the tree structure and step-by-step plan.

6. Use the chat interface to discuss and refine the project requirements.

## Project Structure

- `main.py`: Entry point for the application
- `streamlit_app.py`: Main Streamlit application with all UI components
- `requirements.txt`: Required Python packages
- `start.sh`: Shell script to start the application

## License

MIT
