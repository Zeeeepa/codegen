(function(){
  function render(){
    const wrap = document.createElement('div');
    const runsBtn = document.createElement('button'); runsBtn.className='btn'; runsBtn.textContent='Runs';
    const tplBtn = document.createElement('button'); tplBtn.className='btn'; tplBtn.textContent='Templates';

    function sel(which){
      window.CGTabControl.active = which;
      document.getElementById('controls').style.display = which==='runs'?'block':'none';
      document.getElementById('runs').style.display = which==='runs'?'block':'none';
      document.getElementById('pinned').style.display = which==='runs'?'block':'none';
      const main = document.getElementById('app-main');
      const existing = document.getElementById('tplView');
      if (which==='templates') {
        if (!existing) {
          const v = document.createElement('div'); v.id='tplView'; v.appendChild(CGTemplates.render()); main.appendChild(v);
        }
      } else {
        if (existing) existing.remove();
      }
    }

    runsBtn.onclick = ()=> sel('runs');
    tplBtn.onclick = ()=> sel('templates');

    wrap.appendChild(runsBtn); wrap.appendChild(tplBtn);
    return wrap;
  }
  window.CGTabControl = { render, active: 'runs' };
})();

