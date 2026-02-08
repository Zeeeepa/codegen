// Tiny store with pub/sub (no deps)
(function(){
  const state = {
    activeCount: 0,
    runs: [],
    filter: 'active', // 'active' | 'past'
    pinned: [], // array of run ids
    watched: {}, // id -> boolean
    templates: JSON.parse(localStorage.getItem('cg_templates')||'[]'),
  };
  const subs = [];
  function notify(){ subs.forEach(fn=>fn(state)); save(); }
  function save(){ localStorage.setItem('cg_pins', JSON.stringify(state.pinned)); localStorage.setItem('cg_templates', JSON.stringify(state.templates)); }
  function init(){ try { state.pinned = JSON.parse(localStorage.getItem('cg_pins')||'[]'); } catch(_){} }
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
  window.CGStore = { state, subscribe, setRuns, setFilter, pin, unpin, setWatched, addTemplate, updateTemplate, deleteTemplate };
})();

