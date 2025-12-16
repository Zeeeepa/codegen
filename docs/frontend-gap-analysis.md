# 🔍 Controller Dashboard Frontend Gap Analysis (IRIS Report)

**Date**: December 15, 2025  
**Analysis Method**: IRIS (Intelligent Requirements and Implementation Solution)  
**Scope**: Controller Dashboard Web Frontend  
**Status**: ⚠️ **CRITICAL GAPS IDENTIFIED**

---

## Executive Summary

The Controller Dashboard backend implementation is **100% complete and production-ready**, with comprehensive Python CLI/TUI functionality. However, **0% of web frontend exists**. This represents a complete greenfield web development project.

### Quick Stats
- **Backend Completion**: ✅ 100% (2,360 lines, 6 files)
- **TUI Completion**: ✅ 100% (Terminal UI fully functional)
- **Web Frontend**: ❌ 0% (No web UI components exist)
- **Estimated Frontend Effort**: 16-20 weeks for production-ready web app

---

## 📊 Current State Analysis

### ✅ What EXISTS (Terminal UI)

**Python-Based Terminal Interface** (`src/codegen/cli/tui/`)
- `MinimalTUI` class with 1100+ lines of ANSI rendering
- Keyboard navigation (↑↓ arrows, space, enter, tab, q)
- 5 controller tabs:
  - `workflows` - Workflow management
  - `sandboxes` - Execution monitoring
  - `monitoring` - Real-time metrics
  - `projects` - Placeholder
  - `prds` - Placeholder
- Color scheme:
  - Purple: `RGB(82,19,217)` - Primary accent
  - Orange: `RGB(255,202,133)` - Active state
  - Green: `RGB(66,196,153)` - Success
  - Red: `RGB(255,103,103)` - Error
- Auto-refresh: Every 10 seconds (configurable)
- Status visualization: Kanban-style with colored indicators

### ❌ What is MISSING (Web Frontend)

**Zero Web UI Components:**
```bash
$ find . -name "*.tsx" -o -name "*.jsx" | grep -v node_modules
./docs/samples/sample.tsx        # Documentation example only
./docs/settings/repo-rules.tsx   # Documentation example only
```

**No Web Infrastructure:**
- No `package.json` or `node_modules/`
- No React, Vue, or Angular setup
- No build system (Webpack, Vite, Parcel)
- No component library
- No state management
- No routing system

---

## 🚨 Critical Gaps Identified

### Gap #1: No Web Dashboard Framework
**Impact**: 🔴 CRITICAL  
**Effort**: 8 weeks  
**Priority**: P0

**Missing Components:**
- Modern web framework (React 18+ recommended)
- TypeScript configuration
- Build tooling (Vite recommended for speed)
- Component library (Tailwind CSS + shadcn/ui recommended)
- State management (Zustand or Jotai for simplicity)
- Routing (React Router v6)
- HTTP client (TanStack Query + Axios)

**Evidence:**
```bash
# No frontend directory exists
$ ls -la | grep -E "(frontend|web|ui|app)"
# No results
```

**What Should Exist:**
```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard/
│   │   │   ├── WorkflowList.tsx
│   │   │   ├── WorkflowCard.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   └── MetricsPanel.tsx
│   │   ├── Workflows/
│   │   │   ├── WorkflowToggle.tsx
│   │   │   ├── WorkflowDetails.tsx
│   │   │   ├── WorkflowScheduler.tsx
│   │   │   └── WorkflowForm.tsx
│   │   ├── Sandboxes/
│   │   │   ├── SandboxList.tsx
│   │   │   ├── SandboxMonitor.tsx
│   │   │   ├── LogViewer.tsx
│   │   │   └── MetricsChart.tsx
│   │   ├── Projects/
│   │   │   ├── ProjectList.tsx
│   │   │   ├── ProjectForm.tsx
│   │   │   └── TeamManager.tsx
│   │   ├── PRDs/
│   │   │   ├── PRDEditor.tsx
│   │   │   ├── VersionHistory.tsx
│   │   │   └── RequirementTracker.tsx
│   │   └── common/
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Input.tsx
│   │       └── Modal.tsx
│   ├── pages/
│   │   ├── DashboardPage.tsx
│   │   ├── WorkflowsPage.tsx
│   │   ├── MonitoringPage.tsx
│   │   ├── ProjectsPage.tsx
│   │   └── PRDsPage.tsx
│   ├── api/
│   │   ├── controllerClient.ts
│   │   ├── websocket.ts
│   │   └── types.ts
│   ├── store/
│   │   ├── workflowStore.ts
│   │   ├── sandboxStore.ts
│   │   └── authStore.ts
│   ├── hooks/
│   │   ├── useWorkflows.ts
│   │   ├── useWebSocket.ts
│   │   └── useAuth.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   └── validators.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── public/
│   └── assets/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

**Current Reality**: NONE of this exists

---

### Gap #2: API Layer Not Frontend-Optimized
**Impact**: 🔴 CRITICAL  
**Effort**: 2 weeks  
**Priority**: P0

**Missing Features:**
1. **Pagination**: APIs likely return full lists (bad for performance)
2. **Filtering/Sorting**: No query parameters for advanced searches
3. **WebSocket Server**: No real-time bi-directional communication
4. **SSE (Server-Sent Events)**: No streaming for logs/metrics
5. **CORS Configuration**: No cross-origin resource sharing setup
6. **API Documentation**: No OpenAPI/Swagger spec for frontend devs
7. **Rate Limiting**: No protection against abuse
8. **Caching Headers**: No ETags or Cache-Control

**Current API Implementation** (`src/codegen/cli/api/controller_endpoints.py`):
```python
class ControllerAPI:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.auth_token = auth_token
        self.headers = {"Authorization": f"Bearer {auth_token}"}
    
    def get_workflows(self) -> dict:
        # Returns all workflows (no pagination)
        response = requests.get(f"{self.base_url}/workflows", headers=self.headers)
        return response.json()
```

**What's Needed:**
```python
# Pagination support
GET /api/v1/workflows?page=1&limit=20&sort=created_at&order=desc

# Filtering
GET /api/v1/workflows?status=enabled&tags=production

# WebSocket for real-time updates
WS /api/v1/monitor?workflows=wf-123,wf-456

# SSE for log streaming
GET /api/v1/sandboxes/{id}/logs/stream (text/event-stream)

# GraphQL (optional but powerful)
POST /graphql
{
  workflows(status: ENABLED) {
    id
    name
    metrics { tokenUsage, successRate }
  }
}
```

---

### Gap #3: No Visual Workflow Editor
**Impact**: 🟠 HIGH  
**Effort**: 4 weeks  
**Priority**: P1

**Current State:**
- Workflows defined in Python `WorkflowConfig` dataclass
- TUI shows only text list view
- No visual representation of workflow DAG (Directed Acyclic Graph)
- No drag-and-drop interface

**What's Missing:**
```typescript
// Visual workflow builder
import ReactFlow from 'reactflow';
import 'reactflow/dist/style.css';

<ReactFlow
  nodes={[
    { id: '1', type: 'trigger', data: { label: 'On Schedule' } },
    { id: '2', type: 'action', data: { label: 'Code Review' } },
    { id: '3', type: 'condition', data: { label: 'If Issues Found' } }
  ]}
  edges={[
    { id: 'e1-2', source: '1', target: '2' },
    { id: 'e2-3', source: '2', target: '3' }
  ]}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
  fitView
/>

// Libraries needed:
// - reactflow (for DAG visualization)
// - dagre (for auto-layout algorithms)
// - d3 (for custom visualizations)
```

**Competitor Examples** (Zapier, n8n, Prefect, Temporal):
- Drag-and-drop node creation
- Visual connections between workflow steps
- Real-time execution path highlighting
- Inline parameter editing
- Workflow templates gallery
- Version history with visual diff

---

### Gap #4: No Real-Time Web Monitoring
**Impact**: 🔴 CRITICAL  
**Effort**: 3 weeks  
**Priority**: P0

**Current TUI Implementation:**
- Polls API every 5 seconds
- Python background thread in `ControllerDashboard`
- ANSI text output only
- Limited to terminal window size

**What's Missing for Web:**
```typescript
// Real-time dashboard with WebSocket
import { useWebSocket } from './hooks/useWebSocket';
import { LineChart } from 'recharts';

function MonitoringDashboard() {
  const { metrics, logs, status } = useWebSocket('/api/v1/monitor');
  
  return (
    <div className="grid grid-cols-3 gap-4">
      <MetricsChart data={metrics} />
      <LogStream logs={logs} />
      <StatusGrid statuses={status} />
    </div>
  );
}

// Tech stack needed:
// - WebSocket client (native or socket.io)
// - Chart library (Recharts, Chart.js, ApexCharts)
// - Virtual scroller (react-window for large logs)
// - Real-time data synchronization (TanStack Query)
```

**Features to Implement:**
- Live metrics charts (line, bar, pie)
- Real-time log streaming with filtering
- Status indicators that update instantly
- Resource usage gauges (CPU, memory, network)
- Alerting system (toast notifications)
- Historical data comparison
- Customizable dashboard layouts (drag-and-drop widgets)

---

### Gap #5: No Project Management UI
**Impact**: 🟡 MEDIUM  
**Effort**: 2 weeks  
**Priority**: P2

**Current State:**
```python
# src/codegen/cli/tui/controller_integration.py
elif self.current_view == "projects":
    return "🚧 Projects tab placeholder 🚧"
```

**What's Needed:**
```typescript
<ProjectDashboard>
  <ProjectList />
  <ProjectCreator>
    <Form>
      <Input name="projectName" />
      <TextArea name="description" />
      <TeamSelector />
      <WorkflowSelector />
    </Form>
  </ProjectCreator>
  <ProjectSettings>
    <AccessControl />
    <Integrations />
    <Notifications />
  </ProjectSettings>
  <ProjectAnalytics>
    <MetricsOverview />
    <ActivityTimeline />
    <TeamPerformance />
  </ProjectAnalytics>
</ProjectDashboard>
```

---

### Gap #6: No PRD Editor
**Impact**: 🟡 MEDIUM  
**Effort**: 3 weeks  
**Priority**: P2

**Current State:**
```python
elif self.current_view == "prds":
    return "🚧 PRDs tab placeholder 🚧"
```

**What's Needed:**
```typescript
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';

<PRDEditor>
  <LexicalComposer initialConfig={config}>
    <RichTextPlugin />
    <MarkdownPlugin />
    <CollaborationPlugin />
    <VersionHistoryPlugin />
  </LexicalComposer>
  <RequirementList>
    <RequirementCard status="implemented" />
    <RequirementCard status="in-progress" />
    <RequirementCard status="pending" />
  </RequirementList>
  <ImplementationTracker>
    <LinkedIssues />
    <LinkedPRs />
    <TestCoverage />
  </ImplementationTracker>
</PRDEditor>

// Rich text editor options:
// - Lexical (Meta's modern editor)
// - TipTap (Vue-compatible, React adapter)
// - Slate (fully customizable)
// - Quill (simple and reliable)
```

**Features:**
- Real-time collaborative editing (CRDT)
- Markdown support
- Version history with diff view
- Commenting system
- Requirement tracking
- Implementation status
- Export to PDF/Markdown

---

### Gap #7: No Responsive Design
**Impact**: 🔴 CRITICAL  
**Effort**: 2 weeks  
**Priority**: P0

**Current State:**
- TUI is fixed-width (80-column terminal standard)
- Keyboard-only navigation
- No concept of touch interactions

**What's Needed:**
```css
/* Tailwind breakpoints */
@media (min-width: 375px)  { /* Mobile */ }
@media (min-width: 768px)  { /* Tablet */ }
@media (min-width: 1024px) { /* Desktop */ }
@media (min-width: 1920px) { /* Large Desktop */ }

/* Responsive layout example */
.dashboard {
  @apply grid grid-cols-1 gap-4;
  
  @screen md {
    @apply grid-cols-2;
  }
  
  @screen lg {
    @apply grid-cols-3;
  }
}
```

**Mobile Considerations:**
- Touch-friendly buttons (min 44x44px)
- Swipe gestures for navigation
- Collapsible sidebars
- Bottom navigation bar
- Pull-to-refresh
- Optimized data loading (pagination)

---

### Gap #8: No Authentication UI
**Impact**: 🟠 HIGH  
**Effort**: 1 week  
**Priority**: P1

**Current State:**
- CLI uses `codegen login` command
- Token stored in `~/.codegen/config`
- No web-based authentication flow

**What's Needed:**
```typescript
<AuthProvider>
  <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/signup" element={<SignupPage />} />
    <Route path="/oauth/callback" element={<OAuthCallback />} />
    <Route path="/dashboard" element={
      <ProtectedRoute>
        <DashboardPage />
      </ProtectedRoute>
    } />
  </Routes>
</AuthProvider>

// Features:
// - Email/password login
// - OAuth (GitHub, Google, GitLab)
// - 2FA support
// - Password reset flow
// - Session management
// - Remember me functionality
// - Logout everywhere
```

---

### Gap #9: No Design System
**Impact**: 🔴 CRITICAL  
**Effort**: 3 weeks  
**Priority**: P0

**Current State:**
- TUI has hardcoded ANSI colors:
  - Primary Purple: `\033[38;2;82;19;217m`
  - Orange: `\033[38;2;255;202;133m`
  - Green: `\033[38;2;66;196;153m`
  - Red: `\033[38;2;255;103;103m`
- No formal design system documentation
- No reusable components

**What's Needed:**
```typescript
// theme/colors.ts
export const colors = {
  primary: {
    DEFAULT: 'rgb(82, 19, 217)',    // Purple from TUI
    light: 'rgb(162, 119, 255)',
    dark: 'rgb(52, 12, 140)'
  },
  accent: {
    DEFAULT: 'rgb(255, 202, 133)',  // Orange from TUI
    light: 'rgb(255, 225, 180)',
    dark: 'rgb(200, 150, 80)'
  },
  success: 'rgb(66, 196, 153)',
  error: 'rgb(255, 103, 103)',
  warning: 'rgb(255, 202, 133)',
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    // ... through 900
  }
};

// Component library structure
components/
├── Button/
│   ├── Button.tsx
│   ├── Button.stories.tsx
│   ├── Button.test.tsx
│   └── Button.module.css
├── Card/
├── Input/
├── Modal/
└── ... (30+ base components)
```

**Design System Requirements:**
- Color palette (extracted from TUI)
- Typography scale
- Spacing system (4px/8px grid)
- Component library (buttons, inputs, cards, modals)
- Icon library (Lucide or Heroicons)
- Animation tokens
- Accessibility standards (WCAG 2.1 AA)
- Dark mode support

---

### Gap #10: No Build/Deploy Pipeline
**Impact**: 🔴 CRITICAL  
**Effort**: 1 week  
**Priority**: P0

**What's Missing:**
```json
// package.json
{
  "name": "controller-dashboard-ui",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint . --ext ts,tsx",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.22.0",
    "@tanstack/react-query": "^5.25.0",
    "zustand": "^4.5.0",
    "tailwindcss": "^3.4.1",
    "recharts": "^2.12.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.64",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.4.2",
    "vite": "^5.1.6",
    "vitest": "^1.3.1"
  }
}
```

**Deployment Pipeline:**
```yaml
# .github/workflows/frontend-deploy.yml
name: Deploy Frontend
on:
  push:
    branches: [main]
    paths: ['frontend/**']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run build
      - run: cd frontend && npm run test
      - name: Deploy to Vercel/Netlify/Cloudflare Pages
        run: npx vercel --prod
```

---

## 📈 Impact Assessment Matrix

| Gap # | Name | Impact | Effort (weeks) | Priority | Blocks |
|-------|------|--------|----------------|----------|--------|
| 1 | Web Dashboard Framework | 🔴 CRITICAL | 8 | P0 | 100% of web users |
| 2 | API Optimization | 🔴 CRITICAL | 2 | P0 | All frontend features |
| 3 | Visual Workflow Editor | 🟠 HIGH | 4 | P1 | Advanced workflow users |
| 4 | Real-Time Monitoring | 🔴 CRITICAL | 3 | P0 | Operations teams |
| 5 | Project Management UI | 🟡 MEDIUM | 2 | P2 | Project managers |
| 6 | PRD Editor | 🟡 MEDIUM | 3 | P2 | Product teams |
| 7 | Responsive Design | 🔴 CRITICAL | 2 | P0 | Mobile/tablet users |
| 8 | Authentication UI | 🟠 HIGH | 1 | P1 | New web users |
| 9 | Design System | 🔴 CRITICAL | 3 | P0 | UI consistency |
| 10 | Build/Deploy Pipeline | 🔴 CRITICAL | 1 | P0 | Deployment |

**Total Estimated Effort**: 29 weeks (could be parallelized to 16-20 weeks with team)

---

## 💡 Recommended Technology Stack

### Core Framework
```json
{
  "framework": "React 18+",
  "reason": "Largest ecosystem, best tooling, most hiring options"
}
```

**Alternatives Considered:**
- **Vue 3**: Simpler learning curve, but smaller ecosystem
- **Svelte**: Best performance, but less mature ecosystem
- **Angular**: Over-engineered for dashboard-style apps

### Build Tool
```json
{
  "bundler": "Vite 5+",
  "reason": "10x faster than Webpack, excellent DX, native ESM"
}
```

### Language
```json
{
  "language": "TypeScript 5+",
  "reason": "Type safety prevents bugs, better IDE support, required for scale"
}
```

### Styling
```json
{
  "styling": "Tailwind CSS 3+",
  "reason": "Utility-first, fast development, small bundle size"
}
```

**Component Library Options:**
1. **shadcn/ui** (Recommended): Unstyled, copy-paste, full control
2. **Radix UI**: Primitives for building custom components
3. **Material-UI**: Complete system but heavy
4. **Chakra UI**: Good DX but larger bundle

### State Management
```json
{
  "stateManagement": "Zustand",
  "reason": "Simple API, no boilerplate, React 18 concurrent mode ready"
}
```

**Alternatives:**
- **Jotai**: Atomic state, better for complex apps
- **Redux Toolkit**: Industry standard but verbose
- **Context API**: Built-in but performance issues at scale

### Data Fetching
```json
{
  "dataFetching": "TanStack Query (React Query)",
  "reason": "Caching, refetching, optimistic updates, devtools"
}
```

### Charts/Visualization
```json
{
  "charts": "Recharts",
  "reason": "React-native, composable, good docs, TypeScript support"
}
```

**Alternatives:**
- **Chart.js**: Imperative API, harder to integrate
- **ApexCharts**: Feature-rich but heavy
- **Victory**: Modular but verbose

### Form Handling
```json
{
  "forms": "React Hook Form",
  "reason": "Best performance, minimal re-renders, great DX"
}
```

### Testing
```json
{
  "unitTests": "Vitest",
  "e2eTests": "Playwright (already installed!)",
  "reason": "Vitest is Vite-native, Playwright for browser testing"
}
```

### Real-Time Communication
```json
{
  "websocket": "Native WebSocket API + TanStack Query",
  "reason": "No extra dependency needed, works with existing query cache"
}
```

**Alternative:** Socket.IO (if need room-based subscriptions)

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Minimal web app that displays workflow list

**Tasks:**
1. Initialize Vite + React + TypeScript project
   ```bash
   npm create vite@latest controller-dashboard-ui -- --template react-ts
   cd controller-dashboard-ui
   npm install
   ```

2. Install core dependencies
   ```bash
   npm install react-router-dom @tanstack/react-query zustand axios
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

3. Set up basic routing
   ```typescript
   // src/App.tsx
   <BrowserRouter>
     <Routes>
       <Route path="/" element={<DashboardPage />} />
       <Route path="/workflows" element={<WorkflowsPage />} />
     </Routes>
   </BrowserRouter>
   ```

4. Create API client
   ```typescript
   // src/api/controllerClient.ts
   export class ControllerClient {
     private baseUrl: string;
     private token: string;
     
     async getWorkflows() {
       return fetch(`${this.baseUrl}/workflows`, {
         headers: { Authorization: `Bearer ${this.token}` }
       }).then(r => r.json());
     }
   }
   ```

5. Build workflow list component (read-only)

**Deliverable**: Basic web app showing workflow list

---

### Phase 2: Interactivity (Weeks 3-5)
**Goal**: Toggle workflows, view details, monitor sandboxes

**Tasks:**
1. Implement workflow toggle
   ```typescript
   const toggleWorkflow = useMutation({
     mutationFn: (workflowId: string) => 
       api.toggleWorkflow(workflowId),
     onSuccess: () => queryClient.invalidateQueries(['workflows'])
   });
   ```

2. Add workflow details modal
3. Build sandbox monitoring view
4. Implement basic metrics display
5. Add loading/error states

**Deliverable**: Interactive dashboard with core features

---

### Phase 3: Real-Time (Weeks 6-8)
**Goal**: Live updates, streaming logs, WebSocket integration

**Tasks:**
1. Set up WebSocket connection
   ```typescript
   const ws = useWebSocket('/api/v1/monitor', {
     onMessage: (event) => {
       const data = JSON.parse(event.data);
       updateMetrics(data);
     }
   });
   ```

2. Build real-time metrics charts (Recharts)
3. Implement log streaming viewer
4. Add status indicators that update instantly
5. Optimize for performance (virtual scrolling)

**Deliverable**: Real-time monitoring dashboard

---

### Phase 4: Advanced Features (Weeks 9-12)
**Goal**: Workflow editor, responsive design, authentication

**Tasks:**
1. Integrate React Flow for workflow editor
2. Build workflow node palette
3. Implement responsive layouts (mobile/tablet/desktop)
4. Add authentication UI (login/signup)
5. Create user settings page

**Deliverable**: Full-featured dashboard with workflow builder

---

### Phase 5: Polish (Weeks 13-16)
**Goal**: Production-ready with design system and testing

**Tasks:**
1. Build comprehensive design system
2. Add dark mode support
3. Write unit tests (Vitest)
4. Write E2E tests (Playwright)
5. Performance optimization
6. Accessibility audit (WCAG 2.1 AA)
7. Documentation

**Deliverable**: Production-ready web application

---

## 🎯 Quick Start Commands

### Option 1: Create with Vite (Recommended)
```bash
# In the root of codegen repo
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install

# Install dependencies
npm install react-router-dom@6 @tanstack/react-query@5 zustand@4 \
  axios recharts@2 react-hook-form@7 lucide-react

# Install Tailwind CSS
npm install -D tailwindcss@3 postcss autoprefixer
npx tailwindcss init -p

# Install dev dependencies
npm install -D @types/node vitest @testing-library/react \
  @testing-library/jest-dom @testing-library/user-event

# Start development server
npm run dev
```

### Option 2: Use Template (Alternative)
```bash
git clone https://github.com/shadcn-ui/taxonomy.git frontend
cd frontend
npm install
npm run dev
```

---

## 📋 Acceptance Criteria for MVP

### Functional Requirements
- [ ] User can view list of workflows
- [ ] User can toggle workflow on/off
- [ ] User can view workflow details
- [ ] User can see real-time sandbox status
- [ ] User can view metrics charts
- [ ] User can filter/search workflows
- [ ] User can authenticate (login)
- [ ] User can navigate between tabs
- [ ] Mobile users can access on phone (responsive)

### Non-Functional Requirements
- [ ] Page load < 2 seconds
- [ ] Time to interactive < 3 seconds
- [ ] Real-time updates within 1 second
- [ ] Works on Chrome, Firefox, Safari, Edge
- [ ] Passes WCAG 2.1 AA accessibility
- [ ] All tests pass (unit + E2E)
- [ ] Zero console errors
- [ ] Lighthouse score > 90

---

## 🔗 Resources

### Documentation to Create
1. **Frontend Setup Guide** (`frontend/README.md`)
2. **Component Storybook** (optional but helpful)
3. **API Integration Guide** (`frontend/docs/api.md`)
4. **Contribution Guidelines** (`frontend/CONTRIBUTING.md`)
5. **Design System Docs** (`frontend/docs/design-system.md`)

### External Resources
- [React Flow Docs](https://reactflow.dev/)
- [Tailwind CSS Docs](https://tailwindcss.com/)
- [TanStack Query Docs](https://tanstack.com/query/)
- [Vite Docs](https://vitejs.dev/)
- [shadcn/ui Components](https://ui.shadcn.com/)

---

## ✅ Next Steps

**Immediate Actions Required:**

1. **Decision**: Approve technology stack (React + TypeScript + Vite + Tailwind)
2. **Decision**: Allocate frontend development resources (1-2 engineers for 4 months)
3. **Action**: Create `frontend/` directory and initialize Vite project
4. **Action**: Set up API endpoints for frontend consumption
5. **Action**: Design initial mockups/wireframes (Figma)

**Recommended First PR:**
- Create `frontend/` scaffold with Vite + React + TypeScript
- Implement basic routing and layout
- Build read-only workflow list component
- Deploy to Vercel/Netlify for preview

---

## 📞 Questions?

**Contact**: Development team  
**Slack Channel**: `#controller-dashboard`  
**Documentation**: `docs/controller-dashboard.md`

---

**Generated by**: IRIS (Intelligent Requirements and Implementation Solution)  
**Last Updated**: December 15, 2025  
**Status**: ⚠️ **Action Required - Frontend Development Needed**

