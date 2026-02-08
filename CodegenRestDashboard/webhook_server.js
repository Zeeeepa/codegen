/**
 * Cloudflare Worker script for handling Codegen webhooks
 * This script should be deployed to Cloudflare Workers
 * and configured to handle requests to www.pixelium.uk/webhook
 */

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  // Only accept POST requests
  if (request.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 })
  }

  try {
    // Get the webhook payload
    const payload = await request.json()

    console.log('Received Codegen webhook:', JSON.stringify(payload, null, 2))

    // Validate webhook (you should implement proper signature verification)
    // For now, we'll just log and acknowledge

    // Process different webhook event types
    switch (payload.event_type) {
      case 'agent_run_completed':
        await handleAgentRunCompleted(payload)
        break
      case 'agent_run_started':
        await handleAgentRunStarted(payload)
        break
      case 'agent_run_failed':
        await handleAgentRunFailed(payload)
        break
      default:
        console.log(`Unknown webhook event type: ${payload.event_type}`)
    }

    // Forward webhook to our main dashboard server
    await forwardWebhookToDashboard(payload)

    // Return success response
    return new Response(JSON.stringify({
      success: true,
      received: true,
      timestamp: new Date().toISOString()
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json'
      }
    })

  } catch (error) {
    console.error('Webhook processing error:', error)

    return new Response(JSON.stringify({
      success: false,
      error: error.message
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json'
      }
    })
  }
}

async function handleAgentRunCompleted(payload) {
  console.log(`Agent run ${payload.agent_run_id || payload.run_id} completed`)

  // Here you could:
  // - Send notifications
  // - Trigger follow-up actions
  // - Update external systems
  // - Log analytics

  // For the dashboard, we'll forward this to the main server
}

async function handleAgentRunStarted(payload) {
  console.log(`Agent run ${payload.agent_run_id || payload.run_id} started`)

  // Handle run started events
}

async function handleAgentRunFailed(payload) {
  console.log(`Agent run ${payload.agent_run_id || payload.run_id} failed:`, payload.error)

  // Handle run failure events
}

async function forwardWebhookToDashboard(payload) {
  try {
    // Forward to local dashboard server (adjust URL for your setup)
    const dashboardUrl = 'http://localhost:3001/webhook'

    const response = await fetch(dashboardUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Webhook-Source': 'cloudflare'
      },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      console.error('Failed to forward webhook to dashboard:', response.status, response.statusText)
    } else {
      console.log('Successfully forwarded webhook to dashboard')
    }
  } catch (error) {
    console.error('Error forwarding webhook to dashboard:', error)
  }
}

/**
 * Deployment instructions for Cloudflare Workers:
 *
 * 1. Install Wrangler CLI: npm install -g wrangler
 * 2. Login to Cloudflare: wrangler auth login
 * 3. Create a new worker: wrangler init codegen-webhook-worker
 * 4. Replace the worker script with this code
 * 5. Deploy: wrangler deploy
 * 6. Configure route: wrangler routes add www.pixelium.uk/webhook
 *
 * Environment variables to set:
 * - DASHBOARD_URL: URL of your main dashboard server
 * - WEBHOOK_SECRET: Secret for webhook signature verification
 */

