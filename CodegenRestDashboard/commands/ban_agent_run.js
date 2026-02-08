#!/usr/bin/env node
const { apiPost } = require('../utils/apiClient');
const { loadEnv } = require('../utils/env');
const path = require('path');
loadEnv(path.join(__dirname, '..', '.env'));

function pathBan(org){ return `/v1/organizations/${org}/agent/run/ban`; }

async function main(){
  const args = process.argv.slice(2);
  let id; let before=null; let after=null;
  for (let i=0;i<args.length;i++){
    if (args[i]==='--id') id = Number(args[++i]);
    else if (args[i]==='--before') before = args[++i];
    else if (args[i]==='--after') after = args[++i];
  }
  if (!id) { console.error('Usage: ban_agent_run.js --id <runId> [--before <order>] [--after <order>]'); process.exit(2); }
  const org = process.env.CODEGEN_ORG_ID;
  const body = { agent_run_id: id };
  if (before!==null) body.before_card_order_id = before;
  if (after!==null) body.after_card_order_id = after;
  const data = await apiPost(pathBan(org), body);
  console.log(JSON.stringify(data, null, 2));
}

if (require.main===module){ main().catch(e=>{ console.error(e.message||e); process.exit(1); }); }
module.exports = main;

