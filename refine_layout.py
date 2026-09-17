from pathlib import Path
p=Path('prototype/index.html');s=p.read_text(encoding='utf-8');start=s.index('<aside>');end=s.index('<section class="preview-card">',start)
s=s[:start]+'''<section class="export-actions"><div hidden><span id="count"></span><span id="subtotal"></span><span id="vat"></span><span id="grand"></span></div><p id="limit"></p><p id="message" role="status" aria-live="polite"></p><button id="preview" class="primary">สร้างตัวอย่าง PDF</button><a id="download" class="download" hidden download="เอกสารจัดซื้อ-ทดลอง.pdf">ดาวน์โหลด PDF</a></section>'''+s[end:];p.write_text(s,encoding='utf-8')
p=Path('prototype/style.css');s=p.read_text(encoding='utf-8')+'''\nmain{display:block;max-width:1140px}.export-actions{margin:16px auto 28px;text-align:center}.export-actions .primary,.export-actions .download{max-width:340px;margin:10px auto}.preview-card{padding:20px;background:#eeedf2}#pdf{max-width:720px;margin:20px auto}.card{padding:26px}.grid{gap:18px 24px}\n''';p.write_text(s,encoding='utf-8')
p=Path('prototype/app.js');s=p.read_text(encoding='utf-8');a=s.index("b[k]=input.value;if(k==='budgetFile')");z=s.index('invalidate()',a)
s=s[:a]+"linkBudget(b,k,input.value);for(const key of ['budgetFile','network','expense']){const linked=card.querySelector('[data-options='+key+'-options]');if(linked&&linked!==input)linked.value=b[key]||'';}"+s[z:]
s=s.replace('function optionsFor(input){', '''function linkBudget(b,key,value){b[key]=value;if(!['budgetFile','network'].includes(key))return;const entry=master.budgetFiles.find(f=>key==='budgetFile'?f.code===value:f.network===value);if(entry){b.budgetFile=entry.code;b.network=entry.network;if(!entry.expenses.includes(b.expense))b.expense='';}else if(key==='budgetFile'){b.network='';}else{b.budgetFile='';}}
function optionsFor(input){''')
s=s.replace("if(id==='expense-options'){", "if(id==='network-options'){const file=input.closest('fieldset')?.querySelector('[data-options=budgetFile-options]')?.value;if(file)list=master.budgetFiles.filter(f=>f.code===file).map(f=>({value:f.network,label:f.network+' — '+f.code}));}if(id==='expense-options'){")
p.write_text(s,encoding='utf-8')
p=Path('template-review/refine_pdf.py');s=p.read_text(encoding='utf-8').replace("c.showPage();page(0);text(85,778,'เอกสารจัดซื้อ (ต่อ)',18,True)","c.showPage();page(0)")
a=s.index('def approval(');z=s.index("page(1,True)",a)
s=s[:a]+'''def fitted_center(x,y,t,size=15,width=200):
 while pdfmetrics.stringWidth(mapped(t) if data else t,'PSK',size)>width and size>10:size-=.5
 centered(x,y,t,size)

def signature(center,y,name,job,width=200):
 fitted_center(center,y,'ลงชื่อ ................................................',15,width)
 fitted_center(center,y-21,'('+name+')',15,width)
 fitted_center(center,y-40,job,14,width)

def approval(x,y,w=216,h=157):
 c.rect(x,y-h,w,h);centered(x+w/2,y-24,'อนุมัติตามเสนอ',16,True)
 signature(x+w/2,y-76,'ผู้อนุมัติตัวอย่าง',position('approver'),w-20)
 centered(x+w/2,y-140,'วันที่ ...................................',14)

def officer(x,y):
 centered(x+94,y+21,'เจ้าหน้าที่จัดทำเอกสาร',15)
 signature(x+94,y,'เจ้าหน้าที่ตัวอย่าง',position('officer'),188)
 centered(x+94,y-64,'วันที่ ...................................',14)

''' +s[z:]
a=s.index('cy=710');z=s.index('c.showPage()',a)
s=s[:a]+'''cy=708
for i,(name,role) in enumerate(committee):
 text(149,cy,str(i+1)+'.',15)
 text(173,cy,name,15)
 text(173,cy-20,positions.get(name,'ตำแหน่ง ........................................'),14)
 text(440,cy,role,14)
 cy-=44
y=indented('จึงเรียนมาเพื่อโปรดพิจารณา หากเห็นชอบขอได้โปรดอนุมัติให้ดำเนินการตามรายละเอียดในรายงานขอซื้อดังกล่าวข้างต้น',cy-12,size=16,leading=22)
approval(88,y-15,w=216,h=157);officer(333,y-48)
para(note,y-195,size=11,leading=15)
''' +s[z:]
s=s.replace('page(4);c.rect(50,472,297,291)','page(4);c.rect(50,388,297,375)')
a=s.index("for s in ['ลงชื่อ");z=s.index('officer(380,738)',a)
s=s[:a]+'''for name,role in committee:
 fitted_center(198,y-3,'ลงชื่อ .................................... '+role,13,277)
 fitted_center(198,y-20,'('+name+')',14,277)
 fitted_center(198,y-36,positions.get(name,'ตำแหน่ง ........................................'),13,277)
 y-=48
y=para('ข้าพเจ้าได้รับมอบวัสดุและอุปกรณ์ทั้ง 3 รายการดังกล่าวเพื่อนำไปใช้งานแล้วตั้งแต่วันที่ .......................',y-3,x=57,w=282,size=14,leading=18)
signature(198,y-14,'ผู้รับของตัวอย่าง',position('receiver'),277)
centered(198,y-75,'วันที่ ...............................',14)
''' +s[z:]
s=s.replace('para(note,452','para(note,365').replace('c.rect(85,160,440,190);centered(305,329','c.rect(85,120,440,190);centered(305,289').replace('175+(140-h)/2','135+(140-h)/2')
p.write_text(s,encoding='utf-8')
