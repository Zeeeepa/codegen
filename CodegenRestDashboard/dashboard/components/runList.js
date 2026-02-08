(function(){
  const runsRoot = document.getElementById('runs');
  const controls = document.getElementById('controls');

  const MODELS = [
    'Sonnet 4.5', 'GPT-5', 'GPT 5 Codex', 'Claude opus 4.5', 'Grok 4', 'Grok 4 Fast reasoning', 'Grok Code Fast 1'
  ];

  function renderControls(state){
    controls.innerHTML = '';
    const wrap = document.createElement('div');
    wrap.className = 'controls';

    // Filter toggle (Active/Past)
    const sel = document.createElement('select');
    ;['active','past'].forEach(v=>{
      const o = document.createElement('option'); o.value = v; o.textContent = v==='active'?'Active':'Past';
      if (state.filter===v) o.selected = true; sel.appendChild(o);
    });
    sel.onchange = ()=> CGStore.setFilter(sel.value);
    wrap.appendChild(sel);

    // Create run prompt input
    const prompt = document.createElement('input');
    prompt.placeholder = 'New agent prompt...'; prompt.style.minWidth = '260px';
    wrap.appendChild(prompt);

    // Model dropdown
    const model = document.createElement('select');
    MODELS.forEach(m=>{ const o=document.createElement('option'); o.value=m; o.textContent=m; model.appendChild(o); });
    wrap.appendChild(model);

    // Repo id (optional)
    const repo = document.createElement('input'); repo.placeholder='repo_id (optional)'; repo.type='number'; repo.style.width='140px';
    wrap.appendChild(repo);

    // Create button
    const btn = document.createElement('button');
    btn.className = 'btn primary'; btn.textContent = 'Create Agent Run';
    btn.onclick = async ()=>{
      const body = { prompt: prompt.value, model: model.value };
      if (!body.prompt) { CGToast.toast('Prompt required'); return; }
      if (repo.value) body.repo_id = Number(repo.value);
      await CGApi.createAgentRun(body);
      CGToast.toast('Agent run created');
      // No manual refresh button: watcher will auto-refresh the list shortly
      prompt.value = '';
    };
    wrap.appendChild(btn);

    controls.appendChild(wrap);
  }

  function renderList(state){
    runsRoot.innerHTML = '';
    const list = document.createElement('div');
    const filtered = state.runs.filter(r=> state.filter==='active' ? (r.status==='ACTIVE'||r.status==='PENDING') : (r.status==='COMPLETED'||r.status==='FAILED'||r.status==='CANCELLED'));
    filtered.forEach(r=>{
      const row = document.createElement('div'); row.className='run-row';
      const title = document.createElement('div'); title.textContent=`#${r.id} ${r.title||''}`; title.style.flex='1';
      const status = document.createElement('div'); status.textContent=r.status; status.className = r.status==='ACTIVE'?'status-active': (r.status==='COMPLETED'?'status-completed':'');
      const pinBtn = document.createElement('button'); pinBtn.className='btn'; pinBtn.textContent = CGStore.state.pinned.includes(r.id)?'Unpin':'Pin';
      pinBtn.onclick = ()=> CGStore.state.pinned.includes(r.id) ? CGStore.unpin(r.id) : CGStore.pin(r.id);
      const watchBtn = document.createElement('button'); watchBtn.className='btn'; watchBtn.textContent = CGStore.state.watched[r.id]?'Unwatch':'Watch';
      watchBtn.onclick = ()=> CGStore.setWatched(r.id, !CGStore.state.watched[r.id]);
      const openBtn = document.createElement('button'); openBtn.className='btn'; openBtn.textContent='Open'; openBtn.onclick=()=> CGRunDialog.open(r.id);
      row.appendChild(title); row.appendChild(status); row.appendChild(pinBtn); row.appendChild(watchBtn); row.appendChild(openBtn);
      list.appendChild(row);
    });
    runsRoot.appendChild(list);
  }

  function render(state){ renderControls(state); renderList(state); }
  window.CGRunList = { render };
})();

