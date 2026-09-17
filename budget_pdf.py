"""Operating-budget slips, six slots per A4 page with inline photographs."""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
import base64,json
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

DEPARTMENTS=['ผปร.','ผบค.','ผบง.','ผกป.','กบห.']
AMOUNTS=[('approved','งบประมาณอนุมัติ'),('paid','จ่ายไปแล้ว'),('balanceBefore','คงเหลือ'),('payment','จ่ายครั้งนี้'),('balanceAfter','คงเหลือ')]
MONTHS=['มกราคม','กุมภาพันธ์','มีนาคม','เมษายน','พฤษภาคม','มิถุนายน','กรกฎาคม','สิงหาคม','กันยายน','ตุลาคม','พฤศจิกายน','ธันวาคม']

def validate(payload,master):
 rows=payload.get('rows') if isinstance(payload,dict) else None
 if not isinstance(rows,list) or not rows:raise ValueError('กรุณาเพิ่มรายการอย่างน้อย 1 รายการ')
 accounts={str(a['code']):a['name'] for a in master['accounts']}
 result=[]
 for i,r in enumerate(rows,1):
  if not isinstance(r,dict):raise ValueError('รูปแบบรายการไม่ถูกต้อง')
  out={}
  for key,limit in [('description',100),('orderNumber',30)]:
   value=r.get(key,'')
   if not isinstance(value,str) or (key=='description' and not value.strip()) or len(value)>limit:raise ValueError(f'รายการ {i}: กรุณาตรวจรายละเอียดหรือความยาวหมายเลขใบสั่ง')
   out[key]=value.strip()
  if r.get('department') not in DEPARTMENTS:raise ValueError(f'รายการ {i}: กรุณาเลือกแผนก')
  out['department']=r['department']
  code=r.get('accountCode')
  if code not in accounts:raise ValueError(f'รายการ {i}: กรุณาเลือกรหัสบัญชีจากข้อมูลล่าสุด')
  out.update(accountCode=code,accountName=accounts[code])
  try:person=json.loads(r.get('controller',''))
  except (ValueError,TypeError):raise ValueError(f'รายการ {i}: กรุณาเลือกผู้ควบคุมงบ')
  if not isinstance(person,dict) or not any(p['name']==person.get('name') and p['position']==person.get('position') for p in master['people']):raise ValueError(f'รายการ {i}: กรุณาเลือกผู้ควบคุมงบจากรายชื่อหลังบ้านล่าสุด')
  out['controller']=person
  try:out['date']=date.fromisoformat(r.get('date',''))
  except (TypeError,ValueError):raise ValueError(f'รายการ {i}: วันที่ไม่ถูกต้อง')
  for key,label in AMOUNTS:
   if key in ['balanceBefore','balanceAfter']:continue
   try:
    n=Decimal(str(r.get(key,'')))
    if not n.is_finite() or abs(n)>Decimal('999999999999.99'):raise ValueError()
    if key not in ['balanceBefore','balanceAfter'] and n<0:raise ValueError()
    out[key]=n.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
   except (ValueError,InvalidOperation):raise ValueError(f'รายการ {i}: กรุณาตรวจจำนวนเงิน {label}')
  out['balanceBefore']=out['approved']-out['paid']
  out['balanceAfter']=out['balanceBefore']-out['payment']
  result.append(out)
 return result

def validate_images(images):
 if not isinstance(images,list) or len(images)>3:raise ValueError('แนบรูปได้สูงสุด 3 รูป')
 result=[]
 for value in images:
  try:
   if not isinstance(value,str) or not value.startswith('data:image/jpeg;base64,') or len(value)>3000000:raise ValueError()
   raw=base64.b64decode(value.split(',',1)[1],validate=True)
   with Image.open(BytesIO(raw)) as im:
    if im.format!='JPEG' or max(im.size)>1800:raise ValueError()
    im.verify()
   result.append(raw)
  except Exception:raise ValueError('รูปภาพไม่ถูกต้อง กรุณาเลือกรูปใหม่')
 return result

def render(rows,images=None):
 if 'BudgetThai' not in pdfmetrics.getRegisteredFontNames():
  pdfmetrics.registerFont(TTFont('BudgetThai','C:/Windows/Fonts/THSarabun.ttf'))
  pdfmetrics.registerFont(TTFont('BudgetThaiBold','C:/Windows/Fonts/THSarabun Bold.ttf'))
 output=BytesIO();c=canvas.Canvas(output,pagesize=A4)
 c.setTitle('ใบตัดงบทำการ')
 pagew,pageh=A4;margin=25;gapx=14;gapy=14;w=(pagew-2*margin-gapx)/2;h=(pageh-2*margin-2*gapy)/3
 def text(x,y,value,size=13,bold=False,width=None):
  font='BudgetThaiBold' if bold else 'BudgetThai';value=str(value)
  if width:
   while pdfmetrics.stringWidth(value,font,size)>width and size>9:size-=.25
  c.setFont(font,size);c.drawString(x,y,value)
 def wrapped(value,width,size=13):
  lines=['']
  for ch in value:
   if pdfmetrics.stringWidth(lines[-1]+ch,'BudgetThai',size)>width:lines.append('')
   lines[-1]+=ch
  return lines
 images=images or []
 entries=[('row',r) for r in rows]+[('image',(i,raw)) for i,raw in enumerate(images)]
 for index,(kind,r) in enumerate(entries):
  slot=(index+(1 if len(rows)==1 and kind=='image' else 0))%6
  if index and slot==0:c.showPage()
  x=margin+(slot%2)*(w+gapx);top=pageh-margin-(slot//2)*(h+gapy)
  if len(rows)==1 and kind=='row':x=(pagew-w)/2
  if kind=='image':
   number,raw=r;picture=ImageReader(BytesIO(raw));iw,ih=picture.getSize()
   # Long side 8 cm, preserving the original aspect ratio.
   scale=(8*72/2.54)/max(iw,ih);dw,dh=iw*scale,ih*scale
   y=top-(h-dh-16)/2-dh
   c.drawImage(picture,x+(w-dw)/2,y,width=dw,height=dh)
   c.setFont('BudgetThai',12);c.drawCentredString(x+w/2,y-15,'รูปประกอบที่ '+str(number+1))
   continue
  bottom=top-h
  c.drawImage(str(Path(__file__).with_name('budget-logo.png')),x+w/2-30,top-49,width=60,height=49,mask='auto')
  c.setFont('BudgetThai',14);c.drawCentredString(x+w/2,top-61,'ใบตัดงบ')
  desc_size=12
  while len(wrapped(r['description'],w-16,desc_size))>2 and desc_size>9:desc_size-=.25
  lines=wrapped(r['description'],w-16,desc_size)
  if len(lines)>2:raise ValueError('รายละเอียดรายการยาวเกินพื้นที่ใบตัดงบ กรุณาย่อข้อความ')
  c.setFont('BudgetThai',desc_size)
  for j,line in enumerate(lines):c.drawCentredString(x+w/2,top-73-j*11,line)
  box_top=top-89
  c.setLineWidth(.65);c.rect(x,bottom,w,box_top-bottom)
  def dotted(left,right,y):
   c.saveState();c.setLineWidth(.35);c.setDash(1,1.5);c.line(left,y,right,y);c.restoreState()
  def centered_value(left,right,y,value,size=12):
   value=str(value)
   while pdfmetrics.stringWidth(value,'BudgetThai',size)>right-left and size>8:size-=.25
   c.setFont('BudgetThai',size);c.drawCentredString((left+right)/2,y,value);dotted(left,right,y-2)
  y=box_top-15;d=r['date']
  text(x+5,y,'วันที่',12);centered_value(x+30,x+72,y,d.day)
  text(x+76,y,'เดือน',12);centered_value(x+101,x+176,y,MONTHS[d.month-1])
  text(x+180,y,'พ.ศ.',12);centered_value(x+202,x+w-10,y,d.year+543)
  y-=12;text(x+5,y,'แผนก',12);centered_value(x+37,x+100,y,r['department'])
  text(x+108,y,'รหัสบัญชี',12);centered_value(x+153,x+w-10,y,r['accountCode'])
  if r['orderNumber']:
   y-=12;text(x+5,y,'หมายเลขใบสั่ง',12);centered_value(x+80,x+w-10,y,r['orderNumber'])
  y-=12;text(x+5,y,'บัญชี',12);centered_value(x+35,x+w-10,y,r['accountName'])
  for key,label in AMOUNTS:
   y-=12;text(x+5,y,label,12)
   centered_value(x+84,x+w-42,y,f'{r[key]:,.2f}');text(x+w-34,y,'บาท',12)
  signature_y=bottom+32
  text(x+27,signature_y,'ลงชื่อ',12);dotted(x+62,x+w-70,signature_y-2);text(x+w-67,signature_y,'ผู้ควบคุมงบ',12)
  def signature_center(value,y):
   size=11
   while pdfmetrics.stringWidth(value,'BudgetThai',size)>w-18 and size>8:size-=.25
   c.setFont('BudgetThai',size);c.drawCentredString(x+w/2,y,value)
  signature_center('('+r['controller']['name']+')',bottom+18)
  signature_center(r['controller']['position'],bottom+6)

 c.showPage()
 c.save();return output.getvalue()
