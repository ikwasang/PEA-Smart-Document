"""Project-budget forms using the source workbook's cell geometry and borders."""
import json,re
from datetime import datetime,timedelta,timezone
from pathlib import Path
from io import BytesIO
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parent
LAYOUT=json.loads((ROOT/'project-budget-template.json').read_text(encoding='utf-8'))
MONEY=['budget','paid','payment','remaining']

def validate(payload,master):
 if not isinstance(payload,dict):raise ValueError('ข้อมูลไม่ถูกต้อง')
 result={'documentDate':datetime.now(timezone(timedelta(hours=7))).strftime('%Y-%m-%d')}
 for key,limit in [('description',180)]:
  value=payload.get(key,'')
  if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError('กรุณากรอกรายละเอียดค่าใช้จ่ายให้ครบ')
  result[key]=value.strip()
 for key,pattern in [('operationsController',r'ผปร\.|(?:หผ|ชผ)\.ปร\.'),('financeController',r'ผบง\.|(?:หผ|ชผ)\.บง\.')]:
  try:person=json.loads(payload.get(key,''))
  except (ValueError,TypeError):raise ValueError('กรุณาเลือกผู้ควบคุมงบทั้งสองฝ่าย')
  if not isinstance(person,dict) or not any(p['name']==person.get('name') and p['position']==person.get('position') and re.search(pattern,p['position']) for p in master['people']):raise ValueError('ผู้ควบคุมงบไม่ตรงกับแผนกหรือรายชื่อหลังบ้านล่าสุด')
  result[key]=person
 rows=payload.get('rows')
 if not isinstance(rows,list) or not rows:raise ValueError('กรุณาเพิ่มรายการ')
 result['rows']=[]
 for i,row in enumerate(rows,1):
  if not isinstance(row,dict):raise ValueError('รูปแบบรายการไม่ถูกต้อง')
  file=next((f for f in master['budgetFiles'] if f['code']==row.get('workCode')),None)
  network=next((n for n in file['networks'] if n['code']==row.get('network')),None) if file else None
  if not network or row.get('activity') not in network['expenses']:raise ValueError(f'รายการ {i}: กรุณาเลือกหมายเลขงาน โครงข่าย และกิจกรรมที่สัมพันธ์กัน')
  if not network.get('approval'):raise ValueError(f'รายการ {i}: ไม่พบหนังสืออนุมัติ กรุณาอัปเดต Excel งบแฟ้มงานในหลังบ้าน')
  out={key:row[key] for key in ['workCode','network','activity']}
  out.update(workName=network.get('workName') or file['name'],approval=network['approval'])
  if network.get('conflict'):raise ValueError('ข้อมูลโครงข่ายซ้ำขัดแย้ง กรุณาตรวจ Google Sheets ต้นทาง')
  for key in MONEY:
   if key=='remaining':continue
   try:
    value=Decimal(str(network.get('activityBudgets' if key=='budget' else 'activitySpent',{}).get(row['activity'],'') if key in ['budget','paid'] else row.get(key,'')))
    if not value.is_finite() or abs(value)>Decimal('999999999999.99'):raise ValueError()
    out[key]=value.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
   except (ValueError,InvalidOperation):raise ValueError(f'รายการ {i}: กรุณากรอกจำนวนเงินให้ครบ')
  out['remaining']=out['budget']-out['paid']-out['payment']
  result['rows'].append(out)
 return result

def render(data):
 if 'ProjectThai' not in pdfmetrics.getRegisteredFontNames():
  pdfmetrics.registerFont(TTFont('ProjectThai','C:/Windows/Fonts/THSarabun.ttf'))
  pdfmetrics.registerFont(TTFont('ProjectThaiBold','C:/Windows/Fonts/THSarabun Bold.ttf'))
 output=BytesIO();c=canvas.Canvas(output,pagesize=A4);c.setTitle('ใบตัดงบแฟ้มงาน')
 xs=[0];ys=[0]
 for width in LAYOUT['widths']:xs.append(xs[-1]+width)
 heights=list(LAYOUT['heights']);heights[4]=0;heights[5]=0
 # Keep the compressed balance row readable without moving the block boundary.
 for row in [18,19,29,30]:heights[row-1]=0
 for height in heights:ys.append(ys[-1]+height)
 scale=min((A4[0]-64.4)/xs[-1],(A4[1]-108)/ys[-1]);left=50.4;top=A4[1]-54
 def rect(col,row,endcol=None,endrow=None):
  endcol=endcol or col;endrow=endrow or row
  return left+xs[col-1]*scale,top-ys[endrow]*scale,(xs[endcol]-xs[col-1])*scale,(ys[endrow]-ys[row-1])*scale
 def put(value,col,row,endcol=None,endrow=None,size=14,bold=False,align='left'):
  if value is None or value=='':return
  x,y,w,h=rect(col,row,endcol,endrow);value=str(value);font='ProjectThaiBold' if bold else 'ProjectThai';size*=scale
  while pdfmetrics.stringWidth(value,font,size)>w-4 and size>6:size-=.2
  if pdfmetrics.stringWidth(value,font,size)>w-4:raise ValueError(f'ข้อความยาวเกินช่อง ({col}, {row}): {value}')
  c.setFont(font,size);baseline=y+(h-size)/2+size*.22
  if align=='center':c.drawCentredString(x+w/2,baseline,value)
  elif align=='right':c.drawRightString(x+w-2,baseline,value)
  else:c.drawString(x+2,baseline,value)
 slots=[(0,0),(11,0),(0,11),(11,11)]
 for start in range(0,len(data['rows']),4):
  values={(1,6):'',(1,8):data['description']}
  # Remove all example inputs; unused blocks remain blank as in the template.
  for dx,dy in slots:
   for col,row in [(3,12),(3,13),(5,14),(3,15),(8,15),(5,16),(5,17),(5,18),(3,19),(7,19),(5,20),(5,21)]:values[(col+dx,row+dy)]=''
  for index,r in enumerate(data['rows'][start:start+4]):
   dx,dy=slots[index]
   for col,row,key in [(3,12,'workName'),(3,13,'approval'),(5,14,'workCode'),(3,15,'network'),(8,15,'activity'),(5,16,'budget'),(5,17,'paid'),(5,20,'payment'),(5,21,'remaining')]:values[(col+dx,row+dy)]=f'{r[key]:,.2f}' if key in MONEY else r[key]
  # Draw original cell borders, retaining dashed input rules and merged areas.
  for cell in LAYOUT['cells']:
   col,row=cell['col'],cell['row']
   if row in [18,19,29,30]:continue
   x,y,w,h=rect(col,row)
   edges={'left':(x,y,x,y+h),'right':(x+w,y,x+w,y+h),'top':(x,y+h,x+w,y+h),'bottom':(x,y,x+w,y)}
   containing=next((m for m in LAYOUT['merges'] if m[0]<=col<=m[2] and m[1]<=row<=m[3]),None)
   for side,style in cell['borders'].items():
    if containing and ((side=='left' and col!=containing[0]) or (side=='right' and col!=containing[2]) or (side=='top' and row!=containing[1]) or (side=='bottom' and row!=containing[3])):continue
    if row in [5,6] and side in ['left','right'] and col not in [1,22]:continue
    if 12<=row<=33 and side in ['left','right'] and not ((side=='left' and col in [1,12]) or (side=='right' and col in [11,22])):continue
    if style:
     c.setLineWidth(.4 if style in ['dashed','dotted','hair'] else .6);c.setDash(1,2) if style in ['dashed','dotted'] else c.setDash();c.line(*edges[side])
  c.setDash()
  for cell in LAYOUT['cells']:
   col,row=cell['col'],cell['row'];value=values.get((col,row),cell['value'])
   if row>=35 or row in [18,19,29,30]:continue
   if value is None or value=='':continue
   merged=next((m for m in LAYOUT['merges'] if m[0]==col and m[1]==row),None)
   if not merged and any(m[0]<=col<=m[2] and m[1]<=row<=m[3] for m in LAYOUT['merges']):continue
   ec,er=(merged[2],merged[3]) if merged else (col,row)
   # Labels span the adjacent empty cells in Excel.
   if not merged and (col in [1,12]) and row in list(range(12,22))+list(range(23,33)):
    ec=col+(1 if row in [12,13,15,23,24,26] else 3)
   if not merged and (col,row) in [(7,35),(19,35)]:ec=col+3
   if not merged and (col,row) in [(1,35),(13,35)]:ec=col+2
   if (col,row) in [(15,19),(15,30),(4,30)]:ec=col+2
   if (col,row)==(1,6):row=5;ec=22;er=6
   put(value,col,row,ec,er,size=cell['size'],bold=cell['bold'],align='center' if (col,row) in values else cell['align'])
  # Template logo occupies the merged header area above the title.
  x,y,w,h=rect(1,1,22,4);lw=82*scale;lh=lw*275/335
  c.drawImage(str(ROOT/'budget-logo.png'),x+(w-lw)/2,y+(h-lh)/2,lw,lh,mask='auto')
  for unused in range(len(data['rows'][start:start+4]),4):
   dx,dy=slots[unused];x,y,w,h=rect(1+dx,12+dy,11+dx,22+dy)
   c.saveState();c.setLineWidth(1);c.setDash();c.line(x+3,y+3,x+w-3,y+h-3);c.line(x+3,y+h-3,x+w-3,y+3);c.restoreState()
  d=datetime.strptime(data['documentDate'],'%Y-%m-%d')
  date_text=f'{d.day:02d}/{d.month:02d}/{d.year+543}'
  for key,col,endcol,label in [('operationsController',1,11,'ผปร.ควบคุมงบ'),('financeController',12,22,'นบช.ควบคุมงบ')]:
   person=data[key]
   put('(ลงชื่อ) ........................................ '+label,col,35,endcol,35,size=13,align='center')
   put('('+person['name']+')',col,36,endcol,36,size=14,align='center')
   put(person['position'],col,37,endcol,37,size=13,align='center')
   put('วันที่ '+date_text,col,38,endcol,38,size=13,align='center')
  c.showPage()
 c.save();return output.getvalue()
