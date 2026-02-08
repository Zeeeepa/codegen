// Simple static server + proxy without external deps
const http = require('http');
const fs = require('fs');
const path = require('path');
const { loadEnv } = require('./utils/env');
loadEnv(path.join(__dirname, '.env'));

const PORT = Number(process.env.PORT || 8787);
const API_BASE = (process.env.CODEGEN_API_BASE || 'https://api.codegen.com').replace(/\/$/, '');
const TOKEN = process.env.CODEGEN_TOKEN || '';
const ORG_ID = process.env.CODEGEN_ORG_ID || '';
const OFFLINE = String(process.env.CODEGEN_OFFLINE || '0') === '1';

// In-memory webhook events cache (best-effort; dev only)
const webhookEvents = [];

function serveWebhook(req, res){
  let body = '';
  req.on('data', c => body += c);
  req.on('end', ()=>{
    try {
      const json = JSON.parse(body || '{}');
      webhookEvents.push({ ts: Date.now(), body: json });
    } catch(_) {
      webhookEvents.push({ ts: Date.now(), raw: body });
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true }));
  });
}

function serveEvents(req, res){
  // Return and clear (so each event is processed once). Client can poll /api/events frequently.
  const copy = webhookEvents.splice(0, webhookEvents.length);
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ events: copy }));
}


function contentType(filePath) {
  if (filePath.endsWith('.html')) return 'text/html; charset=utf-8';
  if (filePath.endsWith('.css')) return 'text/css; charset=utf-8';
  if (filePath.endsWith('.js')) return 'application/javascript; charset=utf-8';
  if (filePath.endsWith('.json')) return 'application/json; charset=utf-8';
  return 'text/plain; charset=utf-8';
}

function serveStatic(req, res) {
  let file = req.url.split('?')[0];
  if (file === '/' || file === '') file = '/index.html';
  const p = path.join(__dirname, 'dashboard', file);
  if (!p.startsWith(path.join(__dirname, 'dashboard'))) {
    res.writeHead(403); return res.end('Forbidden');
  }
  fs.readFile(p, (err, data) => {
    if (err) { res.writeHead(404); return res.end('Not found'); }
    res.writeHead(200, { 'Content-Type': contentType(p) });
    res.end(data);
  });
}

async function proxyApi(req, res) {
  if (!TOKEN || !ORG_ID) { res.writeHead(500); return res.end('Missing CODEGEN_TOKEN or CODEGEN_ORG_ID'); }
  let body = '';
  req.on('data', (c) => body += c);
  req.on('end', async () => {
    try {
      // Map /api/* to real endpoints; the incoming path already contains /v1/...
      const target = `${API_BASE}${req.url.replace(/^\/api/, '')}`;
      if (OFFLINE) {
        // Minimal offline mock
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: true, offline: true, url: target }));
      }
      const r = await fetch(target, {
        method: req.method,
        headers: {
          'Authorization': `Bearer ${TOKEN}`,
          'Content-Type': req.headers['content-type'] || 'application/json'
        },
        body: ['POST','PUT','PATCH'].includes(req.method) ? body : undefined,
      });
      const txt = await r.text();
      res.writeHead(r.status, { 'Content-Type': r.headers.get('content-type') || 'application/json' });
      res.end(txt);
    } catch (e) {
      res.writeHead(500); res.end(e.message || 'Proxy error');
    }
  });
}

const server = http.createServer((req, res) => {
  if (req.url.startsWith('/api/events') && req.method==='GET') return serveEvents(req, res);
  if (req.url === '/webhook' && req.method==='POST') return serveWebhook(req, res);
  if (req.url.startsWith('/api/')) return proxyApi(req, res);
  return serveStatic(req, res);
});

server.listen(PORT, () => {
  console.log(`[CodegenRestDashboard] Server listening on http://localhost:${PORT}`);
});
