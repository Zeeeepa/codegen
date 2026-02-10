#!/usr/bin/env node
const { apiPost, pathCreate } = require('../utils/apiClient');

const MODELS = [
  'Sonnet 4.5',
  'GPT-5',
  'GPT 5 Codex',
  'Claude opus 4.5',
  'Grok 4',
  'Grok 4 Fast reasoning',
  'Grok Code Fast 1',
];

async function main() {
  const args = process.argv.slice(2);
  let prompt = '';
  let model = '';
  let repo_id = undefined;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--prompt') prompt = args[++i] || '';
    else if (args[i] === '--model') model = args[++i] || '';
    else if (args[i] === '--repo_id') repo_id = Number(args[++i]);
  }

  if (!prompt) {
    console.error('Usage: create_agent_run.js --prompt "..." [--model "Sonnet 4.5"|...] [--repo_id 123]');
    process.exit(2);
  }
  if (model && !MODELS.includes(model)) {
    console.error(`Model must be one of: ${MODELS.join(', ')}`);
    process.exit(2);
  }

  const body = { prompt };
  if (model) body.model = model;
  if (repo_id) body.repo_id = repo_id;

  const data = await apiPost(pathCreate(), body);
  console.log(JSON.stringify(data, null, 2));
}

if (require.main === module) {
  main().catch((e) => { console.error(e.message || e); process.exit(1); });
}

module.exports = main;

