// Minimal .env loader without dependencies
// Usage: loadEnv(path.join(__dirname, '..', '.env'))
const fs = require('fs');
const path = require('path');

function loadEnv(envPath) {
  try {
    if (!envPath) envPath = path.join(process.cwd(), 'CodegenRestDashboard', '.env');
    if (!fs.existsSync(envPath)) return;
    const content = fs.readFileSync(envPath, 'utf8');
    content.split(/\r?\n/).forEach((line) => {
      if (!line || line.trim().startsWith('#')) return;
      const idx = line.indexOf('=');
      if (idx === -1) return;
      const key = line.slice(0, idx).trim();
      const val = line.slice(idx + 1).trim();
      if (key && !(key in process.env)) process.env[key] = val;
    });
  } catch (e) {
    console.error('[env] Failed to load .env:', e.message);
  }
}

module.exports = { loadEnv };

