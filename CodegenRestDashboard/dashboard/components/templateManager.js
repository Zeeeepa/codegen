(function(){
  function render(){
    const c = document.createElement('div');
    c.style.padding = '10px 0';

    const list = document.createElement('div');
    (CGStore.state.templates||[]).forEach((t, i)=>{
      const row = document.createElement('div'); row.className='run-row';
      const name = document.createElement('div'); name.textContent = t.name; name.style.flex='1';
      const edit = document.createElement('button'); edit.className='btn'; edit.textContent='Edit'; edit.onclick=()=> editTpl(i);
      const del = document.createElement('button'); del.className='btn'; del.textContent='Delete'; del.onclick=()=> CGStore.deleteTemplate(i);
      row.appendChild(name); row.appendChild(edit); row.appendChild(del); list.appendChild(row);
    });

    const add = document.createElement('button'); add.className='btn primary'; add.textContent='Add Template'; add.onclick=()=> addTpl();

    c.appendChild(list); c.appendChild(add);
    return c;
  }

  function addTpl(){
    const name = window.prompt('Template name:'); if (!name) return;
    const text = window.prompt('Template text:'); if (text==null) return;
    CGStore.addTemplate({ name, text });
  }
  function editTpl(idx){
    const cur = CGStore.state.templates[idx];
    const name = window.prompt('Template name:', cur.name); if (!name) return;
    const text = window.prompt('Template text:', cur.text); if (text==null) return;
    CGStore.updateTemplate(idx, { name, text });
  }

  window.CGTemplates = { render };
})();

