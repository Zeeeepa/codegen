#!/usr/bin/env node
const { apiPost, pathResume } = require('../utils/apiClient');

async function main() {
  const args = process.argv.slice(2);
  let id = undefined;
  let prompt = '';

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--id') id = Number(args[++i]);
    else if (args[i] === '--prompt') prompt = args[++i] || '';
  }

  if (!id) {
    console.error('Usage: resume_agent_run.js --id 123 [--prompt "..."]');
    process.exit(2);
  }

  const body = { agent_run_id: id };
  if (prompt) body.prompt = prompt;

  const data = await apiPost(pathResume(), body);
  console.log(JSON.stringify(data, null, 2));
}

if (require.main === module) {
  main().catch((e) => { console.error(e.message || e); process.exit(1); });
}

module.exports = main;

