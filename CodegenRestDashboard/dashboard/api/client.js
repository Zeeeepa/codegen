// Browser-side client calls the local proxy server under /api
(function(){
  const api = {};
  const base = '/api';

  function get(path, params={}){
    const qs = new URLSearchParams(params).toString();
    return fetch(`${base}${path}${qs?`?${qs}`:''}`).then(r=>r.json());
  }
  function post(path, body={}){
    return fetch(`${base}${path}`, { method: 'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify(body) }).then(r=>r.json());
  }

  // Helpers mirroring Node client paths
  function createAgentRun(payload){ return post(`/v1/organizations/${CG_ENV.ORG_ID}/agent/run`, payload); }
  function listAgentRuns(params){ return get(`/v1/organizations/${CG_ENV.ORG_ID}/agent/runs`, params); }
  function getAgentRun(id){ return get(`/v1/organizations/${CG_ENV.ORG_ID}/agent/run/${id}`); }
  function getAgentLogs(id, params){ return get(`/v1/alpha/organizations/${CG_ENV.ORG_ID}/agent/run/${id}/logs`, params); }
  function resumeAgentRun(payload){ return post(`/v1/organizations/${CG_ENV.ORG_ID}/agent/run/resume`, payload); }

  window.CGApi = { createAgentRun, listAgentRuns, getAgentRun, getAgentLogs, resumeAgentRun };
})();

