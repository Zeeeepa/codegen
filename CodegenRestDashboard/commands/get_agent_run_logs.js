#!/usr/bin/env node
const { apiGet, pathLogs } = require('../utils/apiClient');

async function main(){
  const args = process.argv.slice(2);
  let id; let skip=0; let limit=100;
  for (let i=0;i<args.length;i++){
    if (args[i]==='--id') id = Number(args[++i]);
    else if (args[i]==='--skip') skip = Number(args[++i]);
    else if (args[i]==='--limit') limit = Number(args[++i]);
  }
  if (!id) { console.error('Usage: get_agent_run_logs.js --id <runId> [--skip 0] [--limit 100]'); process.exit(2); }
  const data = await apiGet(pathLogs(id), { skip, limit });
  console.log(JSON.stringify(data, null, 2));
}

if (require.main===module){ main().catch(e=>{ console.error(e.message||e); process.exit(1); }); }
module.exports = main;

