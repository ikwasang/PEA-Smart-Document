from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
import threading
import io
from PIL import Image
import json,subprocess,os,tempfile,uuid,base64
from urllib.parse import quote,unquote
import master_admin
import budget_pdf
import project_budget
import budget_sync
import access

FORM_DOWNLOADS={
 'supervisor.docx':'บันทึกผู้ควบคุมงานจ้าง.docx',
 'acceptance.docx':'บันทึกตรวจรับงานจ้าง.docx',
 'conditions.pdf':'เงื่อนไขประกอบใบสั่งจ้าง.pdf',
 'bank-payment.pdf':'แบบคำขอรับเงินผ่านธนาคาร.pdf',
 'electronic-transfer.pdf':'หนังสือแจ้งความประสงค์ขอรับเงินโอนอิเล็กทรอนิกส์.pdf',
 'electronic-transfer-example.pdf':'ตัวอย่างหนังสือแจ้งความประสงค์ขอรับเงินโอนอิเล็กทรอนิกส์.pdf'
}

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
DRAFT_LOCK=threading.Lock()
DRAFT=ROOT/'local-data'/'current-draft.json'
PYTHON='C:/Users/513635/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
def cents(v):
 d=Decimal(str(v))
 if not d.is_finite() or d<0:raise ValueError('จำนวนเงินต้องไม่ติดลบ')
 return int((d*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
def validate(d):
 kind=d.get('documentType','purchase')
 if kind not in ['purchase','hiring']:raise ValueError('ประเภทเอกสารไม่ถูกต้อง')
 if kind=='hiring' and (not isinstance(d.get('supervisor'),str) or not d['supervisor'].strip() or len(d['supervisor'])>40):raise ValueError('กรุณาระบุผู้ควบคุมงาน')
 rows=d.get('items',[])
 if not isinstance(rows,list) or not rows:raise ValueError('กรุณาเพิ่มรายการพัสดุ')
 sub=vat=0
 for row in rows:
  if not str(row['name']).strip() or len(row['name'])>45:raise ValueError('ชื่อรายการต้องมี 1–45 ตัวอักษร')
  q=Decimal(str(row['qty']))
  if not q.is_finite() or q<=0 or q>999:raise ValueError('จำนวนต้องมากกว่า 0 และไม่เกิน 999')
  price=cents(row['price']);rowvat=cents(row['vat'])
  sub+=int((q*price).quantize(Decimal('1'),rounding=ROUND_HALF_UP));vat+=rowvat
 if sub+vat>1000000:raise ValueError('ยอดรวมเกิน 10,000 บาท ขอบเขตของรุ่นแรก')
 required=['department','description','reason','vendor','chair','officer','approver','receiver']
 for k in required:
  if not str(d.get(k,'')).strip():raise ValueError('กรุณากรอกข้อมูลให้ครบ')
  if len(str(d[k]))>100:raise ValueError('ข้อความยาวเกินขอบเขตตัวอย่าง')
 if d['department'] not in ['ผปร.','ผบค.','ผบง.']:raise ValueError('แผนกไม่ถูกต้อง')
 for k in ['member1','member2']:
  d[k]=str(d.get(k,'')).strip()
  if len(d[k])>40:raise ValueError('ชื่อกรรมการยาวเกินไป')
 committee=[d[k].strip() for k in ['chair','member1','member2'] if d[k].strip()]
 if len(set(committee))!=len(committee):raise ValueError('ประธานและกรรมการต้องไม่ซ้ำกัน')
 if not 1<=int(d.get('days',0))<=365:raise ValueError('วันส่งมอบต้องอยู่ระหว่าง 1–365')
 budgets=d.get('budgets',[])
 if not isinstance(budgets,list) or not 1<=len(budgets)<=len(rows):raise ValueError('จำนวนรายการงบไม่ถูกต้อง')
 used=[]
 for b in budgets:
  if b.get('type') not in ['งบทำการ','งบแฟ้มงาน']:raise ValueError('ประเภทงบไม่ถูกต้อง')
  keys=['account','costCenter']+(['budgetFile','network','expense'] if b['type']=='งบแฟ้มงาน' else [])
  for k in keys:
   if not str(b.get(k,'')).strip() or len(str(b[k]))>200:raise ValueError('กรุณากรอกข้อมูลงบให้ครบและไม่ยาวเกินไป')
  ix=b.get('itemIndices',[])
  if not isinstance(ix,list) or not ix or any(type(i)!=int or i<0 or i>=len(rows) for i in ix):raise ValueError('กรุณาเลือกสินค้าในแต่ละงบ')
  used.extend(ix)
 if sorted(used)!=list(range(len(rows))):raise ValueError('สินค้าแต่ละรายการต้องอยู่ในงบเดียว และเลือกให้ครบ')
 for k in ['costCenter','budgetFile','network','expense','account']:d[k]=str(budgets[0].get(k,''))
 images=d.get('images',[])
 if not isinstance(images,list) or len(images)>3:raise ValueError('ใส่รูปได้สูงสุด 3 รูป')
 for value in images:
  if not isinstance(value,str) or not value.startswith('data:image/jpeg;base64,') or len(value)>3000000:raise ValueError('รูปภาพไม่ถูกต้องหรือใหญ่เกินไป')
  try:
   raw=base64.b64decode(value.split(',',1)[1],validate=True)
   with Image.open(io.BytesIO(raw)) as im:
    if im.format!='JPEG' or max(im.size)>1200:raise ValueError('ขนาดรูปไม่ถูกต้อง')
    im.verify()
  except Exception:raise ValueError('อ่านรูปภาพไม่ได้ กรุณาเลือกรูปใหม่')
 return sub,vat
class Handler(BaseHTTPRequestHandler):
 def gate(self):
  self.user=None
  try:c=access.config()
  except (ValueError,OSError):self.send(503,{'error':'การตั้งค่าบัญชียังไม่พร้อม'});return False
  self.access_config=c
  if self.path in ['/login','/account.js','/api/access/config','/api/access/login','/style.css','/font.ttf']:return True
  if not c:
   if self.headers.get('Host') not in ['127.0.0.1:8765','localhost:8765'] or self.headers.get('X-Forwarded-For'):
    self.send(503,{'error':'ยังไม่ได้เปิดระบบหลายผู้ใช้'});return False
   self.user={'id':'local','name':'ใช้งานบนเครื่องนี้','email':'','role':'admin'}
   return True
  self.user=access.current(self.headers)
  if not self.user:
   if self.command=='GET' and self.path in ['/','/budget','/project-budget','/admin','/history']:
    self.send_response(303);self.send_header('Location','/login');self.end_headers()
   else:self.send(401,{'error':'กรุณาเข้าสู่ระบบ'})
   return False
  if (self.path.startswith('/api/admin/') or self.path in ['/admin','/admin.js']) and self.user['role']!='admin':
   self.send(403,{'error':'เฉพาะ admin เท่านั้น'});return False
  if not self.user['name'] and self.path not in ['/api/access/me','/api/access/name','/api/access/logout']:
   if self.command=='GET' and self.path in ['/','/budget','/project-budget','/admin','/history']:
    self.send_response(303);self.send_header('Location','/login');self.end_headers()
   else:self.send(403,{'error':'กรุณาตั้งชื่อก่อนใช้งาน'})
   return False
  return True
 def origin_ok(self):
  expected=self.access_config['origin'].rstrip('/') if self.access_config else 'http://127.0.0.1:8765'
  return self.headers.get('Origin')==expected
 def send(self,status,body,kind='application/json'):
  if status==200 and self.command=='POST' and getattr(self,'user',None):
   action={'/api/budget/pdf':'สร้าง PDF ใบตัดงบทำการ','/api/project-budget/pdf':'สร้าง PDF ใบตัดงบแฟ้มงาน','/api/pdf':'สร้าง PDF '+getattr(self,'document_label','เอกสาร'),'/api/project-budget/sync':'ดึงข้อมูลแฟ้มงานล่าสุด','/api/admin/commit':'อัปเดตข้อมูล Excel','/api/admin/budget-sources':'เปลี่ยนลิงก์ข้อมูลแฟ้มงาน'}.get(self.path)
   if action:access.log(self.user,action)

  if isinstance(body,dict):body=json.dumps(body,ensure_ascii=False).encode()
  self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
 def do_GET(self):
  if not self.gate():return
  if self.path in ['/login','/history','/account.js']:
   filename={'/login':'login.html','/history':'history.html','/account.js':'account.js'}[self.path]
   self.send(200,(ROOT/filename).read_bytes(),'text/javascript; charset=utf-8' if filename.endswith('.js') else 'text/html; charset=utf-8');return
  if self.path=='/api/access/config':
   self.send(200,{'configured':bool(self.access_config),'clientId':self.access_config['clientId'] if self.access_config else ''});return
  if self.path=='/api/access/me':self.send(200,{'user':self.user,'configured':bool(self.access_config)});return
  if self.path=='/api/access/history':self.send(200,{'events':access.history(self.user)});return

  if self.path=='/api/admin/access-users':
   c=access.config();self.send(200,{'admins':c['admins'] if c else [],'users':c.get('users',[]) if c else []});return
  if self.path=='/api/admin/budget-sources':self.send(200,budget_sync.config(ROOT));return
  if self.path=='/sync-gate.js':self.send(200,(ROOT/'sync-gate.js').read_bytes(),'text/javascript; charset=utf-8');return
  if self.path in ['/project-budget','/project-budget.js']:
   filename,kind=('project-budget.html','text/html; charset=utf-8') if self.path=='/project-budget' else ('project-budget.js','text/javascript; charset=utf-8')
   self.send(200,(ROOT/filename).read_bytes(),kind);return
  if self.path in ['/budget','/budget.js']:
   filename,kind=('budget.html','text/html; charset=utf-8') if self.path=='/budget' else ('budget.js','text/javascript; charset=utf-8')
   self.send(200,(ROOT/filename).read_bytes(),kind);return
  if self.path in ['/admin','/admin.js']:
   filename,kind=('admin.html','text/html; charset=utf-8') if self.path=='/admin' else ('admin.js','text/javascript; charset=utf-8')
   self.send(200,(ROOT/filename).read_bytes(),kind);return
  if self.path.startswith('/forms/'):
   name=self.path[len('/forms/'):]
   if name not in FORM_DOWNLOADS or not (ROOT/'forms'/name).is_file():self.send(404,{'error':'ไม่พบแบบฟอร์ม'});return
   body=(ROOT/'forms'/name).read_bytes()
   self.send_response(200)
   self.send_header('Content-Type','application/pdf' if name.endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
   self.send_header('Content-Disposition',"attachment; filename*=UTF-8''"+quote(FORM_DOWNLOADS[name]))
   self.send_header('Content-Length',str(len(body)))
   self.send_header('X-Content-Type-Options','nosniff')
   self.end_headers();self.wfile.write(body);return
  if self.path=='/api/draft':
   with DRAFT_LOCK:
    body=access.draft(self.user).read_bytes() if access.draft(self.user).exists() else b'null'
   self.send(200,body);return
  files={'/hiring-ui.js':ROOT/'hiring-ui.js','/master-data.json':ROOT/'master-data.json','/':ROOT/'index.html','/app.js':ROOT/'app.js','/style.css':ROOT/'style.css','/font.ttf':Path('C:/Windows/Fonts/THSarabun.ttf'),'/logo.jpg':WORK/'template-review/image1.jpeg'}
  if self.path not in files:self.send(404,{'error':'ไม่พบหน้า'});return
  mime={'/hiring-ui.js':'text/javascript; charset=utf-8','/master-data.json':'application/json; charset=utf-8','/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8','/font.ttf':'font/ttf','/logo.jpg':'image/jpeg'}
  self.send(200,files[self.path].read_bytes(),mime[self.path])
 def do_POST(self):
  if not self.gate():return
  if not self.origin_ok():self.send(403,{'error':'ต้นทางไม่ถูกต้อง'});return
  if self.path.startswith('/api/access/'):
   try:
    n=int(self.headers.get('Content-Length','0'))
    if not 0<n<20000:raise ValueError('ข้อมูลไม่ถูกต้อง')
    data=json.loads(self.rfile.read(n))
    if self.path=='/api/access/login':
     token,user=access.login(data.get('credential',''))
     self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store')
     secure='; Secure' if self.access_config['origin'].startswith('https://') else ''
     self.send_header('Set-Cookie','psdp_session='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200'+secure)
     self.end_headers();self.wfile.write(json.dumps({'user':user}).encode());return
    if self.user['id']=='local':raise ValueError('กรุณาเชื่อมบัญชี Google ก่อน')
    if self.path=='/api/access/name':access.rename(self.user,data.get('name'))
    elif self.path=='/api/access/logout':access.logout(self.headers,self.user)
    elif self.path=='/api/access/event':
     events={'purchase':'เปิดเอกสารจัดซื้อ','hiring':'เปิดเอกสารจัดจ้าง','budget':'เปิดใบตัดงบทำการ','project-budget':'เปิดใบตัดงบแฟ้มงาน','print':'เปิดหน้าต่างพิมพ์เอกสาร','download':'กดดาวน์โหลด PDF'}
     if data.get('event') not in events:raise ValueError('กิจกรรมไม่ถูกต้อง')
     access.log(self.user,events[data['event']])
    else:self.send(404,{'error':'ไม่พบคำสั่ง'});return
    self.send(200,{'ok':True})
   except (ValueError,TypeError):self.send(400,{'error':'ดำเนินการไม่ได้ กรุณาตรวจบัญชีที่ได้รับสิทธิ์ หรือเข้าสู่ระบบใหม่'})
   return

  if self.path=='/api/admin/access-users':
   try:
    n=int(self.headers.get('Content-Length','0'))
    if not 0<n<10000:raise ValueError('ข้อมูลไม่ถูกต้อง')
    if not self.access_config:raise ValueError('ยังไม่ได้เชื่อม Google Login')
    access.update_users(self.user,json.loads(self.rfile.read(n)).get('users'))
    self.send(200,{'ok':True})
   except (ValueError,TypeError) as e:self.send(400,{'error':str(e)})
   return
  if self.path=='/api/admin/budget-sources':
   if not self.origin_ok():self.send(403,{'error':'ต้นทางไม่ถูกต้อง'});return
   try:
    n=int(self.headers.get('Content-Length','0'))
    if not 0<n<10000:raise ValueError('ข้อมูลไม่ถูกต้อง')
    self.send(200,budget_sync.save_config(ROOT,json.loads(self.rfile.read(n))))
   except (ValueError,TypeError) as e:self.send(400,{'error':str(e)})
   return
  if self.path in ['/api/pdf','/api/project-budget/pdf'] and not budget_sync.authorized(self.headers.get('X-Budget-Sync','')):
   self.send(403,{'error':'กรุณากดดึงข้อมูลแฟ้มงานล่าสุดก่อนสร้างเอกสาร'});return
  if self.path=='/api/admin/preview/budgets':self.send(400,{'error':'ข้อมูลแฟ้มงานใช้ Google Sheets เท่านั้น กรุณาแก้ลิงก์หลังบ้าน'});return
  if self.path=='/api/project-budget/sync':
   if not self.origin_ok():self.send(403,{'error':'ต้นทางไม่ถูกต้อง'});return
   try:self.send(200,budget_sync.sync(ROOT))
   except ValueError as e:self.send(400,{'error':str(e)})
   except Exception:self.send(400,{'error':'อ่านรูปแบบ Google Sheets ไม่สำเร็จ ข้อมูลเดิมยังอยู่ กรุณาตรวจไฟล์ต้นทาง'})
   return
  if self.path in ['/api/budget/pdf','/api/project-budget/pdf']:
   if not self.origin_ok():self.send(403,{'error':'ต้นทางไม่ถูกต้อง'});return
   try:
    n=int(self.headers.get('Content-Length','0'))
    if not 0<n<=9500000:raise ValueError('ข้อมูลมีขนาดไม่ถูกต้อง')
    payload=json.loads(self.rfile.read(n))
    master=json.loads((ROOT/'master-data.json').read_text(encoding='utf-8'))
    if self.path=='/api/project-budget/pdf':pdf=project_budget.render(project_budget.validate(payload,master))
    else:
     rows=budget_pdf.validate(payload,master)
     images=budget_pdf.validate_images(payload.get('images',[]))
     pdf=budget_pdf.render(rows,images)
    folder=ROOT/'tmp'/uuid.uuid4().hex;folder.mkdir()
    try:
     out=Path(folder)/'budget.pdf';out.write_bytes(pdf)
     process=subprocess.run(['C:/Users/513635/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe','-scale-to','1800','-png',str(out),str(Path(folder)/'page')],capture_output=True,timeout=60)
     if process.returncode:raise RuntimeError('สร้างตัวอย่างไม่สำเร็จ')
     pages=[base64.b64encode(p.read_bytes()).decode() for p in sorted(Path(folder).glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]))]
    finally:
     for artifact in folder.iterdir():artifact.unlink()
     folder.rmdir()
    self.send(200,{'pdf':base64.b64encode(pdf).decode(),'pages':pages})
   except (ValueError,TypeError) as e:self.send(400,{'error':str(e)})
   except Exception:self.send(500,{'error':'สร้างตัวอย่างไม่ได้ กรุณาลองใหม่'})
   return
  if self.path.startswith('/api/admin/'):
   if not self.origin_ok():self.send(403,{'error':'กรุณาเปิดหน้าจัดการข้อมูลจากเครื่องนี้'});return
   try:
    n=int(self.headers.get('Content-Length','0'))
    if not 0<n<=15*1024*1024:raise ValueError('ขนาดไฟล์ต้องไม่เกิน 15 MB')
    raw=self.rfile.read(n)
    if self.path.startswith('/api/admin/preview/'):
     kind=self.path.rsplit('/',1)[-1];filename=unquote(self.headers.get('X-File-Name','Excel.xlsx'))
     result=master_admin.preview(ROOT,kind,raw,filename)
    elif self.path=='/api/admin/commit':result=master_admin.commit(ROOT,json.loads(raw).get('token',''))
    else:self.send(404,{'error':'ไม่พบคำสั่ง'});return
    self.send(200,result)
   except ValueError as e:self.send(400,{'error':str(e)})
   except Exception:self.send(400,{'error':'ดำเนินการไม่สำเร็จ กรุณาตรวจว่าเป็นไฟล์ .xlsx ตามต้นแบบ หรือเปิดไฟล์แล้วบันทึกใหม่ใน Excel'})
   return
  if self.path not in ['/api/pdf','/api/draft']:self.send(404,{'error':'ไม่พบคำสั่ง'});return
  origin=self.headers.get('Origin','')
  if not self.origin_ok():self.send(403,{'error':'ต้นทางไม่ถูกต้อง'});return
  try:
   n=int(self.headers.get('Content-Length','0'))
   if n<=0 or n>9500000:raise ValueError('ข้อมูลมีขนาดไม่ถูกต้อง')
   d=json.loads(self.rfile.read(n))
   if self.path=='/api/draft':
    if not isinstance(d,dict) or d.get('schema')!=1 or not isinstance(d.get('fields'),dict) or not isinstance(d.get('items'),list) or not len(d['items'])>=1 or not isinstance(d.get('budgets'),list) or not len(d['budgets'])>=1 or not isinstance(d.get('photos'),list) or len(d['photos'])>3:raise ValueError('รูปแบบร่างไม่ถูกต้อง')
    DRAFT=access.draft(self.user)
    with DRAFT_LOCK:
     DRAFT.parent.mkdir(exist_ok=True)
     pending=DRAFT.with_suffix('.tmp');pending.write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8');pending.replace(DRAFT)
    self.send(200,{'saved':True});return
   sub,vat=validate(d)
   self.document_label='เอกสารจัดจ้าง' if d.get('documentType')=='hiring' else 'เอกสารจัดซื้อ'
   from contextlib import nullcontext
   temp=ROOT/'tmp'/uuid.uuid4().hex;temp.mkdir()
   with nullcontext(temp):
    data=Path(temp)/'data.json';data.write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8')
    out=Path(temp)/'document.pdf';env=os.environ.copy();env['PSDP_DATA']=str(data);env['PSDP_PDF']=str(out)
    job=subprocess.run([PYTHON,str(WORK/'template-review/refine_pdf.py')],cwd=WORK,env=env,capture_output=True,timeout=180)
    if job.returncode or not out.exists():
     print(job.stderr.decode('utf-8',errors='replace'),flush=True)
     raise RuntimeError('สร้าง PDF ไม่สำเร็จ กรุณาลองใหม่')
    render=subprocess.run(['C:/Users/513635/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe','-scale-to','1800','-png',str(out),str(temp/'page')],capture_output=True,timeout=180)
    if render.returncode:raise RuntimeError('Preview failed')
    self.send(200,{'pdf':base64.b64encode(out.read_bytes()).decode(),'pages':[base64.b64encode(f.read_bytes()).decode() for f in sorted(temp.glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]))]})
    for f in temp.iterdir():f.unlink()
    temp.rmdir()
  except (ValueError,KeyError,TypeError,ArithmeticError) as e:self.send(400,{'error':str(e)})
  except Exception:self.send(500,{'error':'สร้าง PDF ไม่สำเร็จ กรุณาตรวจข้อมูลหรือลองใหม่'})
 def log_message(self,*args):pass
if __name__=='__main__':
 (ROOT/'tmp').mkdir(exist_ok=True)
 print('PSDP prototype: http://127.0.0.1:8765',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()

