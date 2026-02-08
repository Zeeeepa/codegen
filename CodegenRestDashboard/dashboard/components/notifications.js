(function(){
  const root = document.getElementById('toasts');
  function toast(msg, timeout=3000){
    const el = document.createElement('div');
    el.className = 'toast';
    el.textContent = msg;
    root.appendChild(el);
    setTimeout(()=>{ root.removeChild(el); }, timeout);
  }
  window.CGToast = { toast };
})();

