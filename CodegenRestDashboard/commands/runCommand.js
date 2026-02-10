#!/usr/bin/env node
const cmds = require('./index');

async function main() {
  const [,, name, ...rest] = process.argv;
  if (!name || !cmds[name]) {
    console.error('Usage: runCommand.js <create|resume|list|get|genSetup> [args...]');
    process.exit(2);
  }
  // Re-dispatch by spawning module main
  await cmds[name]();
}

main().catch((e)=>{ console.error(e.message || e); process.exit(1); });

