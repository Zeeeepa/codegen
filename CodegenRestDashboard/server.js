const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const WebSocket = require('ws');
const http = require('http');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

// Import command modules
const createAgentRun = require('./commands/create_agent_run');
const resumeAgentRun = require('./commands/resume_agent_run');
const listAgentRuns = require('./commands/list_agent_runs');
const getAgentRun = require('./commands/get_agent_run');
const generateSetupCommands = require('./commands/generate_setup_commands');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Middleware
app.use(helmet());
app.use(compression());
app.use(morgan('combined'));
app.use(cors({
  origin: process.env.NODE_ENV === 'production' ? false : true,
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Serve static files from dashboard build
app.use(express.static(path.join(__dirname, 'dashboard/build')));

// WebSocket connections for real-time updates
const clients = new Set();
const activeRuns = new Map(); // Track active runs and their watchers
const runEvents = new Map(); // Store event history per run

wss.on('connection', (ws) => {
  console.log('Client connected');
  clients.add(ws);

  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message.toString());
      if (data.type === 'subscribe' && data.runId) {
        // Client wants to subscribe to a specific run
        if (!activeRuns.has(data.runId)) {
          activeRuns.set(data.runId, new Set());
        }
        activeRuns.get(data.runId).add(ws);

        // Send existing events for this run
        const events = runEvents.get(data.runId) || [];
        if (events.length > 0) {
          ws.send(JSON.stringify({
            type: 'run_events',
            runId: data.runId,
            events
          }));
        }
      }
    } catch (error) {
      console.error('WebSocket message error:', error);
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');
    clients.delete(ws);

    // Remove from all active run subscriptions
    for (const [runId, watchers] of activeRuns) {
      watchers.delete(ws);
      if (watchers.size === 0) {
        activeRuns.delete(runId);
      }
    }
  });
});

// Broadcast to all clients
function broadcast(data) {
  clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(data));
    }
  });
}

// Broadcast to watchers of a specific run
function broadcastToRunWatchers(runId, data) {
  const watchers = activeRuns.get(runId);
  if (watchers) {
    watchers.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify(data));
      }
    });
  }
}

// Store event for a run
function storeRunEvent(runId, event) {
  if (!runEvents.has(runId)) {
    runEvents.set(runId, []);
  }
  const events = runEvents.get(runId);
  events.push({
    ...event,
    timestamp: new Date().toISOString()
  });

  // Keep only last 100 events per run
  if (events.length > 100) {
    events.shift();
  }
}

// API Routes

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Create agent run
app.post('/api/agent-runs', async (req, res) => {
  try {
    const result = await createAgentRun(req.body);
    storeRunEvent(result.id, {
      type: 'created',
      data: result
    });
    broadcastToRunWatchers(result.id, {
      type: 'run_created',
      runId: result.id,
      data: result
    });
    res.json(result);
  } catch (error) {
    console.error('Create agent run error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Resume agent run
app.post('/api/agent-runs/:id/resume', async (req, res) => {
  try {
    const result = await resumeAgentRun({
      agent_run_id: parseInt(req.params.id),
      ...req.body
    });
    storeRunEvent(result.id, {
      type: 'resumed',
      data: result
    });
    broadcastToRunWatchers(result.id, {
      type: 'run_resumed',
      runId: result.id,
      data: result
    });
    res.json(result);
  } catch (error) {
    console.error('Resume agent run error:', error);
    res.status(500).json({ error: error.message });
  }
});

// List agent runs
app.get('/api/agent-runs', async (req, res) => {
  try {
    const options = {};
    if (req.query.status) options.status = req.query.status;
    if (req.query.limit) options.limit = parseInt(req.query.limit);
    if (req.query.skip) options.skip = parseInt(req.query.skip);

    const result = await listAgentRuns(options);
    res.json(result);
  } catch (error) {
    console.error('List agent runs error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get agent run
app.get('/api/agent-runs/:id', async (req, res) => {
  try {
    const result = await getAgentRun({
      agent_run_id: parseInt(req.params.id)
    });

    // Store status update event
    storeRunEvent(result.id, {
      type: 'status_update',
      data: result
    });

    // Broadcast status update to watchers
    broadcastToRunWatchers(result.id, {
      type: 'run_update',
      runId: result.id,
      data: result
    });

    res.json(result);
  } catch (error) {
    console.error('Get agent run error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Generate setup commands
app.post('/api/setup-commands/generate', async (req, res) => {
  try {
    const result = await generateSetupCommands(req.body);
    res.json(result);
  } catch (error) {
    console.error('Generate setup commands error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Webhook endpoint for Codegen completion notifications
app.post('/webhook', express.raw({ type: 'application/json' }), async (req, res) => {
  try {
    // Parse the webhook payload
    const payload = JSON.parse(req.body.toString());

    console.log('Received webhook:', payload);

    // Process webhook based on event type
    if (payload.event_type === 'agent_run_completed' || payload.event_type === 'agent_run_updated') {
      const runId = payload.agent_run_id || payload.run_id;

      if (runId) {
        // Get updated run details
        const runDetails = await getAgentRun({ agent_run_id: runId });

        // Store completion event
        storeRunEvent(runId, {
          type: 'webhook_update',
          event: payload.event_type,
          data: runDetails
        });

        // Broadcast to watchers
        broadcastToRunWatchers(runId, {
          type: 'run_webhook_update',
          runId: runId,
          event: payload.event_type,
          data: runDetails
        });

        // Broadcast general update for UI refresh
        broadcast({
          type: 'runs_updated',
          timestamp: new Date().toISOString()
        });
      }
    }

    res.status(200).json({ received: true });
  } catch (error) {
    console.error('Webhook processing error:', error);
    res.status(500).json({ error: 'Webhook processing failed' });
  }
});

// Serve React app for all other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dashboard/build/index.html'));
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`🚀 Codegen Dashboard server running on port ${PORT}`);
  console.log(`📊 WebSocket server ready for real-time updates`);
  console.log(`🔗 Webhook endpoint: http://localhost:${PORT}/webhook`);
});

module.exports = { app, server, wss };
