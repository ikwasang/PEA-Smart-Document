from pathlib import Path
p=Path('template-review/refine_pdf.py');s=p.read_text(encoding='utf-8')
s=s.replace('def page(n,head=False):','physical_page=0\ndef page(n,head=False):\n global physical_page\n physical_page+=1').replace("if n in (2,4):centered(306,814,str(n),14)","if not head:centered(306,814,str(physical_page),14)")
start=s.index('def table(y):');end=s.index('\ndef approval',start)
s=s[:start]+'''def continuation():
 c.showPage();page(0);text(85,778,'เอกสารจัดซื้อ (ต่อ)',18,True)
 return 746

def para(t,y,x=L,w=R-L,size=16,leading=19):
 for line in wrap(t,w,size):
  if y<65:y=continuation()
  text(x,y,line,size);y-=leading
 return y

def table(y):
 sty=ParagraphStyle('ref',fontName='PSK',fontSize=12,leading=14,wordWrap='CJK',alignment=1)
 P=lambda t:Paragraph(t,sty)
 headers=[[P('ลำดับ<br/>ที่'),P('รายการพิจารณา'),P('จำนวน (1)'),P('ราคาต่อหน่วย<br/>(ไม่รวม VAT)<br/>(บาท)<br/>(2)'),P('ราคารวม'),'',''],['','','','',P('ราคาไม่รวม VAT<br/>(บาท)<br/>(3) = (1) × (2)'),P('VAT (บาท)<br/>(4)'),P('รวมทั้งสิ้น<br/>(บาท)<br/>(5) = (3) + (4)')]]
 body=[]
 for i,(name,q,p,v) in enumerate(items,1):
  label=P(escape(name));height=max(25,label.wrap(150,10000)[1]+8)
  body.append(([str(i),label,str(q),money(p),money((q*p).quantize(Decimal('.01'))),money(v),money((q*p).quantize(Decimal('.01'))+v)],height))
 offset=0
 while offset<len(body):
  rows=[r[:] for r in headers];heights=[20,65];start=offset
  while offset<len(body) and sum(heights)+body[offset][1]+39<=y-260:
   row,h=body[offset];rows.append(row);heights.append(h);offset+=1
  if offset==start:y=continuation();continue
  last=offset==len(body)
  if last:
   rows.extend([['รวม','','','',money(subtotal),money(vat),money(total)],[words,'','','','','','']]);heights.extend([19,20])
  t=Table(rows,colWidths=[25,156,50,59,61,48,74],rowHeights=heights)
  cmds=[('FONTNAME',(0,0),(-1,-1),'PSK'),('FONTSIZE',(0,0),(-1,-1),12),('GRID',(0,0),(-1,-1),.6,colors.black),('SPAN',(4,0),(6,0)),('ALIGN',(0,2),(0,-1),'CENTER'),('ALIGN',(2,2),(2,-1),'CENTER'),('ALIGN',(3,2),(-1,-1),'RIGHT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]
  for i in range(4):cmds.append(('SPAN',(i,0),(i,1)))
  if last:cmds.extend([('SPAN',(0,-2),(3,-2)),('SPAN',(0,-1),(6,-1)),('ALIGN',(0,-2),(0,-1),'RIGHT')])
  t.setStyle(TableStyle(cmds));t.wrap(473,10000);bottom=y-sum(heights);t.drawOn(c,85,bottom)
  if not last:y=continuation()
 return bottom
''' +s[end:]
start=s.index("if data and len(data.get('budgets',[]))>1:");end=s.index("heading('4.",start)
s=s[:start]+'''if data and data.get('budgets'):
 y=para('3. วงเงินที่จะจัดซื้อ '+summary,bottom-22,size=15,leading=19)
 for n,b in enumerate(data['budgets'],1):
  detail=f"งบ {n}: "+b['type']+' ศูนย์ต้นทุน '+b['costCenter']
  if b['type']=='งบแฟ้มงาน':detail+=' แฟ้มงาน '+b['budgetFile']+' โครงข่าย '+b['network']+' '+b['expense']
  detail+=' รหัสบัญชี '+b['account']
  if len(data['budgets'])>1:detail+=' (พัสดุลำดับ '+', '.join(str(i+1) for i in b['itemIndices'])+')'
  y=para(detail,y,size=14,leading=18)
else:
 y=para('3. วงเงินที่จะจัดซื้อ '+summary,bottom-22,size=15,leading=19)
if y<230:y=continuation()
''' +s[end:]
start=s.index("if data and len(data.get('budgets',[]))>1:",s.index("photos=data"));end=s.index('c.save()',start);s=s[:start]+s[end:]
# Fill known personnel positions from the same imported workbook.
s=s.replace("def approval(x,y,w=216,h=157):", "positions={p['name']:p['position'] for p in json.loads(Path('prototype/master-data.json').read_text(encoding='utf-8'))['people']}\ndef position(role):return positions.get(data.get(role,''),'........................................') if data else '........................................'\n\ndef approval(x,y,w=216,h=157):")
s=s.replace("centered(x+w/2,y-124,'ตำแหน่งตามข้อมูลที่เลือก',15)","centered(x+w/2,y-124,position('approver'),15)").replace("centered(x+94,y-45,'ตำแหน่งตามข้อมูลที่เลือก',15)","centered(x+94,y-45,position('officer'),15)").replace("centered(197,y-55,'ตำแหน่งตามข้อมูลที่เลือก',14)","centered(197,y-55,position('receiver'),14)")
p.write_text(s,encoding='utf-8')
