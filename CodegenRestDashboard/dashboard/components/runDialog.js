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
        <div style="margin:8px 0; display:flex; gap:8px; align-items:center;">
          <label for="tplSel">Template:</label>
          <select id="tplSel"></select>
          <button class="btn" id="applyTplBtn">Set Default</button>
        </div>
        <div class="logs" id="logBox"></div>
      </div>
    </div>`;

    function close(){ clearInterval(t); dialogs.removeChild(wrapper); }
    wrapper.querySelector('#closeBtn').onclick = close;

    // Populate template selector and persist default single-template selection
    const sel = wrapper.querySelector('#tplSel');
    function refreshTemplateSelector(){
      const tpls = CGStore.state.templates || [];
      sel.innerHTML = '';
      const noneOpt = document.createElement('option'); noneOpt.value = ''; noneOpt.textContent = 'None'; sel.appendChild(noneOpt);
      tpls.forEach((t,i)=>{ const o=document.createElement('option'); o.value=String(i); o.textContent=t.name||`Template ${i+1}`; sel.appendChild(o); });
      const existing = (CGStore.getChain(id)||[]);
      if (existing.length>0) sel.value = String(existing[0]);
    }
    refreshTemplateSelector();

    wrapper.querySelector('#applyTplBtn').onclick = ()=>{
      const v = sel.value; const arr = v===''? [] : [Number(v)];
      CGStore.setChain(id, arr);
      CGToast.toast('Default template updated');
    };

    wrapper.querySelector('#resumeBtn').onclick = async ()=>{
      const tpls = CGStore.state.templates || [];
      const chain = CGStore.getChain(id) || [];
      let promptText = '';
      if (chain.length>0 && tpls[chain[0]]) {
        promptText = tpls[chain[0]].text || '';
      } else {
        const pick = promptWindow('Follow-up prompt (leave empty to cancel):');
        if (!pick) return;
        promptText = pick;
      }
      // Resolve template variables using current run meta
      let meta = {};
      try { meta = await CGApi.getAgentRun(id); } catch(_){}
      const vars = {
        run_id: id,
        status: meta.status,
        title: meta.title,
        summary: meta.summary,
        result: meta.result,
        created_at: meta.created_at,
        now: new Date().toISOString(),
        agent_run: meta,
      };
      const finalPrompt = (window.CGTemplate && CGTemplate.renderTemplate)
        ? CGTemplate.renderTemplate(promptText, vars)
        : promptText;

      await CGApi.resumeAgentRun({ agent_run_id: id, prompt: finalPrompt });
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

