#!/usr/bin/env node
const { apiPost, pathGenerateSetup } = require('../utils/apiClient');

async function main() {
  const args = process.argv.slice(2);
  let repo_id = undefined;
  let language = undefined; // optional

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--repo_id') repo_id = Number(args[++i]);
    else if (args[i] === '--language') language = args[++i] || undefined;
  }

  if (!repo_id) {
    console.error('Usage: generate_setup_commands.js --repo_id 123 [--language node|python|...]');
    process.exit(2);
  }

  const body = { repo_id };
  if (language) body.language = language;

  const data = await apiPost(pathGenerateSetup(), body);
  console.log(JSON.stringify(data, null, 2));
}

if (require.main === module) {
  main().catch((e) => { console.error(e.message || e); process.exit(1); });
}

module.exports = main;

