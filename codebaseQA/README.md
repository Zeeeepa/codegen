# CodebaseQA

A tool for exploring and researching codebases using AI.

## Project Structure

- `backend/`: FastAPI backend that provides the research API
- `frontend/`: Next.js frontend application

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

- `POST /research`: Perform research on a codebase
- `POST /research/stream`: Stream research results
- `POST /similar-files`: Find similar files in a codebase
- `POST /codebase-stats`: Get statistics about a codebase
- `POST /symbol-info`: Get information about a symbol in the codebase
