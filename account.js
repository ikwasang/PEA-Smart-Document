(async()=>{
 const status=document.querySelector('#account-status');
 const message=s=>{if(status)status.textContent=s;};
 async function api(path,data){const r=await fetch('/api/access/'+path,data?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}:{});const result=await r.json();if(!r.ok)throw Error(result.error||'เชื่อมต่อไม่สำเร็จ');return result;}
 let me;
 const profile=document.querySelector('#profile-form');
 function editName(user){document.querySelector('#google-login').hidden=true;profile.hidden=false;document.querySelector('#profile-name').value=user.name||'';message('เข้าสู่ระบบแล้ว กรุณาตั้งชื่อที่ต้องการใช้');}
 if(profile){
  profile.onsubmit=async e=>{e.preventDefault();try{await api('name',{name:document.querySelector('#profile-name').value});location.href='/';}catch(e){message(e.message);}};
  try{const c=await api('config');if(!c.configured){message('ยังไม่ได้เชื่อม Google Login กรุณาให้ admin ตั้งค่าบัญชีและที่อยู่เว็บก่อนเปิดใช้งานหลายคน');return;}
   try{me=await api('me');if(me.user){editName(me.user);return;}}catch{}
   const script=document.createElement('script');script.src='https://accounts.google.com/gsi/client';script.async=true;script.onerror=()=>message('เชื่อมต่อ Google ไม่ได้ กรุณาลองใหม่');script.onload=()=>{google.accounts.id.initialize({client_id:c.clientId,callback:async response=>{try{const result=await api('login',{credential:response.credential});if(result.user.name)location.href='/';else editName(result.user);}catch(e){message(e.message);}}});google.accounts.id.renderButton(document.querySelector('#google-login'),{theme:'outline',size:'large'});message('ใช้บัญชี Gmail ที่ได้รับสิทธิ์จาก admin');};document.head.append(script);
  }catch(e){message(e.message);}return;
 }
 try{me=await api('me');if(!me.configured)return;}catch{return;}
 const bar=document.createElement('div');bar.className='account-bar';const name=document.createElement('span');name.textContent=me.user.name+(me.user.role==='admin'?' · admin':'');const history=document.createElement('a');history.href='/history';history.textContent='ประวัติการใช้งาน';const rename=document.createElement('a');rename.href='/login';rename.textContent='เปลี่ยนชื่อ';const logout=document.createElement('button');logout.type='button';logout.textContent='ออกจากระบบ';logout.onclick=async()=>{await api('logout',{});location.href='/login';};bar.append(name,history,rename,logout);(document.querySelector('header')||document.body).append(bar);
 if(me.user.role!=='admin')document.querySelectorAll('a[href="/admin"]').forEach(a=>a.remove());
 if(location.pathname==='/admin'&&me.user.role==='admin'){
  const panel=document.createElement('section');panel.className='card';panel.innerHTML='<h2>สิทธิ์ผู้ใช้งาน</h2><p>เพิ่ม Gmail ผู้ใช้ได้สูงสุด 19 คน บัญชีที่นำออกจะเข้าใช้งานต่อไม่ได้</p><form><label>Gmail ผู้ใช้ (หนึ่งบัญชีต่อบรรทัด)<textarea rows="8" style="width:100%"></textarea></label><button>บันทึกสิทธิ์ผู้ใช้</button><p role="status"></p></form>';document.querySelector('main').prepend(panel);
  const input=panel.querySelector('textarea'),info=panel.querySelector('[role=status]');try{const r=await fetch('/api/admin/access-users');const data=await r.json();if(!r.ok)throw Error(data.error);input.value=data.users.join('\n');}catch(e){info.textContent=e.message;}
  panel.querySelector('form').onsubmit=async e=>{e.preventDefault();try{const r=await fetch('/api/admin/access-users',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({users:input.value.split(/\s+/).filter(Boolean)})});const result=await r.json();if(!r.ok)throw Error(result.error);info.textContent='บันทึกสิทธิ์แล้ว';}catch(e){info.textContent=e.message;}};
 }
 const events=document.querySelector('#history-rows');
 if(events){document.querySelector('#history-scope').textContent=me.user.role==='admin'?'ประวัติของผู้ใช้งานทุกคน':'ประวัติการใช้งานของคุณ';const refresh=async()=>{try{const result=await api('history');events.replaceChildren(...result.events.map(e=>{const row=document.createElement('tr');for(const value of [new Date(e.at*1000).toLocaleString('th-TH',{timeZone:'Asia/Bangkok'}),e.name||'ยังไม่ตั้งชื่อ',e.action]){const td=document.createElement('td');td.textContent=value;row.append(td);}return row;}));message(result.events.length?'':'ยังไม่มีประวัติ');}catch(e){message(e.message);}};document.querySelector('#history-refresh').onclick=refresh;await refresh();}
 const event=kind=>api('event',{event:kind}).catch(()=>{});
 if(location.pathname==='/budget')event('budget');
 if(location.pathname==='/project-budget')event('project-budget');
 document.addEventListener('click',e=>{const b=e.target.closest('[data-kind],#document-print,#budget-print,#project-print,#download,#budget-download,#project-download');if(!b||b.disabled||b.hidden)return;if(b.dataset.kind)event(b.dataset.kind);else event(b.id.includes('print')?'print':'download');});
})();
