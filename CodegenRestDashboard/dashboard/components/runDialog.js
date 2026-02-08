(function(){
  const dialogs = document.getElementById('dialogs');

  function fmtLog(l){ return `[${l.timestamp}] ${l.level||'INFO'} - ${l.message}`; }

  function open(id){
    const wrapper = document.createElement('div');
    wrapper.className = 'dialog';
    wrapper.innerHTML = `<div class="panel">
      <div class="dialog-header">
        <div>Run #${id}</div>
        <div>
          <button class="btn" id="resumeBtn">Resume</button>
          <button class="btn" id="closeBtn">Close</button>
        </div>
      </div>
      <div class="dialog-body">
        <div id="runMeta"></div>
        <div class="logs" id="logBox"></div>
      </div>
    </div>`;

    function close(){ clearInterval(t); dialogs.removeChild(wrapper); }
    wrapper.querySelector('#closeBtn').onclick = close;

    wrapper.querySelector('#resumeBtn').onclick = async ()=>{
      // Use template if selected in Templates tab, or prompt user
      const tpls = CGStore.state.templates || [];
      let prompt = '';
      if (tpls.length) {
        const names = tpls.map((t,i)=>`${i+1}) ${t.name}`).join('\n');
        const pick = promptWindow(`Pick template index (1..${tpls.length}) or leave empty to type: \n${names}`);
        if (pick) {
          const idx = Number(pick)-1; if (idx>=0 && idx<tpls.length) prompt = tpls[idx].text;
        }
      }
      if (!prompt) prompt = promptWindow('Follow-up prompt:');
      if (!prompt) return;
      await CGApi.resumeAgentRun({ agent_run_id: id, prompt });
      CGToast.toast('Resume requested');
    };

    dialogs.appendChild(wrapper);

    // Poll run + logs for streaming effect
    let skip = 0;
    async function refresh(){
      try {
        const meta = await CGApi.getAgentRun(id);
        wrapper.querySelector('#runMeta').textContent = `Status: ${meta.status}`;
        const logs = await CGApi.getAgentLogs(id, { skip, limit: 100 });
        const box = wrapper.querySelector('#logBox');
        (logs.logs || []).forEach(l=>{
          const line = document.createElement('div');
          line.textContent = fmtLog(l);
          box.appendChild(line);
        });
        skip += (logs.logs || []).length;
        if (meta.status === 'COMPLETED' || meta.status === 'FAILED' || meta.status === 'CANCELLED') {
          clearInterval(t);
        }
      } catch (e) { console.error(e); }
    }
    refresh();
    const t = setInterval(refresh, 2000);
  }

  function promptWindow(msg){
    // Avoid blocking native prompt for better UX, but spec asks no dependencies; use window.prompt
    return window.prompt(msg || '');
  }

  window.CGRunDialog = { open };
})();

