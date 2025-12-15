# Frontend Setup Guide

## Iris-Enhanced Codegen Frontend

This frontend is powered by **Iris optimization framework** and uses **agent chaining** via Codegen REST API.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Iris

Iris configuration is already set up in `frontend/.iris/config.yaml`. No manual configuration needed!

### 3. Set Environment Variables

Create `.env` file:

```bash
VITE_CODEGEN_API_BASE=https://api.codegen.com
VITE_CODEGEN_ORG_ID=your-org-id
VITE_CODEGEN_TOKEN=your-api-token
```

### 4. Run Development Server

```bash
npm run dev
```

---

## 🎯 User Flow

### Complete PRD → Implementation Flow

```
1. Launch Frontend
   ↓
2. Navigate to "PRD to Implementation" tab
   ↓
3. Select Repository (dropdown with your repos)
   ↓
4. Create/Edit PRD (text editor with templates)
   ↓
5. Press "Implement" Button
   ↓
6. Watch Agent Chain Execute:
   - Developer Agent (implement feature)
   - Visual Testing Agent (UI/UX validation)
   - Validator Agent (real-life testing)
   - Debugging Agent (if errors detected)
   - PR Agent (create pull request)
   - Commit Agent (commit changes)
   - Reflection Agent (self-review)
   - Validation Agent (final approval)
   ↓
7. View Results (PR link, commit hash, validation report)
```

---

## 🤖 How Agent Chaining Works

### The Core Pattern: **WAIT FOR STATE CHANGE → RESUME WITH NEXT TASK**

```typescript
// Step 1: Create agent run
const { agentRunId } = await createAgentRun(orgId, token, {
  task: "Implement feature X",
  context: { prd, mcp, templates }
});

// Step 2: Watch status (poll every 2s)
while (true) {
  const status = await getAgentRunStatus(orgId, token, agentRunId);
  
  if (status === "completed") {
    // Step 3: Resume with next task
    await resumeAgentRun(orgId, token, agentRunId, {
      task: "Now run visual tests",
      context: { previousResult, testTemplates }
    });
    break;
  }
  
  await sleep(2000);
}

// Step 4: Repeat for entire chain
```

**That's it!** No complex event streaming, no WebSockets. Just:
- Poll status
- Wait for "completed"
- Resume with next task + updated context

---

## 📂 Project Structure

```
frontend/
├── .iris/
│   ├── config.yaml          # Iris configuration
│   ├── templates/           # Task templates
│   └── learning/            # Pattern storage
│
├── src/
│   ├── orchestration/
│   │   └── agentChain.ts    # Agent chaining logic
│   │
│   ├── services/
│   │   └── codegenApi.ts    # Codegen REST API client
│   │
│   ├── components/
│   │   ├── PRDToImplementation.tsx   # Main UI
│   │   ├── AgentChainMonitor.tsx     # Real-time monitoring
│   │   └── RepositorySelector.tsx    # Repo selection
│   │
│   ├── store/               # Zustand state management
│   │   ├── index.ts         # Main store
│   │   ├── profileSlice.ts  # Profile management
│   │   └── chainSlice.ts    # Chain execution state
│   │
│   └── schemas/
│       ├── profiles.ts      # Profile types
│       └── chains.ts        # Chain types
│
└── tests/
    ├── e2e/
    │   └── prd-to-implementation.spec.ts
    └── integration/
        └── agentChain.test.ts
```

---

## 🎨 Key Features

### 1. **Repository Selection**
- Dropdown populated with user's repositories
- Fetched from Codegen API
- Cached in local storage

### 2. **PRD Editor**
- Rich text editor with Markdown support
- Template library (SaaS, API, CLI, etc.)
- Auto-save to local storage
- Import from file (MD, PDF, DOCX)

### 3. **Agent Chain Configuration**
- Pre-configured chains (Feature Implementation, Bug Fix, etc.)
- Custom chain builder (drag-and-drop agents)
- Conditional branching (if errors, run debugging agent)

### 4. **Real-Time Monitoring**
- Live progress bar
- Agent status indicators
- Log stream
- Performance metrics (duration, token usage)

### 5. **Result Visualization**
- Success/failure indicators
- Detailed result per agent
- PR link (clickable)
- Commit hash (clickable)
- Validation report (downloadable)

---

## 🔧 Configuration

### Iris Configuration (`.iris/config.yaml`)

```yaml
chain:
  timeout: 1800000        # 30 min max per chain
  pollInterval: 2000      # Poll status every 2s
  
agents:
  developer:
    model: "sonnet"
    timeout: 600000       # 10 min per agent
  
context:
  maxSize: 100000         # 100KB max context
  compressionEnabled: true
```

### Environment Variables

```bash
VITE_CODEGEN_API_BASE=https://api.codegen.com
VITE_CODEGEN_ORG_ID=your-org-id
VITE_CODEGEN_TOKEN=your-api-token
```

---

## 🧪 Testing

### Run E2E Tests

```bash
npm run test:e2e
```

Tests include:
- PRD to implementation flow
- Agent chaining logic
- Error handling
- Timeout scenarios

### Run Integration Tests

```bash
npm run test:integration
```

Tests include:
- API integration
- State management
- Context building

---

## 🚢 Deployment

### Build for Production

```bash
npm run build
```

### Deploy to Vercel

```bash
vercel --prod
```

### Deploy to Cloudflare Pages

```bash
npm run build
wrangler pages publish dist
```

---

## 📚 Documentation

### Agent Chain API

See `src/orchestration/agentChain.ts` for complete API documentation.

Key classes:
- `AgentChainExecutor` - Main executor
- `createFeatureImplementationChain()` - Pre-configured chain

### Codegen API

See `src/services/codegenApi.ts` for API wrapper.

Key functions:
- `createAgentRun()` - Start agent run
- `getAgentRunStatus()` - Poll status
- `resumeAgentRun()` - Resume with next task

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Create pull request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🆘 Support

- GitHub Issues: [Report a bug](https://github.com/your-org/codegen/issues)
- Discord: [Join our community](https://discord.gg/codegen)
- Docs: [Read the documentation](https://docs.codegen.com)

---

**Happy Building! 🚀**

