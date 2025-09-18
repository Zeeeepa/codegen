/**
 * GraphQL Client
 * Apollo Client configuration for the visual interface
 */

import { ApolloClient, InMemoryCache, createHttpLink, split } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { getMainDefinition } from '@apollo/client/utilities';
import { createClient } from 'graphql-ws';

// HTTP link for queries and mutations
const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URL || '/api/graphql',
});

// WebSocket link for subscriptions
const wsLink = typeof window !== 'undefined' ? new GraphQLWsLink(
  createClient({
    url: process.env.NEXT_PUBLIC_GRAPHQL_WS_URL || 'ws://localhost:4000/api/graphql/subscriptions',
    connectionParams: () => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('codegen_token') : null;
      const organizationId = typeof window !== 'undefined' ? localStorage.getItem('codegen_organization_id') : null;
      
      return {
        authorization: token ? `Bearer ${token}` : '',
        organizationId,
      };
    },
    on: {
      connected: () => console.log('GraphQL WebSocket connected'),
      closed: () => console.log('GraphQL WebSocket closed'),
      error: (error) => console.error('GraphQL WebSocket error:', error),
    },
  })
) : null;

// Auth link to add authentication headers
const authLink = setContext((_, { headers }) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('codegen_token') : null;
  const organizationId = typeof window !== 'undefined' ? localStorage.getItem('codegen_organization_id') : null;

  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
      'x-organization-id': organizationId || '',
    },
  };
});

// Split link to route queries/mutations to HTTP and subscriptions to WebSocket
const splitLink = typeof window !== 'undefined' && wsLink
  ? split(
      ({ query }) => {
        const definition = getMainDefinition(query);
        return (
          definition.kind === 'OperationDefinition' &&
          definition.operation === 'subscription'
        );
      },
      wsLink,
      authLink.concat(httpLink)
    )
  : authLink.concat(httpLink);

// Apollo Client configuration
const client = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache({
    typePolicies: {
      Query: {
        fields: {
          agentRuns: {
            keyArgs: ['organizationId', 'sourceType', 'status', 'userId'],
            merge(existing = { items: [], total: 0, page: 1, pageSize: 10, pages: 1 }, incoming) {
              // Handle pagination merging
              if (incoming.page === 1) {
                return incoming;
              }
              
              return {
                ...incoming,
                items: [...existing.items, ...incoming.items],
              };
            },
          },
          agentRunLogs: {
            keyArgs: ['organizationId', 'agentRunId'],
            merge(existing = { items: [], total: 0, page: 1, size: 50, pages: 1 }, incoming) {
              // Handle pagination merging for logs
              if (incoming.page === 1) {
                return incoming;
              }
              
              return {
                ...incoming,
                items: [...existing.items, ...incoming.items],
              };
            },
          },
        },
      },
      AgentRun: {
        fields: {
          logs: {
            merge(existing = { items: [] }, incoming) {
              return {
                ...incoming,
                items: [...existing.items, ...incoming.items],
              };
            },
          },
        },
      },
      Organization: {
        fields: {
          agentRuns: {
            merge(existing = { items: [] }, incoming) {
              return {
                ...incoming,
                items: [...existing.items, ...incoming.items],
              };
            },
          },
        },
      },
    },
  }),
  defaultOptions: {
    watchQuery: {
      errorPolicy: 'all',
      fetchPolicy: 'cache-and-network',
    },
    query: {
      errorPolicy: 'all',
      fetchPolicy: 'cache-first',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
  connectToDevTools: process.env.NODE_ENV === 'development',
});

// Helper function to update authentication
export const updateAuthToken = (token: string, organizationId?: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('codegen_token', token);
    if (organizationId) {
      localStorage.setItem('codegen_organization_id', organizationId);
    }
    
    // Clear Apollo cache to force re-authentication
    client.clearStore();
  }
};

// Helper function to clear authentication
export const clearAuth = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('codegen_token');
    localStorage.removeItem('codegen_organization_id');
    
    // Clear Apollo cache
    client.clearStore();
  }
};

// Helper function to get current auth state
export const getAuthState = () => {
  if (typeof window === 'undefined') {
    return { token: null, organizationId: null };
  }
  
  return {
    token: localStorage.getItem('codegen_token'),
    organizationId: localStorage.getItem('codegen_organization_id'),
  };
};

export default client;
