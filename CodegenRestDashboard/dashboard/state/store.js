// Tiny store with pub/sub (no deps)
(function(){
  const state = {
    activeCount: 0,
    runs: [],
    filter: 'active', // 'active' | 'past'
    pinned: [], // array of run ids
    watched: {}, // id -> boolean
    templates: JSON.parse(localStorage.getItem('cg_templates')||'[]'),
    followUpTemplateMap: {}, // runId -> array of template indices (chain)
    chainProgressMap: {}, // runId -> integer pointer into chain
  };
  const subs = [];
  function notify(){ subs.forEach(fn=>fn(state)); save(); }
  function save(){
    localStorage.setItem('cg_pins', JSON.stringify(state.pinned));
    localStorage.setItem('cg_templates', JSON.stringify(state.templates));
    localStorage.setItem('cg_watched', JSON.stringify(state.watched));
    localStorage.setItem('cg_chain_map', JSON.stringify(state.followUpTemplateMap));
    localStorage.setItem('cg_chain_prog', JSON.stringify(state.chainProgressMap));
  }
  function init(){
    try { state.pinned = JSON.parse(localStorage.getItem('cg_pins')||'[]'); } catch(_){ }
  function setChain(runId, tplIdxArr){ state.followUpTemplateMap[runId] = Array.isArray(tplIdxArr)? tplIdxArr.slice(0) : []; notify(); }
  function setChainProgress(runId, n){ state.chainProgressMap[runId] = n|0; notify(); }
  function getChain(runId){ return state.followUpTemplateMap[runId] || []; }
  function getChainProgress(runId){ return (state.chainProgressMap[runId] | 0); }

    try { state.watched = JSON.parse(localStorage.getItem('cg_watched')||'{}'); } catch(_){ }
    try { state.followUpTemplateMap = JSON.parse(localStorage.getItem('cg_chain_map')||'{}'); } catch(_){ }
    try { state.chainProgressMap = JSON.parse(localStorage.getItem('cg_chain_prog')||'{}'); } catch(_){ }
  }
  function subscribe(fn){ subs.push(fn); fn(state); return ()=>{ const i=subs.indexOf(fn); if(i>=0) subs.splice(i,1); } }
  function setRuns(runs){ state.runs = runs; state.activeCount = runs.filter(r=>r.status==='ACTIVE' || r.status==='PENDING' ).length; notify(); }
  function setFilter(f){ state.filter = f; notify(); }
  function pin(id){ if(!state.pinned.includes(id)) { state.pinned.unshift(id); notify(); } }
  function unpin(id){ state.pinned = state.pinned.filter(x=>x!==id); notify(); }
  function setWatched(id, v){ state.watched[id] = !!v; notify(); }
  function addTemplate(t){ state.templates.push(t); notify(); }
  function updateTemplate(i, t){ state.templates[i]=t; notify(); }
  function deleteTemplate(i){ state.templates.splice(i,1); notify(); }
  init();
  window.CGStore = { state, subscribe, setRuns, setFilter, pin, unpin, setWatched, addTemplate, updateTemplate, deleteTemplate, setChain, setChainProgress, getChain, getChainProgress };
})();
