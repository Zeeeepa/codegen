# 🎤 Voice Automation Hub

> **Multi-Agent Orchestration Platform with Visual MCP Management**

A production-grade voice-controlled automation platform that spawns specialized sub-agents, dynamically assigns MCP tools, orchestrates event-driven workflows, and validates outputs through quality gates.

[![Windows](https://img.shields.io/badge/Windows-10%2F11-blue)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node-18%2B-brightgreen)](https://nodejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🌟 Features

### 🎯 Multi-Agent Orchestration
- **Voice → Agent Creator** → Decomposes tasks into subtasks
- **Dynamic Sub-Agent Spawning** → Specialized agents for each subtask
- **MCP Tool Assignment** → Each agent gets appropriate MCP servers
- **DAG-Based Workflows** → Event-driven inter-agent coordination
- **Quality Gates** → Automatic validation before task completion

### 🔌 Visual MCP Management
- **Real-Time Dashboard** → See all active MCP servers
- **One-Click Installation** → Install from 500+ available MCPs
- **Dynamic Assignment** → Assign MCPs to agents visually
- **Live Status Monitoring** → Connection health, logs, metrics

### 🎙️ Voice Interface
- **Push-to-Talk** → Web Speech API integration
- **Text-to-Speech** → Natural voice responses
- **Command Recognition** → Intelligent intent parsing
- **Progress Narration** → Hear updates as agents work

### 🤖 Automation Tools
- **CLI Executor** → Run PowerShell/CMD commands
- **Browser Automation** → Playwright-powered web control
- **Test Runner** → pytest integration with live results
- **Research Agent** → Web search + document synthesis

### 📊 Real-Time Monitoring
- **Agent Hierarchy Tree** → Visual parent/child relationships
- **Workflow Canvas** → Interactive DAG visualization
- **Progress Timeline** → Live execution tracking
- **Event Stream** → WebSocket-powered live updates
- **Webhook Integration** → External system notifications

## 🏗️ Architecture

```
Voice Command
    ↓
┌─────────────────────────────────────────┐
│   🧠 Agent Creator (Orchestrator)       │
│   - Task decomposition                  │
│   - Sub-agent spawning                  │
│   - Workflow definition                 │
│   - Quality gate setup                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   🤖 Sub-Agents + MCP Assignment        │
│                                         │
│   [Research Agent]                      │
│    ├─ MCP: Context7, Tavily            │
│    └─ Webhook: /webhook/agent-1        │
│                                         │
│   [Code Analyzer]                       │
│    ├─ MCP: GitHub, AST Parser          │
│    └─ Webhook: /webhook/agent-2        │
│                                         │
│   [Report Generator]                    │
│    ├─ MCP: Markdown, PDF               │
│    └─ Webhook: /webhook/agent-3        │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   🔄 Workflow Engine                    │
│   - Event-driven execution              │
│   - Progress emission (WebSocket)       │
│   - Webhook coordination                │
│   - Error handling & retries            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   ✅ Quality Gates                      │
│   - Completion validation               │
│   - Output quality checks               │
│   - Error detection                     │
│   - Success criteria                    │
└─────────────────────────────────────────┘
    ↓
🎤 Voice Response + Visual Dashboard
```

## 🚀 Quick Start

### Prerequisites
- **Windows 10/11**
- **Python 3.10+**
- **Node.js 18+**
- **OpenAI API Key**

### Installation

#### Option 1: Automated Windows Setup (Recommended)
```powershell
# Run as Administrator
cd voice-automation-hub
.\scripts\windows\setup.ps1
```

#### Option 2: Manual Setup
```bash
# Backend
cd voice-automation-hub/backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Frontend
cd ../frontend
npm install

# Environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Running

#### Start Backend
```bash
cd voice-automation-hub/backend
python server.py
# Backend runs on http://localhost:8000
```

#### Start Frontend
```bash
cd voice-automation-hub/frontend
npm run dev
# Frontend runs on http://localhost:3000
```

### First Commands

1. **Open** → http://localhost:3000
2. **Click** → Microphone button
3. **Say** → "Create an agent to research Python tutorials"
4. **Watch** → Multi-agent workflow executes with live progress
5. **Hear** → TTS response with results

## 📖 Example Workflows

### 1. Code Analysis Pipeline
```
Voice: "Analyze my GitHub repos and run tests"

→ Spawns Research Agent (GitHub MCP)
  ├─ Fetches repo list
  ├─ Progress: 25%
  └─ Webhook fires → triggers next agent

→ Spawns Code Analyzer (AST MCP)
  ├─ Analyzes code patterns
  ├─ Progress: 50%
  └─ Webhook fires → triggers next agent

→ Spawns Test Runner (pytest)
  ├─ Runs test suite
  ├─ Progress: 75%
  └─ Webhook fires → triggers next agent

→ Spawns Report Generator (Markdown MCP)
  ├─ Creates summary
  ├─ Progress: 100%
  └─ Quality gates validate

✅ Complete: "Analysis found 3 issues, all tests passed"
```

### 2. Research & Synthesis
```
Voice: "Research AI agents and create a summary"

→ Spawns Research Agent (Context7 + Tavily)
→ Spawns Summarizer Agent (OpenAI)
→ Quality gates check output quality
✅ Complete: Summary with citations
```

### 3. Web Automation
```
Voice: "Open Google, search for Python docs, take screenshot"

→ Spawns Browser Agent (Playwright MCP)
→ Real-time screenshots shown
✅ Complete: Screenshot saved
```

## 🎨 Visual Dashboard

### MCP Server Management
<img src="docs/images/mcp-dashboard.png" width="600" alt="MCP Dashboard" />

- See all installed MCP servers
- Install new servers with one click
- Assign MCPs to agents
- Monitor connection health

### Agent Hierarchy Tree
<img src="docs/images/agent-tree.png" width="600" alt="Agent Tree" />

- Visual parent/child relationships
- Real-time status updates
- Progress bars for each agent
- Webhook status indicators

### Workflow Canvas
<img src="docs/images/workflow-canvas.png" width="600" alt="Workflow Canvas" />

- Interactive DAG visualization
- Drag-and-drop workflow building
- Live execution highlighting
- Quality gate checkpoints

## 🔧 Configuration

### Environment Variables
```bash
# .env file
OPENAI_API_KEY=sk-...              # Required for LLM
TAVILY_API_KEY=tvly-...            # Optional for research
PORT=8000                          # Backend port
FRONTEND_URL=http://localhost:3000 # CORS
```

### MCP Server Registry
Edit `backend/mcp_manager/mcp_registry.py` to add custom MCP servers:
```python
CUSTOM_MCPS = {
    "my-custom-mcp": {
        "name": "My Custom MCP",
        "install_command": "npm install -g my-custom-mcp",
        "start_command": "my-custom-mcp",
        "capabilities": ["tool1", "tool2"]
    }
}
```

### Quality Gates
Define custom validation in `backend/orchestration/quality_gates.py`:
```python
class CustomQualityGate(QualityGate):
    async def validate(self, workflow: Workflow) -> bool:
        # Your validation logic
        return True
```

## 📚 Documentation

- [🏗️ Architecture Guide](docs/ARCHITECTURE.md)
- [🔌 MCP Integration](docs/MCP_GUIDE.md)
- [🤖 Multi-Agent Orchestration](docs/MULTI_AGENT.md)
- [🔗 Webhook System](docs/WEBHOOKS.md)
- [✅ Quality Gates](docs/QUALITY_GATES.md)
- [🛠️ API Reference](docs/API.md)
- [🐛 Troubleshooting](docs/TROUBLESHOOTING.md)

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## 🌐 API Endpoints

### Backend API
- `GET /` - Health check
- `POST /api/sessions` - Create ChatKit session
- `POST /api/chatkit` - Main ChatKit endpoint (SSE)
- `POST /api/voice/transcribe` - Whisper transcription
- `GET /api/health` - Detailed health status

### WebSocket Events
- `agent.progress` - Progress updates
- `agent.complete` - Completion notifications
- `workflow.update` - Workflow state changes
- `mcp.status` - MCP server status

### Webhook Events
- `POST /webhook/agent/{agent_id}` - Agent completion
- `POST /webhook/workflow/{workflow_id}` - Workflow events

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

- Built with [OpenAI ChatKit](https://github.com/openai/chatkit)
- MCP Protocol by [Anthropic](https://modelcontextprotocol.io)
- Inspired by [AutoGen](https://github.com/microsoft/autogen) and [LangChain](https://github.com/langchain-ai/langchain)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Zeeeepa/codegen/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Zeeeepa/codegen/discussions)
- **Email**: support@voiceautomationhub.dev

---

**Made with ❤️ for the AI Agent Community**

