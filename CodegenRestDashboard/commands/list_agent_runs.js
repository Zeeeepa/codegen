#!/usr/bin/env node
const { apiGet, pathList } = require('../utils/apiClient');

async function main() {
  const args = process.argv.slice(2);
  let state = '';
  let page = 1;
  let limit = 50;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--state') state = args[++i] || '';
    else if (args[i] === '--page') page = Number(args[++i]);
    else if (args[i] === '--limit') limit = Number(args[++i]);
  }

  const params = { page, limit };
  if (state) params.state = state; // server may ignore if unsupported

  const data = await apiGet(pathList(), params);
  console.log(JSON.stringify(data, null, 2));
}

if (require.main === module) {
  main().catch((e) => { console.error(e.message || e); process.exit(1); });
}

module.exports = main;

