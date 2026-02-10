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
      const status = document.createElement('div'); status.textContent=''; status.className = r.status==='ACTIVE'?'status-active': (r.status==='COMPLETED'?'status-completed':''); status.title=r.status;
      const pinBtn = document.createElement('button'); pinBtn.className='btn'; pinBtn.textContent = CGStore.state.pinned.includes(r.id)?'Unpin':'Pin';
      pinBtn.onclick = ()=> CGStore.state.pinned.includes(r.id) ? CGStore.unpin(r.id) : CGStore.pin(r.id);
      const watchBtn = document.createElement('button'); watchBtn.className='btn'; watchBtn.textContent = CGStore.state.watched[r.id]?'Unwatch':'Watch';
      watchBtn.onclick = ()=> CGStore.setWatched(r.id, !CGStore.state.watched[r.id]);

      // If ACTIVE: show inline chain selector; if not: clicking row opens dialog for resume/logs
      const actions = document.createElement('div'); actions.style.display='flex'; actions.style.gap='6px';
      if (r.status==='ACTIVE' || r.status==='PENDING') {
        const chainWrap = document.createElement('div'); chainWrap.style.position='relative';
        const chainBtn = document.createElement('button'); chainBtn.className='btn'; chainBtn.textContent='Chain';
        const panel = document.createElement('div'); panel.style.display='none'; panel.style.position='absolute'; panel.style.top='28px'; panel.style.right='0'; panel.style.background='white'; panel.style.border='1px solid #e5e7eb'; panel.style.padding='8px'; panel.style.borderRadius='6px'; panel.style.zIndex='5';
        const listBox = document.createElement('div'); listBox.style.maxHeight='200px'; listBox.style.overflow='auto';
        const tpls = CGStore.state.templates || [];
        const selected = new Set((CGStore.getChain(r.id)||[]).map(Number));
        tpls.forEach((t,i)=>{
          const lbl = document.createElement('label'); lbl.style.display='flex'; lbl.style.alignItems='center'; lbl.style.gap='6px'; lbl.style.fontSize='12px';
          const cb = document.createElement('input'); cb.type='checkbox'; cb.checked=selected.has(i);
          cb.onchange = ()=>{ if (cb.checked) selected.add(i); else selected.delete(i); };
          const span = document.createElement('span'); span.textContent=t.name||`Template ${i+1}`;
          lbl.appendChild(cb); lbl.appendChild(span); listBox.appendChild(lbl);
        });
        const saveBtn = document.createElement('button'); saveBtn.className='btn primary'; saveBtn.textContent='Save'; saveBtn.style.marginTop='6px';
        saveBtn.onclick = ()=>{ CGStore.setChain(r.id, Array.from(selected)); panel.style.display='none'; CGToast.toast('Chain updated'); };
        panel.appendChild(listBox); panel.appendChild(saveBtn);
        chainBtn.onclick = ()=>{ panel.style.display = panel.style.display==='none'?'block':'none'; };
        chainWrap.appendChild(chainBtn); chainWrap.appendChild(panel);
        actions.appendChild(chainWrap);
        // Clicking title opens dialog too for logs
        title.style.cursor='pointer'; title.onclick=()=> CGRunDialog.open(r.id);
      } else {
        // Completed or failed: clicking title resumes via dialog
        title.style.cursor='pointer'; title.onclick=()=> CGRunDialog.open(r.id);
      }
      actions.appendChild(pinBtn); actions.appendChild(watchBtn);
      row.appendChild(title); row.appendChild(status); row.appendChild(actions);
      list.appendChild(row);
    });
    runsRoot.appendChild(list);
  }

  function render(state){ renderControls(state); renderList(state); }
  window.CGRunList = { render };
})();
