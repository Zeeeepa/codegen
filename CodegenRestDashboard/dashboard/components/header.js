(function(){
  const header = document.getElementById('app-header');

  function render(state){
    header.innerHTML = '';

    // Left: App title
    const title = document.createElement('div');
    title.textContent = 'Codegen REST Dashboard';
    header.appendChild(title);

    // Active count with hover list
    const activeWrap = document.createElement('div');
    activeWrap.className = 'header-item';
    const label = document.createElement('span');
    label.textContent = 'Active Runs';
    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = String(state.activeCount);
    activeWrap.appendChild(label);
    activeWrap.appendChild(badge);

    const hover = document.createElement('div');
    hover.className = 'hover-card';
    state.runs.filter(r=>r.status==='ACTIVE'||r.status==='PENDING').slice(0,10).forEach((r)=>{
      const row = document.createElement('div');
      row.className = 'run-row';
      row.textContent = `#${r.id} ${r.title || ''}`;
      row.onclick = ()=> window.CGRunDialog.open(r.id);
      hover.appendChild(row);
    });
    if (!hover.childElementCount) { const e=document.createElement('div'); e.className='run-row'; e.textContent='No active runs'; hover.appendChild(e); }
    activeWrap.appendChild(hover);

    header.appendChild(activeWrap);

    // Right: Tabs (Runs / Templates)
    const tabs = window.CGTabControl.render();
    header.appendChild(tabs);
  }

  window.CGHeader = { render };
})();

