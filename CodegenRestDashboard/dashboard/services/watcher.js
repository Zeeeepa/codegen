(function(){
  let interval = null;

  async function tick(){
    try {
      const data = await CGApi.listAgentRuns({ page: 1, limit: 50 });
      const runs = (data.data||data.runs||[]);
      CGStore.setRuns(runs);

      // Watch pinned/watched runs for status transitions (poll individually)
      const watchedIds = Object.entries(CGStore.state.watched)
        .filter(([,v])=>v)
        .map(([k])=>Number(k));
      const ids = new Set([ ...watchedIds, ...CGStore.state.pinned ]);
      for (const id of ids){
        try {
          const r = await CGApi.getAgentRun(id);
          const old = CGStore.state.runs.find(x=>x.id===id);
          if (old && old.status!==r.status && (r.status==='COMPLETED'||r.status==='FAILED'||r.status==='CANCELLED')){
            CGToast.toast(`Run #${id} ${r.status}`);
            if ('Notification' in window && Notification.permission==='granted'){
              try { new Notification(`Run #${id} ${r.status}`); } catch(_){}
            }
          }
        } catch (e){ /* ignore individual errors */ }
      }

      // Consume webhook events once per tick (outside per-run loop)
      try {
        const ev = await fetch('/api/events').then(r=>r.json()).catch(()=>({events:[]}));
        (ev.events||[]).forEach(async (e)=>{
          const id = e?.body?.agent_run_id || e?.body?.id;
          if (!id) return;
          try {
            const r = await CGApi.getAgentRun(id);
            const old = CGStore.state.runs.find(x=>x.id===id);
            if (old && old.status!==r.status){
              CGToast.toast(`Run #${id} ${r.status}`);
              if ('Notification' in window && Notification.permission==='granted'){
                try { new Notification(`Run #${id} ${r.status}`); } catch(_){ }
              }
            }
          } catch(_){ /* ignore */ }
        });
      } catch(_){ /* ignore webhook errors */ }

    } catch (e) { console.error('watcher error', e); }
  }

  function start(){ if (interval) clearInterval(interval); tick(); interval = setInterval(tick, 3000); }
  window.CGWatcher = { start };
})();

