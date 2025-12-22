# Single View Dashboard - CodeGen Autonomous Management Interface

## 🎯 Overview

A fully autonomous, single-tab management interface for CodeGen workflows with real API integration, pinned runs management, and visual PRD → CICD flow tracking.

## ✨ Key Features

### 🎨 Single Unified View
- **NO multi-tab navigation** - All features accessible from one main view
- Clean, focused interface optimized for workflow management
- Dialog-based feature access keeps main view uncluttered

### 📊 Header with Active Runs Counter
- **Live count**: "Active Agent Runs: <Number>"
- **Hover dropdown**: Shows list of all active runs with real-time status
- **Click-to-navigate**: Open any run details with single click
- **Auto-refresh**: Updates every 5 seconds via polling

### 📌 Pinned Runs Section
- **Always visible** at top of main view
- **Pin/unpin** any agent run for quick access
- **Persistent**: Saved in localStorage across sessions
- **Max 10 pinned**: Prevents clutter
- Shows status, progress, and metadata for each pinned run

### ⚡ Active Runs Section
- Displays all currently **running, pending, or paused** agent runs
- Real-time progress bars and step indicators
- Quick actions: View details, pause/resume
- Empty state with call-to-action when no active runs

### 🎭 Four Feature Dialogs

#### 1. **Past Agent Runs Dialog**
- View **all historical runs** with comprehensive table
- **Search** by workflow name or run ID
- **Filter** by status (success, failure, running, pending, paused)
- **Sort** by date, duration, or status
- **Pin/unpin** runs directly from table
- Export functionality

#### 2. **Chainings Dialog**
- Create sequences of chained agent operations
- Add conditional logic between chain steps
- Configure error handling and retry strategies
- Visual chain builder (future enhancement)

#### 3. **Task Templates Dialog**
- Create reusable text templates for agent tasks
- Variable substitution support
- Template marketplace (future enhancement)
- Quick apply to new workflows

#### 4. **Workflows Dialog**
- Connect chainings with conditional statements
- Process agent responses for state management
- Visual workflow canvas (integrates existing WorkflowCanvas)
- Save/load workflows

### 🚀 PRD → CICD Flow Management
- **Visual flow tracker**: PRD → Code → Test → Deploy → Verify
- **Real-time state updates**: Track each stage's status
- **PRD input interface**: Enter requirements and select target projects
- **Codebase state monitoring**: Track branches, commits, files changed
- **Verification metrics**: Tests passing, coverage, build status
- **Integration with workflows**: Auto-create CICD pipelines from PRD

## 🔧 Technical Architecture

### Component Structure
```
SingleViewDashboard
├── Header (Active Runs Counter + Dropdown)
├── Action Buttons Row
│   ├── Past Agent Runs Button
│   ├── Chainings Button
│   ├── Task Templates Button
│   └── Workflows Button
├── Pinned Runs Section
│   └── RunCard[] (grid layout)
├── Active Runs Section
│   └── RunCard[] (grid layout)
└── Dialogs
    ├── PastRunsDialog
    ├── ChainingsDialog
    ├── TaskTemplatesDialog
    ├── WorkflowsDialog
    └── PRDFlowDialog
```

### State Management
- **Local State**: Dialog open/close, dropdown visibility
- **API Client**: Real-time data from CodeGen API
- **LocalStorage**: Pinned run IDs (persistent across sessions)
- **Polling**: Active runs update every 5 seconds

### API Integration
- Uses `CodegenClient` from Frontend2 (superior API implementation)
- Real credentials from `.env`: `VITE_CODEGEN_API_KEY`, `VITE_CODEGEN_ORG_ID`
- Endpoints:
  - `GET /organizations/{orgId}/agent/runs` - Fetch all runs
  - `POST /organizations/{orgId}/agent/run` - Create new run
  - `GET /organizations/{orgId}/workflows` - Fetch workflows
  - More endpoints as needed for full CICD integration

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- CodeGen API credentials

### Installation

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure credentials** (already done in `.env`):
   ```env
   VITE_CODEGEN_API_KEY=sk-92083737-4e5b-4a48-a2a1-f870a3a096a6
   VITE_CODEGEN_ORG_ID=323
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

5. **Open browser**:
   ```
   http://localhost:3000
   ```

### Deployment with dev-browser

As requested, test with [dev-browser](https://github.com/SawyerHood/dev-browser):

```bash
# Install dev-browser
npm install -g dev-browser

# Build production bundle
npm run build

# Serve with dev-browser
dev-browser dist/
```

## 📖 Usage Guide

### Viewing Active Runs
1. Look at header: "Active Agent Runs: X"
2. Hover over counter to see dropdown list
3. Click on any run in dropdown to view details
4. Or scroll down to Active Runs section for full view

### Pinning a Run
1. Find any run (in Active section or Past Runs dialog)
2. Click the pin icon (📌)
3. Run appears in Pinned Runs section at top
4. Maximum 10 pinned runs allowed
5. Click pin-off icon to unpin

### Creating a Chaining
1. Click "Chainings" button in action row
2. Dialog opens with chaining builder
3. Add steps with conditional logic
4. Configure error handling
5. Save and execute

### Using Task Templates
1. Click "Task Templates" button
2. Create new template with variables
3. Use template in chainings or workflows
4. Templates are reusable across projects

### Building a Workflow
1. Click "Workflows" button
2. Visual canvas opens
3. Connect chainings with conditional statements
4. Add agent response processing
5. Save workflow configuration
6. Enable/disable workflows as needed

### PRD → CICD Flow
1. Click "PRD Flow" button in header
2. Enter PRD requirements in text area
3. Select target project
4. Click "Start Implementation Flow"
5. Visual flow tracker shows progress:
   - PRD Input → Code Generation → Testing → Deployment → Verification
6. Monitor codebase state and verification metrics
7. View detailed logs for each stage

## 🎨 UI/UX Features

### Responsive Design
- Mobile-first approach
- Breakpoints: Mobile (< 768px), Tablet (768-1024px), Desktop (> 1024px)
- Touch-friendly buttons and interactions

### Accessibility
- ARIA labels on all interactive elements
- Keyboard navigation support
- High contrast mode compatible
- Screen reader friendly

### Performance
- Lazy loading for heavy components
- Optimistic UI updates
- Efficient polling (only active runs)
- LocalStorage for offline pin persistence

### Visual Feedback
- Loading states for all async operations
- Success/error toast notifications
- Progress bars for running operations
- Status badges with color coding:
  - 🟢 Success (green)
  - 🔴 Failure (red)
  - 🔵 Running (blue, animated)
  - 🟡 Pending (yellow)
  - ⚫ Paused (gray)

## 🔒 Security

- **API Key**: Stored in environment variables (never in code)
- **HTTPS Only**: All API requests use secure connections
- **CORS**: Proper CORS configuration for production
- **Auth Tokens**: Bearer token authentication
- **Validation**: Client-side validation before API calls

## 📊 Data Flow

```
User Action
    ↓
Component State Update
    ↓
API Call (CodegenClient)
    ↓
CodeGen API Server
    ↓
Response Processing
    ↓
State Update + UI Refresh
    ↓
LocalStorage (for pins)
```

## 🧪 Testing Strategy

### Manual Testing Checklist
- [ ] Active runs counter updates correctly
- [ ] Hover dropdown shows active runs
- [ ] Pinning/unpinning works
- [ ] Pinned runs persist across page refresh
- [ ] All dialogs open/close properly
- [ ] Past runs dialog filters work
- [ ] Real API integration functional
- [ ] Error handling displays correctly
- [ ] Mobile responsive layout works
- [ ] Keyboard navigation functional

### Automated Testing (Future)
- Unit tests for components
- Integration tests for API calls
- E2E tests for critical workflows
- Performance benchmarks

## 📈 Future Enhancements

### Phase 2 Features
- [ ] WebSocket for truly real-time updates (replace polling)
- [ ] Advanced chaining visual builder with drag-and-drop
- [ ] Template marketplace with community templates
- [ ] Run comparison tool (side-by-side)
- [ ] Export/import workflows as JSON
- [ ] Team collaboration features (share pins)
- [ ] Advanced analytics dashboard
- [ ] Custom alerts and notifications
- [ ] Workflow versioning and rollback
- [ ] Integration with external tools (Slack, GitHub, etc.)

### Performance Optimizations
- [ ] Virtual scrolling for large run lists
- [ ] Debounced search in Past Runs dialog
- [ ] Memoized expensive computations
- [ ] Service worker for offline support
- [ ] CDN caching for static assets

## 🐛 Troubleshooting

### Common Issues

**Issue**: "Configuration Required" error
- **Solution**: Check `.env` file has `VITE_CODEGEN_API_KEY` and `VITE_CODEGEN_ORG_ID`

**Issue**: Active runs not updating
- **Solution**: Check browser console for API errors, verify credentials are valid

**Issue**: Pinned runs not persisting
- **Solution**: Check browser localStorage is enabled (not in incognito mode)

**Issue**: Dialogs not opening
- **Solution**: Check browser console for React errors, clear browser cache

**Issue**: Slow performance
- **Solution**: Reduce polling interval in `.env`, check network tab for slow API calls

## 🤝 Contributing

### Development Workflow
1. Create feature branch from `UI`
2. Make changes
3. Test thoroughly (manual + automated)
4. Submit PR with description
5. Code review
6. Merge to `UI` branch

### Code Style
- TypeScript strict mode
- ESLint configuration
- Prettier formatting
- Semantic HTML
- TailwindCSS for styling

## 📝 Changelog

### v1.0.0 (Current)
- ✅ Single unified view (no tabs)
- ✅ Header with active runs counter
- ✅ Pinned runs section (persistent)
- ✅ Active runs section
- ✅ Four feature dialogs
- ✅ PRD → CICD flow visualization
- ✅ Real API integration
- ✅ LocalStorage persistence
- ✅ Responsive design

## 📚 Additional Resources

- [CodeGen API Documentation](https://api.codegen.com/docs)
- [React 18 Documentation](https://react.dev)
- [TailwindCSS Documentation](https://tailwindcss.com)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- [Dev Browser Tool](https://github.com/SawyerHood/dev-browser)

## 📞 Support

For issues, questions, or feature requests:
- GitHub Issues: [Create Issue](https://github.com/Zeeeepa/codegen/issues)
- Email: support@codegen.com
- Discord: [Join Community](https://discord.gg/codegen)

---

**Built with ❤️ for autonomous AI-powered development workflows**

Last Updated: December 19, 2025
Version: 1.0.0

