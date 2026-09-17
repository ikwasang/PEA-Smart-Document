from pathlib import Path
p=Path('prototype/server.py');s=p.read_text(encoding='utf-8').replace('import io','import threading\nimport io',1).replace("WORK=ROOT.parent","WORK=ROOT.parent\nDRAFT_LOCK=threading.Lock()\nDRAFT=ROOT/'local-data'/'current-draft.json'")
s=s.replace("  files={'/':", "  if self.path=='/api/draft':\n   with DRAFT_LOCK:\n    body=DRAFT.read_bytes() if DRAFT.exists() else b'null'\n   self.send(200,body);return\n  files={'/':")
s=s.replace("  if self.path!='/api/pdf':", "  if self.path not in ['/api/pdf','/api/draft']:")
s=s.replace("   d=json.loads(self.rfile.read(n));sub,vat=validate(d)", """   d=json.loads(self.rfile.read(n))
   if self.path=='/api/draft':
    if not isinstance(d,dict) or d.get('schema')!=1 or not isinstance(d.get('fields'),dict) or not isinstance(d.get('items'),list) or not 1<=len(d['items'])<=3 or not isinstance(d.get('budgets'),list) or not 1<=len(d['budgets'])<=3 or not isinstance(d.get('photos'),list) or len(d['photos'])>3:raise ValueError('รูปแบบร่างไม่ถูกต้อง')
    with DRAFT_LOCK:
     DRAFT.parent.mkdir(exist_ok=True)
     pending=DRAFT.with_suffix('.tmp');pending.write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8');pending.replace(DRAFT)
    self.send(200,{'saved':True});return
   sub,vat=validate(d)""")
p.write_text(s,encoding='utf-8')
p=Path('prototype/index.html');s=p.read_text(encoding='utf-8').replace('ข้อมูลตัวอย่างสำหรับทดสอบ · ยังไม่บันทึกร่าง ไม่เชื่อมรายชื่อจริง และไม่ใช่ระบบออนไลน์','ทดลองใช้บนเครื่องนี้ · บันทึกร่างล่าสุด 1 ชุดอัตโนมัติ · รายชื่อเริ่มต้นยังเป็นตัวอย่าง กรุณาตรวจข้อมูลก่อนพิมพ์').replace('ข้อมูลหายเมื่อปิดหรือโหลดหน้าใหม่','บันทึกร่างไว้บนเครื่องนี้ · ใช้ทีละหน้าต่าง').replace('<form id="form">','<p id="draft-status" role="status">กำลังเปิดร่างล่าสุด…</p><form id="form">').replace('id="reset" class="quiet"','id="reset" class="quiet" disabled');p.write_text(s,encoding='utf-8')
p=Path('prototype/app.js');s=p.read_text(encoding='utf-8').replace('let photos=[]', 'let draftReady=false,draftDirty=false,draftSaving=false,draftTimer=null;\nlet photos=[]').replace("function invalidate(){version++;", "function invalidate(){scheduleDraft();version++;").replace("$('#reset').onclick=reset;", "$('#reset').onclick=()=>{if(confirm('แทนที่ร่างปัจจุบันด้วยข้อมูลตัวอย่าง? กรุณาดาวน์โหลด PDF ที่ต้องการเก็บก่อน'))reset();};").replace("finally{photoBusy=false;renderPhotos();}","finally{photoBusy=false;renderPhotos();scheduleDraft();}")
s=s.rsplit('reset();',1)[0]+'''
function scheduleDraft(){if(!draftReady)return;draftDirty=true;$('#draft-status').textContent='มีการแก้ไข · กำลังบันทึก…';clearTimeout(draftTimer);draftTimer=setTimeout(saveDraft,400);}
async function saveDraft(){if(!draftReady||draftSaving||photoBusy||!draftDirty)return;draftSaving=true;draftDirty=false;const snapshot={schema:1,fields:Object.fromEntries(new FormData(form)),items,budgets,photos,memberCount:$('#member-count').value,savedAt:new Date().toISOString()};try{const r=await fetch('/api/draft',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(snapshot)});if(!r.ok)throw Error();if(!draftDirty)$('#draft-status').textContent='บันทึกร่างบนเครื่องแล้ว · '+new Date().toLocaleTimeString('th-TH');}catch(e){draftDirty=true;$('#draft-status').textContent='บันทึกไม่สำเร็จ กรุณาเปิดโปรแกรมไว้แล้วลองแก้ไขอีกครั้ง';}finally{draftSaving=false;if(draftDirty)draftTimer=setTimeout(saveDraft,2500);}}
async function openDraft(){form.inert=true;$('#preview').disabled=true;reset();try{const r=await fetch('/api/draft');if(!r.ok)throw Error();const d=await r.json();if(d){for(const [k,v]of Object.entries(d.fields))if(form.elements[k])form.elements[k].value=v;items=d.items;budgets=d.budgets;photos=d.photos;$('#member-count').value=d.memberCount;setMembers();renderPhotos();renderBudgets();render();$('#draft-status').textContent='เปิดร่างล่าสุดที่บันทึกไว้แล้ว';}else $('#draft-status').textContent='พร้อมทดลอง · แก้ข้อมูลแล้วจะบันทึกอัตโนมัติ';draftReady=true;$('#reset').disabled=false;}catch(e){$('#draft-status').textContent='เปิดร่างไม่สำเร็จ กรุณาโหลดหน้าใหม่ก่อนเริ่มกรอก';}finally{form.inert=!draftReady;totals();$('#preview').disabled=!draftReady;}}
window.addEventListener('beforeunload',e=>{if(draftDirty||draftSaving||photoBusy){e.preventDefault();e.returnValue='';}});
openDraft();
''';p.write_text(s,encoding='utf-8')
