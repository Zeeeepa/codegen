const apiClient = require('./apiClient');

/**
 * List agent runs for an organization
 * @param {Object} options - Options for listing agent runs
 * @param {number} [options.user_id] - Filter by user ID who initiated the agent runs
 * @param {string} [options.source_type] - Filter by source type
 * @param {string} [options.status] - Filter by status (active/completed)
 * @param {number} [options.skip=0] - Number of items to skip
 * @param {number} [options.limit=100] - Number of items to return (max 100)
 * @returns {Promise<Object>} Paginated list of agent runs
 */
async function listAgentRuns(options = {}) {
  const {
    user_id,
    source_type,
    status,
    skip = 0,
    limit = 100
  } = options;

  // Validate parameters
  if (skip < 0) {
    throw new Error('skip must be >= 0');
  }

  if (limit < 1 || limit > 100) {
    throw new Error('limit must be between 1 and 100');
  }

  // Build query parameters
  const params = { skip, limit };

  if (user_id) {
    params.user_id = user_id;
  }

  if (source_type) {
    const validSourceTypes = [
      'LOCAL', 'SLACK', 'GITHUB', 'GITHUB_CHECK_SUITE', 'GITHUB_PR_REVIEW',
      'LINEAR', 'API', 'CHAT', 'JIRA', 'CLICKUP', 'MONDAY', 'SETUP_COMMANDS'
    ];
    if (!validSourceTypes.includes(source_type)) {
      throw new Error(`Invalid source_type. Must be one of: ${validSourceTypes.join(', ')}`);
    }
    params.source_type = source_type;
  }

  try {
    console.log(`Listing agent runs (skip: ${skip}, limit: ${limit})`);

    const response = await apiClient.get(`/organizations/${process.env.ORG_ID}/agent/runs`, params);

    // Filter by status if specified (client-side filtering since API doesn't support status filter)
    let items = response.items || [];

    if (status) {
      if (status === 'active') {
        // Consider runs active if they don't have a result yet or status indicates running
        items = items.filter(run =>
          !run.result ||
          run.status === 'running' ||
          run.status === 'in_progress' ||
          run.status === 'pending'
        );
      } else if (status === 'completed') {
        // Consider runs completed if they have a result or status indicates completion
        items = items.filter(run =>
          run.result ||
          run.status === 'completed' ||
          run.status === 'success' ||
          run.status === 'failed'
        );
      }
    }

    const filteredResponse = {
      ...response,
      items,
      total: items.length // Update total to reflect filtered count
    };

    console.log(`Found ${items.length} agent runs (total: ${response.total || 0})`);

    return filteredResponse;
  } catch (error) {
    console.error('Failed to list agent runs:', error.message);
    throw error;
  }
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2);
  const options = {};

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--user-id':
        options.user_id = parseInt(args[++i]);
        break;
      case '--source-type':
        options.source_type = args[++i];
        break;
      case '--status':
        options.status = args[++i];
        break;
      case '--skip':
        options.skip = parseInt(args[++i]);
        break;
      case '--limit':
        options.limit = parseInt(args[++i]);
        break;
      case '--help':
        console.log('Usage: node list_agent_runs.js [options]');
        console.log('Options:');
        console.log('  --user-id <id>           Filter by user ID');
        console.log('  --source-type <type>     Filter by source type');
        console.log('  --status <status>        Filter by status (active/completed)');
        console.log('  --skip <number>          Number of items to skip (default: 0)');
        console.log('  --limit <number>         Number of items to return (default: 100, max: 100)');
        process.exit(0);
      default:
        console.error(`Unknown option: ${args[i]}`);
        console.error('Use --help for usage information');
        process.exit(1);
    }
  }

  listAgentRuns(options)
    .then(result => {
      console.log('\nAgent runs:');
      console.log(`Total: ${result.total}, Page: ${result.page}, Size: ${result.size}, Pages: ${result.pages}`);
      console.log('\nItems:');

      result.items.forEach(run => {
        console.log(`- ID: ${run.id}`);
        console.log(`  Status: ${run.status || 'unknown'}`);
        console.log(`  Created: ${run.created_at || 'unknown'}`);
        console.log(`  Web URL: ${run.web_url || 'not available'}`);
        console.log(`  Summary: ${run.summary ? run.summary.substring(0, 100) + (run.summary.length > 100 ? '...' : '') : 'none'}`);
        console.log('');
      });
    })
    .catch(error => {
      console.error('Error:', error.message);
      process.exit(1);
    });
}

module.exports = listAgentRuns;

