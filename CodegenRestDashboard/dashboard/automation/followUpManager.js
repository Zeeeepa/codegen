(function(){
  // Monitors watched runs; when a run moves to COMPLETED, automatically send a resume request
  // using the run's configured chain of templates (if any), one-by-one per completion cycle.
  let lastStatuses = new Map();

  async function check(){
    const watched = Object.entries(CGStore.state.watched).filter(([,v])=>v).map(([k])=>Number(k));
    for (const id of watched){
      try {
        const cur = await CGApi.getAgentRun(id);
        const prev = lastStatuses.get(id);
        if (prev && prev!=='COMPLETED' && cur.status==='COMPLETED'){
          const chain = CGStore.getChain(id) || [];
          const prog = CGStore.getChainProgress(id) || 0;
          if (prog < chain.length){
            const tplIdx = chain[prog];
            const tpls = CGStore.state.templates||[];
            if (tpls[tplIdx]){
              const text = tpls[tplIdx].text || '';
              if (text){
                await CGApi.resumeAgentRun({ agent_run_id: id, prompt: text });
                CGStore.setChainProgress(id, prog+1);
                CGToast.toast(`Auto-follow-up ${prog+1}/${chain.length} sent for #${id}`);
              }
            }
          }
        }
        lastStatuses.set(id, cur.status);
      } catch (e){ /* ignore */ }
    }
  }

  function start(){ setInterval(check, 4000); }
  window.CGFollowUp = { start };
})();
