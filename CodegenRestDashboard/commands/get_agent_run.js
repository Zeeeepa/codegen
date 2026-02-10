#!/usr/bin/env node
const { apiGet, pathGet, pathLogs } = require('../utils/apiClient');

async function main() {
  const args = process.argv.slice(2);
  let id = undefined;
  let withLogs = false;
  let skip = 0;
  let limit = 50;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--id') id = Number(args[++i]);
    else if (args[i] === '--logs') withLogs = true;
    else if (args[i] === '--skip') skip = Number(args[++i]);
    else if (args[i] === '--limit') limit = Number(args[++i]);
  }

  if (!id) {
    console.error('Usage: get_agent_run.js --id 123 [--logs] [--skip 0] [--limit 50]');
    process.exit(2);
  }

  const res = await apiGet(pathGet(id));
  if (!withLogs) return console.log(JSON.stringify(res, null, 2));

  const logs = await apiGet(pathLogs(id), { skip, limit });
  console.log(JSON.stringify({ run: res, logs }, null, 2));
}

if (require.main === module) {
  main().catch((e) => { console.error(e.message || e); process.exit(1); });
}

module.exports = main;

