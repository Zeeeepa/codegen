(function(){
  // Monitors watched runs; when a run moves to COMPLETED, automatically send a resume request
  // using the first template (if any). You can extend to map templates per run later.
  let lastStatuses = new Map();

  async function check(){
    const watched = Object.entries(CGStore.state.watched).filter(([,v])=>v).map(([k])=>Number(k));
    for (const id of watched){
      try {
        const cur = await CGApi.getAgentRun(id);
        const prev = lastStatuses.get(id);
        if (prev && prev!=='COMPLETED' && cur.status==='COMPLETED'){
          const tpls = CGStore.state.templates||[];
          if (tpls.length){
            const text = tpls[0].text;
            await CGApi.resumeAgentRun({ agent_run_id: id, prompt: text });
            CGToast.toast(`Auto-follow-up sent for #${id}`);
          }
        }
        lastStatuses.set(id, cur.status);
      } catch (e){ /* ignore */ }
    }
  }

  function start(){ setInterval(check, 4000); }
  window.CGFollowUp = { start };
})();

