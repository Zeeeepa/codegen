#!/usr/bin/env node
const path = require('path');
const { loadEnv } = require('../utils/env');
loadEnv(path.join(__dirname, '..', '.env'));

// Minimal inlined renderer to avoid depending on dashboard file
function getPath(obj, p){ try { return p.split('.').reduce((a,k)=>(a&&a[k]!=null?a[k]:undefined), obj);} catch(_){ return undefined; } }
function renderTemplate(tpl, vars){ return String(tpl||'').replace(/\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}/g,(_,k)=>{ const v=getPath(vars||{},k); return v==null? '': String(v); }); }

async function main(){
  const args = process.argv.slice(2);
  let template = '';
  let varsJson = '{}';
  for (let i=0;i<args.length;i++){
    if (args[i]==='--template') template = args[++i]||'';
    else if (args[i]==='--vars') varsJson = args[++i]||'{}';
  }
  if (!template){
    console.error('Usage: render_template.js --template "Hello {{run_id}}" --vars "{\"run_id\":123,\"result\":\"OK\"}"');
    process.exit(2);
  }
  let vars={};
  try { vars = JSON.parse(varsJson); } catch(e){ console.error('Invalid JSON for --vars'); process.exit(2); }
  const out = renderTemplate(template, vars);
  console.log(out);
}

if (require.main===module){ main().catch(e=>{ console.error(e.message||e); process.exit(1); }); }
module.exports = main;

