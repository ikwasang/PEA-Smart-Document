"""Configured Google Sheets budgets, atomically refreshed as one dataset."""
import json,threading,re,uuid,time
from urllib.request import urlopen,Request
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import master_admin
DEFAULTS={'I':'https://docs.google.com/spreadsheets/d/1aLDUeD14j5WLJxbI3KDSmgL2pJXqd0uHtDj676s65ng/edit','C':'https://docs.google.com/spreadsheets/d/1_GcTn1xtkWl3MJ4MB4R4wA6AUloCmk0s--kuYgIkTmA/edit'}
SYNC_LOCK=threading.Lock()
TOKENS={}
def normalize(url):
 m=re.fullmatch(r'https://docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]+)(?:/[^\s]*)?',str(url).strip())
 if not m:raise ValueError('กรุณาใช้ลิงก์ Google Sheets ที่ถูกต้อง')
 return 'https://docs.google.com/spreadsheets/d/'+m[1]+'/edit'
def config(root):
 p=root/'local-data/budget-sources.json'
 return json.loads(p.read_text(encoding='utf-8')) if p.exists() else DEFAULTS.copy()
def save_config(root,data):
 new={k:normalize(data.get(k,'')) for k in DEFAULTS}
 if new['I']==new['C']:raise ValueError('งบ I และ C ต้องเป็นคนละชีต')
 with SYNC_LOCK:
  p=root/'local-data/budget-sources.json';p.parent.mkdir(exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(new,ensure_ascii=False),encoding='utf-8');t.replace(p);TOKENS.clear()
 return new
def authorized(token):return TOKENS.get(token,0)>time.time()
def download(item):
 kind,url=item
 try:
  with urlopen(Request(url.rsplit('/edit',1)[0]+'/export?format=xlsx',headers={'User-Agent':'PEA-Smart-Document'}),timeout=30) as response:raw=response.read(15*1024*1024+1)
 except Exception as e:raise ValueError('เชื่อมต่อ Google Sheets งบ '+kind+' ไม่สำเร็จ กรุณาตรวจอินเทอร์เน็ตและสิทธิ์อ่านชีต') from e
 if len(raw)>15*1024*1024:raise ValueError('ไฟล์ใหญ่เกิน 15 MB')
 changes,warnings=master_admin.parse_excel('budgets',raw)
 files=changes['budgetFiles']
 if any(not f['code'].startswith(kind+'-') for f in files):raise ValueError('ลิงก์งบ '+kind+' มีรหัสงานผิดประเภท กรุณาตรวจลิงก์')
 for f in files:f['fundType']=kind
 return files,warnings
def sync(root):
 with SYNC_LOCK:
  sources=config(root)
  with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(download,sources.items()))
  files=[f for group,w in results for f in group];warnings=[w for group,ws in results for w in ws]
  with master_admin.LOCK:
   path=root/'master-data.json';original=path.read_bytes();data=json.loads(original);data['budgetFiles']=files
   now=datetime.now(timezone.utc).isoformat();data.setdefault('updates',{})['budgets']={'filename':'Google Sheets งบ I และ C','updatedAt':now};data['budgetWarnings']=warnings
   backup=root/'local-data/master-backups';backup.mkdir(parents=True,exist_ok=True);(backup/(datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json')).write_bytes(original)
   temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(path)
  for t in list(TOKENS):
   if TOKENS[t]<time.time():del TOKENS[t]
  token=uuid.uuid4().hex;TOKENS[token]=time.time()+12*3600
  return {'data':data,'updatedAt':now,'counts':master_admin.counts(data),'warnings':warnings,'token':token}
