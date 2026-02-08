const apiClient = require('./apiClient');

/**
 * Get detailed information about a specific agent run
 * @param {Object} options - Options for getting agent run details
 * @param {number} options.agent_run_id - ID of the agent run to retrieve
 * @returns {Promise<Object>} Detailed agent run information
 */
async function getAgentRun(options = {}) {
  const { agent_run_id } = options;

  if (!agent_run_id || typeof agent_run_id !== 'number') {
    throw new Error('agent_run_id is required and must be a number');
  }

  try {
    console.log(`Getting agent run details for ID: ${agent_run_id}`);

    const response = await apiClient.get(`/organizations/${process.env.ORG_ID}/agent/run/${agent_run_id}`);

    console.log(`Retrieved agent run ${agent_run_id}`);
    console.log(`Status: ${response.status || 'unknown'}`);
    console.log(`Created: ${response.created_at || 'unknown'}`);
    console.log(`Has result: ${!!response.result}`);
    console.log(`Has summary: ${!!response.summary}`);

    return response;
  } catch (error) {
    console.error(`Failed to get agent run ${agent_run_id}:`, error.message);
    throw error;
  }
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.error('Usage: node get_agent_run.js <agent_run_id>');
    process.exit(1);
  }

  const agentRunId = parseInt(args[0]);

  if (isNaN(agentRunId)) {
    console.error('agent_run_id must be a valid number');
    process.exit(1);
  }

  getAgentRun({ agent_run_id: agentRunId })
    .then(result => {
      console.log('\nAgent run details:');
      console.log(JSON.stringify(result, null, 2));

      // Additional formatted output
      console.log('\n--- Formatted Output ---');
      console.log(`ID: ${result.id}`);
      console.log(`Organization ID: ${result.organization_id}`);
      console.log(`Status: ${result.status || 'unknown'}`);
      console.log(`Created At: ${result.created_at || 'unknown'}`);
      console.log(`Web URL: ${result.web_url || 'not available'}`);
      console.log(`Source Type: ${result.source_type || 'unknown'}`);

      if (result.summary) {
        console.log(`Summary: ${result.summary}`);
      }

      if (result.result) {
        console.log(`Result Length: ${result.result.length} characters`);
        console.log(`Result Preview: ${result.result.substring(0, 200)}${result.result.length > 200 ? '...' : ''}`);
      }

      if (result.github_pull_requests && result.github_pull_requests.length > 0) {
        console.log(`GitHub PRs: ${result.github_pull_requests.length}`);
        result.github_pull_requests.forEach(pr => {
          console.log(`  - ${pr.title} (${pr.url})`);
        });
      }

      if (result.metadata && Object.keys(result.metadata).length > 0) {
        console.log(`Metadata: ${JSON.stringify(result.metadata, null, 2)}`);
      }
    })
    .catch(error => {
      console.error('Error:', error.message);
      process.exit(1);
    });
}

module.exports = getAgentRun;

