/**
 * GraphQL Resolvers
 * Implements GraphQL schema by connecting to Codegen API
 */

import { getCodegenClient } from '@/lib/api/codegen-client';
import { getWebSocketClient } from '@/lib/websocket/websocket-client';
import { withFilter } from 'graphql-subscriptions';
import { PubSub } from 'graphql-subscriptions';

const pubsub = new PubSub();

// Helper function to get authenticated API client
const getAuthenticatedClient = (context: any) => {
  const token = context.token || context.req?.headers?.authorization?.replace('Bearer ', '');
  if (!token) {
    throw new Error('Authentication required');
  }
  return getCodegenClient(undefined, token);
};

// Helper function to validate organization access
const validateOrganizationAccess = async (client: any, organizationId: string, context: any) => {
  try {
    const organizations = await client.getOrganizations();
    const hasAccess = organizations.some((org: any) => org.id === organizationId);
    if (!hasAccess) {
      throw new Error('Access denied to organization');
    }
  } catch (error) {
    throw new Error('Failed to validate organization access');
  }
};

export const resolvers = {
  // Scalar resolvers
  DateTime: {
    serialize: (date: Date) => date.toISOString(),
    parseValue: (value: string) => new Date(value),
    parseLiteral: (ast: any) => new Date(ast.value),
  },
  
  JSON: {
    serialize: (value: any) => value,
    parseValue: (value: any) => value,
    parseLiteral: (ast: any) => JSON.parse(ast.value),
  },

  // Union resolvers
  SearchResult: {
    __resolveType: (obj: any) => {
      if (obj.prompt) return 'AgentRun';
      if (obj.nodes) return 'Workflow';
      if (obj.repositoryIds) return 'Project';
      return null;
    },
  },

  // Type resolvers
  Organization: {
    users: async (parent: any, args: any, context: any) => {
      // TODO: Implement when user listing API is available
      return [];
    },
    
    repositories: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      return await client.getRepositories(parent.id);
    },
    
    agentRuns: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      return await client.listAgentRuns(parent.id, {
        page: args.page,
        page_size: args.pageSize,
        source_type: args.sourceType,
        status: args.status,
      });
    },
  },

  Repository: {
    checkSuiteSettings: async (parent: any, args: any, context: any) => {
      // TODO: Implement when check suite settings API is available
      return null;
    },
  },

  AgentRun: {
    logs: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      return await client.getAgentRunLogs(parent.organizationId, parent.id, {
        skip: args.skip,
        limit: args.limit,
      });
    },
    
    repository: async (parent: any, args: any, context: any) => {
      if (!parent.repoId) return null;
      const client = getAuthenticatedClient(context);
      const repositories = await client.getRepositories(parent.organizationId);
      return repositories.find((repo: any) => repo.id === parent.repoId);
    },
    
    user: async (parent: any, args: any, context: any) => {
      // TODO: Implement user lookup when API is available
      return {
        id: parent.userId,
        email: 'user@example.com',
        name: 'User',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
    },
  },

  Project: {
    repositories: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      const allRepositories = await client.getRepositories(parent.organizationId);
      return allRepositories.filter((repo: any) => 
        parent.repositoryIds.includes(repo.id)
      );
    },
    
    workflows: async (parent: any, args: any, context: any) => {
      // TODO: Implement when workflow API is available
      return [];
    },
  },

  Workflow: {
    project: async (parent: any, args: any, context: any) => {
      // TODO: Implement project lookup
      return {
        id: parent.projectId,
        name: 'Project',
        organizationId: 'org-1',
        repositoryIds: [],
        status: 'ACTIVE',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        starred: false,
        tags: [],
      };
    },
  },

  // Query resolvers
  Query: {
    me: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      return await client.getCurrentUser();
    },

    organizations: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      return await client.getOrganizations();
    },

    organization: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      const organizations = await client.getOrganizations();
      return organizations.find((org: any) => org.id === args.id);
    },

    agentRuns: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      await validateOrganizationAccess(client, args.organizationId, context);
      
      return await client.listAgentRuns(args.organizationId, {
        page: args.page,
        page_size: args.pageSize,
        source_type: args.sourceType,
        status: args.status,
        user_id: args.userId,
      });
    },

    agentRun: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      await validateOrganizationAccess(client, args.organizationId, context);
      
      return await client.getAgentRun(args.organizationId, args.id);
    },

    agentRunLogs: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      await validateOrganizationAccess(client, args.organizationId, context);
      
      return await client.getAgentRunLogs(args.organizationId, args.agentRunId, {
        skip: args.skip,
        limit: args.limit,
      });
    },

    repositories: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      await validateOrganizationAccess(client, args.organizationId, context);
      
      return await client.getRepositories(args.organizationId);
    },

    repository: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      await validateOrganizationAccess(client, args.organizationId, context);
      
      const repositories = await client.getRepositories(args.organizationId);
      return repositories.find((repo: any) => repo.id === args.id);
    },

    integrations: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      await validateOrganizationAccess(client, args.organizationId, context);
      
      return await client.getIntegrations(args.organizationId);
    },

    projects: async (parent: any, args: any, context: any) => {
      // TODO: Implement when project API is available
      return [];
    },

    project: async (parent: any, args: any, context: any) => {
      // TODO: Implement when project API is available
      return null;
    },

    workflows: async (parent: any, args: any, context: any) => {
      // TODO: Implement when workflow API is available
      return [];
    },

    workflow: async (parent: any, args: any, context: any) => {
      // TODO: Implement when workflow API is available
      return null;
    },

    dashboardStats: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      await validateOrganizationAccess(client, args.organizationId, context);
      
      // Aggregate data from multiple API calls
      const [agentRuns, repositories, integrations] = await Promise.all([
        client.listAgentRuns(args.organizationId, { page: 1, page_size: 100 }),
        client.getRepositories(args.organizationId),
        client.getIntegrations(args.organizationId),
      ]);

      const activeAgents = agentRuns.items.filter((run: any) => 
        run.status === 'RUNNING' || run.status === 'PENDING'
      ).length;

      const completedRuns = agentRuns.items.filter((run: any) => 
        run.status === 'COMPLETE'
      ).length;

      const successRate = agentRuns.total > 0 
        ? (completedRuns / agentRuns.total) * 100 
        : 0;

      const recentActivity = agentRuns.items
        .slice(0, 10)
        .map((run: any) => ({
          id: run.id,
          type: 'agent_run',
          title: run.prompt.substring(0, 50) + '...',
          status: run.status.toLowerCase(),
          timestamp: run.createdAt,
          metadata: {
            agentRunId: run.id,
            sourceType: run.sourceType,
          },
        }));

      return {
        activeAgents,
        totalWorkflows: 0, // TODO: Implement when workflow API is available
        totalProjects: 0, // TODO: Implement when project API is available
        successRate,
        recentActivity,
      };
    },

    search: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      await validateOrganizationAccess(client, args.organizationId, context);
      
      const results: any[] = [];

      // Search agent runs if requested
      if (args.types.includes('agent_runs')) {
        const agentRuns = await client.listAgentRuns(args.organizationId, {
          page: 1,
          page_size: args.limit,
        });
        
        const filteredRuns = agentRuns.items.filter((run: any) =>
          run.prompt.toLowerCase().includes(args.query.toLowerCase()) ||
          run.summary?.toLowerCase().includes(args.query.toLowerCase())
        );
        
        results.push(...filteredRuns);
      }

      // TODO: Add project and workflow search when APIs are available

      return results.slice(0, args.limit);
    },
  },

  // Mutation resolvers
  Mutation: {
    createAgentRun: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      const organizationId = args.input.organizationId;
      
      if (organizationId) {
        await validateOrganizationAccess(client, organizationId, context);
      }

      const agentRun = await client.createAgentRun(
        organizationId || context.organizationId,
        args.input
      );

      // Publish real-time update
      pubsub.publish('AGENT_RUN_UPDATES', {
        agentRunUpdates: agentRun,
        organizationId: agentRun.organizationId,
      });

      return agentRun;
    },

    resumeAgentRun: async (parent: any, args: any, context: any) => {
      const client = getAuthenticatedClient(context);
      await validateOrganizationAccess(client, args.organizationId, context);

      const agentRun = await client.resumeAgentRun(args.organizationId, args.agentRunId);

      // Publish real-time update
      pubsub.publish('AGENT_RUN_UPDATES', {
        agentRunUpdates: agentRun,
        organizationId: agentRun.organizationId,
      });

      return agentRun;
    },

    createProject: async (parent: any, args: any, context: any) => {
      // TODO: Implement when project API is available
      const project = {
        id: `project_${Date.now()}`,
        ...args.input,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        starred: false,
      };

      return project;
    },

    updateProject: async (parent: any, args: any, context: any) => {
      // TODO: Implement when project API is available
      const project = {
        id: args.id,
        ...args.input,
        updatedAt: new Date().toISOString(),
      };

      return project;
    },

    deleteProject: async (parent: any, args: any, context: any) => {
      // TODO: Implement when project API is available
      return true;
    },

    toggleProjectStar: async (parent: any, args: any, context: any) => {
      // TODO: Implement when project API is available
      return {
        id: args.id,
        starred: true,
      };
    },

    createWorkflow: async (parent: any, args: any, context: any) => {
      // TODO: Implement when workflow API is available
      const workflow = {
        id: `workflow_${Date.now()}`,
        ...args.input,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        version: 1,
      };

      return workflow;
    },

    updateWorkflow: async (parent: any, args: any, context: any) => {
      // TODO: Implement when workflow API is available
      const workflow = {
        ...args.input,
        updatedAt: new Date().toISOString(),
        version: 2,
      };

      // Publish real-time update
      pubsub.publish('WORKFLOW_UPDATES', {
        workflowUpdates: workflow,
        projectId: workflow.projectId,
      });

      return workflow;
    },

    deleteWorkflow: async (parent: any, args: any, context: any) => {
      // TODO: Implement when workflow API is available
      return true;
    },
  },

  // Subscription resolvers
  Subscription: {
    agentRunUpdates: {
      subscribe: withFilter(
        () => pubsub.asyncIterator(['AGENT_RUN_UPDATES']),
        (payload, variables) => {
          return payload.organizationId === variables.organizationId;
        }
      ),
    },

    workflowUpdates: {
      subscribe: withFilter(
        () => pubsub.asyncIterator(['WORKFLOW_UPDATES']),
        (payload, variables) => {
          return payload.projectId === variables.projectId;
        }
      ),
    },

    systemNotifications: {
      subscribe: withFilter(
        () => pubsub.asyncIterator(['SYSTEM_NOTIFICATIONS']),
        (payload, variables) => {
          return payload.organizationId === variables.organizationId;
        }
      ),
    },
  },
};

// WebSocket event handlers for GraphQL subscriptions
const webSocketClient = getWebSocketClient();

// Set up WebSocket event forwarding to GraphQL subscriptions
export const setupWebSocketSubscriptions = (organizationId: string, token: string) => {
  webSocketClient.connect(
    {
      url: process.env.WEBSOCKET_URL || 'ws://localhost:3001',
      token,
      organizationId,
    },
    {
      onAgentRunUpdate: (data) => {
        pubsub.publish('AGENT_RUN_UPDATES', {
          agentRunUpdates: data,
          organizationId,
        });
      },
      onWorkflowUpdate: (data) => {
        pubsub.publish('WORKFLOW_UPDATES', {
          workflowUpdates: data,
          projectId: data.projectId,
        });
      },
      onEvent: (event) => {
        if (event.type === 'system_notification') {
          pubsub.publish('SYSTEM_NOTIFICATIONS', {
            systemNotifications: event.data,
            organizationId: event.organization_id,
          });
        }
      },
    }
  );
};

export default resolvers;
