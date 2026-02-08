(function(){
  const root = document.getElementById('pinned');

  function render(state){
    root.innerHTML = '';
    if (!state.pinned.length) return;
    const wrap = document.createElement('div');
    const title = document.createElement('div');
    title.textContent = 'Pinned'; title.style.marginBottom='6px';
    wrap.appendChild(title);

    state.pinned.forEach(id=>{
      const run = state.runs.find(r=>r.id===id) || { id, status: 'UNKNOWN' };
      const card = document.createElement('div'); card.className='pin-card';
      const head = document.createElement('div'); head.textContent = `#${id} ${run.title||''}`; head.style.fontWeight='600';
      const status = document.createElement('div'); status.textContent = ''; status.className = run.status==='ACTIVE'?'status-active': (run.status==='COMPLETED'?'status-completed':''); status.title = run.status;
      const controls = document.createElement('div'); controls.style.display='flex'; controls.style.gap='6px';
      const unpin = document.createElement('button'); unpin.className='btn'; unpin.textContent='Unpin'; unpin.onclick=()=> CGStore.unpin(id);
      const open = document.createElement('button'); open.className='btn'; open.textContent='Open'; open.onclick=()=> CGRunDialog.open(id);

      // Inline chain selector for active runs
      if (run.status==='ACTIVE' || run.status==='PENDING'){
        const chain = document.createElement('button'); chain.className='btn'; chain.textContent='Chain';
        const panel = document.createElement('div'); panel.style.display='none'; panel.style.marginTop='6px';
        const listBox = document.createElement('div');
        const tpls = CGStore.state.templates || [];
        const selected = new Set((CGStore.getChain(id)||[]).map(Number));
        tpls.forEach((t,i)=>{
          const lbl = document.createElement('label'); lbl.style.display='flex'; lbl.style.alignItems='center'; lbl.style.gap='6px'; lbl.style.fontSize='12px';
          const cb = document.createElement('input'); cb.type='checkbox'; cb.checked=selected.has(i);
          cb.onchange = ()=>{ if (cb.checked) selected.add(i); else selected.delete(i); };
          const span = document.createElement('span'); span.textContent=t.name||`Template ${i+1}`;
          lbl.appendChild(cb); lbl.appendChild(span); listBox.appendChild(lbl);
        });
        const save = document.createElement('button'); save.className='btn primary'; save.textContent='Save'; save.style.marginTop='6px';
        save.onclick = ()=> { CGStore.setChain(id, Array.from(selected)); panel.style.display='none'; CGToast.toast('Chain updated'); };
        panel.appendChild(listBox); panel.appendChild(save);
        chain.onclick = ()=>{ panel.style.display = panel.style.display==='none'?'block':'none'; };
        controls.appendChild(chain); controls.appendChild(panel);
      }

      controls.appendChild(unpin); controls.appendChild(open);
      card.appendChild(head); card.appendChild(status); card.appendChild(controls);
      wrap.appendChild(card);
    });

    root.appendChild(wrap);
  }

  window.CGPinnedRuns = { render };
})();
