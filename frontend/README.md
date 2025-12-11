# CodeGen Chain Dashboard - Enhanced Frontend

A sophisticated React-based dashboard for orchestrating AI agent workflows with the CodeGen API.

## 🚀 Features

### Core Capabilities
- **Advanced Chain Orchestration**: Create and execute complex multi-step AI workflows
- **Intelligent Context Management**: Automatic context passing between agent runs with token optimization
- **Parallel Execution**: Run multiple agents simultaneously with configurable merge strategies
- **Error Analysis & Recovery**: Built-in error analysis with automatic retry and debugging
- **Template System**: Pre-built templates for common workflows (debugging, implementation, testing, deployment)
- **Real-time Monitoring**: Live updates of chain executions with detailed step tracking

### Enhanced Features
1. **Smart Context Passing**
   - Accumulate mode: Full context from all previous steps
   - Selective mode: Only last success + errors
   - Minimal mode: Bare minimum context
   - Token limit enforcement

2. **Task-Type System**
   - Implementation, Testing, Debugging, Refactoring, Documentation, Review, Deployment
   - Pre-built prompt templates with variable substitution
   - Task-specific context strategies

3. **Parallel Debugging**
   - Visual error tracking across parallel branches
   - Branch-level error analysis
   - Configurable merge strategies (wait-all, wait-any, race)

4. **Error Handling**
   - Conditional steps with retry logic
   - Error analysis with suggested fixes
   - Escalating debug levels
   - Global retry configuration

## 📦 Installation

```bash
cd frontend
npm install
```

## 🏃 Running the Application

### Development Mode (Port 3000)
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm run preview
```

### Testing
```bash
npm run test
npm run typecheck
npm run lint
```

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ChainConfigDialog.tsx
│   │   ├── ChainExecutionView.tsx
│   │   ├── ParallelBranchView.tsx
│   │   └── ErrorAnalysisPanel.tsx
│   ├── pages/               # Page components
│   │   ├── Dashboard.tsx
│   │   ├── ChainList.tsx
│   │   └── ActiveChains.tsx
│   ├── services/            # API and business logic
│   │   ├── api.ts          # CodeGen API client
│   │   └── chainExecutor.ts # Chain execution engine
│   ├── utils/               # Utility functions
│   │   └── contextManager.ts # Context management
│   ├── templates/           # Chain and prompt templates
│   │   └── chainTemplates.ts
│   ├── types/               # TypeScript definitions
│   │   └── index.ts
│   └── App.tsx              # Root component
├── public/                  # Static assets
├── config/                  # Configuration files
├── package.json
├── vite.config.ts          # Vite configuration (Port 3000)
├── tsconfig.json
└── tailwind.config.js
```

## 🎨 Chain Templates

### 1. Fix Until Works
**Category**: Debugging  
**Description**: Automatically retry fixes until tests pass  
**Features**:
- Conditional execution with up to 5 retries
- Intelligent error analysis
- Context-aware retry prompts

### 2. Implement → Test → Document
**Category**: Workflow  
**Description**: Complete feature development pipeline  
**Steps**:
1. Implementation
2. Comprehensive testing
3. Documentation generation

### 3. Review → Refactor → Optimize
**Category**: Quality  
**Description**: Code quality improvement pipeline  
**Steps**:
1. Code review
2. Refactoring
3. Performance optimization

### 4. Parallel Feature Development
**Category**: Workflow  
**Description**: Simultaneous component development  
**Features**:
- Frontend + Backend + Tests in parallel
- Configurable merge strategies
- Integration step after parallel execution

### 5. Debug Cascade
**Category**: Debugging  
**Description**: Progressive debugging with escalating detail  
**Features**:
- Escalating verbosity levels
- Diagnostic report generation
- Error history tracking

### 6. Deployment Pipeline
**Category**: Deployment  
**Description**: Automated CI/CD workflow  
**Steps**:
1. Code changes
2. Test execution
3. Build (with retry)
4. Staging deployment

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the `frontend` directory:

```env
VITE_API_BASE_URL=https://api.codegen.com/v1
VITE_DEFAULT_MODEL=Sonnet 4.5
VITE_MAX_CONTEXT_TOKENS=8000
```

### Context Strategies

```typescript
{
  mode: 'accumulate',    // or 'selective', 'minimal'
  maxTokens: 8000,       // Token limit for context
  includeErrors: true,   // Include error history
  includeLogs: false     // Include execution logs
}
```

### Error Handling

```typescript
{
  autoRetry: true,           // Enable automatic retries
  maxGlobalRetries: 3,       // Max retries at chain level
  escalateOnFailure: true,   // Escalate to higher model on failure
  notifyOnError: true        // Send notifications on errors
}
```

## 📝 Usage Examples

### Creating a Custom Chain

```typescript
const customChain: ChainConfig = {
  name: 'Custom Workflow',
  description: 'My custom agent workflow',
  repoId: '123',
  steps: [
    {
      type: 'initial',
      prompt: 'Analyze the codebase for security vulnerabilities',
      model: 'Sonnet 4.5',
      taskType: 'review'
    },
    {
      type: 'sequential',
      prompt: 'Fix the vulnerabilities found: {{result}}',
      model: 'Sonnet 4.5',
      taskType: 'implementation',
      waitForPrevious: true
    },
    {
      type: 'conditional',
      maxRetries: 3,
      successCondition: 'all_tests_pass',
      retryPrompt: 'Tests failed: {{error}}. Fix and retry.',
      model: 'Sonnet 4.5',
      taskType: 'debugging',
      errorAnalysis: true
    }
  ],
  contextStrategy: {
    mode: 'accumulate',
    maxTokens: 6000,
    includeErrors: true
  }
};
```

### Using Task Prompt Templates

```typescript
import { getTaskPrompt } from '@/templates/chainTemplates';

const prompt = getTaskPrompt('implementation', {
  feature_name: 'User Authentication',
  requirements: 'Email/password login with OAuth2 support'
});
```

### Context Management

```typescript
import { contextManager } from '@/utils/contextManager';

// Build context from previous steps
const context = contextManager.buildContext(
  steps,
  'selective',  // mode
  true          // includeErrors
);

// Replace template variables
const prompt = contextManager.replaceTemplateVariables(
  'Fix the issue: {{error}} from step {{step_1_result}}',
  contextSnapshot
);
```

## 🔬 Advanced Features

### Parallel Branch Debugging

When parallel branches execute, the dashboard provides:
- Individual branch status tracking
- Per-branch error analysis
- Visual diff of branch results
- Merge conflict detection

### Error Analysis

The system automatically analyzes errors and provides:
- Root cause analysis
- Suggested fixes with confidence scores
- Historical error patterns
- Recovery strategies

### Context Snapshots

Each execution step creates a context snapshot containing:
- Step results indexed by step number
- Global execution state
- Error history with timestamps
- Execution metrics

## 🎯 API Integration

### CodeGen API Endpoints Used

```typescript
// Create agent run
POST /organizations/{orgId}/agent/run
{
  "prompt": "string",
  "model": "Sonnet 4.5",
  "agent_type": "codegen",
  "repo_id": 123
}

// Get run status
GET /organizations/{orgId}/agent/run/{runId}

// Resume run
POST /organizations/{orgId}/agent/run/resume
{
  "agent_run_id": "string",
  "prompt": "string"
}
```

## 🐛 Debugging

### Enable Debug Logs

```typescript
// In chainExecutor.ts
execution.logs.push({
  timestamp: new Date(),
  level: 'debug',
  message: 'Detailed debug information',
  metadata: { /* additional context */ }
});
```

### View Execution Logs

Logs are stored in the `ChainExecution` object and displayed in the UI.

## 🚀 Performance Optimization

1. **Token Management**: Automatic truncation to stay within limits
2. **Selective Context**: Minimize context size while preserving relevance
3. **Parallel Execution**: Reduce total execution time
4. **Caching**: Store template results for reuse

## 📊 Monitoring

The dashboard provides real-time metrics:
- Active chains count
- Active runs count
- Success/failure rates
- Average execution time per step
- Error patterns

## 🤝 Contributing

1. Follow TypeScript best practices
2. Add tests for new features
3. Update documentation
4. Use consistent code formatting

## 📄 License

MIT

## 🆘 Support

For issues or questions:
1. Check existing issues on GitHub
2. Review API documentation
3. Contact support team

---

**Built with ❤️ for AI-powered development workflows**

