# Codegen REST Dashboard

A comprehensive dashboard for monitoring and managing Codegen AI agent runs in real-time. Built with Node.js, Express, React, and WebSocket for live updates.

## Features

### 🚀 Core Functionality
- **Real-time Agent Monitoring**: Live tracking of active agent runs with automatic status updates
- **Interactive Dashboard**: Single-tab interface with filtering between active and past runs
- **Streaming Logs**: Click any run to view real-time logs and agent state in a modal dialog
- **Run Pinning**: Pin important runs to keep them visible regardless of filters
- **Model Selection**: Choose from supported AI models (Sonnet 4.5, GPT-5, etc.) when creating runs
- **Auto-refresh**: Automatic polling of run status every 30 seconds

### 🔄 Advanced Features
- **Chained Prompts**: Create template-based prompt chains that execute automatically upon run completion
- **Webhook Integration**: Cloudflare Workers webhook handler for real-time completion notifications
- **Browser Notifications**: Desktop notifications when runs complete
- **Template Management**: CRUD interface for managing prompt templates
- **Resume Functionality**: Continue paused agent runs with new prompts

### 🛠️ Technical Features
- **WebSocket Real-time Updates**: Live synchronization across all connected clients
- **REST API Commands**: Complete CLI interface for all Codegen API operations
- **Error Boundaries**: Comprehensive error handling with user-friendly messages
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **PWA Ready**: Installable web app with offline capabilities

## Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Codegen API credentials

### Installation

1. **Clone and setup**:
```bash
cd CodegenRestDashboard
npm install
cd dashboard && npm install
```

2. **Configure environment**:
```bash
# Copy and edit the .env file
cp .env.example .env
# Edit .env with your Codegen token and org ID
```

3. **Start the application**:
```bash
# Start backend server
npm start

# In another terminal, start frontend
cd dashboard && npm start
```

4. **Access the dashboard**:
Open http://localhost:3000 in your browser

### Environment Configuration

Create a `.env` file with:
```env
CODEGEN_TOKEN=sk-your-codegen-token-here
ORG_ID=your-org-id
PORT=3001
NODE_ENV=development
WEBHOOK_SECRET=your-webhook-secret
CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
```

## API Commands

The dashboard includes a complete CLI interface for Codegen operations:

```bash
# Create a new agent run
node commands/create_agent_run.js "Your prompt here" --model "Sonnet 4.5"

# Resume a paused run
node commands/resume_agent_run.js 123 "Continue with this..."

# List agent runs
node commands/list_agent_runs.js --status active --limit 50

# Get detailed run info
node commands/get_agent_run.js 123

# Generate setup commands
node commands/generate_setup_commands.js --repo-id 456 --prompt "Setup Node.js project"
```

## Webhook Integration

### Cloudflare Workers Setup

1. **Deploy webhook handler**:
```bash
# Install Wrangler CLI
npm install -g wrangler

# Configure Cloudflare
wrangler auth login

# Deploy webhook worker
wrangler deploy webhook_server.js
```

2. **Configure webhook URL**:
Set up your webhook endpoint at `www.pixelium.uk/webhook` to point to the deployed worker.

3. **Environment variables** for webhook worker:
```env
DASHBOARD_URL=http://your-dashboard-url:3001/webhook
WEBHOOK_SECRET=your-secret-for-verification
```

## Chained Prompts

Create automated workflows where agent runs trigger follow-up actions:

1. **Create Templates**: Use the Templates tab to define prompt templates
2. **Apply Chains**: Select templates when creating or resuming runs
3. **Automatic Execution**: Chains execute automatically when runs complete

Example template:
```json
{
  "name": "Code Review Follow-up",
  "prompt": "Review the following code changes and suggest improvements: {{result}}",
  "trigger_condition": "completion",
  "variables": {
    "result": "{{result}}",
    "run_id": "{{run_id}}"
  }
}
```

## Testing

### End-to-End Tests
```bash
# Install Playwright browsers
npx playwright install

# Run E2E tests
npm run test:e2e

# Run with UI
npx playwright test --ui
```

### Manual Testing Checklist
- [ ] Dashboard loads without errors
- [ ] Active runs count updates in header
- [ ] Run creation works with different models
- [ ] Logs stream in real-time
- [ ] Pinning functionality works
- [ ] Tab switching works
- [ ] Templates can be created and managed
- [ ] Webhook notifications work
- [ ] Responsive design on mobile/tablet
- [ ] Error handling works gracefully

## Architecture

### Backend (Express + WebSocket)
- **Server**: Express.js with CORS, security middleware
- **Real-time**: WebSocket server for live updates
- **API**: REST endpoints for Codegen operations
- **Webhook**: Handler for completion notifications

### Frontend (React)
- **State Management**: React hooks with WebSocket integration
- **UI**: Material-UI components with responsive design
- **Real-time**: Automatic updates via WebSocket
- **Error Handling**: Error boundaries and user feedback

### Commands (CLI)
- **API Client**: Shared client with authentication
- **Operations**: Create, resume, list, get agent runs
- **Setup Commands**: Repository initialization

## Development

### Project Structure
```
CodegenRestDashboard/
├── server.js                 # Express server with WebSocket
├── webhook_server.js        # Cloudflare webhook handler
├── commands/                 # CLI commands
│   ├── apiClient.js         # Shared API client
│   ├── create_agent_run.js
│   ├── resume_agent_run.js
│   └── ...
├── dashboard/               # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API services
│   │   └── ...
│   └── public/
├── tests/                   # E2E tests
└── .env                     # Environment config
```

### Available Scripts
```bash
# Development
npm run dev          # Start backend with nodemon
npm start           # Start production server

# Frontend
cd dashboard
npm start           # Start React dev server
npm run build       # Build for production

# Testing
npm run test:e2e    # Run Playwright tests
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check the troubleshooting section below
- Open an issue on GitHub
- Review the Codegen API documentation

## Troubleshooting

### Common Issues

**Dashboard not loading**:
- Check that both backend (port 3001) and frontend (port 3000) are running
- Verify environment variables are set correctly
- Check browser console for errors

**API calls failing**:
- Verify CODEGEN_TOKEN and ORG_ID in .env
- Check token permissions and expiration
- Review API rate limits

**WebSocket not connecting**:
- Ensure backend server is running on port 3001
- Check firewall settings
- Verify WebSocket URL in frontend

**Webhook not working**:
- Confirm Cloudflare worker is deployed
- Check webhook URL configuration
- Verify webhook secret matches

### Logs and Debugging

Enable debug logging:
```bash
DEBUG=* npm start
```

Check application logs in the terminal where servers are running.

