const apiClient = require('./apiClient');

/**
 * Resume a paused agent run
 * @param {Object} options - Options for resuming the agent run
 * @param {number} options.agent_run_id - ID of the agent run to resume
 * @param {string} options.prompt - The new prompt/query for the resumed agent
 * @param {string[]} [options.images] - Array of base64 encoded image data URIs
 * @returns {Promise<Object>} The resumed agent run response
 */
async function resumeAgentRun(options = {}) {
  const {
    agent_run_id,
    prompt,
    images = []
  } = options;

  if (!agent_run_id || typeof agent_run_id !== 'number') {
    throw new Error('agent_run_id is required and must be a number');
  }

  if (!prompt || typeof prompt !== 'string') {
    throw new Error('Prompt is required and must be a string');
  }

  if (prompt.trim().length === 0) {
    throw new Error('Prompt cannot be empty');
  }

  const payload = {
    agent_run_id,
    prompt: prompt.trim()
  };

  // Add optional images if provided
  if (images && images.length > 0) {
    payload.images = images;
  }

  try {
    console.log(`Resuming agent run ${agent_run_id} with prompt: "${prompt.substring(0, 100)}${prompt.length > 100 ? '...' : ''}"`);

    const response = await apiClient.post(`/organizations/${process.env.ORG_ID}/agent/run/resume`, payload);

    console.log(`Agent run ${agent_run_id} resumed successfully`);
    console.log(`Status: ${response.status}`);
    console.log(`Web URL: ${response.web_url || 'Not available'}`);

    return response;
  } catch (error) {
    console.error(`Failed to resume agent run ${agent_run_id}:`, error.message);
    throw error;
  }
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('Usage: node resume_agent_run.js <agent_run_id> <prompt> [options]');
    console.error('Options:');
    console.error('  --images <image1,image2>    Comma-separated list of base64 image data URIs');
    process.exit(1);
  }

  const agentRunId = parseInt(args[0]);
  const prompt = args[1];

  if (isNaN(agentRunId)) {
    console.error('agent_run_id must be a valid number');
    process.exit(1);
  }

  const options = { agent_run_id: agentRunId, prompt };

  for (let i = 2; i < args.length; i++) {
    switch (args[i]) {
      case '--images':
        options.images = args[++i].split(',').map(img => img.trim());
        break;
      default:
        console.error(`Unknown option: ${args[i]}`);
        process.exit(1);
    }
  }

  resumeAgentRun(options)
    .then(result => {
      console.log('\nAgent run resumed successfully:');
      console.log(JSON.stringify(result, null, 2));
    })
    .catch(error => {
      console.error('Error:', error.message);
      process.exit(1);
    });
}

module.exports = resumeAgentRun;

