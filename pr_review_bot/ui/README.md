# PR Review Bot UI

A modern web interface for the PR Review Bot, built with FastAPI and Next.js.

## Structure

The UI is divided into two main components:

- `backend/`: FastAPI backend that provides API endpoints for the frontend
- `frontend/`: Next.js frontend application that displays the dashboard

## Backend

The backend is built with FastAPI and provides the following endpoints:

- `/api/dashboard`: Get the main dashboard data
- `/api/repositories`: Get all repositories
- `/api/errors`: Get all errors
- `/api/repository/{repo_name}`: Get details for a specific repository

### Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

The backend will run on http://localhost:8000 by default.

## Frontend

The frontend is built with Next.js and uses:

- TypeScript for type safety
- Tailwind CSS for styling
- SWR for data fetching
- React Icons for icons

### Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will run on http://localhost:3000 by default.

## Development

During development, the frontend proxies API requests to the backend using Next.js rewrites. This is configured in `next.config.js`.

## Production

For production, you should:

1. Build the frontend: `cd frontend && npm run build`
2. Configure a proper reverse proxy (like Nginx) to serve both the frontend and backend
3. Set up proper CORS configuration in the backend

## Screenshots

(Screenshots will be added once the UI is deployed)

## Future Improvements

- Add authentication
- Add more detailed repository views
- Add user management
- Add notification settings
- Add dark mode support