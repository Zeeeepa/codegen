/**
 * GraphQL API Route
 * Next.js API route for GraphQL endpoint
 */

import { ApolloServer } from '@apollo/server';
import { startServerAndCreateNextHandler } from '@as-integrations/next';
import { makeExecutableSchema } from '@graphql-tools/schema';
import { createServer } from 'http';
import { SubscriptionServer } from 'subscriptions-transport-ws';
import { execute, subscribe } from 'graphql';

import typeDefs from '@/lib/graphql/schema';
import resolvers, { setupWebSocketSubscriptions } from '@/lib/graphql/resolvers';

// Create executable schema
const schema = makeExecutableSchema({
  typeDefs,
  resolvers,
});

// Create Apollo Server
const server = new ApolloServer({
  schema,
  introspection: process.env.NODE_ENV !== 'production',
  plugins: [
    // Plugin to handle authentication context
    {
      requestDidStart() {
        return {
          willSendResponse(requestContext) {
            // Add CORS headers
            requestContext.response.http.headers.set('Access-Control-Allow-Origin', '*');
            requestContext.response.http.headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
            requestContext.response.http.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
          },
        };
      },
    },
  ],
});

// Create the Next.js handler
const handler = startServerAndCreateNextHandler(server, {
  context: async (req, res) => {
    // Extract authentication token from headers
    const token = req.headers.authorization?.replace('Bearer ', '');
    
    // Extract organization ID from headers or query params
    const organizationId = req.headers['x-organization-id'] || req.url?.searchParams?.get('organizationId');

    return {
      req,
      res,
      token,
      organizationId,
    };
  },
});

// Handle GET and POST requests
export async function GET(request: Request) {
  return handler(request);
}

export async function POST(request: Request) {
  return handler(request);
}

// Handle OPTIONS for CORS preflight
export async function OPTIONS(request: Request) {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Organization-ID',
    },
  });
}

// WebSocket subscription server setup (for development)
if (process.env.NODE_ENV === 'development') {
  const httpServer = createServer();
  
  const subscriptionServer = SubscriptionServer.create(
    {
      schema,
      execute,
      subscribe,
      onConnect: (connectionParams: any) => {
        // Handle WebSocket authentication
        const token = connectionParams.authorization?.replace('Bearer ', '');
        const organizationId = connectionParams.organizationId;

        if (!token) {
          throw new Error('Authentication required for subscriptions');
        }

        // Set up WebSocket subscriptions for this connection
        if (organizationId) {
          setupWebSocketSubscriptions(organizationId, token);
        }

        return {
          token,
          organizationId,
        };
      },
      onDisconnect: () => {
        console.log('GraphQL subscription client disconnected');
      },
    },
    {
      server: httpServer,
      path: '/api/graphql/subscriptions',
    }
  );

  const port = process.env.GRAPHQL_SUBSCRIPTION_PORT || 4000;
  httpServer.listen(port, () => {
    console.log(`GraphQL subscriptions server running on http://localhost:${port}/api/graphql/subscriptions`);
  });
}
