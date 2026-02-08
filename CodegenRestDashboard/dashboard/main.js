(function(){
  // Inject CG_ENV for browser (org id only; token stays server-side!)
  window.CG_ENV = { ORG_ID: (new URLSearchParams(location.search).get('org') || '323') };

  // Render reactive UI
  CGStore.subscribe((state)=>{
    CGHeader.render(state);
    CGPinnedRuns.render(state);
    if (window.CGTabControl.active==='runs') CGRunList.render(state);
  });

  // Start background watchers (auto-refresh; no manual refresh button)
  CGWatcher.start();
  CGFollowUp.start();
})();

