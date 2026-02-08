const apiClient = require('./apiClient');

/**
 * Create a new agent run
 * @param {Object} options - Options for creating the agent run
 * @param {string} options.prompt - The prompt/query for the agent
 * @param {string[]} [options.images] - Array of base64 encoded image data URIs
 * @param {Object} [options.metadata] - Arbitrary JSON metadata
 * @param {number} [options.repo_id] - ID of the repository to use
 * @param {string} [options.model] - Model to use (optional, uses org default if not specified)
 * @param {string} [options.agent_type] - Type of agent ("codegen" or "claude_code")
 * @returns {Promise<Object>} The created agent run response
 */
async function createAgentRun(options = {}) {
  const {
    prompt,
    images = [],
    metadata = {},
    repo_id,
    model,
    agent_type = 'codegen'
  } = options;

  if (!prompt || typeof prompt !== 'string') {
    throw new Error('Prompt is required and must be a string');
  }

  if (prompt.trim().length === 0) {
    throw new Error('Prompt cannot be empty');
  }

  // Validate agent_type
  const validAgentTypes = ['codegen', 'claude_code'];
  if (!validAgentTypes.includes(agent_type)) {
    throw new Error(`Invalid agent_type. Must be one of: ${validAgentTypes.join(', ')}`);
  }

  // Validate model if provided
  const validModels = [
    'Sonnet 4.5',
    'GPT-5',
    'GPT 5 Codex',
    'Claude opus 4.5',
    'Grok 4',
    'Grok 4 Fast reasoning',
    'Grok Code Fast 1'
  ];

  if (model && !validModels.includes(model)) {
    console.warn(`Warning: Model "${model}" may not be supported. Valid models: ${validModels.join(', ')}`);
  }

  const payload = {
    prompt: prompt.trim(),
    agent_type,
    metadata
  };

  // Add optional fields if provided
  if (images && images.length > 0) {
    payload.images = images;
  }

  if (repo_id) {
    payload.repo_id = repo_id;
  }

  if (model) {
    payload.model = model;
  }

  try {
    console.log(`Creating agent run with prompt: "${prompt.substring(0, 100)}${prompt.length > 100 ? '...' : ''}"`);
    console.log(`Using agent type: ${agent_type}${model ? `, model: ${model}` : ''}`);

    const response = await apiClient.post(`/organizations/${process.env.ORG_ID}/agent/run`, payload);

    console.log(`Agent run created successfully with ID: ${response.id}`);
    console.log(`Status: ${response.status}`);
    console.log(`Web URL: ${response.web_url || 'Not available'}`);

    return response;
  } catch (error) {
    console.error('Failed to create agent run:', error.message);
    throw error;
  }
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.error('Usage: node create_agent_run.js <prompt> [options]');
    console.error('Options:');
    console.error('  --model <model>          Model to use');
    console.error('  --agent-type <type>      Agent type (codegen or claude_code)');
    console.error('  --repo-id <id>           Repository ID');
    console.error('  --metadata <json>        JSON metadata');
    process.exit(1);
  }

  const prompt = args[0];
  const options = {};

  for (let i = 1; i < args.length; i++) {
    switch (args[i]) {
      case '--model':
        options.model = args[++i];
        break;
      case '--agent-type':
        options.agent_type = args[++i];
        break;
      case '--repo-id':
        options.repo_id = parseInt(args[++i]);
        break;
      case '--metadata':
        try {
          options.metadata = JSON.parse(args[++i]);
        } catch (e) {
          console.error('Invalid JSON for metadata');
          process.exit(1);
        }
        break;
      default:
        console.error(`Unknown option: ${args[i]}`);
        process.exit(1);
    }
  }

  createAgentRun({ prompt, ...options })
    .then(result => {
      console.log('\nAgent run created successfully:');
      console.log(JSON.stringify(result, null, 2));
    })
    .catch(error => {
      console.error('Error:', error.message);
      process.exit(1);
    });
}

module.exports = createAgentRun;

