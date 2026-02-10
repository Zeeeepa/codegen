// Minimal API client (Node-only)
const { loadEnv } = require('./env');
const http = require('http');
const https = require('https');

loadEnv();

const API_BASE = process.env.CODEGEN_API_BASE?.replace(/\/$/, '') || 'https://api.codegen.com';
const ORG_ID = process.env.CODEGEN_ORG_ID;
const TOKEN = process.env.CODEGEN_TOKEN;
const OFFLINE = String(process.env.CODEGEN_OFFLINE || '0') === '1';

function nodeFetch(url, options) {
  // Prefer global fetch if available (Node 18+), else fallback to https
  if (typeof fetch === 'function') {
    return fetch(url, options);
  }
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const mod = u.protocol === 'http:' ? http : https;
    const req = mod.request({
      method: options?.method || 'GET',
      hostname: u.hostname,
      port: u.port || (u.protocol === 'http:' ? 80 : 443),
      path: u.pathname + u.search,
      headers: options?.headers || {},
    }, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        resolve({
          ok: res.statusCode >= 200 && res.statusCode < 300,
          status: res.statusCode,
          json: async () => JSON.parse(data || '{}'),
          text: async () => data,
        });
      });
    });
    req.on('error', reject);
    if (options?.body) req.write(options.body);
    req.end();
  });
}

function authHeaders() {
  if (!TOKEN || !ORG_ID) throw new Error('Missing CODEGEN_TOKEN or CODEGEN_ORG_ID');
  return {
    'Authorization': `Bearer ${TOKEN}`,
    'Content-Type': 'application/json',
  };
}

async function apiGet(path, params = {}) {
  if (OFFLINE) return mockResponse(path, params, 'GET');
  const qs = new URLSearchParams(params).toString();
  const url = `${API_BASE}${path}${qs ? `?${qs}` : ''}`;
  const res = await nodeFetch(url, { method: 'GET', headers: authHeaders() });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

async function apiPost(path, body = {}) {
  if (OFFLINE) return mockResponse(path, body, 'POST');
  const url = `${API_BASE}${path}`;
  const res = await nodeFetch(url, { method: 'POST', headers: authHeaders(), body: JSON.stringify(body) });
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error(`POST ${path} failed: ${res.status} ${txt}`);
  }
  return res.json();
}

// Mock data for offline mode
function mockResponse(path, payload, method) {
  if (path.includes('/agent/runs')) {
    return Promise.resolve({
      data: [
        { id: 101, status: 'ACTIVE', title: 'Active run A', created_at: new Date().toISOString() },
        { id: 99, status: 'COMPLETED', title: 'Past run X', created_at: new Date(Date.now()-86400000).toISOString() },
      ],
      total: 2,
      page: 1,
      limit: 50,
    });
  }
  if (path.includes('/agent/run/resume')) {
    return Promise.resolve({ success: true, resumed: true, ...payload });
  }
  if (path.includes('/agent/run/') && method === 'GET' && path.match(/\/agent\/run\/(\d+)/)) {
    const id = Number(path.match(/\/(\d+)$/)?.[1] || 0);
    return Promise.resolve({ id, status: id % 2 ? 'ACTIVE' : 'COMPLETED', title: `Run ${id}` });
  }
  if (path.includes('/agent/run') && method === 'POST') {
    return Promise.resolve({ id: Math.floor(Math.random()*1000)+200, status: 'PENDING', ...payload });
  }
  if (path.includes('/setup-commands/generate')) {
    return Promise.resolve({ status: 'QUEUED', repo_id: payload.repo_id, agent_run_id: 555 });
  }
  if (path.includes('/logs')) {
    return Promise.resolve({
      agent_run: { id: payload.id || 999, status: 'ACTIVE' },
      logs: [ { id: 1, message: 'Mock log line 1', level: 'INFO', timestamp: new Date().toISOString() } ],
      pagination: { skip: 0, limit: 50, total: 1 }
    });
  }
  return Promise.resolve({ ok: true, echo: { path, payload, method } });
}

// High-level API wrappers
function pathCreate() { return `/v1/organizations/${ORG_ID}/agent/run`; }
function pathGet(id) { return `/v1/organizations/${ORG_ID}/agent/run/${id}`; }
function pathList() { return `/v1/organizations/${ORG_ID}/agent/runs`; }
function pathResume() { return `/v1/organizations/${ORG_ID}/agent/run/resume`; }
function pathLogs(id) { return `/v1/alpha/organizations/${ORG_ID}/agent/run/${id}/logs`; }
function pathGenerateSetup() { return `/v1/organizations/${ORG_ID}/setup-commands/generate`; }

module.exports = {
  apiGet,
  apiPost,
  pathCreate,
  pathGet,
  pathList,
  pathResume,
  pathLogs,
  pathGenerateSetup,
};
