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
      const status = document.createElement('div'); status.textContent = `Status: ${run.status}`;
      const controls = document.createElement('div');
      const unpin = document.createElement('button'); unpin.className='btn'; unpin.textContent='Unpin'; unpin.onclick=()=> CGStore.unpin(id);
      const open = document.createElement('button'); open.className='btn'; open.textContent='Open'; open.onclick=()=> CGRunDialog.open(id);
      controls.appendChild(unpin); controls.appendChild(open);
      card.appendChild(head); card.appendChild(status); card.appendChild(controls);
      wrap.appendChild(card);
    });

    root.appendChild(wrap);
  }

  window.CGPinnedRuns = { render };
})();

