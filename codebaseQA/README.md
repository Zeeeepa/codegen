# CodebaseQA

A tool for exploring and researching codebases using AI.

## Project Structure

- `backend/`: FastAPI backend that provides the research API
- `frontend/`: Next.js frontend application

## Features

### Codebase Research
- AI-powered code exploration and research
- Semantic search across codebases
- Symbol information and definition lookup
- Codebase statistics and insights

### GitHub Project Discovery and Management
- **Project Search**: Search GitHub repositories by name, owner, description, and topics with advanced filtering options
- **Project Saving**: Save repositories to your personal dashboard for quick access
- **Repository Categorization**: Organize repositories with custom categories and tags
- **Category Filtering**: Filter your saved repositories by categories with custom views
- **Trending Repositories**: Discover trending GitHub repositories by day, week, or month
- **Personalized Recommendations**: Get repository suggestions based on your interests and saved projects
- **Repository Dashboard**: Comprehensive dashboard with sorting, filtering, and search capabilities

## Running Locally

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - You'll need to set up the appropriate API keys for the language models
   - For OpenAI, set `OPENAI_API_KEY` environment variable
   - For GitHub API, set `GITHUB_API_KEY` environment variable
   - For other required secrets, check the code or set up a `.env` file

4. Run the backend server:
   ```
   python api.py
   ```
   
   This will start the FastAPI server at http://localhost:8000

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run dev
   ```

   This will start the Next.js development server at http://localhost:3000

## Deploying to Modal

If you want to deploy the backend to Modal:

1. Make sure you have Modal CLI installed and configured:
   ```
   pip install modal
   modal token new
   ```

2. Deploy the backend:
   ```
   cd backend
   DEPLOY_TO_MODAL=true python api.py
   ```

## API Endpoints

### Codebase Research
- `POST /research`: Perform research on a codebase
- `POST /research/stream`: Stream research results
- `POST /similar-files`: Find similar files in a codebase
- `POST /codebase-stats`: Get statistics about a codebase
- `POST /symbol-info`: Get information about a symbol in the codebase

### GitHub Project Management
- `GET /github/search`: Search for GitHub repositories
- `GET /github/trending`: Get trending GitHub repositories
- `GET /github/recommendations`: Get personalized repository recommendations
- `POST /user/repositories`: Save a repository to user's dashboard
- `DELETE /user/repositories/{id}`: Remove a repository from user's dashboard
- `GET /user/repositories`: Get user's saved repositories
- `POST /user/categories`: Create a new repository category
- `PUT /user/categories/{id}`: Update a repository category
- `DELETE /user/categories/{id}`: Delete a repository category
- `GET /user/categories`: Get user's repository categories
- `POST /user/views`: Create a custom dashboard view
- `GET /user/views`: Get user's custom dashboard views

## Implementation Phases

### Phase 1 (MVP)
- Basic GitHub repository search
- Save repositories to dashboard
- Simple categorization system
- Basic trending repositories view
- Essential user authentication

### Phase 2
- Advanced search capabilities
- Enhanced categorization with multi-category assignment
- Custom views and filters
- Personalized recommendations
- Repository details and quick actions

### Phase 3
- Collaboration features
- Advanced analytics and insights
- Integration with external tools
- Mobile application support
