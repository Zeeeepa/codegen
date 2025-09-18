/**
 * Zustand Store for Application State Management
 * Centralized state management for the Codegen Visual Interface
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { 
  AppState, 
  User, 
  Organization, 
  AgentRun, 
  Project, 
  Workflow, 
  Notification,
  RealTimeEvent
} from '@/types/codegen';
import { getCodegenClient } from '@/lib/api/codegen-client';
import { getWebSocketClient } from '@/lib/websocket/websocket-client';

interface AppStore extends AppState {
  // Auth actions
  login: (token: string) => Promise<void>;
  logout: () => void;
  setOrganization: (org: Organization) => void;
  
  // Agent actions
  fetchAgentRuns: () => Promise<void>;
  createAgentRun: (prompt: string, model?: string, repoId?: string) => Promise<AgentRun>;
  selectAgentRun: (run: AgentRun | null) => void;
  updateAgentRunStatus: (runId: string, status: string) => void;
  
  // Project actions
  fetchProjects: () => Promise<void>;
  createProject: (project: Omit<Project, 'id' | 'created_at' | 'updated_at'>) => Promise<Project>;
  selectProject: (project: Project | null) => void;
  toggleProjectStar: (projectId: string) => void;
  
  // Workflow actions
  fetchWorkflows: () => Promise<void>;
  createWorkflow: (workflow: Omit<Workflow, 'id' | 'created_at' | 'updated_at' | 'version'>) => Promise<Workflow>;
  selectWorkflow: (workflow: Workflow | null) => void;
  updateWorkflow: (workflow: Workflow) => Promise<void>;
  setWorkflowEditing: (isEditing: boolean) => void;
  
  // UI actions
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setActiveView: (view: AppState['ui']['activeView']) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markNotificationRead: (notificationId: string) => void;
  clearNotifications: () => void;
  
  // Real-time updates
  initializeWebSocket: () => Promise<void>;
  disconnectWebSocket: () => void;
  handleRealTimeEvent: (event: RealTimeEvent) => void;
}

const useAppStore = create<AppStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        auth: {
          user: null,
          token: null,
          organization: null,
          isAuthenticated: false,
          isLoading: false,
        },
        agents: {
          runs: [],
          currentRun: null,
          isLoading: false,
          error: null,
        },
        projects: {
          list: [],
          current: null,
          starred: [],
          isLoading: false,
          error: null,
        },
        workflows: {
          list: [],
          current: null,
          isEditing: false,
          isLoading: false,
          error: null,
        },
        ui: {
          sidebarOpen: true,
          theme: 'light',
          notifications: [],
          activeView: 'dashboard',
        },

        // Auth actions
        login: async (token: string) => {
          set((state) => ({
            auth: { ...state.auth, isLoading: true },
          }));

          try {
            const client = getCodegenClient();
            const user = await client.authenticate(token);
            const organizations = await client.getOrganizations();
            
            set((state) => ({
              auth: {
                ...state.auth,
                user,
                token,
                organization: organizations[0] || null,
                isAuthenticated: true,
                isLoading: false,
              },
            }));

            // Fetch initial data
            get().fetchAgentRuns();
            get().fetchProjects();
            
            // Initialize WebSocket connection
            get().initializeWebSocket();
          } catch (error) {
            console.error('Login failed:', error);
            set((state) => ({
              auth: { ...state.auth, isLoading: false },
            }));
            throw error;
          }
        },

        logout: () => {
          const client = getCodegenClient();
          client.clearCache();
          
          // Disconnect WebSocket
          get().disconnectWebSocket();
          
          set({
            auth: {
              user: null,
              token: null,
              organization: null,
              isAuthenticated: false,
              isLoading: false,
            },
            agents: {
              runs: [],
              currentRun: null,
              isLoading: false,
              error: null,
            },
            projects: {
              list: [],
              current: null,
              starred: [],
              isLoading: false,
              error: null,
            },
            workflows: {
              list: [],
              current: null,
              isEditing: false,
              isLoading: false,
              error: null,
            },
          });
        },

        setOrganization: (org: Organization) => {
          set((state) => ({
            auth: { ...state.auth, organization: org },
          }));
          
          // Refresh data for new organization
          get().fetchAgentRuns();
          get().fetchProjects();
        },

        // Agent actions
        fetchAgentRuns: async () => {
          const { auth } = get();
          if (!auth.organization) return;

          set((state) => ({
            agents: { ...state.agents, isLoading: true, error: null },
          }));

          try {
            const client = getCodegenClient();
            const response = await client.listAgentRuns(auth.organization.id, {
              page: 1,
              page_size: 50,
              source_type: 'API',
            });

            set((state) => ({
              agents: {
                ...state.agents,
                runs: response.items,
                isLoading: false,
              },
            }));
          } catch (error) {
            console.error('Failed to fetch agent runs:', error);
            set((state) => ({
              agents: {
                ...state.agents,
                isLoading: false,
                error: 'Failed to fetch agent runs',
              },
            }));
          }
        },

        createAgentRun: async (prompt: string, model?: string, repoId?: string) => {
          const { auth } = get();
          if (!auth.organization) throw new Error('No organization selected');

          try {
            const client = getCodegenClient();
            const agentRun = await client.createAgentRun(auth.organization.id, {
              prompt,
              model,
              repo_id: repoId,
            });

            set((state) => ({
              agents: {
                ...state.agents,
                runs: [agentRun, ...state.agents.runs],
                currentRun: agentRun,
              },
            }));

            get().addNotification({
              type: 'success',
              title: 'Agent Run Created',
              message: `Agent run ${agentRun.id} has been created successfully.`,
            });

            return agentRun;
          } catch (error) {
            console.error('Failed to create agent run:', error);
            get().addNotification({
              type: 'error',
              title: 'Agent Creation Failed',
              message: 'Failed to create agent run. Please try again.',
            });
            throw error;
          }
        },

        selectAgentRun: (run: AgentRun | null) => {
          set((state) => ({
            agents: { ...state.agents, currentRun: run },
          }));
        },

        updateAgentRunStatus: (runId: string, status: string) => {
          set((state) => ({
            agents: {
              ...state.agents,
              runs: state.agents.runs.map((run) =>
                run.id === runId ? { ...run, status: status as any } : run
              ),
              currentRun:
                state.agents.currentRun?.id === runId
                  ? { ...state.agents.currentRun, status: status as any }
                  : state.agents.currentRun,
            },
          }));
        },

        // Project actions (placeholder implementations)
        fetchProjects: async () => {
          set((state) => ({
            projects: { ...state.projects, isLoading: true, error: null },
          }));

          // TODO: Implement actual project fetching when API is available
          setTimeout(() => {
            set((state) => ({
              projects: {
                ...state.projects,
                list: [],
                isLoading: false,
              },
            }));
          }, 1000);
        },

        createProject: async (project) => {
          // TODO: Implement actual project creation
          const newProject: Project = {
            ...project,
            id: `project_${Date.now()}`,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };

          set((state) => ({
            projects: {
              ...state.projects,
              list: [newProject, ...state.projects.list],
            },
          }));

          return newProject;
        },

        selectProject: (project: Project | null) => {
          set((state) => ({
            projects: { ...state.projects, current: project },
          }));
        },

        toggleProjectStar: (projectId: string) => {
          set((state) => {
            const project = state.projects.list.find((p) => p.id === projectId);
            if (!project) return state;

            const updatedProject = { ...project, starred: !project.starred };
            const updatedList = state.projects.list.map((p) =>
              p.id === projectId ? updatedProject : p
            );
            const updatedStarred = updatedProject.starred
              ? [...state.projects.starred, updatedProject]
              : state.projects.starred.filter((p) => p.id !== projectId);

            return {
              projects: {
                ...state.projects,
                list: updatedList,
                starred: updatedStarred,
              },
            };
          });
        },

        // Workflow actions (placeholder implementations)
        fetchWorkflows: async () => {
          set((state) => ({
            workflows: { ...state.workflows, isLoading: true, error: null },
          }));

          // TODO: Implement actual workflow fetching
          setTimeout(() => {
            set((state) => ({
              workflows: {
                ...state.workflows,
                list: [],
                isLoading: false,
              },
            }));
          }, 1000);
        },

        createWorkflow: async (workflow) => {
          const newWorkflow: Workflow = {
            ...workflow,
            id: `workflow_${Date.now()}`,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            version: 1,
          };

          set((state) => ({
            workflows: {
              ...state.workflows,
              list: [newWorkflow, ...state.workflows.list],
            },
          }));

          return newWorkflow;
        },

        selectWorkflow: (workflow: Workflow | null) => {
          set((state) => ({
            workflows: { ...state.workflows, current: workflow },
          }));
        },

        updateWorkflow: async (workflow: Workflow) => {
          const updatedWorkflow = {
            ...workflow,
            updated_at: new Date().toISOString(),
            version: workflow.version + 1,
          };

          set((state) => ({
            workflows: {
              ...state.workflows,
              list: state.workflows.list.map((w) =>
                w.id === workflow.id ? updatedWorkflow : w
              ),
              current: updatedWorkflow,
            },
          }));

          return updatedWorkflow;
        },

        setWorkflowEditing: (isEditing: boolean) => {
          set((state) => ({
            workflows: { ...state.workflows, isEditing },
          }));
        },

        // UI actions
        toggleSidebar: () => {
          set((state) => ({
            ui: { ...state.ui, sidebarOpen: !state.ui.sidebarOpen },
          }));
        },

        setTheme: (theme: 'light' | 'dark') => {
          set((state) => ({
            ui: { ...state.ui, theme },
          }));
        },

        setActiveView: (view: AppState['ui']['activeView']) => {
          set((state) => ({
            ui: { ...state.ui, activeView: view },
          }));
        },

        addNotification: (notification) => {
          const newNotification: Notification = {
            ...notification,
            id: `notification_${Date.now()}`,
            timestamp: new Date().toISOString(),
            read: false,
          };

          set((state) => ({
            ui: {
              ...state.ui,
              notifications: [newNotification, ...state.ui.notifications].slice(0, 50), // Keep only last 50
            },
          }));
        },

        markNotificationRead: (notificationId: string) => {
          set((state) => ({
            ui: {
              ...state.ui,
              notifications: state.ui.notifications.map((n) =>
                n.id === notificationId ? { ...n, read: true } : n
              ),
            },
          }));
        },

        clearNotifications: () => {
          set((state) => ({
            ui: { ...state.ui, notifications: [] },
          }));
        },

        // WebSocket management
        initializeWebSocket: async () => {
          const { auth } = get();
          if (!auth.token || !auth.organization) {
            console.warn('Cannot initialize WebSocket: missing auth data');
            return;
          }

          try {
            const wsClient = getWebSocketClient();
            await wsClient.connect(
              {
                url: process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:3001',
                token: auth.token,
                organizationId: auth.organization.id,
              },
              {
                onConnect: () => {
                  console.log('WebSocket connected');
                  get().addNotification({
                    type: 'success',
                    title: 'Connected',
                    message: 'Real-time updates are now active.',
                  });
                },
                onDisconnect: (reason) => {
                  console.log('WebSocket disconnected:', reason);
                  get().addNotification({
                    type: 'warning',
                    title: 'Disconnected',
                    message: 'Real-time updates are currently unavailable.',
                  });
                },
                onError: (error) => {
                  console.error('WebSocket error:', error);
                  get().addNotification({
                    type: 'error',
                    title: 'Connection Error',
                    message: 'Failed to connect to real-time updates.',
                  });
                },
                onEvent: get().handleRealTimeEvent,
              }
            );
          } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
          }
        },

        disconnectWebSocket: () => {
          try {
            const wsClient = getWebSocketClient();
            wsClient.disconnect();
          } catch (error) {
            console.error('Failed to disconnect WebSocket:', error);
          }
        },

        // Real-time event handling
        handleRealTimeEvent: (event: RealTimeEvent) => {
          console.log('Handling real-time event:', event);
          
          switch (event.type) {
            case 'agent_run_status_change':
              get().updateAgentRunStatus(event.data.id, event.data.status);
              
              // Show notification for status changes
              get().addNotification({
                type: event.data.status === 'COMPLETE' ? 'success' : 
                      event.data.status === 'FAILED' ? 'error' : 'info',
                title: 'Agent Run Update',
                message: `Agent run ${event.data.id} is now ${event.data.status.toLowerCase()}.`,
              });
              break;
              
            case 'agent_run_log':
              // Handle new log entries - could trigger a refresh of logs
              if (get().agents.currentRun?.id === event.data.agent_run_id) {
                // Refresh current run data if it's being viewed
                const { auth } = get();
                if (auth.organization) {
                  // Could implement a more efficient log update here
                  console.log('New log entry for current run:', event.data);
                }
              }
              break;
              
            case 'pr_update':
              // Handle PR updates - refresh agent runs that have PRs
              get().addNotification({
                type: 'info',
                title: 'Pull Request Update',
                message: `Pull request #${event.data.number} has been updated.`,
                actions: event.data.html_url ? [{
                  label: 'View PR',
                  action: () => window.open(event.data.html_url, '_blank')
                }] : undefined,
              });
              break;
              
            case 'workflow_update':
              // Handle workflow updates
              console.log('Workflow updated:', event.data);
              break;
              
            default:
              console.log('Unknown real-time event type:', event.type);
          }
        },
      }),
      {
        name: 'codegen-app-store',
        partialize: (state) => ({
          auth: {
            token: state.auth.token,
            organization: state.auth.organization,
          },
          ui: {
            theme: state.ui.theme,
            sidebarOpen: state.ui.sidebarOpen,
          },
        }),
      }
    ),
    { name: 'codegen-app-store' }
  )
);

export default useAppStore;
