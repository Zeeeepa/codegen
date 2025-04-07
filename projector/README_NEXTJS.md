# Projector: Next.js + FastAPI Implementation

This document outlines the new implementation of the Projector application using Next.js for the frontend and FastAPI for the backend.

## Architecture

The application is split into two main components:

1. **Backend (FastAPI)**: Provides RESTful API endpoints for all functionality
2. **Frontend (Next.js)**: Provides a modern, responsive UI that consumes the API

### Backend (FastAPI)

The backend is implemented using FastAPI, a modern, fast web framework for building APIs with Python. It provides the following features:

- RESTful API endpoints for all functionality
- Automatic API documentation with Swagger UI
- Type checking with Pydantic models
- Dependency injection for services
- Asynchronous request handling

### Frontend (Next.js)

The frontend is implemented using Next.js, a React framework for building server-rendered applications. It provides the following features:

- Server-side rendering for improved performance and SEO
- Static site generation for faster page loads
- API routes for backend functionality
- TypeScript support for type safety
- Material-UI for UI components

## Directory Structure

```
projector/
├── api/                  # FastAPI backend
│   ├── main.py           # Main FastAPI application
│   ├── models/           # Pydantic models
│   └── routes/           # API routes
├── backend/              # Backend services (shared with Streamlit)
├── frontend/             # Frontend applications
│   ├── nextjs/           # Next.js frontend
│   │   ├── public/       # Static files
│   │   ├── src/          # Source code
│   │   │   ├── components/ # React components
│   │   │   ├── pages/    # Next.js pages
│   │   │   └── styles/   # CSS styles
│   │   ├── next.config.js # Next.js configuration
│   │   ├── package.json  # NPM package configuration
│   │   └── tsconfig.json # TypeScript configuration
│   └── streamlit/        # Original Streamlit frontend
```

## Features

The application provides the following features:

1. **Multi-project Management**: Create and manage multiple projects (1-50)
2. **Dynamic Concurrency Settings**: Set the number of concurrent tasks per project (1-10)
3. **Custom Document Management**: Add and categorize project documents
4. **Implementation Tree View**: Visualize the implementation plan with task dependencies
5. **Project-specific Chat Interface**: Chat with the AI assistant in the context of a project
6. **Recent Activity Dashboard**: View recent GitHub activity for projects

## UI Layout

The UI follows a three-column layout as specified in the mockup:

1. **Left Column**: Step-by-step structure view
2. **Middle Column**: Project context document view with tabbed interface
3. **Right Column**: Tree structure view with completion checkmarks
4. **Bottom Section**: Chat interface

## Installation and Setup

### Backend (FastAPI)

1. Install dependencies:
   ```bash
   pip install fastapi uvicorn
   ```

2. Run the FastAPI server:
   ```bash
   cd projector
   uvicorn api.main:app --reload
   ```

3. Access the API documentation at http://localhost:8000/docs

### Frontend (Next.js)

1. Install dependencies:
   ```bash
   cd projector/frontend/nextjs
   npm install
   ```

2. Run the Next.js development server:
   ```bash
   npm run dev
   ```

3. Access the application at http://localhost:3000

## API Endpoints

The backend provides the following API endpoints:

- **Projects**:
  - `GET /api/projects`: List all projects
  - `GET /api/projects/{project_id}`: Get a project by ID
  - `POST /api/projects`: Create a new project
  - `PUT /api/projects/{project_id}`: Update a project
  - `DELETE /api/projects/{project_id}`: Delete a project
  - `POST /api/projects/{project_id}/documents`: Add a document to a project
  - `POST /api/projects/{project_id}/analyze`: Analyze project requirements
  - `PUT /api/projects/{project_id}/tasks/{task_id}`: Update task status
  - `GET /api/projects/{project_id}/recent-activity`: Get recent activity

- **GitHub**:
  - `GET /api/github/repos/{owner}/{repo}/contents/{path}`: Get repository contents
  - `GET /api/github/repos/{owner}/{repo}/pulls`: Get pull requests
  - `GET /api/github/repos/{owner}/{repo}/pulls/{pr_number}`: Get a pull request
  - `GET /api/github/repos/{owner}/{repo}/pulls/{pr_number}/comments`: Get PR comments
  - `POST /api/github/repos/{owner}/{repo}/pulls/{pr_number}/comments`: Create PR comment
  - `GET /api/github/repos/{owner}/{repo}/branches`: Get branches
  - `GET /api/github/repos/{owner}/{repo}/commits`: Get commits
  - `GET /api/github/repos/{owner}/{repo}/merges`: Get recent merges

- **Slack**:
  - `POST /api/slack/messages`: Send a message to Slack
  - `GET /api/slack/channels`: List available Slack channels
  - `GET /api/slack/users`: List Slack users
  - `GET /api/slack/messages/{channel}`: Get messages from a channel
  - `POST /api/slack/upload`: Upload a file to Slack

- **Chat**:
  - `POST /api/chat`: Chat with the AI assistant
  - `POST /api/chat/upload`: Upload a file and chat with the AI assistant

## Future Improvements

1. **Authentication**: Add user authentication and authorization
2. **Real-time Updates**: Add WebSocket support for real-time updates
3. **File Upload**: Improve file upload functionality
4. **Mobile Responsiveness**: Improve mobile responsiveness
5. **Offline Support**: Add offline support with service workers
6. **Testing**: Add unit and integration tests
7. **Deployment**: Add deployment configuration for production