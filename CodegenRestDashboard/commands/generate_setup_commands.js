const apiClient = require('./apiClient');

/**
 * Generate setup commands for a repository
 * @param {Object} options - Options for generating setup commands
 * @param {number} options.repo_id - ID of the repository to generate setup commands for
 * @param {string} [options.prompt] - Optional prompt to guide the setup command generation
 * @param {string} [options.trigger_source='setup-commands'] - Source that triggered the generation
 * @returns {Promise<Object>} Setup command generation response
 */
async function generateSetupCommands(options = {}) {
  const {
    repo_id,
    prompt,
    trigger_source = 'setup-commands'
  } = options;

  if (!repo_id || typeof repo_id !== 'number') {
    throw new Error('repo_id is required and must be a number');
  }

  const payload = {
    repo_id,
    trigger_source
  };

  // Add optional prompt if provided
  if (prompt && typeof prompt === 'string') {
    payload.prompt = prompt.trim();
  }

  try {
    console.log(`Generating setup commands for repository ID: ${repo_id}`);
    if (prompt) {
      console.log(`Using prompt: "${prompt.substring(0, 100)}${prompt.length > 100 ? '...' : ''}"`);
    }

    const response = await apiClient.post(`/organizations/${process.env.ORG_ID}/setup-commands/generate`, payload);

    console.log(`Setup command generation initiated successfully`);
    console.log(`Agent Run ID: ${response.agent_run_id}`);
    console.log(`Status: ${response.status}`);
    console.log(`URL: ${response.url}`);

    return response;
  } catch (error) {
    console.error(`Failed to generate setup commands for repo ${repo_id}:`, error.message);
    throw error;
  }
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.error('Usage: node generate_setup_commands.js <repo_id> [options]');
    console.error('Options:');
    console.error('  --prompt <text>              Optional prompt to guide generation');
    console.error('  --trigger-source <source>    Trigger source (default: setup-commands)');
    process.exit(1);
  }

  const repoId = parseInt(args[0]);

  if (isNaN(repoId)) {
    console.error('repo_id must be a valid number');
    process.exit(1);
  }

  const options = { repo_id: repoId };

  for (let i = 1; i < args.length; i++) {
    switch (args[i]) {
      case '--prompt':
        options.prompt = args[++i];
        break;
      case '--trigger-source':
        options.trigger_source = args[++i];
        break;
      default:
        console.error(`Unknown option: ${args[i]}`);
        process.exit(1);
    }
  }

  generateSetupCommands(options)
    .then(result => {
      console.log('\nSetup command generation initiated:');
      console.log(JSON.stringify(result, null, 2));
    })
    .catch(error => {
      console.error('Error:', error.message);
      process.exit(1);
    });
}

module.exports = generateSetupCommands;

